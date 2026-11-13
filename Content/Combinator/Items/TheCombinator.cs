using Cogpunk.Content.Combinator.Tiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator.Items
{
	/// <summary>
	/// The Combinator (O Combinador), Cogpunk's Hardmode progression station (user-set 2026-11-12): places a
	/// <see cref="CombinatorTile"/>. Crafted at a Mythril (or Orichalcum) Anvil from <see cref="TheFirstHalf"/>,
	/// <see cref="TheSecondHalf"/> and the <see cref="CombinatorBlueprint"/>, each found once per world: Trash-Tr0m's cache,
	/// Westworld's bank vault and the Wall of Flesh's first defeat. No shimmer decraft (the parts are one of a kind).
	/// </summary>
	public class TheCombinator : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<CombinatorTile>());
			Item.width = 48;
			Item.height = 36;
			Item.value = Item.sellPrice(gold: 10);
			Item.rare = ItemRarityID.Pink;
		}

		public override void ModifyResearchSorting(ref ContentSamples.CreativeHelper.ItemGroup itemGroup) {
			itemGroup = ContentSamples.CreativeHelper.ItemGroup.CraftingObjects;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<TheFirstHalf>()
				.AddIngredient<TheSecondHalf>()
				.AddIngredient<CombinatorBlueprint>()
				.AddTile(TileID.MythrilAnvil)
				.DisableDecraft()
				.Register();
		}
	}
}
