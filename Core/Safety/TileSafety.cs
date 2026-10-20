using Terraria;

namespace Cogpunk.Core.Safety
{
	/// <summary>
	/// Bounds-checked tile access. <c>Main.tile[x, y]</c> outside the world throws and crashes the game,
	/// and edits within a few tiles of the edge break framing/lighting. Use these for any coordinate
	/// that comes from math, player input, the network or a random roll.
	/// </summary>
	public static class TileSafety
	{
		/// <summary>Default margin from the world edge for edits; vanilla world generation uses similar margins.</summary>
		public const int EditMargin = 10;

		public static bool InWorld(int x, int y, int margin = EditMargin) {
			return WorldGen.InWorld(x, y, margin);
		}

		public static bool TryGetTile(int x, int y, out Tile tile, int margin = 0) {
			if (!WorldGen.InWorld(x, y, margin)) {
				tile = default;
				return false;
			}
			tile = Main.tile[x, y];
			return true;
		}
	}
}
