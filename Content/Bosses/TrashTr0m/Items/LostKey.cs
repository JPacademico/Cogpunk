using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Items
{
	/// <summary>
	/// Lost Key: Trash-Tr0m's drop, the only thing that opens the Junkyard Cache (<see cref="Furniture.ScrappyTrunkTile"/>,
	/// style 1). Right-clicking the locked cache with it in the inventory (or an open Void Bag) uses it up and unlocks the
	/// cache into a plain Scrappy Trunk with the loot still inside (vanilla <c>Chest.Unlock</c>, synced with
	/// <c>MessageID.LockAndUnlock</c>, as ExampleMod 1.4.4's ExampleChest does).
	/// </summary>
	public class LostKey : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;
		}

		public override void SetDefaults() {
			Item.width = 32;
			Item.height = 32;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Blue;
		}
	}
}
