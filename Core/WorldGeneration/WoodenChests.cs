using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Core.WorldGeneration
{
	/// <summary>
	/// Which chests count as vanilla's plain Wooden Chest for Cogpunk's world-generation loot (Scrappy Trunks, the Glass
	/// Container): <c>TileID.Containers</c> style 0 only, never Gold, Water (coral), biome, locked or modded chests. A chest
	/// with wire or an actuator on it is skipped too, which leaves the trapped Dead Man's Chests alone.
	/// </summary>
	public static class WoodenChests
	{
		public const int ChestStyleWidth = 36;           // 2 tiles x 18 px per chest style

		/// <summary>All four cells of the chest at (x, y) are an unwired style-0 <c>TileID.Containers</c> tile (bounds
		/// checked through <see cref="TileSafety"/>).</summary>
		public static bool IsPlain(int x, int y) {
			for (int dx = 0; dx < 2; dx++) {
				for (int dy = 0; dy < 2; dy++) {
					if (!TileSafety.TryGetTile(x + dx, y + dy, out Tile tile, TileSafety.EditMargin) || !tile.HasTile
						|| tile.TileType != TileID.Containers || tile.TileFrameX / ChestStyleWidth != 0
						|| tile.RedWire || tile.BlueWire || tile.GreenWire || tile.YellowWire || tile.HasActuator) {
						return false;
					}
				}
			}
			return true;
		}
	}
}
