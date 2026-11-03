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
	/// The <see cref="TarShower"/>'s full-charge glob (user-set 2026-10-30: "a big tar projectile with gravity that pierces
	/// enemy and leaves a big (6 tiles) tar stain on the ground"): x<see cref="TarShower.MaxChargeMultiplier"/> damage on a
	/// gravity arc, through every enemy in its way (each once), plaguing them; where it comes down it leaves a
	/// <see cref="TarStain"/> on the ground under the splash (searched at most <see cref="MaxDrop"/> tiles down, through
	/// <see cref="TileSafety"/>: none over a pit). <see cref="Headings"/> pre-rendered headings, never rotated (D4).
	/// <para>D2: the owner's projectile; the owner alone places the stain (its own projectile, synced by vanilla).</para>
	/// </summary>
	public class TarShowerBigGlob : CogpunkProjectile
	{
		public const int Headings = 16;
		public const float Gravity = 0.25f;
		public const int PlagueTicks = 180;
		public const int MaxDrop = 16;
		private const int FrameSize = 32, FrameStride = 34;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Headings;
		}

		public override void SetDefaults() {
			Projectile.width = 22;
			Projectile.height = 22;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = -1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;           // through every enemy, each once
			Projectile.tileCollide = true;
			Projectile.timeLeft = 240;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 14f);
			MathSafety.Sanitize(ref Projectile.velocity);
			Projectile.frame = TarShowerGlob.HeadingFrame(Projectile.velocity, Headings);
			if (Main.dedServ) {
				return;
			}
			Lighting.AddLight(Projectile.Center, 0.12f, 0.1f, 0.3f);
			if (Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust drip)) {
				drip.velocity = -Projectile.velocity * 0.15f + Vector2.UnitY;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			TarPlague.InflictOn(target, Main.player[Projectile.owner], PlagueTicks);
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Projectile.owner == Main.myPlayer && FindGround(Projectile.Center, out Vector2 ground)) {
				TarStain.Spawn(Projectile, ground);
			}
			return true;
		}

		/// <summary>The top of the first floor (a solid tile or a platform, with open space above it) under a point, at most
		/// <see cref="MaxDrop"/> tiles down; bounds-checked through <see cref="TileSafety"/> (D0).</summary>
		public static bool FindGround(Vector2 at, out Vector2 ground) {
			ground = at;
			int x = (int)(at.X / 16f);
			int y0 = (int)(at.Y / 16f) - 1;
			for (int y = y0; y < y0 + MaxDrop; y++) {
				if (!TileSafety.TryGetTile(x, y, out Tile tile) || !TileSafety.TryGetTile(x, y - 1, out Tile above)) {
					return false;
				}
				if (IsFloor(tile) && !IsFloor(above)) {
					ground = new Vector2(at.X, y * 16f);
					return true;
				}
			}
			return false;
		}

		private static bool IsFloor(Tile tile) {
			return tile.HasTile && !tile.IsActuated && (Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType]);
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCDeath1 with { Volume = 0.7f, Pitch = -0.5f, MaxInstances = 3 }, Projectile.Center);
			for (int i = 0; i < 16; i++) {
				if (i > 5 && !CogpunkClientConfig.RollEffect()) {
					continue;
				}
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust d)) {
					d.velocity = Main.rand.NextVector2Circular(4f, 3f) - Vector2.UnitY * 2f;
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
