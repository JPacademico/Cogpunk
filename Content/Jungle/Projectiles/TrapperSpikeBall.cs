using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Jungle.Projectiles
{
	/// <summary>
	/// A spike ball lobbed by the <see cref="NPCs.Trapper"/>: it falls under <see cref="Gravity"/>, bounces (losing
	/// speed, <see cref="Bounce"/>) and then lies on the ground like the goblins' Spiky Balls (vanilla projectile 24,
	/// aiStyle 14, rolls to a stop), still hurting anyone who steps on it, for up to <see cref="Lifetime"/> ticks; it
	/// fades out over its last <see cref="FadeTicks"/>. Pre-rendered spin frames (no runtime rotation, D4), turned by the
	/// distance it rolls.
	/// <para>D2: a hostile projectile spawned by the server; <c>ai[1]</c> is the thrower (for its per-Trapper cap). D1: a
	/// fixed lifetime; the Trapper keeps at most 6 alive.</para>
	/// </summary>
	public class TrapperSpikeBall : CogpunkProjectile
	{
		public const float Gravity = 0.3f;
		public const float Bounce = 0.45f;
		public const float RollFriction = 0.94f;
		public const int Lifetime = 600;                   // 10 s
		public const int FadeTicks = 60;
		public const int Frames = 4;
		private const int FrameSize = 20, FrameStride = 22;

		private ref float Spin => ref Projectile.localAI[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 14;                           // vanilla Spiky Ball: 14x14
			Projectile.height = 14;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = -1;                       // a lingering trap: player immunity spaces the hits
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		/// <summary>The launch velocity of a lob from <paramref name="from"/> landing on <paramref name="to"/>: the flight
		/// lasts 30-60 ticks depending on distance, clamped so a far target just gets the strongest throw.</summary>
		public static Vector2 Lob(Vector2 from, Vector2 to) {
			Vector2 d = to - from;
			float time = MathHelper.Clamp(Math.Abs(d.X) / 6f, 30f, 60f);
			float vx = d.X / time;
			float vy = (d.Y - 0.5f * Gravity * time * time) / time;
			return new Vector2(MathHelper.Clamp(vx, -10f, 10f), MathHelper.Clamp(vy, -12f, 6f));
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 12f);
			Spin += Projectile.velocity.X * 0.08f;
			int frame = (int)Math.Floor(Spin) % Frames;
			Projectile.frame = frame < 0 ? frame + Frames : frame;
			Projectile.alpha = Projectile.timeLeft < FadeTicks ? (int)(255f * (1f - Projectile.timeLeft / (float)FadeTicks)) : 0;
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Math.Abs(Projectile.velocity.X - oldVelocity.X) > 0.01f) {
				Projectile.velocity.X = -oldVelocity.X * Bounce;
			}
			if (Math.Abs(Projectile.velocity.Y - oldVelocity.Y) > 0.01f) {
				Projectile.velocity.Y = Math.Abs(oldVelocity.Y) > 2f ? -oldVelocity.Y * Bounce : 0f;
				if (oldVelocity.Y > 0f) {
					Projectile.velocity.X *= RollFriction;    // on the ground: it rolls to a stop
					if (Math.Abs(Projectile.velocity.X) < 0.05f) {
						Projectile.velocity.X = 0f;
					}
				}
				if (Math.Abs(oldVelocity.Y) > 2f && !Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Dig with { Pitch = 0.6f, Volume = 0.4f, MaxInstances = 4 }, Projectile.Center);
				}
			}
			return false;                                    // it stays
		}

		public override bool TileCollideStyle(ref int width, ref int height, ref bool fallThrough, ref Vector2 hitboxCenterFrac) {
			fallThrough = false;                             // rests on platforms too
			return true;
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ || timeLeft <= 0) {
				return;
			}
			for (int i = 0; i < 4; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Iron, out _);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameSize, FrameSize);
			Vector2 centre = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Vector2 position = new((int)(centre.X - FrameSize * 0.5f), (int)(centre.Y - FrameSize * 0.5f));
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
