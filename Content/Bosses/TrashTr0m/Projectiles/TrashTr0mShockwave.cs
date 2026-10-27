using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;

namespace Cogpunk.Content.Bosses.TrashTr0m.Projectiles
{
	/// <summary>
	/// The slam's shockwave: a rolling mound of dirt and scrap that runs along the ground away from Trash-Tr0m's fist
	/// (hostile colours: ember sparks, steam dust). Its hitbox is the mound itself, measured from the sprite
	/// (<see cref="HitboxWidth"/> x <see cref="HitboxHeight"/>: the 82 px wide dirt mound without the dust puffs above it),
	/// so a jump at the right moment clears it: a vanilla jump keeps the feet above 40 px for ~25 ticks and the wave
	/// passes under a 20 px player in (76 + 20) / <see cref="TrashTr0m.ShockwaveSpeed"/> = 7 ticks.
	/// <para>It follows the terrain: every tick it finds the surface under its leading edge, climbing steps of up to
	/// <see cref="MaxStepUp"/> tiles and dropping up to <see cref="MaxDrop"/>; a taller wall or a pit breaks it. The search
	/// is deterministic on synced tiles, so every side moves it the same way (D2); at most MaxStepUp + MaxDrop + 1
	/// bounds-checked reads per tick (D0).</para>
	/// </summary>
	public class TrashTr0mShockwave : CogpunkProjectile
	{
		public const int HitboxWidth = 76;
		public const int HitboxHeight = 40;
		public const int Lifetime = 72;                    // ~1000 px = 63 tiles at 14 px/tick
		public const int MaxStepUp = 3;
		public const int MaxDrop = 6;
		public const int Frames = 4;
		public const int TicksPerFrame = 4;
		private const int FrameWidth = 88, FrameHeight = 60, FrameStride = 62;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = HitboxWidth;
			Projectile.height = HitboxHeight;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			int dir = Projectile.velocity.X >= 0f ? 1 : -1;
			Projectile.direction = Projectile.spriteDirection = dir;
			float front = Projectile.Center.X + dir * Projectile.width * 0.5f;
			if (!FindSurface(front, Projectile.Bottom.Y, out float ground)) {
				Projectile.Kill();                         // a wall or a pit: it breaks
				return;
			}
			Projectile.velocity.Y = ground - Projectile.Bottom.Y;
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				int tx = (int)(Projectile.Center.X / 16f) - dir;
				int ty = (int)(ground / 16f);
				SafeSpawn.TryTileDust(tx, ty);
				if (Main.rand.NextBool(3) && SafeSpawn.TryNewDust(Projectile.position, Projectile.width, 8, DustID.Torch, out Dust spark, 0f, -2f)) {
					spark.noGravity = true;
				}
			}
		}

		/// <summary>Top of the first solid surface under <paramref name="worldX"/> within the climb and drop window.</summary>
		private static bool FindSurface(float worldX, float bottom, out float ground) {
			int x = (int)(worldX / 16f);
			int row = (int)((bottom - 1f) / 16f) + 1;      // the row the wave stands on
			bool airAbove = !Solid(x, row - MaxStepUp - 1);
			for (int y = row - MaxStepUp; y <= row + MaxDrop; y++) {
				bool solid = Solid(x, y);
				if (solid && airAbove) {
					ground = y * 16f;
					return true;
				}
				airAbove = !solid;
			}
			ground = bottom;
			return false;
		}

		private static bool Solid(int x, int y) {
			return TileSafety.TryGetTile(x, y, out Tile tile, 1) && tile.HasTile && !tile.IsActuated
				&& (Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType]);
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 12; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 3 == 0 ? DustID.Torch : DustID.Smoke,
					out Dust d, 0f, -2f, 80, default, 1.3f)) {
					d.velocity *= 1.4f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameWidth, FrameHeight);
			Vector2 bottom = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY + 2f);
			Vector2 position = new((int)(bottom.X - FrameWidth * 0.5f), (int)(bottom.Y - FrameHeight));
			// The art rolls to the left; mirror it for a wave running right.
			SpriteEffects effects = Projectile.spriteDirection == 1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Color color = Color.Lerp(lightColor, Color.White, 0.35f) * Projectile.Opacity;
			Main.EntitySpriteDraw(texture, position, source, color, 0f, Vector2.Zero, 1f, effects);
			return false;
		}
	}
}
