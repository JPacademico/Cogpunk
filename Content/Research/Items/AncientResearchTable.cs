using Cogpunk.Content.Research.Tiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Items
{
	/// <summary>
	/// Ancient Research Table (Mesa de Pesquisa Antiga) (user-set 2026-11-18: the book "can be used with wood and clay to craft a
	/// ancient reasearch table"): places <see cref="AncientResearchTableTile"/>. Recipe: the <see cref="AncientResearchBook"/>,
	/// <see cref="WoodCost"/> wood of any kind and <see cref="ClayCost"/> Clay Blocks at a Work Bench (the amounts and the
	/// station are my calls).
	/// </summary>
	public class AncientResearchTable : CogpunkItem
	{
		public const int WoodCost = 20, ClayCost = 10;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<AncientResearchTableTile>());
			Item.width = 32;
			Item.height = 22;
			Item.maxStack = Item.CommonMaxStack;
			Item.rare = ItemRarityID.Green;
			Item.value = Item.sellPrice(silver: 50);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<AncientResearchBook>()
				.AddRecipeGroup(RecipeGroupID.Wood, WoodCost)
				.AddIngredient(ItemID.ClayBlock, ClayCost)
				.AddTile(TileID.WorkBenches)
				.Register();
		}
	}
}
