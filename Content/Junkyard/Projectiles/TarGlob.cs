using System;
using Cogpunk.Content.Junkyard.NPCs;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Projectiles
{
	/// <summary>
	/// A glob of steaming tar flung by a <see cref="LivingTar"/> when it lands: a lob aimed to land on the target
	/// (<see cref="AimAt"/>), that splats on the first tile. A hit coats the player in tar: <see cref="TarPlague"/> for
	/// <see cref="LivingTar.TarTicks"/> ticks.
	/// <para>Art (user-set 2026-10-27: it has to read as a projectile, not a dropped item): a glob stretched into a
	/// teardrop with a trailing tail of drips, pre-rendered for <see cref="Headings"/> headings (heading 0 = flying right,
	/// clockwise, like the Mysterious Map's arrow) with <see cref="Wobbles"/> wobble frames each, so it always points along
	/// its velocity without rotating at runtime (D4). Frame = heading x Wobbles + wobble.</para>
	/// </summary>
	public class TarGlob : CogpunkProjectile
	{
		public const float Gravity = 0.2f;
		public const int Headings = 16;
		public const int Wobbles = 2;
		public const int Frames = Headings * Wobbles;
		public const int TicksPerFrame = 6;
		private const int FrameSize = 28, FrameStride = 30;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 12;
			Projectile.height = 12;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 150;
			Projectile.aiStyle = -1;
		}

		/// <summary>The launch velocity of a lob from <paramref name="from"/> that lands on <paramref name="to"/>: flight time
		/// grows with distance (20-50 ticks), clamped so a far or high target just gets the strongest throw.</summary>
		public static Vector2 AimAt(Vector2 from, Vector2 to) {
			Vector2 d = to - from;
			float time = MathHelper.Clamp(Math.Abs(d.X) / 7f, 20f, 50f);
			float vx = d.X / time;
			float vy = (d.Y - 0.5f * Gravity * time * time) / time;
			return new Vector2(MathHelper.Clamp(vx, -10f, 10f), MathHelper.Clamp(vy, -11f, 6f));
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 12f);
			if (++Projectile.frameCounter >= TicksPerFrame * Wobbles) {
				Projectile.frameCounter = 0;
			}
			Projectile.frame = Heading(Projectile.velocity) * Wobbles + Projectile.frameCounter / TicksPerFrame;
			if (!Main.dedServ && Main.rand.NextBool(5)
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust d)) {
				d.velocity *= 0.3f;                        // drips fall off it
			}
		}

		/// <summary>The nearest of the 16 pre-rendered headings (0 = right, clockwise in screen space).</summary>
		public static int Heading(Vector2 velocity) {
			if (velocity.LengthSquared() < 0.0001f) {
				return 4;                                    // straight down
			}
			int k = (int)MathF.Round(velocity.ToRotation() / MathHelper.TwoPi * Headings);
			return ((k % Headings) + Headings) % Headings;
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(ModContent.BuffType<TarPlague>(), LivingTar.TarTicks);
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCDeath1 with { Pitch = -0.4f, Volume = 0.5f, MaxInstances = 3 }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out _,
					Main.rand.NextFloat(-2f, 2f), -Main.rand.NextFloat(1f, 3f));
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
