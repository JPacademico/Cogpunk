using System;
using Cogpunk.Content.Junkyard.Tar;
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

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The <see cref="TarShower"/>'s part-charged glob: thrown on a gravity arc with the charge's share of the damage
	/// (<see cref="TarShowerCharge"/>), it splats on the first enemy or tile and plagues what it hits. No stain: that takes a
	/// full charge (<see cref="TarShowerBigGlob"/>). <see cref="Headings"/> pre-rendered headings, never rotated (D4).
	/// </summary>
	public class TarShowerGlob : CogpunkProjectile
	{
		public const int Headings = 16;
		public const float Gravity = 0.22f;
		public const int PlagueTicks = 120;
		private const int FrameSize = 20, FrameStride = 22;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Headings;
		}

		public override void SetDefaults() {
			Projectile.width = 12;
			Projectile.height = 12;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = 1;
			Projectile.tileCollide = true;
			Projectile.timeLeft = 180;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 14f);
			MathSafety.Sanitize(ref Projectile.velocity);
			Projectile.frame = HeadingFrame(Projectile.velocity, Headings);
			if (!Main.dedServ && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust drip)) {
				drip.velocity = -Projectile.velocity * 0.15f;
			}
		}

		/// <summary>The pre-rendered heading for a velocity (0 = right, clockwise like screen angles).</summary>
		public static int HeadingFrame(Vector2 velocity, int headings) {
			float angle = MathHelper.WrapAngle(velocity.ToRotation());
			return ((int)Math.Round(angle / MathHelper.TwoPi * headings) % headings + headings) % headings;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			TarPlague.InflictOn(target, Main.player[Projectile.owner], PlagueTicks);
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCDeath1 with { Volume = 0.45f, Pitch = -0.1f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust d)) {
					d.velocity = Main.rand.NextVector2Circular(2.5f, 2.5f) - Vector2.UnitY;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Headings - 1) * FrameStride, FrameSize, FrameSize);
			Vector2 position = (Projectile.Center - Main.screenPosition - new Vector2(FrameSize * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
