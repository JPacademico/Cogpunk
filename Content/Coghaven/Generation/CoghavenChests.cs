using System;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Generation
{
	/// <summary>
	/// Coghaven's chests. Since 2026-11-12 there are only two (user: "coghaven should have only 2 chests now, containing sky
	/// island loot and some other specific items that I will add in the future"): the pagoda's top room and, since 2026-11-16,
	/// the middle of the Jade Vault (the engine deck's boiler hall before; art/coghaven/make_coghaven_blueprints.py). Both are
	/// filled here as Dynasty chests and then turned into <see cref="Tiles.CoghavenChestTile"/>s (<see cref="Convert"/>): the
	/// pagoda's a Locked Pagoda Chest (the Pagoda Key opens it), the vault's the Jade Vault (Jadey guards it). Each is a vanilla Dynasty
	/// Chest (tile 21, style <see cref="DynastyChestStyle"/>, decompiled <c>Item.SetDefaults</c> 2230) filled by vanilla's own
	/// <c>WorldGen.AddBuriedChest</c> around a primary item from vanilla's sky-island list (decompiled <c>IslandHouse</c>: the
	/// Shiny Red Balloon, Starfury, Lucky Horseshoe and Celestial Magnet; passing one makes vanilla treat the chest as a sky
	/// chest and add its sky filler loot, the 1 in 40 Fledgling Wings included). The two primaries are two different ones,
	/// picked at random. Every chest still holds some <see cref="Gems.Items.Jade"/> (user, 2026-11-09: "chests on coghaven
	/// contain some jades"), <see cref="JadeMin"/>-<see cref="JadeMax"/>, plus whatever <see cref="ExtraLoot"/> lists: empty
	/// for now, the place for the items the user will add. (The 2026-11-06 extras, my calls: Jade Bricks, the treasure's Lift
	/// Turbine, Bronze Cogs, Tarnished Brass Bars, gold and its own wings roll, went with the extra chests.)
	/// <para>D0: world generation only, bounded; a chest that can't be placed returns -1 and is skipped (logged once).</para>
	/// </summary>
	internal static class CoghavenChests
	{
		public const int DynastyChestStyle = 28;
		public const int JadeMin = 3, JadeMax = 8;              // inclusive
		private static readonly int[] SkyItems = { ItemID.ShinyRedBalloon, ItemID.Starfury, ItemID.LuckyHorseshoe, ItemID.CelestialMagnet };

		/// <summary>Items every Coghaven chest gets on top of its sky loot: (item type, min stack, max stack). Empty until the
		/// user names them (2026-11-12: "some other specific items that I will add in the future").</summary>
		private static readonly (int Type, int Min, int Max)[] ExtraLoot = System.Array.Empty<(int, int, int)>();

		private static int firstPrimary = -1;                    // this world's first pick, so the second chest differs

		/// <summary>Called before the chests are placed (a pass is reused for every world made in a session).</summary>
		public static void Reset() {
			firstPrimary = -1;
		}

		/// <summary>A Dynasty Chest with its bottom-left tile at (<paramref name="x"/>, <paramref name="y"/>) on a solid floor at
		/// <c>y + 1</c>, filled. Returns the chest's index or -1. (<paramref name="treasure"/>: the pagoda's top room; the same loot
		/// since 2026-11-12.)</summary>
		public static int Place(int x, int y, bool treasure, int order) {
			if (!TileSafety.InWorld(x, y - 1, TileSafety.EditMargin) || !TileSafety.InWorld(x + 1, y + 1, TileSafety.EditMargin)) {
				return -1;
			}
			int pick = WorldGen.genRand.Next(SkyItems.Length);
			if (pick == firstPrimary) {
				pick = (pick + 1 + WorldGen.genRand.Next(SkyItems.Length - 1)) % SkyItems.Length;   // a different one
			}
			int primary = SkyItems[pick];
			// AddBuriedChest(i, j) searches down from j at column i for the floor and places the chest at (i - 1, floor - 1)
			if (!WorldGen.AddBuriedChest(x + 1, y - 1, primary, false, DynastyChestStyle)) {
				return -1;
			}
			int index = Chest.FindChest(x, y - 1);
			if (index < 0 || index >= Main.maxChests || Main.chest[index] == null) {
				return -1;
			}
			if (firstPrimary < 0) {
				firstPrimary = pick;
			}
			Chest chest = Main.chest[index];
			Add(chest, ModContent.ItemType<Gems.Items.Jade>(), WorldGen.genRand.Next(JadeMin, JadeMax + 1));
			foreach ((int type, int min, int max) in ExtraLoot) {
				if (type > 0 && type < ItemLoader.ItemCount && max >= min && min > 0) {
					Add(chest, type, WorldGen.genRand.Next(min, max + 1));
				}
			}
			return index;
		}

		/// <summary>
		/// Turns the 2x2 chest whose top-left tile is (<paramref name="left"/>, <paramref name="top"/>) into
		/// <paramref name="type"/> in <paramref name="style"/>, in place: vanilla gives sky loot only to its own chest tile
		/// (decompiled <c>WorldGen.AddBuriedChest</c>: the sky flag needs <c>chestTileType == 21</c>), so the chest is filled
		/// as a Dynasty chest first; its <c>Main.chest</c> entry is keyed by position and keeps the loot. World generation only;
		/// every tile bounds-checked (D0).
		/// </summary>
		public static void Convert(int left, int top, ushort type, int style) {
			for (int dx = 0; dx < 2; dx++) {
				for (int dy = 0; dy < 2; dy++) {
					if (!TileSafety.TryGetTile(left + dx, top + dy, out Tile tile, TileSafety.EditMargin) || !tile.HasTile) {
						continue;
					}
					tile.TileType = type;
					tile.TileFrameX = (short)(style * 36 + dx * 18);
					tile.TileFrameY = (short)(dy * 18);
				}
			}
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
