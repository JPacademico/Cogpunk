using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Pets
{
	/// <summary>
	/// A small rusted box robot that rolls after its owner on tank treads, hops over ledges, jets over gaps
	/// when it falls far behind, powers down to recharge after the owner stands still for 5 seconds, and
	/// clunks awake when they move again.
	/// <para>States live in <c>ai[0]</c>/<c>ai[1]</c> (synced). Only the owner's client changes state; other
	/// clients run the same physics and animation and follow the synced state (D2). Constants are mirrored in
	/// tools/sim/scrappybot_sim.py for the D5 animation proof.</para>
	/// </summary>
	public class ScrappybotPet : CogpunkProjectile
	{
		private enum PetState { Follow, Fly, Sleep, Wake }

		// ScrappybotPet.png: 16 frames of 32x36 (16x18 art), facing right.
		private const int FrameCount = 16;
		private const int FrameIdle = 0;
		private const int FrameWalk = 1;      // 4 frames
		private const int FrameFly = 5;       // 2 frames
		private const int FrameSettle = 7;    // 2 frames
		private const int FrameSleep = 9;     // 3 frames (charge lights filling)
		private const int FrameWake = 12;     // 4 frames
		private const int FootPadding = 2;    // transparent rows under the treads

		// Timing (ticks; 60 per second). Multiples of 3 keep the D5 GIF timing exact.
		public const int SleepDelay = 300;           // owner still for 5 s
		public const int SettleTicksPerFrame = 12;
		public const int SleepTicksPerFrame = 18;
		public const int FlyTicksPerFrame = 6;
		public const float WalkAnimDistance = 9f;    // pixels travelled per walk frame
		private const int WakeEnd1 = 3, WakeEnd2 = 9, WakeEnd3 = 12, WakeTicks = 18;  // clunky, uneven wake frames

		// Movement.
		private const float Gravity = 0.4f;
		private const float MaxFallSpeed = 10f;
		private const float Acceleration = 0.25f;
		private const float WalkSpeed = 4.5f;
		private const float RunSpeed = 7f;
		private const float JumpSpeed = 7.5f;
		private const float FollowOffset = 48f;
		private const float FlyStartDistance = 480f;
		private const float FlyStopDistance = 120f;
		private const float WakeDistance = 200f;
		private const float TeleportDistance = 2000f;
		private const int StuckTicksBeforeFlying = 45;

		private PetState State {
			get => (PetState)(int)Projectile.ai[0];
			set => Projectile.ai[0] = (float)value;
		}

		private ref float StateTimer => ref Projectile.ai[1];
		private ref float StillTicks => ref Projectile.localAI[0];   // owner client only
		private ref float WalkDistance => ref Projectile.localAI[1];
		private ref float StuckTicks => ref Projectile.localAI[2];

		// Set by OnTileCollide during movement, read by the next AI tick. Per-instance and visual/physics only.
		private bool onGround;
		private bool hitWall;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = FrameCount;
			Main.projPet[Type] = true;
			ProjectileID.Sets.CharacterPreviewAnimations[Type] = ProjectileID.Sets.SimpleLoop(FrameWalk, 4, 6)
				.WhenNotSelected(FrameIdle, 1)
				.WithOffset(-8f, 0f);
		}

		public override void SetDefaults() {
			Projectile.width = 20;
			Projectile.height = 24;
			Projectile.aiStyle = -1;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.netImportant = true;
			Projectile.timeLeft = 2;
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			if (!owner.active) {
				Projectile.Kill();
				return;
			}
			if (!owner.dead && owner.HasBuff<ScrappybotBuff>()) {
				Projectile.timeLeft = 2;
			}

			bool isOwner = Projectile.owner == Main.myPlayer;
			bool grounded = onGround;
			bool blocked = hitWall;
			onGround = false;
			hitWall = false;

			float distanceSq = Vector2.DistanceSquared(owner.Center, Projectile.Center);
			if (isOwner && distanceSq > TeleportDistance * TeleportDistance) {
				Projectile.Center = owner.Center;
				Projectile.velocity = Vector2.Zero;
				ChangeState(PetState.Follow, isOwner);
				Projectile.netUpdate = true;
			}

			StateTimer++;
			switch (State) {
				case PetState.Fly:
					UpdateFly(owner, isOwner);
					break;
				case PetState.Sleep:
					UpdateSleep(owner, isOwner, distanceSq);
					break;
				case PetState.Wake:
					UpdateWake(isOwner, grounded);
					break;
				default:
					UpdateFollow(owner, isOwner, grounded, blocked, distanceSq);
					break;
			}

			// D0: never let NaN movement through (it makes the pet vanish and breaks drawing).
			MathSafety.Sanitize(ref Projectile.velocity);
			if (!MathSafety.IsFinite(Projectile.position)) {
				Projectile.Center = owner.Center;
			}
			UpdateFrame(grounded);
		}

		private void UpdateFollow(Player owner, bool isOwner, bool grounded, bool blocked, float distanceSq) {
			Projectile.tileCollide = true;
			float dx = owner.Center.X - (owner.direction * FollowOffset) - Projectile.Center.X;
			float absDx = Math.Abs(dx);
			bool wantsToMove = absDx > 24f;

			if (wantsToMove) {
				float maxSpeed = absDx > 160f ? RunSpeed : WalkSpeed;
				Projectile.velocity.X = MathHelper.Clamp(Projectile.velocity.X + (Math.Sign(dx) * Acceleration), -maxSpeed, maxSpeed);
				Projectile.spriteDirection = Math.Sign(dx);
			}
			else {
				Projectile.velocity.X *= 0.85f;
				if (Math.Abs(Projectile.velocity.X) < 0.05f) {
					Projectile.velocity.X = 0f;
				}
				Projectile.spriteDirection = owner.Center.X >= Projectile.Center.X ? 1 : -1;
			}

			Collision.StepUp(ref Projectile.position, ref Projectile.velocity, Projectile.width, Projectile.height, ref Projectile.stepSpeed, ref Projectile.gfxOffY);

			bool ownerAbove = owner.velocity.Y == 0f && owner.Bottom.Y < Projectile.Bottom.Y - 48f && absDx < 160f;
			if (grounded && ((wantsToMove && blocked) || ownerAbove)) {
				Projectile.velocity.Y = -JumpSpeed;
			}
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);

			StuckTicks = wantsToMove && blocked && absDx > 160f ? StuckTicks + 1 : 0f;
			if (!isOwner) {
				return;
			}
			if (distanceSq > FlyStartDistance * FlyStartDistance || StuckTicks > StuckTicksBeforeFlying) {
				ChangeState(PetState.Fly, isOwner);
				return;
			}

			bool ownerStill = owner.velocity.LengthSquared() < 0.01f;
			StillTicks = ownerStill && grounded && !wantsToMove ? StillTicks + 1 : 0f;
			if (StillTicks >= SleepDelay) {
				ChangeState(PetState.Sleep, isOwner);
			}
		}

		private void UpdateFly(Player owner, bool isOwner) {
			Projectile.tileCollide = false;
			Vector2 target = owner.Center + new Vector2(-owner.direction * 40f, -40f);
			Vector2 toTarget = target - Projectile.Center;
			float speed = Math.Min((toTarget.Length() / 12f) + 2f, 14f);
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, toTarget.SafeNormalize(Vector2.Zero) * speed, 0.1f);
			if (Math.Abs(Projectile.velocity.X) > 0.2f) {
				Projectile.spriteDirection = Math.Sign(Projectile.velocity.X);
			}

			if (!Main.dedServ && CogpunkClientConfig.RollEffect() && Main.rand.NextBool(3)
				&& SafeSpawn.TryNewDust(Projectile.Bottom + new Vector2(-8f, -4f), 16, 4, DustID.Torch, out Dust flame, 0f, 2f)) {
				flame.noGravity = true;
				flame.scale = 0.9f;
			}

			if (isOwner && Vector2.DistanceSquared(owner.Center, Projectile.Center) < FlyStopDistance * FlyStopDistance
				&& owner.velocity.Y == 0f && !Collision.SolidCollision(Projectile.position, Projectile.width, Projectile.height)) {
				ChangeState(PetState.Follow, isOwner);
			}
		}

		private void UpdateSleep(Player owner, bool isOwner, float distanceSq) {
			Projectile.tileCollide = true;
			Projectile.velocity.X *= 0.8f;
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);

			if (!Main.dedServ && StateTimer > SettleTicksPerFrame * 2 && Main.rand.NextBool(150)
				&& SafeSpawn.TryNewDust(Projectile.Center + new Vector2(-6f, 2f), 12, 4, DustID.Electric, out Dust spark, 0f, -0.6f)) {
				spark.noGravity = true;
				spark.scale = 0.5f;
			}

			if (isOwner && (owner.velocity.LengthSquared() > 0.25f || distanceSq > WakeDistance * WakeDistance)) {
				ChangeState(PetState.Wake, isOwner);
			}
		}

		private void UpdateWake(bool isOwner, bool grounded) {
			Projectile.tileCollide = true;
			Projectile.velocity.X = 0f;
			if (StateTimer == 1f) {
				if (grounded) {
					Projectile.velocity.Y = -2.5f;  // the clunky jolt
				}
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Tink with { Volume = 0.4f, Pitch = -0.35f }, Projectile.Center);
					for (int i = 0; i < 4; i++) {
						if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, 8, DustID.Electric, out Dust spark, Main.rand.NextFloat(-1.5f, 1.5f), -1.5f)) {
							spark.noGravity = true;
							spark.scale = 0.6f;
						}
					}
				}
			}
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);

			if (isOwner && StateTimer >= WakeTicks) {
				ChangeState(PetState.Follow, isOwner);
			}
		}

		/// <summary>Only the owner decides; the change reaches the server and other clients through ai[] (D2).</summary>
		private void ChangeState(PetState next, bool isOwner) {
			if (!isOwner) {
				return;
			}
			State = next;
			StateTimer = 0f;
			StillTicks = 0f;
			StuckTicks = 0f;
			Projectile.netUpdate = true;
		}

		private void UpdateFrame(bool grounded) {
			int t = (int)StateTimer;
			switch (State) {
				case PetState.Fly:
					Projectile.frame = FrameFly + ((t / FlyTicksPerFrame) % 2);
					break;
				case PetState.Sleep:
					if (t < SettleTicksPerFrame) {
						Projectile.frame = FrameSettle;
					}
					else if (t < SettleTicksPerFrame * 2) {
						Projectile.frame = FrameSettle + 1;
					}
					else {
						Projectile.frame = FrameSleep + (((t - (SettleTicksPerFrame * 2)) / SleepTicksPerFrame) % 3);
					}
					break;
				case PetState.Wake:
					Projectile.frame = FrameWake + (t < WakeEnd1 ? 0 : t < WakeEnd2 ? 1 : t < WakeEnd3 ? 2 : 3);
					break;
				default:
					float speed = Math.Abs(Projectile.velocity.X);
					if (!grounded && Projectile.velocity.Y < -0.5f) {
						Projectile.frame = FrameWalk + 1;            // squashed on the treads mid-hop
					}
					else if (speed > 0.3f) {
						if (Projectile.frame < FrameWalk || Projectile.frame >= FrameWalk + 4) {
							Projectile.frame = FrameWalk;
						}
						WalkDistance += speed;
						if (WalkDistance >= WalkAnimDistance) {
							WalkDistance = 0f;
							Projectile.frame = FrameWalk + ((Projectile.frame - FrameWalk + 1) % 4);
						}
					}
					else {
						Projectile.frame = FrameIdle;
					}
					break;
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Projectile.velocity.X != oldVelocity.X) {
				hitWall = true;
			}
			if (Projectile.velocity.Y != oldVelocity.Y && oldVelocity.Y > 0f) {
				onGround = true;
			}
			return false;
		}

		// Drawn by hand: anchored to the hitbox bottom (treads on the ground), flipped by direction,
		// snapped to whole pixels and never rotated, so the pixel art stays crisp (D4).
		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frameHeight = texture.Height / FrameCount;
			int frame = Math.Clamp(Projectile.frame, 0, FrameCount - 1);
			Rectangle source = new(0, frame * frameHeight, texture.Width, frameHeight);
			Vector2 origin = new(texture.Width * 0.5f, frameHeight - FootPadding);
			Vector2 position = (Projectile.Bottom + new Vector2(0f, Projectile.gfxOffY) - Main.screenPosition).Floor();
			SpriteEffects effects = Projectile.spriteDirection == -1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), 0f, origin, 1f, effects);
			return false;
		}
	}
}
