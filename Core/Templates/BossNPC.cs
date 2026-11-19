using System;
using Cogpunk.Core.UI;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Core.Templates
{
	/// <summary>
	/// Base for Cogpunk bosses, which all get a themed death cinematic (art direction 2026-10-26): instead of vanishing on
	/// the killing blow, the boss enters its <see cref="DyingState"/>, can no longer hurt or be hurt, plays its death for
	/// <see cref="DeathAnimationTicks"/> (locking the camera with <c>Core/Visuals/CinematicCamera</c>) and only then dies
	/// for real, dropping its loot and running <c>OnKill</c>.
	/// <para>How it works (decompiled <c>NPC.checkDead</c>: <c>NPCLoader.CheckDead</c> runs before the loot and before
	/// <c>active = false</c>; Moon Lord's core uses the same trick): <see cref="CheckDead"/> refuses the death, puts life
	/// back to 1 and switches to the dying state (server or singleplayer; the state is synced through <c>ai[0]</c>).
	/// When the animation ends, <see cref="UpdateDeath"/> finishes it on the server with <c>NPC.StrikeInstantKill</c>
	/// (sent to clients as a strike), and <see cref="CheckDead"/> lets that one through. A client whose copy is still a
	/// few ticks behind accepts it too (<see cref="FinishGrace"/>), and the server follows the kill with a SyncNPC so no
	/// client keeps a ghost (D2).</para>
	/// <para><b>Defeat card</b> (user rule, 2026-10-26): every boss's death shows the same card, its name and "Defeated"
	/// and nothing else (<see cref="BossTitleSystem.ShowDefeated"/>), at <see cref="DefeatCardTick"/> for players within
	/// <see cref="DefeatCardRange"/>.</para>
	/// <para><b>No natural spawns during a boss fight</b> (user rule, 2026-10-26): every living boss reports itself each
	/// tick (<see cref="IsFightNear"/>), and <c>Core/Systems/BossFightSpawnRule</c> stops natural spawns for players
	/// within <see cref="SpawnBlockRange"/> of it. Minions a boss spawns itself are not natural spawns and still appear.</para>
	/// <para><b>Targeting</b> (user rule, 2026-11-09: "they should target the most damaging player (dps) and change target
	/// every 5 seconds (can't choose the same target)"): the server credits every hit to the player who struck it
	/// (<see cref="HitEffect"/>: vanilla sets <c>lastInteraction</c> to the attacker just before the strike, decompiled
	/// <c>MessageBuffer</c> case 28 and <c>NPC.StrikeNPC</c>), lets the totals fade (<see cref="DamageDecay"/> every
	/// <see cref="DamageDecayInterval"/> ticks: a running DPS that halves in about 3 s), and every
	/// <see cref="TargetSwitchTicks"/> ticks switches to the top damage dealer among the <i>other</i> players a boss may target
	/// (<see cref="CanTarget"/>; ties, as before anyone has hurt it, go to <see cref="TargetTieBreak"/>: the closest by
	/// default). Alone, a player stays the target. A target that dies or leaves is replaced at once (the clock restarts).
	/// Bosses never pick their own target any more: where they used to retarget they call <see cref="EnsureTarget"/>.
	/// <b>Floaty bosses</b> (<see cref="Floaty"/>, the Cursed Conductor) keep within the Blade of Grass's reach of a target
	/// that fights in melee (<see cref="Combat.MeleeFocus"/>, same rule).</para>
	/// <para><b>Floaty bosses drift</b> (user rule, 2026-11-17: "they should not cause contact damage unless specified and should
	/// move from left to right up and down slowly during the fight targeting the players to facilitate melee combat (and so
	/// they feel more alive instead of a perfect lock on that follows the player instantaneously)"): a floaty boss never hurts by
	/// touch unless it says so (<see cref="FloatyContactDamage"/>, checked in <see cref="CanHitPlayer"/>), hovers round a point
	/// that follows its target with a lag (<see cref="FloatFocus"/>: <see cref="FocusFollow"/> of the way a tick, so a running
	/// player gets ahead of it) and sways round its hover spot on a slow figure of eight (<see cref="DriftSway"/>,
	/// <see cref="DriftBob"/>: side to side over <see cref="DriftPeriodX"/> ticks, up and down over <see cref="DriftPeriodY"/>),
	/// the amplitudes the boss's own (small in its melee hover, so a melee fighter keeps it in reach). D2: the clock that drives
	/// the sway (<see cref="DriftClock"/>) counts on every side and rides the boss's own ExtraAI (<see cref="WriteDrift"/>,
	/// <see cref="ReadDrift"/>), so every side sways the same; the focus follows the synced players.</para>
	/// <para>D0: nothing here loops past a fixed bound or spawns; a boss that is already dying ignores further lethal hits.
	/// D2: the server decides the target and syncs <c>NPC.target</c> (vanilla's SyncNPC) only when it changes. D1: the damage
	/// table is one array per boss, made on its first hit (a ModNPC clone shares fields set on its template).</para>
	/// </summary>
	public abstract class BossNPC : StateMachineNPC
	{
		/// <summary>Ticks before the end of the animation in which a client accepts the server's finishing strike.</summary>
		public const int FinishGrace = 30;

		/// <summary>Natural spawns stop for players this close to a living Cogpunk boss.</summary>
		public const float SpawnBlockRange = 300f * 16f;

		public const float DefeatCardRange = 150f * 16f;
		public const int DefeatCardHold = 90;

		private const int MaxTrackedFights = 4;
		private static readonly Vector2[] fightPosition = new Vector2[MaxTrackedFights];
		private static readonly uint[] fightTick = new uint[MaxTrackedFights];
		private static readonly int[] fightNpc = { -1, -1, -1, -1 };

		/// <summary>Ticks between target switches (user-set 2026-11-09: every 5 s).</summary>
		public const int TargetSwitchTicks = 300;

		/// <summary>Recent damage fades by <see cref="DamageDecay"/> every this many ticks.</summary>
		public const int DamageDecayInterval = 30;

		/// <summary>0.891 every half second: recent damage halves in about 3 s (a running DPS).</summary>
		public const float DamageDecay = 0.891f;

		private bool finishing;
		private bool defeatCardShown;
		private float[] damageBy;                          // server: recent damage per player
		private int targetTicks;                           // server: ticks on the current target

		/// <summary>The state index of the death cinematic.</summary>
		protected abstract int DyingState { get; }

		/// <summary>Length of the death cinematic in ticks.</summary>
		protected abstract int DeathAnimationTicks { get; }

		/// <summary>When the defeat card appears (ticks into the death); by default a second before the end.</summary>
		protected virtual int DefeatCardTick => DeathAnimationTicks - 60;

		public bool IsDying => State == DyingState;

		/// <summary>The boss's own per-tick logic (every side), called by the sealed <see cref="UpdateState"/>.</summary>
		protected abstract void UpdateBoss();

		/// <summary>A boss that floats at a distance from its target (the Cursed Conductor): it must come within the Blade of
		/// Grass's reach of a target that fights in melee (user rule 2026-11-09; each floaty boss does it in its own
		/// movement, with <see cref="Combat.MeleeFocus"/> and <see cref="Combat.MeleeGear.BladeOfGrassReach"/>).</summary>
		public virtual bool Floaty => false;

		/// <summary>A floaty boss that the user said hurts by touch (none so far): only then does its body deal contact damage.</summary>
		protected virtual bool FloatyContactDamage => false;

		/// <summary>Floaty bosses don't hurt by touch unless <see cref="FloatyContactDamage"/> (user rule, 2026-11-17).</summary>
		public override bool CanHitPlayer(Player target, ref int cooldownSlot) => !Floaty || FloatyContactDamage;

		// --- the floaty bosses' drift (user rule, 2026-11-17) --------------------------------------------------------------

		/// <summary>Ticks for one sway from side to side and back.</summary>
		public const int DriftPeriodX = 420;

		/// <summary>Ticks for one bob up and down (not a divisor of <see cref="DriftPeriodX"/>: the path is a slow figure of eight
		/// that doesn't repeat every few seconds).</summary>
		public const int DriftPeriodY = 270;

		/// <summary>How much of the way to its target the hover's focus moves each tick (about a 10-tick lag).</summary>
		public const float FocusFollow = 0.1f;

		/// <summary>The sway's clock (every side; synced through the boss's ExtraAI).</summary>
		protected int DriftClock;
		private Vector2 focus;
		private int focusTarget = -1;

		/// <summary>-1..1: where the boss is in its side-to-side sway.</summary>
		protected float DriftSway => MathF.Sin(DriftClock * MathHelper.TwoPi / DriftPeriodX);

		/// <summary>-1..1: where the boss is in its bob (a quarter turn ahead of the sway).</summary>
		protected float DriftBob => MathF.Sin(DriftClock * MathHelper.TwoPi / DriftPeriodY + MathHelper.PiOver2);

		/// <summary>Every side, once a tick while the boss floats: the sway's clock.</summary>
		protected void TickDrift() {
			DriftClock = (DriftClock + 1) % (DriftPeriodX * DriftPeriodY);
		}

		/// <summary>The point a floaty boss hovers round: <paramref name="target"/>'s centre, followed <see cref="FocusFollow"/> of the
		/// way a tick (a new target is taken at once).</summary>
		protected Vector2 FloatFocus(Player target) {
			if (target == null) {
				return focus;
			}
			if (focusTarget != target.whoAmI || !float.IsFinite(focus.X) || !float.IsFinite(focus.Y)) {
				focusTarget = target.whoAmI;
				focus = target.Center;
			}
			focus += (target.Center - focus) * FocusFollow;
			return focus;
		}

		protected void WriteDrift(System.IO.BinaryWriter writer) {
			writer.Write((short)Math.Clamp(DriftClock % 30000, 0, short.MaxValue));
		}

		protected void ReadDrift(System.IO.BinaryReader reader) {
			DriftClock = Math.Max(0, (int)reader.ReadInt16());
		}

		protected sealed override void UpdateState() {
			ReportFight();
			UpdateTargeting();
			UpdateBoss();
		}

		/// <summary>Vanilla's hit hook, sealed to credit the hit to its player first (see <see cref="BossHitEffect"/>).</summary>
		public sealed override void HitEffect(NPC.HitInfo hit) {
			CreditHit(hit);
			BossHitEffect(hit);
		}

		/// <summary>The boss's own hit effects (dust, gore, sounds), on every side, after the hit is credited.</summary>
		protected virtual void BossHitEffect(NPC.HitInfo hit) {
		}

		// --- targeting: the top damage dealer, a different one every TargetSwitchTicks ------------------------------------

		/// <summary>Server: may <paramref name="player"/> be the target? By default: alive and within <see cref="TargetRange"/>.</summary>
		protected virtual bool CanTarget(Player player) {
			return player != null && player.active && !player.dead
				&& Vector2.DistanceSquared(player.Center, NPC.Center) <= TargetRange * TargetRange;
		}

		/// <summary>How far a target may be (the default <see cref="CanTarget"/>).</summary>
		protected virtual float TargetRange => 250f * 16f;

		/// <summary>Server: how a player ranks among equal damage (lower first): the distance by default.</summary>
		protected virtual float TargetTieBreak(Player player) => Vector2.DistanceSquared(player.Center, NPC.Center);

		/// <summary>Server: the damage <paramref name="player"/> has done lately (0 on clients).</summary>
		protected float RecentDamage(int player) {
			return damageBy != null && player >= 0 && player < damageBy.Length ? damageBy[player] : 0f;
		}

		private void CreditHit(NPC.HitInfo hit) {
			int who = NPC.lastInteraction;
			if (!IsAuthority || IsDying || hit.Damage <= 0 || who < 0 || who >= Main.maxPlayers) {
				return;
			}
			damageBy ??= new float[Main.maxPlayers];
			damageBy[who] += hit.Damage;
		}

		/// <summary>Server: the player to target: the most recent damage, ties to <see cref="TargetTieBreak"/>; never
		/// <paramref name="exclude"/> (pass -1 to allow anyone). -1 when nobody can be targeted.</summary>
		protected int BestTarget(int exclude) {
			int best = -1;
			float bestDamage = -1f, bestTie = float.MaxValue;
			foreach (Player player in Main.ActivePlayers) {
				if (player.whoAmI == exclude || !CanTarget(player)) {
					continue;
				}
				float hurt = RecentDamage(player.whoAmI);
				float tie = TargetTieBreak(player);
				if (hurt > bestDamage + 0.5f || (Math.Abs(hurt - bestDamage) <= 0.5f && tie < bestTie)) {
					best = player.whoAmI;
					bestDamage = hurt;
					bestTie = tie;
				}
			}
			return best;
		}

		/// <summary>The synced target when it is a living, active player (every side), else null.</summary>
		protected Player CurrentTarget => NPC.target >= 0 && NPC.target < Main.maxPlayers && Main.player[NPC.target].active
			&& !Main.player[NPC.target].dead ? Main.player[NPC.target] : null;

		/// <summary>Server: keeps a valid target: the current one while <see cref="CanTarget"/> holds, else the best one now.
		/// False when there is nobody to target (the boss leaves, retreats or waits). True on clients.</summary>
		protected bool EnsureTarget() {
			if (!IsAuthority) {
				return true;
			}
			Player current = CurrentTarget;
			if (current != null && CanTarget(current)) {
				return true;
			}
			int best = BestTarget(-1);
			if (best < 0) {
				return false;
			}
			SetTarget(best);
			return true;
		}

		private void SetTarget(int player) {
			targetTicks = 0;
			if (NPC.target != player) {
				NPC.target = player;
				NPC.netUpdate = true;
			}
		}

		/// <summary>Server, every tick: the damage fades; a lost target is replaced at once; every
		/// <see cref="TargetSwitchTicks"/> the target becomes the top damage dealer among the others (alone, the same).</summary>
		private void UpdateTargeting() {
			if (!IsAuthority || IsDying) {
				return;
			}
			if (damageBy != null && Main.GameUpdateCount % DamageDecayInterval == 0) {
				for (int i = 0; i < damageBy.Length; i++) {
					Player player = Main.player[i];
					damageBy[i] = player.active && !player.dead ? damageBy[i] * DamageDecay : 0f;
				}
			}
			Player current = CurrentTarget;
			if (current == null || !CanTarget(current)) {
				int best = BestTarget(-1);
				if (best >= 0) {
					SetTarget(best);
				}
				return;
			}
			if (++targetTicks < TargetSwitchTicks) {
				return;
			}
			int next = BestTarget(NPC.target);                   // "can't choose the same target"
			if (next >= 0) {
				SetTarget(next);
			}
			else {
				targetTicks = 0;                                 // nobody else: keep this one, look again in 5 s
			}
		}

		public sealed override bool CheckDead() {
			if (finishing || (IsDying && Timer >= DeathAnimationTicks - FinishGrace)) {
				return true;
			}
			NPC.life = 1;
			NPC.dontTakeDamage = true;
			if (!IsDying && IsAuthority) {
				ChangeState(DyingState);
				OnDeathStarted();
			}
			return false;
		}

		/// <summary>Server or singleplayer, once, when the lethal blow lands: cancel anything the boss was holding.</summary>
		protected virtual void OnDeathStarted() {
		}

		/// <summary>Call every tick while dying. Keeps the boss untouchable, shows the defeat card on clients and ends
		/// the cinematic on the server.</summary>
		protected void UpdateDeath() {
			NPC.dontTakeDamage = true;
			if (!Main.dedServ && !defeatCardShown && Timer >= DefeatCardTick) {
				defeatCardShown = true;
				Player viewer = Main.LocalPlayer;
				if (viewer != null && viewer.active && Vector2.DistanceSquared(viewer.Center, NPC.Center) <= DefeatCardRange * DefeatCardRange) {
					BossTitleSystem.ShowDefeated(DisplayName, DefeatCardHold);
				}
			}
			if (!IsAuthority || finishing || Timer < DeathAnimationTicks) {
				return;
			}
			finishing = true;
			NPC.StrikeInstantKill();                       // life 1 -> 0: HitEffect, checkDead (now allowed), loot, OnKill
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
			}
		}

		// --- fight registry (no allocation, fixed slots, D1) --------------------------------------------------------------

		private void ReportFight() {
			uint now = Main.GameUpdateCount;
			int slot = -1;
			for (int i = 0; i < MaxTrackedFights; i++) {
				if (fightNpc[i] == NPC.whoAmI) {
					slot = i;
					break;
				}
				if (slot < 0 || now - fightTick[i] > now - fightTick[slot]) {
					slot = i;                              // otherwise reuse the stalest slot
				}
			}
			fightNpc[slot] = NPC.whoAmI;
			fightTick[slot] = now;
			fightPosition[slot] = NPC.Center;
		}

		/// <summary>True if a living Cogpunk boss updated within the last two ticks within <paramref name="range"/> of
		/// <paramref name="position"/>.</summary>
		public static bool IsFightNear(Vector2 position, float range) {
			uint now = Main.GameUpdateCount;
			for (int i = 0; i < MaxTrackedFights; i++) {
				if (fightNpc[i] >= 0 && now - fightTick[i] <= 2 && Vector2.DistanceSquared(fightPosition[i], position) <= range * range) {
					return true;
				}
			}
			return false;
		}
	}
}
