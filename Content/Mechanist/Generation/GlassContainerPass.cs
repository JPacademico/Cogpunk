using System;
using System.Collections.Generic;
using Cogpunk.Content.Mechanist.Accessories;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Terraria;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Mechanist.Generation
{
	/// <summary>
	/// Puts a <see cref="GlassContainer"/> in <see cref="GlassContainer.ChestChance"/> in 100 of the world's plain Wooden
	/// Chests (user-set 2026-10-27; <see cref="WoodenChests.IsPlain"/>: surface and underground, style 0, no wire), in the
	/// first empty slot (a full chest is skipped). Runs after vanilla's last pass, so every chest exists. The Scrappy Trunk
	/// pass, anchored to the same pass, refills the chests it turns into trunks, so whichever runs first, a chest ends up
	/// as a trunk (20%) or as a Wooden Chest with a 10% roll: the two never stack.
	/// <para>New worlds only (it's world generation). D0: one bounded loop over <c>Main.maxChests</c>, coordinates checked
	/// by <see cref="WoodenChests.IsPlain"/>, failures caught by <see cref="SafeGenPass"/>; only <c>WorldGen.genRand</c>.</para>
	/// </summary>
	internal sealed class GlassContainerPass : SafeGenPass
	{
		public GlassContainerPass() : base("Cogpunk: Glass Containers", 0.5) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.GlassContainers");
			int type = ModContent.ItemType<GlassContainer>();
			int candidates = 0;
			int placed = 0;
			for (int i = 0; i < Main.maxChests; i++) {
				if (i % 256 == 0) {
					progress.Set(i / (double)Main.maxChests);
				}
				Chest chest = Main.chest[i];
				if (chest == null || !WoodenChests.IsPlain(chest.x, chest.y)) {
					continue;
				}
				candidates++;
				if (WorldGen.genRand.Next(100) >= GlassContainer.ChestChance) {
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
			SafeLog.Info("WorldGen.GlassContainers", $"Glass Containers: {placed} of {candidates} Wooden Chests.");
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

	/// <summary>Registers <see cref="GlassContainerPass"/> after vanilla's last pass ("Final Cleanup"; appended if it's missing).</summary>
	public sealed class GlassContainerWorldGen : ModSystem
	{
		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			GenPassUtils.InsertAfter(tasks, "Final Cleanup", new GlassContainerPass(), ref totalWeight);
		}
	}
}
