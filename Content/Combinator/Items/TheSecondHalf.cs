using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Combinator.Items
{
	/// <summary>
	/// The Second Half (A Segunda Metade): the right half of the Combinator's core, its press and output chute (user,
	/// 2026-11-12: "on the westworld bank chest"). In Westworld's bank vault, the Brass Strongbox the Sheriff's Key opens
	/// (<see cref="CombinatorSystem"/> puts it there). A material for <see cref="TheCombinator"/>.
	/// </summary>
	public class TheSecondHalf : CogpunkItem
	{
		public override void SetStaticDefaults() {
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
