using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Items
{
	/// <summary>
	/// Treasure Bag (Cursed Conductor): Expert and Master, one per player (vanilla <c>ItemDropRule.BossBag</c> in
	/// <see cref="CursedConductor.ModifyNPCLoot"/>); contents in <see cref="CursedConductorLoot"/>. Set up like ExampleMod
	/// 1.4.4's <c>MinionBossBag</c>; pre-Hardmode (<c>PreHardmodeLikeBossBag</c>: he is fought at the Wall of Flesh's tier).
	/// Art: art/bosses/cursedconductor/make_conductor_art.py.
	/// </summary>
	public class CursedConductorBag : CogpunkItem
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
			CursedConductorLoot.AddBagContents(itemLoot);
		}
	}
}
