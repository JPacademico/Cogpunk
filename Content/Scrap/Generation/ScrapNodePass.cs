using System.Collections;
using Cogpunk.Content.Scrap.Tiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Scrap.Generation
{
	/// <summary>
	/// Turns about one in ten silt nodes into Rusted Scrap. A "node" is a 4-connected cluster of silt, which is
	/// what each vanilla <c>TileRunner(..., TileID.Silt)</c> call in the "Silt" pass produces. Whole nodes convert,
	/// so the scrap keeps the natural silt-pocket shapes.
	/// <para>Cost: one pass over the world plus one flood fill per node (each tile is visited once),
	/// a 2.5 MB bit array on a large world and a fixed 4096-entry queue.</para>
	/// </summary>
	internal sealed class ScrapNodePass : SafeGenPass
	{
		/// <summary>1 in this many silt nodes becomes scrap (10%).</summary>
		public const int ConversionChanceDenominator = 10;

		/// <summary>Flood-fill cap per node. Tiles beyond it are left for a later fill, so merged pockets still work.</summary>
		private const int MaxNodeTiles = 4096;

		public ScrapNodePass() : base("Cogpunk: Rusted Scrap Nodes", 40.0) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.ScrapNodes");

			ushort scrap = (ushort)ModContent.TileType<RustedScrapTile>();
			int width = Main.maxTilesX;
			int height = Main.maxTilesY;
			var visited = new BitArray(width * height);
			var queue = new int[MaxNodeTiles];
			int nodes = 0;
			int converted = 0;

			// Stay one tile inside the world so neighbour checks never leave the array (D0).
			for (int x = 1; x < width - 1; x++) {
				if ((x & 127) == 0) {
					progress.Set((double)x / width);
				}
				for (int y = 1; y < height - 1; y++) {
					if (visited[(x * height) + y] || !IsSilt(x, y)) {
						continue;
					}
					int count = FloodFill(x, y, width, height, visited, queue);
					nodes++;
					if (!WorldGen.genRand.NextBool(ConversionChanceDenominator)) {
						continue;
					}
					for (int i = 0; i < count; i++) {
						Main.tile[queue[i] / height, queue[i] % height].TileType = scrap;
					}
					converted++;
				}
			}
			SafeLog.Info("WorldGen.ScrapNodes", $"Converted {converted} of {nodes} silt nodes into Rusted Scrap.");
		}

		private static bool IsSilt(int x, int y) {
			Tile tile = Main.tile[x, y];
			return tile.HasTile && tile.TileType == TileID.Silt;
		}

		/// <summary>Breadth-first fill from (x, y). Returns how many tiles were written to <paramref name="queue"/>.</summary>
		private static int FloodFill(int startX, int startY, int width, int height, BitArray visited, int[] queue) {
			int count = 0;
			int head = 0;
			visited[(startX * height) + startY] = true;
			queue[count++] = (startX * height) + startY;

			while (head < count) {
				int packed = queue[head++];
				int x = packed / height;
				int y = packed % height;
				TryVisit(x + 1, y);
				TryVisit(x - 1, y);
				TryVisit(x, y + 1);
				TryVisit(x, y - 1);
			}
			return count;

			void TryVisit(int nx, int ny) {
				if (count >= queue.Length || nx < 1 || ny < 1 || nx >= width - 1 || ny >= height - 1) {
					return;
				}
				int index = (nx * height) + ny;
				if (visited[index] || !IsSilt(nx, ny)) {
					return;
				}
				visited[index] = true;
				queue[count++] = index;
			}
		}
	}
}
