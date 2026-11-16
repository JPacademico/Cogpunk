using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>
	/// Pagoda Key (2026-11-16, user: "the pagoda chest on coghaven should be locked and can only be opened with a key obtained
	/// on hardmode (just like default terraria biome chests of the dungeon), this 'pagoda key' will be dropped by a future boss
	/// on hardmode"): a jade key whose bow is a tiny pagoda roof. Right-clicking the Locked Pagoda Chest at the top of
	/// Coghaven's pagoda with it uses it up and opens the chest (<see cref="Tiles.CoghavenChestTile"/>). <b>No source yet:</b>
	/// the Hardmode boss that drops it doesn't exist; it gets its drop rule when that boss is made. Rarity Yellow, like
	/// vanilla's biome keys (terraria.wiki.gg).
	/// </summary>
	public class PagodaKey : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 32;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Yellow;
		}
	}
}
