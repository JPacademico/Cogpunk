using System;
using Cogpunk.Content.Coghaven.Items;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Generation
{
	/// <summary>
	/// Coghaven's chests (my calls, 2026-11-06: the user named no loot). Every chest is a vanilla Dynasty Chest (tile 21,
	/// style <see cref="DynastyChestStyle"/>, decompiled <c>Item.SetDefaults</c> 2230) filled by vanilla's own
	/// <c>WorldGen.AddBuriedChest</c> around a primary item from vanilla's sky-island list (decompiled <c>IslandHouse</c>:
	/// the Shiny Red Balloon, Starfury, Lucky Horseshoe and Celestial Magnet; passing one makes vanilla treat the chest as a
	/// sky chest and add its sky filler loot). Ordinary chests also get a stack of the palace's own jade bricks half the
	/// time; the pagoda's treasure (its top room) adds the Fledgling Wings 1 time in <see cref="WingsOneIn"/>, a Lift Turbine,
	/// two Bronze Cogs, Tarnished Brass Bars and gold. Every chest holds some <see cref="Gems.Items.Jade"/> (user, 2026-11-09:
	/// "chests on coghaven contain some jades"): <see cref="JadeMin"/>-<see cref="JadeMax"/>, the treasure
	/// <see cref="TreasureJadeMin"/>-<see cref="TreasureJadeMax"/>.
	/// <para>D0: world generation only, bounded; a chest that can't be placed returns -1 and is skipped (logged once).</para>
	/// </summary>
	internal static class CoghavenChests
	{
		public const int DynastyChestStyle = 28;
		public const int WingsOneIn = 10;
		public const int JadeMin = 3, JadeMax = 8, TreasureJadeMin = 8, TreasureJadeMax = 15;   // my calls (inclusive)            // vanilla: 1 in 40 in each sky chest (decompiled AddBuriedChest), which every chest here also rolls
		private static readonly int[] SkyItems = { ItemID.ShinyRedBalloon, ItemID.Starfury, ItemID.LuckyHorseshoe, ItemID.CelestialMagnet };

		/// <summary>A Dynasty Chest with its bottom-left tile at (<paramref name="x"/>, <paramref name="y"/>) on a solid floor at
		/// <c>y + 1</c>, filled; <paramref name="order"/> cycles the sky items so a palace holds each before any repeats.
		/// Returns the chest's index or -1.</summary>
		public static int Place(int x, int y, bool treasure, int order) {
			if (!TileSafety.InWorld(x, y - 1, TileSafety.EditMargin) || !TileSafety.InWorld(x + 1, y + 1, TileSafety.EditMargin)) {
				return -1;
			}
			int primary = SkyItems[Math.Abs(order) % SkyItems.Length];
			// AddBuriedChest(i, j) searches down from j at column i for the floor and places the chest at (i - 1, floor - 1)
			if (!WorldGen.AddBuriedChest(x + 1, y - 1, primary, false, DynastyChestStyle)) {
				return -1;
			}
			int index = Chest.FindChest(x, y - 1);
			if (index < 0 || index >= Main.maxChests || Main.chest[index] == null) {
				return -1;
			}
			Chest chest = Main.chest[index];
			if (treasure) {
				if (WorldGen.genRand.NextBool(WingsOneIn)) {
					Add(chest, ItemID.CreativeWings, 1);
				}
				Add(chest, ModContent.ItemType<LiftTurbine>(), 1);
				Add(chest, ModContent.ItemType<BronzeCog>(), 2);
				Add(chest, ModContent.ItemType<TarnishedBrassBar>(), WorldGen.genRand.Next(8, 16));
				Add(chest, ItemID.GoldCoin, WorldGen.genRand.Next(2, 5));
				Add(chest, ModContent.ItemType<Gems.Items.Jade>(), WorldGen.genRand.Next(TreasureJadeMin, TreasureJadeMax + 1));
			}
			else {
				Add(chest, ModContent.ItemType<Gems.Items.Jade>(), WorldGen.genRand.Next(JadeMin, JadeMax + 1));
				if (WorldGen.genRand.NextBool()) {
					Add(chest, ModContent.ItemType<JadeBrick>(), WorldGen.genRand.Next(20, 41));
				}
			}
			return index;
		}

		/// <summary>Puts <paramref name="stack"/> of <paramref name="type"/> in the chest's first empty slot (nothing when it is
		/// full).</summary>
		private static void Add(Chest chest, int type, int stack) {
			for (int k = 0; k < chest.item.Length; k++) {
				chest.item[k] ??= new Item();
				if (chest.item[k].IsAir) {
					chest.item[k].SetDefaults(type);
					chest.item[k].stack = Math.Clamp(stack, 1, chest.item[k].maxStack);
					return;
				}
			}
		}
	}
}
