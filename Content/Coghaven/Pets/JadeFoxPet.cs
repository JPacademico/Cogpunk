using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Pets
{
	/// <summary>
	/// The <see cref="JadeToken"/>'s spirit fox (user-set 2026-11-18: "a small jade colored spirit fox (ensure seamless animations
	/// and behavior like our other pet from the mod) that emits a bit of light"): it behaves like the
	/// <see cref="Scrap.Pets.ScrappybotPet"/>: it trots after its owner, hops ledges and up to them, floats over gaps as a
	/// spirit (paws tucked, tail streaming, through blocks) when it falls far behind, curls up to sleep when its owner stands
	/// still for 5 s and wakes with a stretch when they move. It gives off a little jade light (<see cref="Light"/>), its eye and
	/// tail flame drawn full-bright (the glow sheet).
	/// <para>Art: art/coghaven/make_jade_fox_art.py. Since 2026-11-23 the fox is the user's fennec, the exact in-game model
	/// (reference/jade_fox_user_2026-11-23.png, used with its author's permission) with only its colours changed to jade and
	/// two gilt pixels. Its 24 frames (cells of 26 x 24 at 1x) are that model's own parts moved, nothing added (the user,
	/// 2026-11-23: "a hoping animation does not need to create legs but to add wave motion to its body or tail"): the head bobs
	/// on the body, the front leaves the ground a pixel, a wave runs down the tail; it keeps to the ground while it follows
	/// (no bouncing: its trot frames carry the hop) and jumps only for ledges. The separate tail sheet below
	/// (JadeFoxPet_Tail.png) belonged to an earlier fox; it is drawn only when its width matches the body sheet, so the fennec
	/// (52 px wide) leaves it unused.</para>
	/// <para>D2: its state in <c>ai[0]</c>/<c>ai[1]</c> (synced); only the owner changes state, other clients run the same
	/// physics and frames. D0: NaN guards, the owner index checked. D1: no allocation; light and drawing on clients.</para>
	/// </summary>
	public class JadeFoxPet : CogpunkProjectile
	{
		private enum PetState { Follow, Float, Sleep, Wake }

		public const int FrameCount = 24;
        public const int TailFrames = 16, TailTicksPerFrame = 3;
        private static readonly sbyte[] TailBodyOffset = { 0, 0, 1, 1, 0, 1, 0, -1, 0, 1, 0, -1, -1, 0, 1, 2, 2, 2, 2, 1, 0 };
		public const int FrameIdle = 0, IdleFrames = 4, IdleTicksPerFrame = 12;
		public const int FrameTrot = 4, TrotFrames = 6;
		public const int FrameFloat = 10, FloatFrames = 4, FloatTicksPerFrame = 6;
		public const int FrameSettle = 14, SettleTicksPerFrame = 12;
		public const int FrameSleep = 16, SleepTicksPerFrame = 36;
		public const int FrameWake = 18, WakeTicksPerFrame = 6, WakeTicks = 3 * WakeTicksPerFrame;
		public const int FrameJump = 21;                         // rising, the top of the arc, falling
		/// <summary>The idle frames in order, a step every <see cref="IdleTicksPerFrame"/> ticks (3.2 s): rest, a tail swish, an
		/// ear flick, one blink.</summary>
		private static readonly byte[] IdleSequence = { 0, 0, 1, 1, 0, 0, 0, 2, 0, 0, 1, 1, 0, 0, 0, 3 };
		// 2026-11-23 (the user's fennec, the exact model recoloured): cells of 52 x 48 (26 x 24 at 1x); the body's middle 26 px
		// from the cell's left, 2 px of gap under the cell
		public const int OriginX = 26, FootPadding = 2;
		/// <summary>Ground covered a trot frame: 6 frames a hop, so about 3 hops a second at its walk (4.5 px a tick).</summary>
		public const float TrotAnimDistance = 14f;
		public static readonly Vector3 Light = new(0.12f, 0.34f, 0.26f);   // "a bit of light": jade, faint

		public const int SleepDelay = 300;                      // owner still for 5 s
		private const float Gravity = 0.4f, MaxFallSpeed = 10f, Acceleration = 0.3f, WalkSpeed = 4.5f, RunSpeed = 7.5f, JumpSpeed = 7.5f;
		/// <summary>How far behind its owner it walks, and where it floats (behind and above): the fox is 72 px long, its head
		/// 22 px in front of its middle, so 52 px keeps it just off its owner.</summary>
		public const float FollowOffset = 52f, FloatBehind = 52f, FloatAbove = 40f;
		private const float FloatStartDistance = 480f, FloatStopDistance = 120f, WakeDistance = 200f, TeleportDistance = 2000f;
		private const int StuckTicksBeforeFloating = 45;
		/// <summary>Blocked by a wall this far or more from its spot, it counts as stuck (the Scrappybot's 160 px left a fox hopping
		/// forever at a wall closer than that: 2026-11-18, found in the D5 replay).</summary>
		public const float StuckDistance = 64f;

		private static Asset<Texture2D> glowSheet, tailSheet;

		private PetState State {
			get => (PetState)(int)Projectile.ai[0];
			set => Projectile.ai[0] = (float)value;
		}

		private ref float StateTimer => ref Projectile.ai[1];
		private ref float StillTicks => ref Projectile.localAI[0];
		private ref float TrotDistance => ref Projectile.localAI[1];
		private ref float StuckTicks => ref Projectile.localAI[2];

		private bool onGround, hitWall;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = FrameCount;
			Main.projPet[Type] = true;
			ProjectileID.Sets.CharacterPreviewAnimations[Type] = ProjectileID.Sets.SimpleLoop(FrameTrot, TrotFrames, 5)
				.WhenNotSelected(FrameIdle, 2, 24)
				.WithOffset(-10f, 0f);
			if (!Main.dedServ) {
				const string path = "Cogpunk/Content/Coghaven/Pets/JadeFoxPet_Glow";
				glowSheet = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
                const string tailPath = "Cogpunk/Content/Coghaven/Pets/JadeFoxPet_Tail";
                tailSheet = ModContent.HasAsset(tailPath) ? ModContent.Request<Texture2D>(tailPath) : null;
			}
		}

		public override void Unload() {
			glowSheet = tailSheet = null;
		}

		public override void SetDefaults() {
			Projectile.width = 24;
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
			if (!owner.dead && owner.HasBuff<JadeFoxBuff>()) {
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
				case PetState.Float:
					UpdateFloat(owner, isOwner);
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
			MathSafety.Sanitize(ref Projectile.velocity);
			if (!MathSafety.IsFinite(Projectile.position)) {
				Projectile.Center = owner.Center;
			}
			UpdateFrame(grounded);
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, State == PetState.Sleep ? Light * 0.6f : Light);
			}
		}

		private void UpdateFollow(Player owner, bool isOwner, bool grounded, bool blocked, float distanceSq) {
			Projectile.tileCollide = true;
			float dx = owner.Center.X - (owner.direction * FollowOffset) - Projectile.Center.X;
			float absDx = Math.Abs(dx);
			bool wantsToMove = absDx > 24f;
			if (wantsToMove) {
				float maxSpeed = absDx > 160f ? RunSpeed : WalkSpeed;
				Projectile.velocity.X = MathHelper.Clamp(Projectile.velocity.X + Math.Sign(dx) * Acceleration, -maxSpeed, maxSpeed);
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
				Projectile.velocity.Y = -JumpSpeed;            // a ledge or its owner above: a real jump (its trot frames hop)
				if (isOwner) {
					Projectile.netUpdate = true;
				}
			}
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);
			StuckTicks = wantsToMove && blocked && absDx > StuckDistance ? StuckTicks + 1 : 0f;
			if (!isOwner) {
				return;
			}
			if (distanceSq > FloatStartDistance * FloatStartDistance || StuckTicks > StuckTicksBeforeFloating) {
				ChangeState(PetState.Float, isOwner);
				return;
			}
			bool ownerStill = owner.velocity.LengthSquared() < 0.01f;
			StillTicks = ownerStill && grounded && !wantsToMove ? StillTicks + 1 : 0f;
			if (StillTicks >= SleepDelay) {
				ChangeState(PetState.Sleep, isOwner);
			}
		}

		/// <summary>The spirit float: through blocks, to a point behind and above its owner; a wisp now and then.</summary>
		private void UpdateFloat(Player owner, bool isOwner) {
			Projectile.tileCollide = false;
			Vector2 target = owner.Center + new Vector2(-owner.direction * FloatBehind, -FloatAbove);
			Vector2 toTarget = target - Projectile.Center;
			float speed = Math.Min(toTarget.Length() / 12f + 2f, 14f);
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, toTarget.SafeNormalize(Vector2.Zero) * speed, 0.1f);
			if (Math.Abs(Projectile.velocity.X) > 0.2f) {
				Projectile.spriteDirection = Math.Sign(Projectile.velocity.X);
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect() && Main.rand.NextBool(4)
				&& SafeSpawn.TryNewDust(Projectile.Bottom + new Vector2(-8f, -6f), 16, 4, DustID.GemEmerald, out Dust wisp, 0f, 0.6f)) {
				wisp.noGravity = true;
				wisp.scale = 0.7f;
			}
			if (isOwner && Vector2.DistanceSquared(owner.Center, Projectile.Center) < FloatStopDistance * FloatStopDistance
				&& owner.velocity.Y == 0f && !Collision.SolidCollision(Projectile.position, Projectile.width, Projectile.height)) {
				ChangeState(PetState.Follow, isOwner);
			}
		}

		private void UpdateSleep(Player owner, bool isOwner, float distanceSq) {
			Projectile.tileCollide = true;
			Projectile.velocity.X *= 0.8f;
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);
			if (isOwner && (owner.velocity.LengthSquared() > 0.25f || distanceSq > WakeDistance * WakeDistance)) {
				ChangeState(PetState.Wake, isOwner);
			}
		}

		private void UpdateWake(bool isOwner, bool grounded) {
			Projectile.tileCollide = true;
			Projectile.velocity.X = 0f;
			if (StateTimer == 1f && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item25 with { Volume = 0.25f, Pitch = 0.6f }, Projectile.Center);
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
				case PetState.Float:
					Projectile.frame = FrameFloat + t / FloatTicksPerFrame % FloatFrames;
					break;
				case PetState.Sleep:
					Projectile.frame = t < SettleTicksPerFrame * 2 ? FrameSettle + t / SettleTicksPerFrame
						: FrameSleep + (t - SettleTicksPerFrame * 2) / SleepTicksPerFrame % 2;
					break;
				case PetState.Wake:
					Projectile.frame = FrameWake + Math.Min(2, t / WakeTicksPerFrame);
					break;
				default:
					float speed = Math.Abs(Projectile.velocity.X);
					if (!grounded && Math.Abs(Projectile.velocity.Y) > 0.5f) {
						Projectile.frame = FrameJump + (Projectile.velocity.Y < -1.8f ? 0 : Projectile.velocity.Y < 1.8f ? 1 : 2);
					}
					else if (speed > 0.3f) {
						if (Projectile.frame < FrameTrot || Projectile.frame >= FrameTrot + TrotFrames) {
							Projectile.frame = FrameTrot;
						}
						TrotDistance += speed;
						if (TrotDistance >= TrotAnimDistance) {
							TrotDistance = 0f;
							Projectile.frame = FrameTrot + (Projectile.frame - FrameTrot + 1) % TrotFrames;
						}
					}
					else {
						Projectile.frame = FrameIdle + IdleSequence[(int)(Main.GameUpdateCount / IdleTicksPerFrame % (uint)IdleSequence.Length)];
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

		// Anchored to the hitbox bottom (the feet on the ground) at the art's own foot point, flipped by direction, on whole
		// pixels, never turned (D4); the glow sheet (eye, tail flame, wisps) full-bright over it.
		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frameHeight = texture.Height / FrameCount;
			int frame = Math.Clamp(Projectile.frame, 0, FrameCount - 1);
			Rectangle source = new(0, frame * frameHeight, texture.Width, frameHeight);
			bool flip = Projectile.spriteDirection == -1;
			Vector2 origin = new(flip ? texture.Width - OriginX : OriginX, frameHeight - FootPadding);
			Vector2 position = (Projectile.Bottom + new Vector2(0f, Projectile.gfxOffY) - Main.screenPosition).Floor();
			SpriteEffects effects = flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
            if (tailSheet?.IsLoaded == true && tailSheet.Value.Width == texture.Width) {
                Texture2D tail = tailSheet.Value;
                int stride = tail.Height / TailFrames;
                int tailFrame = (int)(Main.GameUpdateCount / (State == PetState.Sleep ? 7u : (uint)TailTicksPerFrame) % TailFrames);
                Rectangle tailSource = new(0, tailFrame * stride, tail.Width, stride - FootPadding);
                Vector2 tailPosition = position + new Vector2(0f, TailBodyOffset[Math.Clamp(Projectile.frame, 0, TailBodyOffset.Length - 1)] * 2);
                if (tailSource.Height > 0 && tailSource.Bottom <= tail.Height) {
                    Main.EntitySpriteDraw(tail, tailPosition, tailSource, Projectile.GetAlpha(lightColor), 0f, origin, 1f, effects);
                }
            }
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), 0f, origin, 1f, effects);
			if (glowSheet?.IsLoaded == true && glowSheet.Value.Height == texture.Height) {
				Main.EntitySpriteDraw(glowSheet.Value, position, source, Color.White * Projectile.Opacity, 0f, origin, 1f, effects);
			}
			return false;
		}
	}
}
