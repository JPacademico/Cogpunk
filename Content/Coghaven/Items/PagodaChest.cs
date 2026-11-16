using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>Places a Pagoda Chest (<see cref="Tiles.CoghavenChestTile"/>, style 0): red lacquer under a little jade roof.
	/// Recipe like vanilla's chests (8 of the material + 2 Iron or Lead Bars at a Work Bench), with Coghaven's Cinnabar Lacquer
	/// (2026-11-16, my call). Breaking any of Coghaven's chests gives one back.</summary>
	public class PagodaChest : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.CoghavenChestTile>(), Tiles.CoghavenChestTile.PagodaStyle);
			Item.width = 32;
			Item.height = 30;
			Item.value = Item.sellPrice(silver: 1);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<CinnabarLacquer>(8)
				.AddRecipeGroup(RecipeGroupID.IronBar, 2)
				.AddTile(TileID.WorkBenches)
				.Register();
		}
	}
}
