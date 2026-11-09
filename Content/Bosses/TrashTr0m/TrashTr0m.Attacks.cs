using System;
using Cogpunk.Content.Bosses.TrashTr0m.Projectiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	public partial class TrashTr0m
	{
		// --- slam ----------------------------------------------------------------------------------------------------------
		public const int SlamWindupTicks = 45;             // telegraph >= 30 ticks at T0 (D3)
		// The wind-up's poses (ResolvePose): the fist leaves the ground (to SlamLiftTicks), rises (to SlamRiseTicks), goes
		// up (to SlamRaiseTicks), holds high, cocks back (from SlamCockTick) and swings through for the last StrikeTicks.
		public const int SlamLiftTicks = 5;
		public const int SlamRiseTicks = 11;
		public const int SlamRaiseTicks = 18;              // the fist goes up, then cocks back high
		public const int SlamCockTick = 36;
		public const int StrikeTicks = 3;                  // the swing-through frame before the impact (a smear, D4 rule 10)
		public const int SecondSlamWindupTicks = 32;       // enraged: the far claw follows (still >= 30 ticks of telegraph)
		public const int SecondSlamLiftTicks = 8;          // the near fist comes back up off the ground first
		public const int SecondSlamPrepTicks = 13;         // then goes down while the claw comes up
		public const int SecondSlamRaiseTicks = 20;
		public const int SlamRecoverTicks = 40;
		/// <summary>14 px/tick (was 9, user 2026-10-26: less time to react). The wave passes under a jumping player in
		/// (76 + 20) / 14 = 7 ticks; a vanilla jump keeps the feet above its 40 px for ~25 ticks, so it is still fair.</summary>
		public const float ShockwaveSpeed = 14f;

		// --- suck ----------------------------------------------------------------------------------------------------------
		public const int SuckWindupTicks = 45;             // the jaw opens: telegraph
		public const int SuckTicks = 300;                  // 5 s of suction
		public const int SuckRampTicks = 45;               // the pull builds up over the first 0.75 s
		/// <summary>
		/// The pull on a player, in px per tick, applied as a conveyor (added to the player's own movement and taken off
		/// again after collision, <see cref="TrashTr0mPlayer"/>), so it simply subtracts from their run speed. Decompiled
		/// <c>Player.HorizontalMovement</c>: running tops out at <c>maxRunSpeed</c> = 3 px/tick without accessories and
		/// at <c>accRunSpeed</c> = 6 with Hermes Boots (and their upgrades). 5.4 = 90% of the Hermes speed: at full Hermes
		/// speed a player still gains 0.6 px/tick (2.25 tiles/s) and escapes; at 3 (or 4.2 with Swiftness, Aglet and
		/// Anklet) they lose 1.2-2.4 px/tick and are dragged in. Standing still, it is 5.4 px/tick towards the mouth.
		/// </summary>
		public const float MaxPull = 5.4f;
		public const float SuckRange = 40f * 16f;           // nothing beyond this is pulled; a player inside means "suck"
		public const float SuckFullRange = 22f * 16f;       // full strength inside this, fading to 0 at SuckRange
		public const float EnragedSuckScale = 2f;           // enraged: the suction reaches twice as far
		public const float LiftRange = 9f * 16f;            // within this horizontal distance it lifts players into the mouth
		public const float LiftSpeed = 6f;
		public const int MouthBox = 56;                    // touching this square around the mouth = swallowed
		public const float ProjectilePullSpeed = 13f;
		public const float ProjectileSteer = 0.18f;
		public const float EatRadius = 30f;

		// --- swallow / spit ------------------------------------------------------------------------------------------------
		public const int SwallowTicks = 50;
		public const int SpitPlayerTicks = 60;
		public const int SpitReleaseTick = 24;
		/// <summary>The spat player is thrown <b>behind</b> the boss (user-set 2026-10-27: was forwards). Vanilla slows an
		/// airborne player with no keys held by 0.1 px/tick per tick (decompiled Player.HorizontalMovement, runSlowdown / 2), so
		/// 9.5 px/tick carries them 9.5^2 / 0.2 = 450 px back from the mouth: past the boss's back (the mouth is 174 px in
		/// front of the rig origin, the back 190 px behind it) before they come down. They can still steer.</summary>
		public const float SpitSideSpeed = 9.5f;
		public const int GulpTicks = 30;                   // the brief swallow before spitting back
		public const int MaxSpitBack = 15;                 // D1: never more than 15 chunks from one suck
		public const int SpitVolleyInterval = 12;
		public const int SpitVolleySize = 3;
		public const float ChewedScrapSpeed = 11f;
		public const int SpitBallWindTicks = 24;
		public const int SpitBallTicks = 54;
		public const float ScrapBallGravity = TrashTr0mScrapBall.Gravity;

		// --- cog volley (automatic, all fight long) -------------------------------------------------------------------
		/// <summary>A cog every 2.5 s, all fight long, enraged too (user nerf 2026-10-29; it was 1.5 s, and 0.75 s from half
		/// life, since 2026-10-27).</summary>
		public const int CogInterval = 150;
		/// <summary>The stack rattles and puffs this long before each cog (telegraph >= 30 ticks at T0, D3).</summary>
		public const int CogTelegraphTicks = 30;
		/// <summary>The exhaust stacks on its back (rig px, left-facing): the cogs come out of their tops.</summary>
		public const int CogStackX = 120, CogStackY = -318;
		/// <summary>Flight time of the lob: 1 tick per 5 px of horizontal distance, 55-95 ticks, so the cog always goes
		/// up high first and comes down on the player instead of flying straight at them.</summary>
		public const float CogFlightPerPx = 0.2f;
		public const float CogMinFlight = 55f, CogMaxFlight = 95f;
		public const float CogScatter = 40f;               // px either side of the player it may land (server roll)
		/// <summary>Damage in Expert (user-set 25; Classic half, Master 1.5x; hits for 26, the nearest even number, since
		/// hostile hits are x2).</summary>
		public const int CogDamage = 25;

		private int cogTimer;                              // every side counts it; the server's is sent in ExtraAI

		/// <summary>The top of the exhaust stacks in the world.</summary>
		public Vector2 CogStackWorld => RigToWorld(CogStackX, CogStackY);

		/// <summary>Every side: count towards the next cog (only while it fights: not during the intro, the retreat or
		/// the death). The server fires it; every client plays the telegraph and the launch.</summary>
		private void UpdateCogs() {
			if (CurrentPhase == Phase.Emerge || CurrentPhase == Phase.Retreat || CurrentPhase == Phase.Dying) {
				cogTimer = 0;
				return;
			}
			cogTimer++;
			if (!Main.dedServ && cogTimer >= CogInterval - CogTelegraphTicks && cogTimer < CogInterval) {
				CogTelegraph(cogTimer - (CogInterval - CogTelegraphTicks));
			}
			if (cogTimer < CogInterval) {
				return;
			}
			cogTimer = 0;
			if (!Main.dedServ) {
				CogLaunchEffects();
			}
			if (!IsAuthority) {
				return;
			}
			int target = NPC.target;
			if (target < 0 || target >= Main.maxPlayers || !Main.player[target].active || Main.player[target].dead || target == HeldPlayer) {
				return;                                    // nobody to throw at (or it is chewing them): skip this one
			}
			Vector2 from = CogStackWorld;
			Vector2 to = Main.player[target].Center + new Vector2(Main.rand.NextFloat(-CogScatter, CogScatter), 0f);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, CogVelocity(from, to), ModContent.ProjectileType<TrashTr0mCog>(),
				ProjectileDamage(CogDamage), 0f, out _);
		}

		/// <summary>A high lob from <paramref name="from"/> that comes down on <paramref name="to"/> under the cog's gravity.</summary>
		public static Vector2 CogVelocity(Vector2 from, Vector2 to) {
			Vector2 d = to - from;
			float time = MathHelper.Clamp(Math.Abs(d.X) * CogFlightPerPx, CogMinFlight, CogMaxFlight);
			float vx = d.X / time;
			float vy = (d.Y - 0.5f * TrashTr0mCog.Gravity * time * time) / time;
			return new Vector2(MathHelper.Clamp(vx, -14f, 14f), MathHelper.Clamp(vy, -20f, -4f));   // always upwards first
		}

		private bool IsSucking => CurrentPhase == Phase.Suck;

		/// <summary>The suction's reach right now (doubled when enraged).</summary>
		public float CurrentSuckRange => SuckRange * (Enraged ? EnragedSuckScale : 1f);

		public float CurrentSuckFullRange => SuckFullRange * (Enraged ? EnragedSuckScale : 1f);

		// ------------------------------------------------------------------------------------------------------------
		// Rig points in the world (every side: they depend only on synced state)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>A rig point (game px, left-facing, relative to the rig origin) in world space.</summary>
		public Vector2 RigToWorld(int x, int y) {
			return RigOrigin + new Vector2(NPC.spriteDirection == 1 ? -x : x, y);
		}

		/// <summary>The mouth (throat) in world space for the current pose.</summary>
		public Vector2 MouthWorld() {
			ResolvePose(out int body, out _);
			return RigToWorld(TrashTr0mRigData.Mouth[body * 2], TrashTr0mRigData.Mouth[body * 2 + 1]);
		}

		public Vector2 NearHandWorld(int armFrame) {
			return RigToWorld(TrashTr0mRigData.NearContact[armFrame * 2], TrashTr0mRigData.NearContact[armFrame * 2 + 1]);
		}

		public Vector2 FarHandWorld(int armFrame) {
			return RigToWorld(TrashTr0mRigData.FarContact[armFrame * 2], TrashTr0mRigData.FarContact[armFrame * 2 + 1]);
		}

		private int ProjectileDamage(int expert) => ExpertStats.HostileProjectile(NPC, expert);

		// ------------------------------------------------------------------------------------------------------------
		// Slam
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>Which arm is slamming (Arg): 0 the near fist, 1 the far claw (the enraged second slam).</summary>
		public bool FarArmSlam => (CurrentPhase == Phase.SlamWindup || CurrentPhase == Phase.SlamRecover) && Arg == 1f;

		/// <summary>The world point where the slamming hand lands (and the shockwave starts).</summary>
		public Vector2 SlamPoint(bool farArm) {
			return farArm ? FarHandWorld(TrashTr0mRigData.ArmFarSlamHit) : NearHandWorld(TrashTr0mRigData.ArmSlamHit);
		}

		private void DoSlamWindup() {
			bool far = Arg == 1f;
			if (Timer < (far ? SecondSlamWindupTicks : SlamWindupTicks)) {
				return;
			}
			if (IsAuthority) {
				Vector2 at = SlamPoint(far) - new Vector2(0f, TrashTr0mShockwave.HitboxHeight * 0.5f);
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), at, new Vector2(NPC.spriteDirection * ShockwaveSpeed, 0f),
					ModContent.ProjectileType<TrashTr0mShockwave>(), ProjectileDamage(SlamDamage), 0f, out _);
			}
			if (!far && Enraged) {
				ChangeState((int)Phase.SlamWindup);        // enraged: the other arm follows straight away
				Arg = 1f;
				return;
			}
			ChangeState((int)Phase.SlamRecover);
			Arg = far ? 1f : 0f;                           // the recover pose follows the arm that hit
		}

		// ------------------------------------------------------------------------------------------------------------
		// Suck
		// ------------------------------------------------------------------------------------------------------------

		private void DoSuckWindup() {
			if (Timer >= SuckWindupTicks) {
				ChangeState((int)Phase.Suck);
				Arg = 0f;                                  // projectiles eaten
			}
		}

		/// <summary>0..1: how hard it is sucking right now (ramps up, then holds).</summary>
		public float SuckStrength => IsSucking ? MathHelper.Clamp(Timer / SuckRampTicks, 0f, 1f) : 0f;

		private void DoSuck() {
			float strength = SuckStrength;
			Vector2 mouth = MouthWorld();
			PullProjectiles(mouth, strength);
			if (IsAuthority && strength >= 1f) {
				int swallowed = FindPlayerAtMouth(mouth);
				if (swallowed >= 0) {
					ChangeState((int)Phase.SwallowPlayer);
					Arg = swallowed;
					return;
				}
			}
			if (Timer >= SuckTicks) {
				ChangeState((int)Phase.Gulp);              // keeps Arg: the eaten count
			}
		}

		/// <summary>
		/// Steers every edible friendly projectile in range towards the mouth and eats those that reach it. Runs on every
		/// side with the same synced inputs, so every copy of a projectile follows the same path. The owner removes its
		/// projectile and tells the others (KillProjectile, relayed by the server; no OnKill effects: it was eaten); the
		/// server and the other clients drop their copies silently; only the server (or singleplayer) counts it.
		/// </summary>
		private void PullProjectiles(Vector2 mouth, float strength) {
			if (strength <= 0f) {
				return;
			}
			float range = CurrentSuckRange;
			float full = CurrentSuckFullRange;
			float range2 = range * range;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (!IsEdible(p)) {
					continue;
				}
				Vector2 d = mouth - p.Center;
				float dist2 = d.LengthSquared();
				if (dist2 > range2) {
					continue;
				}
				if (dist2 < EatRadius * EatRadius) {
					Eat(p);
					continue;
				}
				float dist = MathF.Sqrt(dist2);
				float pull = strength * (dist < full ? 1f : 1f - (dist - full) / (range - full));
				p.velocity = Vector2.Lerp(p.velocity, d / dist * ProjectilePullSpeed, ProjectileSteer * pull);
			}
		}

		/// <summary>Friendly, damaging, free-flying projectiles. Never minions, sentries, pets, hooks, whips, yoyos, flails,
		/// spears or anything the player is holding.</summary>
		public static bool IsEdible(Projectile p) {
			if (!p.active || !p.friendly || p.hostile || p.damage <= 0 || p.minion || p.sentry || Main.projPet[p.type]) {
				return false;
			}
			switch (p.aiStyle) {
				case ProjAIStyleID.Hook:
				case ProjAIStyleID.Flail:
				case ProjAIStyleID.Spear:
				case ProjAIStyleID.HeldProjectile:
				case ProjAIStyleID.Yoyo:
				case ProjAIStyleID.Whip:
					return false;
			}
			if (ProjectileID.Sets.IsAWhip[p.type] || p.owner < 0 || p.owner >= Main.maxPlayers) {
				return false;
			}
			return Main.player[p.owner].heldProj != p.whoAmI;
		}

		private void Eat(Projectile p) {
			if (Main.netMode == NetmodeID.MultiplayerClient && p.owner == Main.myPlayer) {
				NetMessage.SendData(MessageID.KillProjectile, number: p.identity, number2: p.owner);
			}
			p.active = false;
			if (IsAuthority) {
				Arg = Math.Min(Arg + 1f, 999f);
			}
			if (!Main.dedServ) {
				EatEffect(p.Center);
			}
		}

		/// <summary>Server: is any living player (in the Junkyard, if the world has one) within suction range of the mouth?
		/// The mouth is read from the jaw-open pose the suck would use.</summary>
		private bool AnyPlayerInSuckRange() {
			Vector2 mouth = RigToWorld(TrashTr0mRigData.Mouth[TrashTr0mRigData.BodySuck0 * 2], TrashTr0mRigData.Mouth[TrashTr0mRigData.BodySuck0 * 2 + 1]);
			float range2 = CurrentSuckRange * CurrentSuckRange;
			bool needJunkyard = Junkyard.JunkyardSystem.Exists;
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && (!needJunkyard || Junkyard.JunkyardSystem.Contains(player.Center))
					&& Vector2.DistanceSquared(player.Center, mouth) <= range2) {
					return true;
				}
			}
			return false;
		}

		/// <summary>Server: the first living player whose hitbox touches the mouth box, or -1.</summary>
		private static int FindPlayerAtMouth(Vector2 mouth) {
			Rectangle box = new((int)mouth.X - MouthBox / 2, (int)mouth.Y - MouthBox / 2, MouthBox, MouthBox);
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && player.Hitbox.Intersects(box)) {
					return player.whoAmI;
				}
			}
			return -1;
		}

		/// <summary>
		/// The suction on <paramref name="player"/> this tick (every side, same inputs): <paramref name="conveyX"/> is the
		/// horizontal conveyor in px/tick (see <see cref="MaxPull"/>), and when the player is within <see cref="LiftRange"/>
		/// of the mouth, <paramref name="liftVelocity"/> is the vertical speed that carries them up (or down) into it.
		/// </summary>
		public bool GetPull(Player player, out float conveyX, out float liftVelocity, out bool lifting) {
			conveyX = liftVelocity = 0f;
			lifting = false;
			float strength = SuckStrength;
			if (strength <= 0f || player.dead || !player.active) {
				return false;
			}
			Vector2 mouth = MouthWorld();
			Vector2 d = mouth - player.Center;
			float dist = d.Length();
			float range = CurrentSuckRange;
			float full = CurrentSuckFullRange;
			if (dist > range || dist < 1f) {
				return false;
			}
			float falloff = dist < full ? 1f : 1f - (dist - full) / (range - full);
			float pull = strength * falloff;
			conveyX = Math.Sign(d.X) * Math.Min(MaxPull * pull, Math.Abs(d.X));
			if (Math.Abs(d.X) < LiftRange) {
				lifting = true;
				liftVelocity = MathHelper.Clamp(d.Y * 0.12f, -LiftSpeed, LiftSpeed) * pull;
			}
			return true;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Swallow and spit a player
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>The player currently in its mouth (swallowed, or about to be spat), or -1.</summary>
		public int HeldPlayer {
			get {
				bool holding = CurrentPhase == Phase.SwallowPlayer || (CurrentPhase == Phase.SpitPlayer && Timer < SpitReleaseTick);
				int who = (int)Arg;
				return holding && who >= 0 && who < Main.maxPlayers ? who : -1;
			}
		}

		/// <summary>True on the tick window in which the held player is launched.</summary>
		public bool IsSpitting(int who) => CurrentPhase == Phase.SpitPlayer && Timer >= SpitReleaseTick && (int)Arg == who;

		private void DoSwallowPlayer() {
			int who = (int)Arg;
			bool lost = who < 0 || who >= Main.maxPlayers || !Main.player[who].active || Main.player[who].dead;
			if (lost && IsAuthority) {
				EndAttack();                               // its meal died or left: nothing to spit
				return;
			}
			if (Timer >= SwallowTicks) {
				ChangeState((int)Phase.SpitPlayer);        // keeps Arg: the player
			}
		}

		private void DoSpitPlayer() {
			if (Timer >= SpitPlayerTicks) {
				EndAttack();
			}
		}

		/// <summary>
		/// The launch speed that takes a player from <paramref name="fromBottom"/> to a little over
		/// <see cref="MaxSpitFallTiles"/> tiles above <paramref name="groundY"/>, the boss's ground: falling back there costs
		/// the full (45 - 25) x 10 = 200 life without protection (the spat-fall cap in <see cref="TrashTr0mPlayer"/> keeps it
		/// from ever being more). Discrete kinematics of vanilla's <c>velocity.Y += gravity</c> before each move (decompiled
		/// Player.Update; no cap on upward speed): height = v^2 / 2g - v / 2.
		/// </summary>
		public static float SpitLaunchSpeed(float fromBottom, float groundY, float gravity) {
			float rise = (MaxSpitFallTiles + 1) * 16f - (groundY - fromBottom);
			rise = MathHelper.Clamp(rise, 160f, 1200f);
			float g = gravity > 0.05f ? gravity : Player.defaultGravity;
			float v = (g + MathF.Sqrt(g * g + 8f * g * rise)) * 0.5f;       // v^2 - g v - 2 g rise = 0
			return MathHelper.Clamp(v, 6f, 32f);
		}

		// ------------------------------------------------------------------------------------------------------------
		// Gulp, then spit back what it swallowed (or a scrap ball)
		// ------------------------------------------------------------------------------------------------------------

		private void DoGulp() {
			if (Timer < GulpTicks || !IsAuthority) {
				return;
			}
			int eaten = (int)Arg;
			EnsureTarget();                                // the shared rule's target (BossNPC), not the closest
			FaceTarget();
			if (eaten > 0) {
				ChangeState((int)Phase.SpitScrap);
				Arg = Math.Min(eaten, MaxSpitBack);
			}
			else {
				ChangeState((int)Phase.SpitBall);
			}
		}

		private void DoSpitScrap() {
			int t = (int)Timer;
			if (t > 0 && t % SpitVolleyInterval == 0 && IsAuthority && Arg > 0f) {
				int count = Math.Min(SpitVolleySize, (int)Arg);
				Arg -= count;
				NPC.netUpdate = true;
				SpitVolley(count);
			}
			if (Arg <= 0f && t % SpitVolleyInterval >= 6) {
				EndAttack();
			}
		}

		/// <summary>Server: <paramref name="count"/> chunks of chewed scrap aimed at the target, fanned out.</summary>
		private void SpitVolley(int count) {
			if (!NPC.HasValidTarget) {
				return;
			}
			Vector2 mouth = MouthWorld();
			Vector2 target = Main.player[NPC.target].Center;
			float time = MathHelper.Clamp(Vector2.Distance(mouth, target) / ChewedScrapSpeed, 0f, 90f);
			target.Y -= 0.5f * TrashTr0mChewedScrap.Gravity * time * time;   // aim high enough for the drop
			Vector2 aim = (target - mouth).SafeNormalize(new Vector2(NPC.spriteDirection, 0f));
			int damage = ProjectileDamage(ChewedScrapDamage);
			int type = ModContent.ProjectileType<TrashTr0mChewedScrap>();
			for (int i = 0; i < count; i++) {
				float spread = count == 1 ? 0f : MathHelper.Lerp(-0.22f, 0.22f, i / (float)(count - 1));
				Vector2 velocity = aim.RotatedBy(spread + Main.rand.NextFloat(-0.04f, 0.04f)) * ChewedScrapSpeed;
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), mouth, velocity, type, damage, 0f, out _);
			}
		}

		private void DoSpitBall() {
			if (Timer == SpitBallWindTicks && IsAuthority && NPC.HasValidTarget) {
				Vector2 mouth = MouthWorld();
				Vector2 velocity = BallisticVelocity(mouth, Main.player[NPC.target].Center, ScrapBallGravity);
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), mouth, velocity, ModContent.ProjectileType<TrashTr0mScrapBall>(),
					ProjectileDamage(ScrapBallDamage), 0f, out _);
			}
			if (Timer >= SpitBallTicks) {
				EndAttack();
			}
		}

		/// <summary>A lob that lands on <paramref name="to"/> with the given gravity: flight time grows with distance.</summary>
		public static Vector2 BallisticVelocity(Vector2 from, Vector2 to, float gravity) {
			Vector2 d = to - from;
			float time = MathHelper.Clamp(Math.Abs(d.X) / 9f, 30f, 75f);
			float vx = d.X / time;
			float vy = (d.Y - 0.5f * gravity * time * time) / time;
			return new Vector2(MathHelper.Clamp(vx, -16f, 16f), MathHelper.Clamp(vy, -18f, 10f));
		}
	}
}
