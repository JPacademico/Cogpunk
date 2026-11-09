using System.Collections.Generic;
using Cogpunk.Content.Gems.Tiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Gems.Generation
{
	/// <summary>
	/// Puts jade in the caverns the way vanilla puts its gems (user, 2026-11-09: "same behaviour and spawn as other default
	/// gems from terraria ex: amethyst emerald"), right after vanilla's own "Gems" pass. Vanilla (decompiled 1.4.4
	/// <c>WorldGen</c>, the "Gems" pass): for each gem, <c>maxTilesX * rate * 0.2</c> clusters (Amethyst 0.5, Topaz 0.45,
	/// Sapphire 0.3, Emerald 0.25, Ruby 0.1, Diamond 0.05), each at a random stone tile from the surface layer down to the
	/// world's bottom, grown with <c>WorldGen.TileRunner(x, y, 2..5, 3..6, gem)</c>. Jade takes the Emerald's rate
	/// (<see cref="Rate"/>: 210 clusters in a small world, 420 in a large one).
	/// <para>D0: vanilla looks for stone with an unbounded loop; here each cluster gets <see cref="MaxTries"/> tries and is
	/// skipped if they all miss; every tile read goes through <see cref="TileSafety"/>; only <c>WorldGen.genRand</c>; a
	/// failure is caught by <see cref="SafeGenPass"/>. New worlds only.</para>
	/// </summary>
	internal sealed class JadeGemPass : SafeGenPass
	{
		public const double Rate = 0.25;                  // the Emerald's (vanilla: x 0.2 below)
		public const int MaxTries = 400;

		public JadeGemPass() : base("Cogpunk: Jade", 1.0) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.Jade");
			ushort jade = (ushort)ModContent.TileType<JadeTile>();
			int clusters = (int)(Main.maxTilesX * Rate * 0.2);
			int top = (int)Main.worldSurface;
			if (clusters <= 0 || top < 0 || top >= Main.maxTilesY - 1) {
				return;
			}
			int placed = 0;
			for (int i = 0; i < clusters; i++) {
				progress.Set(i / (double)clusters);
				for (int attempt = 0; attempt < MaxTries; attempt++) {
					int x = WorldGen.genRand.Next(0, Main.maxTilesX);
					int y = WorldGen.genRand.Next(top, Main.maxTilesY);
					if (!TileSafety.TryGetTile(x, y, out Tile tile) || !tile.HasTile || tile.TileType != TileID.Stone) {
						continue;
					}
					WorldGen.TileRunner(x, y, WorldGen.genRand.Next(2, 6), WorldGen.genRand.Next(3, 7), jade);
					placed++;
					break;
				}
			}
			SafeLog.Info("WorldGen.Jade", $"Jade: {placed} of {clusters} clusters.");
		}
	}

	/// <summary>Inserts <see cref="JadeGemPass"/> after vanilla's "Gems" (appended if a mod removed it).</summary>
	internal sealed class JadeGemSystem : ModSystem
	{
		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			GenPassUtils.InsertAfter(tasks, "Gems", new JadeGemPass(), ref totalWeight);
		}
	}
}
