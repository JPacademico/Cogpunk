using System;
using Cogpunk.Content.Bosses.TarTyrant.NPCs;
using Cogpunk.Content.Bosses.TarTyrant.Projectiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.TarTyrant.TarTyrantRigData;

namespace Cogpunk.Content.Bosses.TarTyrant
{
	/// <summary>
	/// Tar Tyrant's attacks (user-set 2026-10-29), server-side: the timings here also drive the pose
	/// (<see cref="ResolveFrame"/>), so the wind-ups the players read are the same ticks the attacks fire on.
	/// <list type="number">
	/// <item><b>Burp</b>: it swells and rears back for <see cref="BurpTick"/> ticks, then heaves <see cref="Bubbles"/>
	/// condensed tar bubbles out of its throat (<see cref="TarTyrantBubble"/>, NPCs: they drift, grow, and burst into two
	/// Living Tar each after 3 s unless popped).</item>
	/// <item><b>Spit</b>: it rears its head back for <see cref="SpitTick"/> ticks and spits a fan of <see cref="Globs"/>
	/// globs at the target, <see cref="GlobSpread"/> apart (<see cref="TarTyrantGlob"/>); each leaves 3 tiles of tar on the
	/// ground for 3 s (<see cref="TarTyrantPuddle"/>).</item>
	/// <item><b>Melt</b> (only when the target is far or out of reach): it slumps into the ground, stays under
	/// <see cref="MeltUnderTicks"/> (1 s) while the ground boils at the spot the target is walking into (its velocity
	/// <see cref="MeltLeadTicks"/> ahead), and rises there.</item>
	/// <item><b>Summon</b>: the claw goes up (the telegraph), and at <see cref="SummonFieldTick"/> tar boils up across the
	/// whole screen every <see cref="SpikeSpacing"/> (a bone 1 tile wide, 5 tiles of room between); it plunges the claw
	/// into the tar and the bones burst up, nearest first (<see cref="TarTyrantBoneSpike"/>).</item>
	/// <item><b>Rage</b> (once, at a third of its life): growl, melt away, five claws (<see cref="TarTyrantClaw"/>, one
	/// every <see cref="ClawEvery"/> ticks, each 1.5 s of warning), and it rises on the other side of its target.</item>
	/// <item><b>Flung bones</b> (on its own, all fight long; user-set 2026-10-29 in place of the femur throw: "bones should
	/// automatically fly out of his upper back every 2.5 seconds bouncing once and causing small damage"; every 3.5 s since
	/// the user's nerf of 2026-10-30): every
	/// <see cref="VentInterval"/> ticks the top of its hump heaves and boils for <see cref="VentTelegraphTicks"/> (the
	/// ends of bones break the skin) and bursts: <see cref="VentBones"/> bones are lobbed at the target's feet,
	/// <see cref="BoneSpread"/> apart (<see cref="TarTyrantBackBone"/>: they bounce once and shatter on the next
	/// contact).</item>
	/// </list>
	/// D0: every spawn goes through SafeSpawn and is capped (bubbles <see cref="MaxBubbles"/>, spikes 2 x
	/// <see cref="SpikeHalfCount"/> + 1, three bones a volley, one claw at a time); ground searches are bounded (TryGround).
	/// </summary>
	public partial class TarTyrant
	{
		// --- burp ----------------------------------------------------------------------------------------------------------
		public const int BurpTick = 48, BurpTicks = 84;
		public const int BurpFrame = 5;                    // the frame its jaws are widest
		public const int Bubbles = 3, MaxBubbles = 9;

		// --- spit ----------------------------------------------------------------------------------------------------------
		public const int SpitTick = 36, SpitTicks = 66;
		public const int SpitFrame = 3;
		public const int Globs = 3;
		public const float GlobFlightTicks = 40f;
		public const float GlobSpread = 5f * 16f;

		// --- melt (user: "after 1 second", "predicting its trajectory"; "a bit faster", 2026-10-29: 160 -> 124 ticks) ---------
		public const int MeltFrameTicks = 3;
		public const int MeltGoneTick = 18;                // from here it is under the tar
		public const int MeltUnderTick = 24;               // fully under: the spot is picked
		public const int MeltUnderTicks = 60;
		public const int MeltLeadTicks = 60;
		public const float MaxLead = 30f * 16f;
		public const int RiseFrameTicks = 4;
		public const int RiseSolidTick = 12;               // the fourth rise frame: its bones are out, it hurts and can be hurt
		public const int MeltRiseTick = MeltUnderTick + MeltUnderTicks;
		public const int MeltTicks = MeltRiseTick + R.RiseFrames * RiseFrameTicks;

		// --- summon --------------------------------------------------------------------------------------------------------
		public const int SummonFieldTick = 30, SummonPlungeTick = 72, SummonEruptTick = 78, SummonTicks = 130;
		public const int SpikeHalfCount = 11;              // 23 bones: 66 tiles each way covers the screen
		public const float SpikeSpacing = 6f * 16f;
		public const int SpikeStagger = 2;                 // ticks between a bone and the next one out

		// --- flung bones (automatic, all fight long) ---------------------------------------------------------------------------
		/// <summary>A volley every 3.5 s, enraged too (user-set 2026-10-29 at 2.5 s; the user's nerf of 2026-10-30).</summary>
		public const int VentInterval = 210;
		/// <summary>The hump heaves and boils this long before each volley (D3: a telegraph of 30 ticks or more at T0-T4).</summary>
		public const int VentTelegraphTicks = 30;
		/// <summary>The burst frames after the bones are out.</summary>
		public const int VentBurstTicks = 12;
		public const int VentBones = 3;
		public const float BoneSpread = 4f * 16f;          // the bones land this far apart, the middle one on the target
		public const float BoneScatter = 16f;              // and up to this far off (server roll)
		/// <summary>Flight time to the target's feet: 1 tick per 6 px, 36-64 ticks (a high lob that comes down on them).</summary>
		public const float BoneFlightPerPx = 1f / 6f;
		public const float BoneMinFlight = 36f, BoneMaxFlight = 64f;

		// --- rage (user: growl, melt, a claw every 2 s x5 with 1.5 s to dodge, rise on the other side) -------------------------
		public const int RageGrowlTicks = 60;
		public const int RageClawStart = RageGrowlTicks + MeltUnderTick;
		public const int RageClaws = 5, ClawEvery = 120;
		public const int RageRiseTick = RageClawStart + RageClaws * ClawEvery;
		public const int RagePickTick = RageRiseTick - 60;  // the spot it comes back at starts boiling a second early
		public const int RageRoarTick = RageRiseTick + R.RiseFrames * RiseFrameTicks;
		public const int RageTicks = RageRoarTick + RoarTicks;
		public const float RageMinDistance = 16f * 16f, RageMaxDistance = 32f * 16f;

		public const int EmergeSolidTick = RiseTicks * 3 / R.RiseFrames;

		/// <summary>Nothing of it is above the ground (the frame is not drawn; the spot it will rise at boils instead).</summary>
		public bool Hidden {
			get {
				int t = (int)Timer;
				return CurrentPhase switch {
					Phase.Melt => t >= MeltUnderTick && t < MeltRiseTick,
					Phase.Rage => t >= RageClawStart && t < RageRiseTick,
					Phase.Retreat => t >= MeltUnderTick,
					_ => false,
				};
			}
		}

		/// <summary>The spot boiling before it rises there (clients draw it), if any.</summary>
		public bool TryGetRisingSpot(out Vector2 spot) {
			spot = destination;
			int t = (int)Timer;
			bool boiling = CurrentPhase == Phase.Melt ? t >= MeltUnderTick && t < MeltRiseTick : CurrentPhase == Phase.Rage && t >= RagePickTick && t < RageRiseTick;
			return boiling && destination != Vector2.Zero;
		}

		private static int CountAlive(int type) {
			int count = 0;
			foreach (NPC other in Main.ActiveNPCs) {
				if (other.type == type) {
					count++;
				}
			}
			return count;
		}

		// --- burp ------------------------------------------------------------------------------------------------------------

		private void DoBurp() {
			if (Timer == BurpTick && IsAuthority) {
				Vector2 mouth = RigPoint(R.Mouth, R.Burp0 + BurpFrame);
				int type = ModContent.NPCType<TarTyrantBubble>();
				int alive = CountAlive(type);
				for (int i = 0; i < Bubbles && alive < MaxBubbles; i++) {
					if (!SafeSpawn.TryNewNPC(NPC.GetSource_FromAI(), (int)mouth.X, (int)mouth.Y + 12, type, out NPC bubble)) {
						break;
					}
					alive++;
					bubble.velocity = new Vector2(NPC.spriteDirection * (1.5f + 2.2f * i), -2.5f - 1.8f * (Bubbles - 1 - i));   // a fan out of its maw
					bubble.target = NPC.target;
					bubble.netUpdate = true;
				}
			}
			if (Timer >= BurpTicks) {
				EndAttack();
			}
		}

		// --- spit ------------------------------------------------------------------------------------------------------------

		private void DoSpit() {
			if (Timer == SpitTick && IsAuthority) {
				Player target = TargetPlayer;
				if (target != null) {
					Vector2 from = RigPoint(R.Mouth, R.Spit0 + SpitFrame);
					int type = ModContent.ProjectileType<TarTyrantGlob>();
					int damage = ExpertStats.HostileProjectile(NPC, GlobDamage);
					for (int i = 0; i < Globs; i++) {
						float offset = (i - (Globs - 1) * 0.5f) * GlobSpread;
						Vector2 at = new(target.Center.X + offset, target.Bottom.Y);
						SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, TarTyrantGlob.LobVelocity(from, at, GlobFlightTicks), type, damage, 2f, out _);
					}
				}
			}
			if (Timer >= SpitTicks) {
				EndAttack();
			}
		}

		// --- melt ------------------------------------------------------------------------------------------------------------

		private void DoMelt() {
			int t = (int)Timer;
			if (t == MeltUnderTick && IsAuthority) {
				destination = PredictSpot(TargetPlayer);
				NPC.netUpdate = true;
			}
			if (ShouldRiseAt(t, MeltRiseTick)) {
				RiseAt(destination);
			}
			if (t >= MeltTicks) {
				EndAttack();
			}
		}

		/// <summary>Server: the ground the target will be standing on in <see cref="MeltLeadTicks"/> at its current speed (at
		/// most <see cref="MaxLead"/> ahead), or under it, or where it stands.</summary>
		private Vector2 PredictSpot(Player target) {
			if (target == null) {
				return RigOrigin;
			}
			float lead = MathHelper.Clamp(target.velocity.X * MeltLeadTicks, -MaxLead, MaxLead);
			if (TryGround(target.Center.X + lead, target.Bottom.Y, out Vector2 ground) || TryGround(target.Center.X, target.Bottom.Y, out ground)) {
				return ground;
			}
			return target.Bottom;
		}

		// --- summon ----------------------------------------------------------------------------------------------------------

		private void DoSummon() {
			if (Timer == SummonFieldTick && IsAuthority) {
				Player target = TargetPlayer;
				if (target != null) {
					SpawnSpikes(target);
				}
			}
			if (Timer >= SummonTicks) {
				EndAttack();
			}
		}

		/// <summary>Server: one bone under the target and one every <see cref="SpikeSpacing"/> each way across the screen,
		/// erupting nearest-first from <see cref="SummonEruptTick"/> (each shows its boiling patch until then: 48 ticks at the
		/// least). A column with no ground near the target's height gets none.</summary>
		private void SpawnSpikes(Player target) {
			int type = ModContent.ProjectileType<TarTyrantBoneSpike>();
			int damage = ExpertStats.HostileProjectile(NPC, SpikeDamage);
			float boss = RigOrigin.X;
			for (int k = -SpikeHalfCount; k <= SpikeHalfCount; k++) {
				float x = target.Center.X + k * SpikeSpacing;
				if (!TryGround(x, target.Bottom.Y, out Vector2 ground)) {
					continue;
				}
				int rank = Math.Min(40, (int)(Math.Abs(x - boss) / SpikeSpacing));
				int delay = SummonEruptTick - SummonFieldTick + rank * SpikeStagger;
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), ground - new Vector2(0f, TarTyrantBoneSpike.HitboxHeight * 0.5f), Vector2.Zero, type,
					damage, 2f, out _, ai0: delay);
			}
		}

		// --- flung bones ----------------------------------------------------------------------------------------------------

		private int ventTimer;                             // every side counts it; the server's is sent in ExtraAI
		private int ventBurst;                             // clients: ticks of the burst frames left

		/// <summary>The volley runs while it stands and fights (between attacks and during the burp, the spit and the
		/// summon); the intro, the melt, the rage, the retreat and the death stop it and start the count again.</summary>
		private bool VentActive => CurrentPhase is Phase.Idle or Phase.Burp or Phase.Spit or Phase.Summon;

		/// <summary>Every side: count towards the next volley. The server throws the bones; every client plays the
		/// telegraph and the burst.</summary>
		private void UpdateVent() {
			if (ventBurst > 0) {
				ventBurst--;
			}
			if (!VentActive) {
				ventTimer = 0;
				ventBurst = 0;
				return;
			}
			ventTimer++;
			if (!Main.dedServ && ventTimer >= VentInterval - VentTelegraphTicks && ventTimer < VentInterval) {
				VentTelegraph(ventTimer - (VentInterval - VentTelegraphTicks));
			}
			if (ventTimer < VentInterval) {
				return;
			}
			ventTimer = 0;
			ventBurst = VentBurstTicks;
			if (!Main.dedServ) {
				VentLaunchEffects();
			}
			if (IsAuthority) {
				SpawnBackBones(TargetPlayer);
			}
		}

		/// <summary>The vent overlay's frame now (clients draw it over the body at its <see cref="R.Vent"/> point); -1: none.</summary>
		public int VentFrame {
			get {
				if (!VentActive) {
					return -1;
				}
				if (ventBurst > 0) {
					int k = (VentBurstTicks - ventBurst) * R.VentBurstFrames / VentBurstTicks;
					return R.VentBurst0 + Math.Clamp(k, 0, R.VentBurstFrames - 1);
				}
				int t = ventTimer - (VentInterval - VentTelegraphTicks);
				return t < 0 ? -1 : R.VentSwell0 + Math.Clamp(t * R.VentSwellFrames / VentTelegraphTicks, 0, R.VentSwellFrames - 1);
			}
		}

		/// <summary>Server: <see cref="VentBones"/> bones out of the vent, lobbed high at the target's feet, one on them and the
		/// others <see cref="BoneSpread"/> either side (bone kinds alternate). Nobody to throw at: the volley is skipped.</summary>
		private void SpawnBackBones(Player target) {
			if (target == null) {
				return;
			}
			Vector2 from = RigPoint(R.Vent, ResolveFrame(false));
			int type = ModContent.ProjectileType<TarTyrantBackBone>();
			int damage = ExpertStats.HostileProjectile(NPC, BackBoneDamage);
			for (int i = 0; i < VentBones; i++) {
				float offset = (i - (VentBones - 1) * 0.5f) * BoneSpread + Main.rand.NextFloat(-BoneScatter, BoneScatter);
				Vector2 at = new(target.Center.X + offset, target.Bottom.Y - 8f);
				float ticks = MathHelper.Clamp(Math.Abs(at.X - from.X) * BoneFlightPerPx, BoneMinFlight, BoneMaxFlight);
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, TarTyrantBackBone.LobVelocity(from, at, ticks), type, damage, 2f, out _,
					ai1: i % R.BoneKinds);
			}
		}

		// --- rage ------------------------------------------------------------------------------------------------------------

		private void DoRage() {
			int t = (int)Timer;
			if (ShouldRiseAt(t, RageRiseTick)) {
				RiseAt(destination);
			}
			if (!IsAuthority) {
				return;
			}
			if (t >= RageClawStart && t < RageRiseTick && (t - RageClawStart) % ClawEvery == 0 && Retarget()) {
				SpawnClaw(TargetPlayer);
			}
			if (t == RagePickTick) {
				destination = OppositeSpot(TargetPlayer);
				NPC.netUpdate = true;
			}
			if (t >= RageTicks && Retarget()) {
				StartIdle();
			}
		}

		/// <summary>The tick it comes up at <see cref="destination"/>: exactly <paramref name="tick"/> on the server; a client moves
		/// its copy itself within a few ticks of it (the server's position follows), so it never rises at the old spot first.</summary>
		private bool ShouldRiseAt(int t, int tick) {
			if (destination == Vector2.Zero) {
				return false;
			}
			if (IsAuthority) {
				return t == tick;
			}
			return t >= tick && t < tick + 4 && Vector2.DistanceSquared(RigOrigin, destination) > 64f;
		}

		/// <summary>Every side: it faces its target from <paramref name="spot"/> and stands there.</summary>
		private void RiseAt(Vector2 spot) {
			Player target = TargetPlayer;
			if (target != null) {
				NPC.direction = NPC.spriteDirection = target.Center.X >= spot.X ? 1 : -1;
			}
			MoveTo(spot);
		}

		/// <summary>Server: a claw out of the ground under the target (or a few tiles under it over a pit).</summary>
		private void SpawnClaw(Player target) {
			if (target == null) {
				return;
			}
			Vector2 ground = TryGround(target.Center.X, target.Bottom.Y, out Vector2 g) ? g : target.Bottom + new Vector2(0f, 4f * 16f);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), ground - new Vector2(0f, TarTyrantClaw.HitboxHeight * 0.5f), Vector2.Zero,
				ModContent.ProjectileType<TarTyrantClaw>(), ExpertStats.HostileProjectile(NPC, ClawDamage), 6f, out _);
		}

		/// <summary>Server: the far side of the target from where the rage began, as far from it as it was then.</summary>
		private Vector2 OppositeSpot(Player target) {
			if (target == null) {
				return RigOrigin;
			}
			float x = target.Center.X - rageSide * rageDistance;
			if (TryGround(x, target.Bottom.Y, out Vector2 ground)) {
				return ground;
			}
			return TryGround(target.Center.X, target.Bottom.Y, out ground) ? ground : RigOrigin;
		}
	}
}
