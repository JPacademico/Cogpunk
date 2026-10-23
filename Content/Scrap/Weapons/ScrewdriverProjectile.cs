using System;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Weapons
{
	/// <summary>
	/// The Screwdriver's thrust, a held projectile in the shape of ExampleMod 1.4.4's <c>ExampleSpearProjectile</c>: over the
	/// item's use animation (<c>itemAnimationMax</c>, so melee speed applies) the tip eases out from <see cref="ReachMin"/> to
	/// <see cref="ReachMax"/> (6.5 tiles; the vanilla Spear reaches about 5) and back.
	/// <para>Two hits per thrust: local NPC immunity lasts for the whole projectile (<c>localNPCHitCooldown = -1</c>), and
	/// it is cleared once when the tip turns around, so every NPC can be hit once going out and once coming back. Damage
	/// is decided by the owner's client, which is where that reset matters (D2).</para>
	/// <para>The hitbox is the shaft itself (a line from the handle to the tip, <see cref="Colliding"/>), so the reach is
	/// exact at any angle. The sprite points right and is rotated to the thrust; it is drawn with the player as their
	/// held projectile.</para>
	/// </summary>
	public class ScrewdriverProjectile : CogpunkProjectile
	{
		public const float ReachMin = 40f;               // tip distance from the player's centre at rest
		public const float ReachMax = 104f;              // 6.5 tiles
		private const float Length = 54f;                // sprite length (2x art), the sharp point at the right end
		private const float ShaftWidth = 10f;
		private const float GripInset = 8f;              // the hand covers the last pixels of the handle: they don't hit

		private ref float ReturnStarted => ref Projectile.localAI[0];

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.aiStyle = -1;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.DamageType = DamageClass.Melee;
			Projectile.ownerHitCheck = true;             // no hits through walls
			Projectile.hide = true;                      // drawn by the player as heldProj
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;         // once per NPC until the reset at the turn
			Projectile.timeLeft = 3600;                  // clamped to the use animation in AI
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player player = Main.player[Projectile.owner];
			if (!player.active || player.dead || player.CCed || player.noItems) {
				Projectile.Kill();
				return;
			}
			int duration = Math.Max(2, player.itemAnimationMax);
			player.heldProj = Projectile.whoAmI;
			if (Projectile.timeLeft > duration) {
				Projectile.timeLeft = duration;
			}
			Projectile.velocity = Projectile.velocity.SafeNormalize(Vector2.UnitX * player.direction);

			float half = duration * 0.5f;
			bool returning = Projectile.timeLeft < half;
			if (returning && ReturnStarted == 0f) {
				ReturnStarted = 1f;
				Array.Clear(Projectile.localNPCImmunity);   // second hit on the way back
			}
			float progress = returning ? Projectile.timeLeft / half : (duration - Projectile.timeLeft) / half;
			Projectile.Center = player.MountedCenter + Projectile.velocity * (Tip(progress) - Length * 0.5f);
			Projectile.rotation = Projectile.velocity.ToRotation();
			Projectile.direction = Projectile.velocity.X >= 0f ? 1 : -1;
		}

		private static float Tip(float progress) {
			return MathHelper.SmoothStep(ReachMin, ReachMax, progress);
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 tip = Projectile.Center + Projectile.velocity * (Length * 0.5f);
			Vector2 grip = Projectile.Center - Projectile.velocity * (Length * 0.5f - GripInset);
			float collisionPoint = 0f;
			return Collision.CheckAABBvLineCollision(targetHitbox.TopLeft(), targetHitbox.Size(), grip, tip, ShaftWidth, ref collisionPoint);
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (CogpunkSets.IsMechanical(target)) {
				modifiers.SourceDamage *= 1f + Screwdriver.MechanicalBonus / 100f;
			}
		}

		// Rotated to the thrust; flipped vertically when pointing left so the handle's lit edge stays on top.
		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			SpriteEffects effects = Projectile.direction < 0 ? SpriteEffects.FlipVertically : SpriteEffects.None;
			Main.EntitySpriteDraw(texture, Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY), null,
				Projectile.GetAlpha(lightColor), Projectile.rotation, texture.Size() * 0.5f, 1f, effects);
			return false;
		}
	}
}
