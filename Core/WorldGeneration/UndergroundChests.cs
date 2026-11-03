using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Core.WorldGeneration
{
	/// <summary>
	/// Which chests count as vanilla's ordinary underground chests for Cogpunk's world-generation loot (the Rusted Nail): a
	/// <c>TileID.Containers</c> Wooden (style 0) or Gold (style 1) Chest whose top is below the surface line and above the
	/// Underworld. Locked, biome, Skyware, Water, Shadow and modded chests are other styles or tiles; a chest with wire or
	/// an actuator on it is skipped too (the trapped Dead Man's Chests), as <see cref="WoodenChests.IsPlain"/> does.
	/// </summary>
	public static class UndergroundChests
	{
		public const int WoodenStyle = 0, GoldStyle = 1;

		/// <summary>All four cells of the chest at (x, y) are an unwired Wooden or Gold <c>TileID.Containers</c> tile of the
		/// same style, below <c>Main.worldSurface</c> and above <c>Main.UnderworldLayer</c> (bounds checked through
		/// <see cref="TileSafety"/>).</summary>
		public static bool IsCandidate(int x, int y) {
			if (y <= Main.worldSurface || y >= Main.UnderworldLayer) {
				return false;
			}
			int style = -1;
			for (int dx = 0; dx < 2; dx++) {
				for (int dy = 0; dy < 2; dy++) {
					if (!TileSafety.TryGetTile(x + dx, y + dy, out Tile tile, TileSafety.EditMargin) || !tile.HasTile
						|| tile.TileType != TileID.Containers || tile.RedWire || tile.BlueWire || tile.GreenWire || tile.YellowWire || tile.HasActuator) {
						return false;
					}
					int s = tile.TileFrameX / WoodenChests.ChestStyleWidth;
					if ((s != WoodenStyle && s != GoldStyle) || (style >= 0 && s != style)) {
						return false;
					}
					style = s;
				}
			}
			return true;
		}
	}
}
