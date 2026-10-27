using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Furniture.Generation
{
	/// <summary>
	/// Turns <see cref="ReplaceChance"/> in 100 of the world's plain Wooden Chests (surface and underground) into Scrappy
	/// Trunks filled by <see cref="ScrappyTrunkLoot"/>. Runs after vanilla's last pass, so every chest vanilla (and earlier
	/// mods) placed exists.
	/// <para>Only the plain Wooden Chest qualifies (<see cref="WoodenChests.IsPlain"/>: style 0, no wire). The swap keeps
	/// the chest's slot in <c>Main.chest</c> and its 2x2 frames (a style-0 trunk has the same frames), and only changes the
	/// tile type and the items, so nothing else in the world moves.</para>
	/// <para>D0: one bounded loop over <c>Main.maxChests</c>; every coordinate goes through <see cref="TileSafety"/>; a
	/// failure is caught by <see cref="SafeGenPass"/>. Server or singleplayer only (world generation), saved with the world.</para>
	/// </summary>
	internal sealed class ScrappyTrunkPass : SafeGenPass
	{
		public const int ReplaceChance = 20;             // percent

		public ScrappyTrunkPass() : base("Cogpunk: Scrappy Trunks", 1.0) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.ScrappyTrunks");
			ushort trunk = (ushort)ModContent.TileType<ScrappyTrunkTile>();
			List<int> trinkets = ScrappyTrunkLoot.CollectTrinkets();
			int candidates = 0;
			int replaced = 0;
			for (int i = 0; i < Main.maxChests; i++) {
				if (i % 256 == 0) {
					progress.Set(i / (double)Main.maxChests);
				}
				Chest chest = Main.chest[i];
				if (chest == null || !WoodenChests.IsPlain(chest.x, chest.y)) {
					continue;
				}
				candidates++;
				if (WorldGen.genRand.Next(100) >= ReplaceChance) {
					continue;
				}
				for (int dx = 0; dx < 2; dx++) {
					for (int dy = 0; dy < 2; dy++) {
						Main.tile[chest.x + dx, chest.y + dy].TileType = trunk;   // bounds checked by WoodenChests.IsPlain
					}
				}
				ScrappyTrunkLoot.Fill(chest, WorldGen.genRand, trinkets);
				replaced++;
			}
			SafeLog.Info("WorldGen.ScrappyTrunks", $"Scrappy Trunks: {replaced} of {candidates} Wooden Chests replaced.");
		}
	}

	/// <summary>Registers <see cref="ScrappyTrunkPass"/> after vanilla's last pass ("Final Cleanup"; appended if it's missing).</summary>
	public sealed class ScrappyTrunkWorldGen : ModSystem
	{
		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			GenPassUtils.InsertAfter(tasks, "Final Cleanup", new ScrappyTrunkPass(), ref totalWeight);
		}
	}
}
