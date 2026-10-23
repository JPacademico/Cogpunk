using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Weapons
{
	/// <summary>
	/// The Scrappy Wand's spark: a small, fast yellow bolt (two updates per tick, so it moves 26 px/tick without skipping
	/// thin targets) that breaks on the first hit or tile. Drawn at full brightness, since it is the light source; the
	/// sprite points right and is rotated to its flight. Friendly colours come from the Brass ramp (D3 colour code).
	/// </summary>
	public class ScrappyWandBolt : CogpunkProjectile
	{
		private const int Lifetime = 60;                 // updates: 30 ticks, about 49 tiles
		private static readonly Vector3 LightColor = new(0.55f, 0.45f, 0.15f);

		public override void SetDefaults() {
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = 1;
			Projectile.tileCollide = true;
			Projectile.extraUpdates = 1;
			Projectile.timeLeft = Lifetime;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			Projectile.rotation = Projectile.velocity.ToRotation();
			if (Main.dedServ) {
				return;
			}
			Lighting.AddLight(Projectile.Center, LightColor);
			if (CogpunkClientConfig.RollEffect() && Main.rand.NextBool(3)
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.YellowTorch, out Dust trail)) {
				trail.noGravity = true;
				trail.velocity *= 0.2f;
				trail.scale = 0.8f;
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 4; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.YellowTorch, out Dust spark)) {
					spark.noGravity = true;
					spark.velocity *= 1.6f;
				}
			}
		}

		public override Color? GetAlpha(Color lightColor) {
			return Color.White * Projectile.Opacity;
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Main.EntitySpriteDraw(texture, Projectile.Center - Main.screenPosition, null, Projectile.GetAlpha(lightColor),
				Projectile.rotation, texture.Size() * 0.5f, 1f, SpriteEffects.None);
			return false;
		}
	}
}
