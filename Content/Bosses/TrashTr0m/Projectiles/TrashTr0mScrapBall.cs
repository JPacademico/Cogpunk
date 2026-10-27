using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;

namespace Cogpunk.Content.Bosses.TrashTr0m.Projectiles
{
	/// <summary>
	/// The big scrap ball Trash-Tr0m spits when its suction caught nothing: a lob aimed to land on the target
	/// (<see cref="TrashTr0m.BallisticVelocity"/>) that shatters on the ground. Its spin is four pre-rendered frames, a
	/// quarter turn apart (D4: no runtime rotation).
	/// </summary>
	public class TrashTr0mScrapBall : CogpunkProjectile
	{
		public const float Gravity = 0.3f;
		public const int Frames = 4;
		public const int TicksPerFrame = 5;
		private const int FrameSize = 60, FrameStride = 62;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 50;                         // the 50-52 px ball in the 60 px frame (measured from the sprite)
			Projectile.height = 50;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 240;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 16f);
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				int step = Projectile.velocity.X >= 0f ? 1 : Frames - 1;      // spins the way it flies
				Projectile.frame = (Projectile.frame + step) % Frames;
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect() && Main.rand.NextBool(2)
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Smoke, out Dust d, 0f, 0f, 120, new Color(127, 135, 148), 1.2f)) {
				d.velocity *= 0.2f;
				d.noGravity = true;
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.4f }, Projectile.Center);
			SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.6f }, Projectile.Center);
			if (CogpunkClientConfig.Instance?.ScreenShake ?? true) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(Projectile.Center, Vector2.UnitY, 5f, 8f, 14, 1200f, "Cogpunk:TrashTr0mBall"));
			}
			for (int i = 0; i < 24; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 3 == 0 ? DustID.Torch : DustID.Iron, out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-5f, 5f), -Main.rand.NextFloat(2f, 7f));
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameSize, FrameSize);
			Vector2 centre = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Vector2 position = new((int)(centre.X - FrameSize * 0.5f), (int)(centre.Y - FrameSize * 0.5f));
			Main.EntitySpriteDraw(texture, position, source, lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
