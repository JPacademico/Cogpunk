using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Tiles
{
	/// <summary>Helpers shared by the Fundamental Ruins' blocks.</summary>
	public static class RuinBlocks
	{
		/// <summary>Makes <paramref name="type"/> merge with the ruins' other blocks both ways (one clump, no seams between
		/// brick, coralstone, rune brick, the arena's Ancient Brick and rune brick, and rubble).</summary>
		public static void Merge(int type) {
			int[] blocks = { ModContent.TileType<FundamentalBrickTile>(), ModContent.TileType<FundamentalCoralTile>(),
				ModContent.TileType<FundamentalRuneTile>(), ModContent.TileType<FundamentalArenaBrickTile>(),
				ModContent.TileType<FundamentalArenaRuneTile>(), ModContent.TileType<FundamentalRubbleTile>() };
			foreach (int other in blocks) {
				if (other != type) {
					Main.tileMerge[type][other] = true;
					Main.tileMerge[other][type] = true;
				}
			}
		}

		/// <summary>A tile's glow frame over it (the tile's own frame from <paramref name="glow"/>), in <paramref name="color"/>.
		/// Nothing when the sheet is missing or the frame lies outside it (D0).</summary>
		public static void DrawGlow(Asset<Texture2D> glow, int i, int j, SpriteBatch spriteBatch, Color color) {
			if (glow?.IsLoaded != true) {
				return;
			}
			Tile tile = Main.tile[i, j];
			Rectangle source = new(tile.TileFrameX, tile.TileFrameY, 16, 16);
			if (source.Right > glow.Value.Width || source.Bottom > glow.Value.Height) {
				return;
			}
			Vector2 zero = Main.drawToScreen ? Vector2.Zero : new Vector2(Main.offScreenRange);
			Vector2 at = new Vector2(i * 16 - (int)Main.screenPosition.X, j * 16 - (int)Main.screenPosition.Y) + zero;
			spriteBatch.Draw(glow.Value, at, source, color, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
		}
	}
}
