using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.BloodMoon.Projectiles
{
	/// <summary>
	/// The <see cref="Weapons.PossessedCog"/> on its string (user-set 2026-11-16: "pierces instead of bouncing off enemies
	/// dealing moderate continuous damage"). Vanilla's yoyo AI (<c>aiStyle</c> 99, ExampleMod 1.4.4's ExampleYoyoProjectile)
	/// steers it, draws its string and handles the Yoyo Glove and counterweights; only the bounce is taken away.
	/// <para><b>The bounce</b> (decompiled 1.4.4 <c>Projectile.Damage</c>): after <c>ModifyHitNPC</c> and before the strike,
	/// an <c>aiStyle</c> 99 projectile that is still out (<c>ai[0] &gt;= 0</c>) gets
	/// <c>velocity = velocity * -0.5 + (away from the enemy) * 16</c> and 20 more ticks on its life clock (60 with no line
	/// of sight to its owner); <c>OnHitNPC</c> runs after the strike. So <see cref="ModifyHitNPC"/> notes the velocity and the
	/// clock and <see cref="OnHitNPC"/> puts both back: the cog flies on through, as the cursor leads it. It cuts each enemy
	/// at most once every <see cref="HitCooldown"/> ticks while it stays inside (local immunity: every enemy in its path
	/// is cut, each on its own clock).</para>
	/// <para>D2: a player projectile; the hit hooks run on its owner's client (where vanilla works out the hit), which syncs
	/// the yoyo as vanilla does (the bounce code's own <c>netUpdate</c>). D1: no allocation; the trail's dust and light on
	/// clients only, throttled. D4: never rotated at runtime (vanilla turns yoyos by <c>rotation</c>): the cog's spin is four
	/// pre-drawn frames (its eight teeth make 45 degrees a full turn), drawn on the 2 px grid, its soul fire a glow sheet
	/// added onto the scene; its hub's eye looks where the cog is heading (nine frames).</para>
	/// </summary>
	public class PossessedCogYoyo : CogpunkProjectile
	{
		public const int HitCooldown = 8;                        // 7.5 cuts a second on each enemy it overlaps
		public const float LifeSeconds = 10f, MaxRange = 210f, TopSpeed = 13f;   // the Valor: 11 s, 225, 14
		public const int SpinFrames = 4, EyeFrames = 9;
		private const int Cell = 26, Gap = 2, EyeCell = 10;     // game px (the art is drawn at 1x and exported 2x)
		private const int SpinTicks = 3;

		private static Asset<Texture2D> glow, eye;

		private Vector2 preHitVelocity;
		private float preHitClock;
		private bool hitNoted;

		public override void SetStaticDefaults() {
			ProjectileID.Sets.YoyosLifeTimeMultiplier[Type] = LifeSeconds;
			ProjectileID.Sets.YoyosMaximumRange[Type] = MaxRange;
			ProjectileID.Sets.YoyosTopSpeed[Type] = TopSpeed;
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
			eye = DepthLayers.RequestOptional(Texture + "_Eye");
		}

		public override void Unload() {
			glow = eye = null;
		}

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.aiStyle = ProjAIStyleID.Yoyo;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.MeleeNoSpeed;
			Projectile.penetrate = -1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = HitCooldown;
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			preHitVelocity = Projectile.velocity;
			preHitClock = Projectile.localAI[0];
			hitNoted = true;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (hitNoted && MathSafety.IsFinite(preHitVelocity)) {
				Projectile.velocity = preHitVelocity;            // no bounce: it grinds on through
				Projectile.localAI[0] = preHitClock;             // and the hit costs it no time on its string
			}
			hitNoted = false;
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				for (int i = 0; i < 3; i++) {
					if (SafeSpawn.TryNewDust(target.Center + (Projectile.Center - target.Center) * 0.5f - new Vector2(4f), 8, 8,
						i == 0 ? DustID.CursedTorch : DustID.Copper, out Dust d)) {
						d.noGravity = true;
						d.velocity = Main.rand.NextVector2Circular(2.5f, 2.5f);
						d.scale = 1.1f;
					}
				}
			}
		}

		public override void PostAI() {
			if (Main.dedServ) {
				return;
			}
			Lighting.AddLight(Projectile.Center, 0.1f, 0.42f, 0.3f);
			if (Main.rand.NextBool(4) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(6f), 12, 12, DustID.CursedTorch, out Dust d)) {
				d.noGravity = true;
				d.velocity = -Projectile.velocity * 0.15f + Main.rand.NextVector2Circular(0.6f, 0.6f);
				d.scale = 0.9f;
			}
		}

		/// <summary>The hub's eye: centre when it hangs still, else the heading's eighth (0 right, then clockwise on screen).</summary>
		private int EyeFrame() {
			Vector2 v = Projectile.velocity;
			if (v.LengthSquared() < 1.5f) {
				return 0;
			}
			int octant = (int)Math.Round(Math.Atan2(v.Y, v.X) / MathHelper.PiOver4);
			return 1 + ((octant % 8) + 8) % 8;
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D sheet = TextureAssets.Projectile[Type].Value;
			if (sheet.Height < SpinFrames * Cell) {
				return true;                                     // the fallback texture: let vanilla draw it
			}
			int frame = (int)((Main.GameUpdateCount / SpinTicks + (uint)Projectile.whoAmI) % SpinFrames);
			Vector2 topLeft = Projectile.Center - Main.screenPosition - new Vector2(Cell * 0.5f);
			topLeft = new Vector2(DepthLayers.Snap(topLeft.X), DepthLayers.Snap(topLeft.Y));
			Rectangle source = new(0, frame * (Cell + Gap), Cell, Cell);
			Main.EntitySpriteDraw(sheet, topLeft, source, Projectile.GetAlpha(lightColor), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true && glow.Value.Height >= SpinFrames * Cell) {
				Main.EntitySpriteDraw(glow.Value, topLeft, source, new Color(255, 255, 255, 0), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			if (eye?.IsLoaded == true && eye.Value.Height >= EyeFrames * EyeCell) {
				Rectangle look = new(0, EyeFrame() * (EyeCell + Gap), EyeCell, EyeCell);
				Vector2 at = topLeft + new Vector2((Cell - EyeCell) * 0.5f);
				Main.EntitySpriteDraw(eye.Value, at, look, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}
}
