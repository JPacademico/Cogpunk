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
	/// <para>D0: nothing here loops past a fixed bound or spawns; a boss that is already dying ignores further lethal hits.</para>
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

		private bool finishing;
		private bool defeatCardShown;

		/// <summary>The state index of the death cinematic.</summary>
		protected abstract int DyingState { get; }

		/// <summary>Length of the death cinematic in ticks.</summary>
		protected abstract int DeathAnimationTicks { get; }

		/// <summary>When the defeat card appears (ticks into the death); by default a second before the end.</summary>
		protected virtual int DefeatCardTick => DeathAnimationTicks - 60;

		public bool IsDying => State == DyingState;

		/// <summary>The boss's own per-tick logic (every side), called by the sealed <see cref="UpdateState"/>.</summary>
		protected abstract void UpdateBoss();

		protected sealed override void UpdateState() {
			ReportFight();
			UpdateBoss();
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
