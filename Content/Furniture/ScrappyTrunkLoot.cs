using System;
using System.Collections.Generic;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Systems;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.Utilities;

namespace Cogpunk.Content.Furniture
{
	/// <summary>
	/// What a Scrappy Trunk found in the world holds (<see cref="Generation.ScrappyTrunkPass"/>):
	/// <list type="number">
	/// <item>a trinket, when any item is in <see cref="CogpunkSets.ScrappyTrunkTrinket"/> (pre-Hardmode, not a boss drop;
	/// none yet), picked at random;</item>
	/// <item><see cref="MinScrap"/>-<see cref="MaxScrap"/> Rusted Scrap;</item>
	/// <item>one or two different pre-Hardmode ores, <see cref="MinOre"/>-<see cref="MaxOre"/> each;</item>
	/// <item><see cref="MinCoins"/>-<see cref="MaxCoins"/> copper coins.</item>
	/// </list>
	/// World generation only, so every roll uses <c>WorldGen.genRand</c> and the trunk's items are saved with the world.
	/// </summary>
	public static class ScrappyTrunkLoot
	{
		public const int MinScrap = 10, MaxScrap = 30;     // inclusive ranges
		public const int MinOre = 5, MaxOre = 15;
		public const int MinCoins = 20, MaxCoins = 99;
		public const int SecondOreChance = 2;            // 1 in 2 trunks hold a second, different ore

		private static readonly int[] Ores = {
			ItemID.CopperOre, ItemID.TinOre, ItemID.IronOre, ItemID.LeadOre,
			ItemID.SilverOre, ItemID.TungstenOre, ItemID.GoldOre, ItemID.PlatinumOre,
		};

		/// <summary>Every item flagged as a trunk trinket, in type order. Built once per world generation.</summary>
		public static List<int> CollectTrinkets() {
			List<int> trinkets = new();
			bool[] set = CogpunkSets.ScrappyTrunkTrinket;
			int count = Math.Min(set.Length, ItemLoader.ItemCount);
			for (int type = 1; type < count; type++) {
				if (set[type]) {
					trinkets.Add(type);
				}
			}
			return trinkets;
		}

		/// <summary>Empties <paramref name="chest"/> and fills it with a fresh trunk roll. Since 0.4.0 (user, 2026-11-27: "make it
		/// so golden and rust underground chests allways contain a crystal heart"), underground trunks always hold a
		/// <c>LifeCrystal</c>.</summary>
		public static void Fill(Chest chest, UnifiedRandom rand, List<int> trinkets, bool underground = false) {
			for (int i = 0; i < chest.item.Length; i++) {
				chest.item[i] ??= new Item();
				chest.item[i].TurnToAir();
			}
			int slot = 0;
			if (underground) {
				Add(chest, ref slot, ItemID.LifeCrystal, 1);
			}
			if (trinkets.Count > 0) {
				Add(chest, ref slot, trinkets[rand.Next(trinkets.Count)], 1);
			}
			Add(chest, ref slot, ModContent.ItemType<RustedScrap>(), rand.Next(MinScrap, MaxScrap + 1));
			int firstOre = rand.Next(Ores.Length);
			Add(chest, ref slot, Ores[firstOre], rand.Next(MinOre, MaxOre + 1));
			if (rand.NextBool(SecondOreChance)) {
				int secondOre = (firstOre + 1 + rand.Next(Ores.Length - 1)) % Ores.Length;   // never the same ore twice
				Add(chest, ref slot, Ores[secondOre], rand.Next(MinOre, MaxOre + 1));
			}
			Add(chest, ref slot, ItemID.CopperCoin, rand.Next(MinCoins, MaxCoins + 1));
		}

		private static void Add(Chest chest, ref int slot, int type, int stack) {
			if (slot >= chest.item.Length || type <= ItemID.None || type >= ItemLoader.ItemCount) {
				return;
			}
			chest.item[slot].SetDefaults(type);
			chest.item[slot].stack = Math.Clamp(stack, 1, chest.item[slot].maxStack);
			slot++;
		}
	}
}
