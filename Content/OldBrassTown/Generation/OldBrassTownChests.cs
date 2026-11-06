using Cogpunk.Content.OldBrassTown.Tiles;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.OldBrassTown.Generation
{
	/// <summary>
	/// Old Brass Town's two special chests (user-set 2026-11-04), both holding "normal gold underground chest loot":
	/// <list type="bullet">
	/// <item>the buried cache (a Gold Chest sealed in the rock under the street) with the <see cref="Items.SheriffsKey"/>;</item>
	/// <item>the bank vault's <see cref="BrassStrongboxTile"/>, locked, with the Sheriff's Revolver and a Broken Whistle.</item>
	/// </list>
	/// The loot is vanilla's own: <c>WorldGen.AddBuriedChest</c> fills the chest. Inside the underground desert vanilla would
	/// make a Sandstone Chest with desert loot of any chest with no preset item (decompiled: <c>contain == 0 &amp;&amp;
	/// IsUndergroundDesert</c>), so the primary item is picked here from vanilla's own Gold Chest lists for the depth
	/// (<see cref="PickPrimary"/>, decompiled) and passed in; the rest (bars, potions, torches, coins...) is vanilla's.
	/// <para>D0: world generation only, bounded, through <see cref="TileSafety"/>; a chest that can't be placed is logged
	/// once and skipped.</para>
	/// </summary>
	internal static class OldBrassTownChests
	{
		private const int GoldChestStyle = 1;

		/// <summary>The primary item vanilla puts in a Gold Chest standing on <paramref name="floorRow"/> (decompiled
		/// <c>WorldGen.AddBuriedChest</c>): above the cavern layer one of six (Band of Regeneration, Magic Mirror, Cloud in a
		/// Bottle, Hermes Boots, Mace, Shoe Spikes); in the cavern layer a Lava Charm 1 in 20 below the lava line, else an
		/// Extractinator 1 in 15, else one of seven (the six and the Flare Gun, which comes with flares).</summary>
		public static int PickPrimary(int floorRow, out bool flareGun) {
			flareGun = false;
			if (floorRow < Main.rockLayer) {
				return WorldGen.genRand.Next(6) switch {
					0 => ItemID.BandofRegeneration,
					1 => ItemID.MagicMirror,
					2 => ItemID.CloudinaBottle,
					3 => ItemID.HermesBoots,
					4 => ItemID.Mace,
					_ => ItemID.ShoeSpikes,
				};
			}
			if (WorldGen.genRand.Next(20) == 0 && floorRow > GenVars.lavaLine) {
				return ItemID.LavaCharm;
			}
			if (WorldGen.genRand.Next(15) == 0) {
				return ItemID.Extractinator;
			}
			int n = WorldGen.genRand.Next(7);
			if (n == 6) {
				flareGun = true;
				return ItemID.FlareGun;
			}
			return n switch {
				0 => ItemID.BandofRegeneration,
				1 => ItemID.MagicMirror,
				2 => ItemID.CloudinaBottle,
				3 => ItemID.HermesBoots,
				4 => ItemID.Mace,
				_ => ItemID.ShoeSpikes,
			};
		}

		/// <summary>A Gold Chest with vanilla's loot, its bottom-left tile at (<paramref name="x"/>, <paramref name="y"/>) on
		/// a solid floor at <c>y + 1</c>. Above the cavern layer vanilla also adds, after a chest's own primary, an
		/// Extractinator 1 in 20 or else a Flare Gun with flares 1 in 20; those come here too. Returns the chest's index or
		/// -1.</summary>
		public static int PlaceGoldChest(int x, int y) {
			if (!TileSafety.InWorld(x, y - 1, TileSafety.EditMargin) || !TileSafety.InWorld(x + 1, y + 1, TileSafety.EditMargin)) {
				return -1;
			}
			int floor = y + 1;
			int primary = PickPrimary(floor, out bool flareGun);
			// AddBuriedChest(i, j) searches down from j at column i for the floor and places the chest at (i - 1, floor - 1)
			if (!WorldGen.AddBuriedChest(x + 1, y - 1, primary, false, GoldChestStyle)) {
				return -1;
			}
			int index = Chest.FindChest(x, y - 1);
			if (index < 0 || index >= Main.maxChests || Main.chest[index] == null) {
				return -1;
			}
			Chest chest = Main.chest[index];
			if (flareGun) {
				Add(chest, ItemID.Flare, WorldGen.genRand.Next(25, 51));
			}
			if (floor < Main.rockLayer) {
				if (WorldGen.genRand.Next(20) == 0) {
					Add(chest, ItemID.Extractinator, 1);
				}
				else if (WorldGen.genRand.Next(20) == 0) {
					Add(chest, ItemID.FlareGun, 1);
					Add(chest, ItemID.Flare, WorldGen.genRand.Next(25, 51));
				}
			}
			return index;
		}

		/// <summary>Turns a placed Gold Chest into the <see cref="BrassStrongboxTile"/>, locked (style 1) or not (style 0):
		/// the same 2x2 frames on a 36 px stride, so the chest entry and its items stay as they are.</summary>
		public static void SetStrongbox(int index, bool locked) {
			if (index < 0 || index >= Main.maxChests || Main.chest[index] == null) {
				return;
			}
			ushort type = (ushort)ModContent.TileType<BrassStrongboxTile>();
			Chest chest = Main.chest[index];
			for (int dx = 0; dx < 2; dx++) {
				for (int dy = 0; dy < 2; dy++) {
					if (TileSafety.TryGetTile(chest.x + dx, chest.y + dy, out Tile tile) && tile.HasTile) {
						tile.TileType = type;
						tile.TileFrameX = (short)((locked ? BrassStrongboxTile.LockedStyle : 0) * 36 + dx * 18);
						tile.TileFrameY = (short)(dy * 18);
					}
				}
			}
		}

		/// <summary>Puts <paramref name="stack"/> of <paramref name="type"/> in the chest's first empty slot; returns the item,
		/// or null when the chest is full.</summary>
		public static Item Add(Chest chest, int type, int stack) {
			for (int k = 0; k < chest.item.Length; k++) {
				chest.item[k] ??= new Item();
				if (chest.item[k].IsAir) {
					chest.item[k].SetDefaults(type);
					chest.item[k].stack = System.Math.Clamp(stack, 1, chest.item[k].maxStack);
					return chest.item[k];
				}
			}
			return null;
		}
	}
}
