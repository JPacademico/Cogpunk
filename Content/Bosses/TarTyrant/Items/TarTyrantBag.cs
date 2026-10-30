using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Items
{
	/// <summary>
	/// Treasure Bag (Tar Tyrant): Expert and Master, one per player (vanilla <c>ItemDropRule.BossBag</c> in
	/// <see cref="TarTyrant.ModifyNPCLoot"/>); contents in <see cref="TarTyrantLoot"/> (always the <see cref="SereneTear"/>).
	/// Set up like ExampleMod 1.4.4's <c>MinionBossBag</c>; pre-Hardmode (<c>PreHardmodeLikeBossBag</c>).
	/// </summary>
	public class TarTyrantBag : CogpunkItem
	{
		public override void SetStaticDefaults() {
			ItemID.Sets.BossBag[Type] = true;
			ItemID.Sets.PreHardmodeLikeBossBag[Type] = true;
			Item.ResearchUnlockCount = 3;
		}

		public override void SetDefaults() {
			Item.maxStack = Item.CommonMaxStack;
			Item.consumable = true;
			Item.width = 36;
			Item.height = 36;
			Item.rare = ItemRarityID.Purple;
			Item.expert = true;
		}

		public override bool CanRightClick() {
			return true;
		}

		public override void ModifyItemLoot(ItemLoot itemLoot) {
			TarTyrantLoot.AddBagContents(itemLoot);
		}
	}
}
