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

namespace Cogpunk.Content.Scrap.Armor
{
	/// <summary>
	/// Scrap armor set bonus shot: a spinning Rusted Cog lobbed in an arc (<see cref="Gravity"/>, capped at
	/// <see cref="MaxFallSpeed"/>). It bounces off up to <see cref="MaxBounces"/> walls or floors (the next contact breaks
	/// it) and breaks on the first enemy it hits. <c>ai[0]</c> = bounces so far (synced); the arc itself is deterministic
	/// from the synced velocity, so every client draws the same path (D2). Fired by <see cref="ScrapArmorPlayer"/>.
	/// </summary>
	public class ScrapCogProjectile : CogpunkProjectile
	{
		public const int MaxBounces = 3;
		private const string CogTexture = "Cogpunk/Content/Scrap/Items/RustedCog";   // looks like the Rusted Cog item
		private const int Size = 18;
		private const int Lifetime = 150;
		private const float SpinSpeed = 0.35f;
		private const float BounceDamping = 0.85f;
		public const float Gravity = 0.3f;                 // px/tick², a little floatier than a thrown item's 0.4
		public const float MaxFallSpeed = 16f;

		private string texture;
		public override string Texture => texture ??= TextureFallback.Resolve(CogTexture);

		private ref float Bounces => ref Projectile.ai[0];

		public override void SetDefaults() {
			Projectile.width = Size;
			Projectile.height = Size;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Generic;
			Projectile.penetrate = 1;                       // breaks on the first enemy
			Projectile.tileCollide = true;
			Projectile.timeLeft = Lifetime;
		}

		public override void AI() {
			if (Projectile.localAI[0] == 0f) {
				Projectile.localAI[0] = 1f;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item1 with { Pitch = 0.5f, Volume = 0.6f }, Projectile.Center);
				}
			}
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);
			MathSafety.Sanitize(ref Projectile.velocity);
			Projectile.rotation += SpinSpeed * (Projectile.velocity.X >= 0f ? 1f : -1f);
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Bounces >= MaxBounces) {
				return true;                                // fourth contact: the cog breaks
			}
			Bounces++;
			if (Projectile.velocity.X != oldVelocity.X) {
				Projectile.velocity.X = -oldVelocity.X * BounceDamping;
			}
			if (Projectile.velocity.Y != oldVelocity.Y) {
				Projectile.velocity.Y = -oldVelocity.Y * BounceDamping;
			}
			if (Projectile.owner == Main.myPlayer) {
				Projectile.netUpdate = true;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Tink with { Volume = 0.5f, PitchVariance = 0.3f }, Projectile.Center);
				SpawnSparks(3);
			}
			return false;
		}

		public override void OnKill(int timeLeft) {
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Tink, Projectile.Center);
				SpawnSparks(8);
			}
		}

		private void SpawnSparks(int count) {
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Copper, out Dust dust)) {
					dust.velocity *= 1.5f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D cog = TextureAssets.Projectile[Type].Value;
			Main.EntitySpriteDraw(cog, Projectile.Center - Main.screenPosition, null, Projectile.GetAlpha(lightColor),
				Projectile.rotation, cog.Size() * 0.5f, 1f, SpriteEffects.None);
			return false;
		}
	}
}
