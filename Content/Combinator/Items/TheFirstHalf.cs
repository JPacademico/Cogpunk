using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Combinator.Items
{
	/// <summary>
	/// The First Half (A Primeira Metade): the left half of the Combinator's core, a split brass housing with a half cog and its
	/// feed hopper (user, 2026-11-12: "found on the trashtr0m boss chest"). In the Junkyard's cache, the trunk under the central
	/// heap that Trash-Tr0m guards (<see cref="CombinatorSystem"/> puts it there). A material: with
	/// <see cref="TheSecondHalf"/> and the <see cref="CombinatorBlueprint"/> at a Mythril Anvil it makes
	/// <see cref="TheCombinator"/>.
	/// </summary>
	public class TheFirstHalf : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Cogpunk.Core.Systems.CogpunkSets.NeverStolen[Type] = true;        // a once-only drop: no thief takes it (2026-11-26)
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 26;
			Item.height = 30;
			Item.maxStack = 1;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Orange;
		}
	}
}
