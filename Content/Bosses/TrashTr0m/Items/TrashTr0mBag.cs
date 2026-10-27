using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Items
{
	/// <summary>
	/// Treasure Bag (Trash-Tr0m): Expert and Master, one per player (vanilla <c>ItemDropRule.BossBag</c> in
	/// <see cref="TrashTr0m.ModifyNPCLoot"/>). Holds 10-30 Rusted Scrap, 1-5 Gold Coins and one weapon from Trash-Tr0m's pool
	/// (<see cref="TrashTr0mLoot"/>). Set up like ExampleMod 1.4.4's <c>MinionBossBag</c>; pre-Hardmode, so dev armor only
	/// on special seeds (<c>PreHardmodeLikeBossBag</c>).
	/// </summary>
	public class TrashTr0mBag : CogpunkItem
	{
		public override void SetStaticDefaults() {
			ItemID.Sets.BossBag[Type] = true;
			ItemID.Sets.PreHardmodeLikeBossBag[Type] = true;
			Item.ResearchUnlockCount = 3;
		}

		public override void SetDefaults() {
			Item.maxStack = Item.CommonMaxStack;
			Item.consumable = true;
			Item.width = 32;
			Item.height = 32;
			Item.rare = ItemRarityID.Purple;
			Item.expert = true;
		}

		public override bool CanRightClick() {
			return true;
		}

		public override void ModifyItemLoot(ItemLoot itemLoot) {
			TrashTr0mLoot.AddBagContents(itemLoot);
		}
	}
}
