using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;

namespace Cogpunk.Content.Bosses.TrashTr0m.Projectiles
{
	/// <summary>
	/// Regurgitated scrap: what Trash-Tr0m swallowed during its suction (players' arrows, bullets, bolts...), chewed into
	/// a hot lump and spat back at its target, one per swallowed projectile (at most <see cref="TrashTr0m.MaxSpitBack"/>).
	/// A light arc; it breaks on tiles. The tumble is three pre-rendered frames (never a runtime rotation, D4).
	/// </summary>
	public class TrashTr0mChewedScrap : CogpunkProjectile
	{
		public const float Gravity = 0.12f;
		public const int Frames = 3;
		public const int TicksPerFrame = 5;
		private const int FrameSize = 32, FrameStride = 34;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 20;                         // the 20 px lump in the 32 px frame (measured from the sprite)
			Projectile.height = 20;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 180;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 12f);
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (!Main.dedServ && Main.rand.NextBool(4) && SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Smoke,
				out Dust d, 0f, 0f, 120, new Color(79, 85, 98), 0.9f)) {
				d.velocity *= 0.2f;
				d.noGravity = true;
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.2f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 6; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 2 == 0 ? DustID.Iron : DustID.Torch, out _);
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
