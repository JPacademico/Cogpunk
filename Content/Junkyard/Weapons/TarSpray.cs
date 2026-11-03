using System;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// A burst of the <see cref="TarShower"/>'s spray: like vanilla's flamethrower flames it spreads as it flies (the hitbox
	/// grows with the sprite, <see cref="Frames"/> sizes over its <see cref="Lifetime"/>), slows, droops a little, goes
	/// through up to three enemies (each once) and stops at walls; mid range, ~16 tiles (4 more since 2026-11-03, user-set). Every enemy it touches gets the Tar
	/// Plague for <see cref="PlagueTicks"/> ticks (10 every half second and half speed, <see cref="TarPlagueNPC"/>).
	/// <para>D1: no allocation, a dust now and then on clients. D2: the owner's projectile, synced by vanilla.</para>
	/// </summary>
	public class TarSpray : CogpunkProjectile
	{
		public const int Lifetime = 36;
		public const int Frames = 5;
		public const int PlagueTicks = 120;
		public const float Drag = 0.985f;
		public const float Gravity = 0.05f;
		private const int FrameSize = 24, FrameStride = 26;
		private static readonly int[] HitboxSizes = { 12, 16, 20, 24, 28 };

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = HitboxSizes[0];
			Projectile.height = HitboxSizes[0];
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = 3;
			Projectile.tileCollide = true;
			Projectile.timeLeft = Lifetime;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;           // each burst hits each enemy once (flamethrower rule, 1.4.4)
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			Projectile.velocity *= Drag;
			Projectile.velocity.Y += Gravity;
			MathSafety.Sanitize(ref Projectile.velocity);
			int frame = Math.Clamp((Lifetime - Projectile.timeLeft) * Frames / Lifetime, 0, Frames - 1);
			if (frame != Projectile.frame) {
				Projectile.frame = frame;
				Projectile.Resize(HitboxSizes[frame], HitboxSizes[frame]);   // the spray spreads as it goes
			}
			if (!Main.dedServ && Main.rand.NextBool(6) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust drop)) {
				drop.velocity = Projectile.velocity * 0.3f;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			TarPlague.InflictOn(target, Main.player[Projectile.owner], PlagueTicks);
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out _);
			}
			return true;
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Frames - 1) * FrameStride, FrameSize, FrameSize);
			Vector2 position = (Projectile.Center - Main.screenPosition - new Vector2(FrameSize * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
