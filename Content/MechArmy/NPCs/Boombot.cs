using System;
using Cogpunk.Content.MechArmy.Projectiles;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Content.Scrap.Weapons;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.MechArmy.MechArmyRigData;

namespace Cogpunk.Content.MechArmy.NPCs
{
	/// <summary>
	/// Boombot (user-set 2026-10-27: "fast but has low health and explodes on contact dealing high damage"): a walking bomb,
	/// redrawn 2026-10-28 as a black, rusted bomb with a lit fuse on short, quick legs. It sprints at its target and hops
	/// walls; the moment it touches a player it detonates (<see cref="BoombotBlast"/>, <see cref="BlastDamage"/> in Expert
	/// to everyone within <see cref="BoombotBlast.Radius"/> px) and is gone. Its warning: a beep and a flare of its fuse that
	/// speed up as it closes in (every <see cref="BeepSlowest"/> ticks at <see cref="BeepRange"/>, every
	/// <see cref="BeepFastest"/> at point blank). Killed first, it only pops: no blast, no damage, and it drops its loot.
	/// <para><b>Tripping</b> (user-set 2026-10-28: "a 2% chance of tripping while running and falling, rolling, then
	/// exploding, not necessarily on the player"): every <see cref="TripCheckInterval"/> ticks it spends sprinting on the
	/// ground it has a <see cref="TripChance"/> chance to catch a foot. It stumbles (<see cref="TripTicks"/>), pitches over
	/// face first with a little hop, lands and rolls on with its momentum (friction <see cref="RollFriction"/>, bouncing off
	/// walls), and when it stops (or after <see cref="RollMaxTicks"/>) its fuse flares and fizzes for
	/// <see cref="FizzTicks"/> ticks (the telegraph, beeping at <see cref="BeepFastest"/>) before it blows up where it lies.
	/// It still detonates at once if it rolls into a player. A detonation or a trip blast counts towards the invasion like a
	/// kill (it was spent) but drops nothing.</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor Goblin Thief, 160 life / 40 contact / 6 defense in
	/// Expert, value 200, the goblin army's fast fighter): <see cref="Life"/> life, <see cref="Defense"/> defense, no
	/// contact damage of its own (the blast is the damage), knockback resistance <see cref="KnockbackResist"/>. Drops (user,
	/// 2026-10-28): the Goblin Thief's coins, 1-2 Rusted Metal and 1-2 Scrap Bombs (pipe bombs).</para>
	/// <para>D2: the server sees the touch (player hitboxes as the server has them, plus <see cref="TouchMargin"/> px of
	/// slack for latency), rolls the trip, decides when the roll ends, spawns the synced hostile blast and removes the
	/// Boombot (SyncNPC); the trip's launch velocity is synced with the state change, and the roll (friction, wall bounce)
	/// runs the same on every side. While rolling its hitbox is the ball (<see cref="RollHeight"/>), from the synced state
	/// on every side. D0: the blast goes through <see cref="SafeSpawn"/>; if it is refused the Boombot keeps going and tries
	/// again next tick. D1: one pass over the players per tick on the server only; beeps and sparks are client-side.</para>
	/// </summary>
	public class Boombot : MechWalker
	{
		private enum Phase { Run, Leap, Trip, Fall, Roll, Fizz }

		public const int Life = 40, Defense = 4;
		public const float KnockbackResist = 0.6f;
		/// <summary>Blast damage in Expert (Classic half, Master 1.5x: <see cref="ExpertStats.HostileProjectile"/>).</summary>
		public const int BlastDamage = 70;
		public const float BlastKnockback = 7f;
		public const float RunSpeed = 5f;
		public const float Accel = 0.35f;
		public const float JumpSpeed = 8f;
		public const int TouchMargin = 4;
		public const float BeepRange = 30f * 16f;
		public const int BeepSlowest = 48, BeepFastest = 6;
		public const int LampFlashTicks = 5;
		public const float RunAnimDistance = 4f;           // short legs: a quick patter

		public const int Width = 26, Height = 34;
		public const int RollHeight = R.BoombotRadius * 2;
		public const int TripCheckInterval = 60;
		public const float TripChance = 0.02f;
		/// <summary>It only trips at a sprint (more than this fraction of <see cref="RunSpeed"/>).</summary>
		public const float TripMinSpeed = 0.6f;
		public const int TripTicks = 15;
		public const float FallHop = 3.5f;
		public const float FallPush = 1.15f;
		public const float MinRollSpeed = 3.5f;
		public const int FallMaxTicks = 90;
		public const float RollFriction = 0.985f;
		public const float RollStopSpeed = 0.6f;
		public const float WallBounce = 0.5f;
		public const int RollMaxTicks = 150;
		public const int FizzTicks = 36;                   // the blast's telegraph (D3: >= 30 ticks at T0-T4)
		/// <summary>Game px rolled per roll frame (an eighth of the ball's circumference: the art turns 45 degrees a frame).</summary>
		public const float RollAnimDistance = MathHelper.TwoPi * R.BoombotRadius / R.BoombotRollFrames;

		private static Asset<Texture2D> far, near, glow;
		private int beepTimer;
		private int lampTimer;
		private int rollFrame;

		private Phase CurrentPhase => (Phase)State;

		private bool Rolling => CurrentPhase == Phase.Roll || CurrentPhase == Phase.Fizz;

		protected override int CellWidth => R.BoombotCellWidth;
		protected override int CellHeight => R.BoombotCellHeight;
		protected override int OriginX => R.BoombotOriginX;
		protected override int OriginY => R.BoombotOriginY;
		protected override int FrameCount => R.BoombotFrames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;

		/// <summary>The fuse spark glows steadily (dimmer), flares on each beep and sputters while it fizzes.</summary>
		protected override float GlowStrength => CurrentPhase == Phase.Fizz ? 0.7f + 0.3f * ((int)Timer / 3 % 2) : (lampTimer > 0 ? 1f : 0.55f);

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			far = near = glow = null;
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, 0, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 200f;                                // the Goblin Thief's (decompiled NPC.SetDefaults, type 27)
			NPC.aiStyle = -1;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedMetal>(), 1, 1, 2));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<ScrapBomb>(), 1, 1, 2));
		}

		protected override void UpdateState() {
			FitHitbox();
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			float haste = Haste;
			switch (CurrentPhase) {
				case Phase.Leap:
					if (IsAuthority && ((Timer > 6f && Grounded) || Timer >= 120f)) {
						ChangeState((int)Phase.Run);
					}
					break;
				case Phase.Trip:
					UpdateTrip();
					break;
				case Phase.Fall:
					if (IsAuthority && ((Timer > 4f && Grounded) || Timer >= FallMaxTicks)) {
						ChangeState((int)Phase.Roll);
					}
					break;
				case Phase.Roll:
					UpdateRoll();
					break;
				case Phase.Fizz:
					NPC.velocity.X *= 0.8f;
					if (IsAuthority && Timer >= FizzTicks) {
						Detonate();
						return;
					}
					break;
				default:
					Run(target != null ? dir : NPC.direction == 0 ? -1 : NPC.direction, target != null ? RunSpeed * haste : RunSpeed * 0.25f, Accel * haste, JumpSpeed);
					if (IsAuthority && target != null && Grounded && target.Bottom.Y < NPC.Top.Y - 24f && Math.Abs(dx) < 120f) {
						NPC.velocity.Y = -JumpSpeed;                // hop up after a player above it
						ChangeState((int)Phase.Leap);
						break;
					}
					FaceMotion(dir);
					RollTrip(target);
					break;
			}
			if (IsAuthority && NPC.active) {
				CheckTouch();
			}
			if (!Main.dedServ && NPC.active) {
				Effects(target);
			}
		}

		/// <summary>Every side: the hitbox is the standing bomb, or just the ball while it rolls (bottom kept in place).</summary>
		private void FitHitbox() {
			int want = Rolling ? RollHeight : Height;
			if (NPC.height != want) {
				NPC.position.Y += NPC.height - want;
				NPC.height = want;
			}
		}

		/// <summary>Server: the 2% roll, once every <see cref="TripCheckInterval"/> ticks of sprinting on the ground.</summary>
		private void RollTrip(Player target) {
			if (!IsAuthority || target == null || !Grounded || Timer < TripCheckInterval || Timer % TripCheckInterval != 0f
				|| Math.Abs(NPC.velocity.X) < RunSpeed * TripMinSpeed) {
				return;
			}
			if (Main.rand.NextFloat() < TripChance) {
				ChangeState((int)Phase.Trip);
			}
		}

		/// <summary>Stumbling: it skids on, then (server) pitches over face first with a hop, its momentum kept.</summary>
		private void UpdateTrip() {
			NPC.velocity.X *= 0.94f;
			if (IsAuthority && Timer >= TripTicks) {
				int dir = NPC.direction == 0 ? -1 : NPC.direction;
				NPC.velocity = new Vector2(dir * Math.Max(Math.Abs(NPC.velocity.X) * FallPush, MinRollSpeed), -FallHop);
				ChangeState((int)Phase.Fall);
			}
		}

		/// <summary>Rolling on its momentum: friction on the ground, a bounce off walls; it fizzes once it stops (server).</summary>
		private void UpdateRoll() {
			if (NPC.collideX && Math.Abs(NPC.oldVelocity.X) > RollStopSpeed) {
				NPC.velocity.X = -NPC.oldVelocity.X * WallBounce;    // vanilla zeroed it against the wall
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item52 with { Volume = 0.5f, Pitch = 0.3f }, NPC.Center);
				}
			}
			if (Grounded) {
				NPC.velocity.X *= RollFriction;
			}
			Collision.StepUp(ref NPC.position, ref NPC.velocity, NPC.width, NPC.height, ref NPC.stepSpeed, ref NPC.gfxOffY);
			if (Math.Abs(NPC.velocity.X) > 0.15f) {
				NPC.direction = NPC.spriteDirection = Math.Sign(NPC.velocity.X);
			}
			if (IsAuthority && ((Grounded && Math.Abs(NPC.velocity.X) < RollStopSpeed) || Timer >= RollMaxTicks)) {
				ChangeState((int)Phase.Fizz);
			}
		}

		/// <summary>Server: detonates on the first living player it touches.</summary>
		private void CheckTouch() {
			Rectangle box = NPC.Hitbox;
			box.Inflate(TouchMargin, TouchMargin);
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && box.Intersects(player.Hitbox)) {
					Detonate();
					return;
				}
			}
		}

		/// <summary>Server: the blast, the invasion's credit, and the Boombot is gone (no loot: it was spent).</summary>
		private void Detonate() {
			int damage = ExpertStats.HostileProjectile(NPC, BlastDamage);
			if (!SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), NPC.Center, Vector2.Zero, ModContent.ProjectileType<BoombotBlast>(), damage, BlastKnockback, out _)) {
				return;
			}
			MechArmyInvasion army = ModContent.GetInstance<MechArmyInvasion>();
			army.Credit(army.KillValue(Type));
			NPC.life = 0;
			NPC.active = false;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
			}
		}

		/// <summary>Clients: the warning beep and fuse flare (faster the closer it is to its target, frantic while it
		/// fizzes), the trip's clank and the landing's thud, and the fuse's sparks.</summary>
		private void Effects(Player target) {
			if (lampTimer > 0) {
				lampTimer--;
			}
			Phase phase = CurrentPhase;
			if (Timer == 1f) {
				if (phase == Phase.Trip) {
					SoundEngine.PlaySound(SoundID.NPCHit4 with { Pitch = 0.6f, Volume = 0.7f }, NPC.Center);       // a foot catches
				}
				else if (phase == Phase.Roll) {
					SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.2f, Volume = 0.8f }, NPC.Center);       // it hits the ground
					for (int i = 0; i < 6; i++) {
						SafeSpawn.TryNewDust(NPC.BottomLeft + new Vector2(0f, -4f), NPC.width, 4, DustID.Smoke, out _);
					}
				}
				else if (phase == Phase.Fizz) {
					SoundEngine.PlaySound(SoundID.Item34 with { Pitch = 0.5f, Volume = 0.5f }, NPC.Center);        // the fuse hisses
				}
			}
			if (phase == Phase.Fizz) {
				if (--beepTimer <= 0) {
					beepTimer = BeepFastest;
					lampTimer = LampFlashTicks;
					SoundEngine.PlaySound(MechArmySounds.Beep with { Pitch = 0.5f }, NPC.Center);
				}
				if (CogpunkClientConfig.RollEffect() && SafeSpawn.TryNewDust(NPC.Center - new Vector2(8f), 16, 16, DustID.Torch, out Dust spark, 0f, -2f)) {
					spark.noGravity = true;
					spark.velocity = Main.rand.NextVector2Circular(2.5f, 2.5f);
				}
				return;
			}
			if (Rolling || target == null) {
				return;
			}
			float distance = Vector2.Distance(target.Center, NPC.Center);
			if (distance > BeepRange) {
				return;
			}
			if (--beepTimer <= 0) {
				float close = 1f - distance / BeepRange;
				beepTimer = (int)MathHelper.Lerp(BeepSlowest, BeepFastest, close * close);
				lampTimer = LampFlashTicks;
				SoundEngine.PlaySound(MechArmySounds.Beep with { Pitch = 0.3f * close }, NPC.Center);
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Trip:
					return R.BoombotTrip;
				case Phase.Fall:
					return Timer < 6f ? R.BoombotTrip : R.BoombotFall;
				case Phase.Roll:
				case Phase.Fizz:
					// The ball turns with the distance it rolls; the art rolls forward (left), and the sprite is mirrored when
					// it rolls right, so the frames always advance.
					NPC.frameCounter += Math.Abs(NPC.velocity.X);
					if (NPC.frameCounter >= RollAnimDistance) {
						int steps = (int)(NPC.frameCounter / RollAnimDistance);
						NPC.frameCounter -= steps * RollAnimDistance;
						rollFrame = (rollFrame + steps) % R.BoombotRollFrames;
					}
					return R.BoombotRoll + rollFrame;
			}
			if (CurrentPhase == Phase.Leap || !Grounded) {
				return R.BoombotLeap;
			}
			if (Math.Abs(NPC.velocity.X) > 0.3f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= RunAnimDistance * R.BoombotRunFrames) {
					NPC.frameCounter -= RunAnimDistance * R.BoombotRunFrames;
				}
				return R.BoombotRun + (int)(NPC.frameCounter / RunAnimDistance) % R.BoombotRunFrames;
			}
			return R.BoombotIdle + (int)(Timer / 15f) % 2;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 10;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, NPC.life > 0 ? DustID.Iron : DustID.Smoke, out _);
			}
			if (NPC.life <= 0) {
				// Shot down before it reached anyone: a dud pop, no blast.
				SoundEngine.PlaySound(SoundID.Item14 with { Volume = 0.35f, Pitch = 0.4f }, NPC.Center);
				MechArmyGores.Spawn(NPC, "Boombot_GoreShell", "Boombot_GoreLamp");
			}
		}
	}
}
