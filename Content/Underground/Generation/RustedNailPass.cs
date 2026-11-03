using System;
using System.Collections.Generic;
using Cogpunk.Content.Underground.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Terraria;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Underground.Generation
{
	/// <summary>
	/// Puts a <see cref="RustedNail"/> in <see cref="RustedNail.ChestChance"/> in 100 of the world's ordinary underground
	/// chests (user-set 2026-11-03: "a chance to spawn on random underground chests"; <see cref="UndergroundChests.IsCandidate"/>:
	/// Wooden and Gold Chests between the surface and the Underworld, no wire), in the first empty slot (a full chest is
	/// skipped). Runs after vanilla's last pass, so every chest exists (the Glass Container pass's pattern).
	/// <para>New worlds only (it's world generation). D0: one bounded loop over <c>Main.maxChests</c>, coordinates checked
	/// by <see cref="UndergroundChests.IsCandidate"/>, failures caught by <see cref="SafeGenPass"/>; only
	/// <c>WorldGen.genRand</c>.</para>
	/// </summary>
	internal sealed class RustedNailPass : SafeGenPass
	{
		public RustedNailPass() : base("Cogpunk: Rusted Nails", 0.5) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.RustedNails");
			int type = ModContent.ItemType<RustedNail>();
			int candidates = 0;
			int placed = 0;
			for (int i = 0; i < Main.maxChests; i++) {
				if (i % 256 == 0) {
					progress.Set(i / (double)Main.maxChests);
				}
				Chest chest = Main.chest[i];
				if (chest == null || !UndergroundChests.IsCandidate(chest.x, chest.y)) {
					continue;
				}
				candidates++;
				if (WorldGen.genRand.Next(100) >= RustedNail.ChestChance) {
					continue;
				}
				int slot = FirstEmptySlot(chest);
				if (slot < 0) {
					continue;
				}
				chest.item[slot] ??= new Item();
				chest.item[slot].SetDefaults(type);
				placed++;
			}
			SafeLog.Info("WorldGen.RustedNails", $"Rusted Nails: {placed} of {candidates} underground chests.");
		}

		private static int FirstEmptySlot(Chest chest) {
			int count = Math.Min(chest.item.Length, Chest.maxItems);
			for (int s = 0; s < count; s++) {
				if (chest.item[s] == null || chest.item[s].IsAir) {
					return s;
				}
			}
			return -1;
		}
	}

	/// <summary>Registers <see cref="RustedNailPass"/> after vanilla's last pass ("Final Cleanup"; appended if it's missing).</summary>
	public sealed class RustedNailWorldGen : ModSystem
	{
		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			GenPassUtils.InsertAfter(tasks, "Final Cleanup", new RustedNailPass(), ref totalWeight);
		}
	}
}
