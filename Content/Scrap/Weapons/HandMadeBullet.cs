using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Weapons
{
	/// <summary>
	/// The <see cref="HandMadeGun"/>'s copper-jacketed slug: fast (28 px/tick across two updates), zero spread, and bounces
	/// once off the first wall it strikes before breaking on a second wall or its first enemy hit. Pre-rendered in
	/// <see cref="Headings"/> headings (D4: never rotated at runtime).
	/// </summary>
	public class HandMadeBullet : CogpunkProjectile
	{
		public const int Headings = 16;
		public const int Lifetime = 240;
		private const int Cell = 12, Stride = 14;

		private ref float Bounces => ref Projectile.ai[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Headings;
		}

		public override void SetDefaults() {
			Projectile.width = 6;
			Projectile.height = 6;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = 1;
			Projectile.tileCollide = true;
			Projectile.extraUpdates = 1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			float a = Projectile.velocity.ToRotation();
			Projectile.frame = (int)Math.Round(MathHelper.WrapAngle(a) / MathHelper.TwoPi * Headings + Headings) % Headings;
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.28f, 0.20f, 0.08f);
				SmokeTrails.Add(Projectile.Center, Projectile.Center + Projectile.velocity);
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Bounces >= 1f) {
				return true;
			}
			Bounces = 1f;
			if (Projectile.velocity.X != oldVelocity.X) {
				Projectile.velocity.X = -oldVelocity.X;
			}
			if (Projectile.velocity.Y != oldVelocity.Y) {
				Projectile.velocity.Y = -oldVelocity.Y;
			}
			if (Projectile.owner == Main.myPlayer) {
				Projectile.netUpdate = true;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item10 with { Pitch = 0.4f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);
				for (int i = 0; i < 4; i++) {
					SafeSpawn.TryNewDust(Projectile.Center - new Vector2(3f), 6, 6, DustID.Copper, out _);
				}
			}
			return false;
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Headings - 1) * Stride, Cell, Cell);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Cell * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, Color.Lerp(lightColor, Color.White, 0.55f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
