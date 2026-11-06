using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>Weathered Planks, the block (see <see cref="Tiles.WeatheredPlankTile"/>).</summary>
	public class WeatheredPlank : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.WeatheredPlankTile>());
			Item.value = 0;
		}

		public override void AddRecipes() {
			CreateRecipe().AddRecipeGroup(RecipeGroupID.Wood).AddTile(TileID.Sawmill).Register();
			CreateRecipe().AddIngredient<WeatheredPlankWall>(4).AddTile(TileID.WorkBenches).Register();
		}
	}
}
