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

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// The Scrap Launcher's left-click shot: the same lump of chewed scrap Trash-Tr0m spits back
	/// (<see cref="Projectiles.TrashTr0mChewedScrap"/>: same size and tumble), re-rendered with friendly brass and aether
	/// glints instead of the boss's ember core (D3 colour coding). No gravity (user-set 2026-10-27): it flies dead straight
	/// for <see cref="Lifetime"/> x <see cref="ScrapLauncher.ChunkSpeed"/> = 1960 px, a whole 1920 px screen. Breaks on the
	/// first enemy or tile in a <see cref="ScrapImpact"/> burst.
	/// </summary>
	public class ScrapLauncherChunk : CogpunkProjectile
	{
		public const int Lifetime = 140;
		public const int Frames = 3;
		public const int TicksPerFrame = 5;
		private const int FrameSize = 32, FrameStride = 34;

		private ref float Launched => ref Projectile.localAI[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 20;                         // the 20 px lump in the 32 px frame
			Projectile.height = 20;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.tileCollide = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			if (Launched == 0f) {
				Launched = 1f;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item61 with { Pitch = -0.2f, Volume = 0.8f, MaxInstances = 3 }, Projectile.Center);
					LaunchPuff(Projectile.Center, Projectile.velocity, 5);
				}
			}
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + (Projectile.velocity.X >= 0f ? 1 : Frames - 1)) % Frames;
			}
			if (!Main.dedServ && Main.rand.NextBool(4) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Smoke, out Dust d, 0f, 0f, 120, new Color(127, 135, 148), 0.9f)) {
				d.velocity *= 0.2f;
				d.noGravity = true;
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ || timeLeft <= 0) {
				return;                                      // ran out of range: it just drops out of sight
			}
			ScrapImpact.Burst(Projectile.Center, Projectile.velocity, big: false);
		}

		public override bool PreDraw(ref Color lightColor) {
			DrawCentredFrame(Projectile, TextureAssets.Projectile[Type].Value, FrameSize, FrameSize, FrameStride, lightColor);
			return false;
		}

		/// <summary>Muzzle steam and brass sparks (clients).</summary>
		internal static void LaunchPuff(Vector2 at, Vector2 velocity, int count) {
			for (int i = 0; i < count; i++) {
				Vector2 v = velocity.RotatedByRandom(0.4f) * Main.rand.NextFloat(0.2f, 0.5f);
				if (SafeSpawn.TryNewDust(at - new Vector2(6f), 12, 12, i % 2 == 0 ? DustID.Smoke : DustID.Enchanted_Gold, out Dust d, v.X, v.Y, 80,
					i % 2 == 0 ? new Color(195, 200, 205) : default, i % 2 == 0 ? 1.2f : 0.9f)) {
					d.noGravity = true;
				}
			}
		}

		/// <summary>A frame of a vertical sheet centred on the projectile at whole pixels (pre-rendered spin, no rotation).</summary>
		internal static void DrawCentredFrame(Projectile projectile, Texture2D texture, int width, int height, int stride, Color light) {
			Rectangle source = new(0, projectile.frame * stride, width, height);
			Vector2 centre = projectile.Center - Main.screenPosition + new Vector2(0f, projectile.gfxOffY);
			Vector2 position = new((int)(centre.X - width * 0.5f), (int)(centre.Y - height * 0.5f));
			Main.EntitySpriteDraw(texture, position, source, projectile.GetAlpha(light), 0f, Vector2.Zero, 1f, SpriteEffects.None);
		}
	}
}
