using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Furniture
{
	/// <summary>Places a <see cref="ScrappyTrunkTile"/> (style 0). Recipe mirrors the vanilla Chest: 8 material + 2 Iron/Lead Bars.</summary>
	public class ScrappyTrunk : CogpunkItem
	{
		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<ScrappyTrunkTile>());
			Item.width = 32;
			Item.height = 30;
			Item.value = Item.sellPrice(silver: 1);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedMetal>(10)                        // 8 -> 10, x1.2 rounded (user, 2026-11-26)
				.AddRecipeGroup(RecipeGroupID.IronBar, 2)
				.AddTile(TileID.WorkBenches)
				.Register();
		}
	}
}
