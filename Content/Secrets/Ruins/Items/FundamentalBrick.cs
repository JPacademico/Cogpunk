using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Items
{
	/// <summary>Fundamental Brick: mined from the Fundamental Ruins (2026-11-10b).</summary>
	public class FundamentalBrick : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.FundamentalBrickTile>());
			Item.value = Item.sellPrice(copper: 20);
		}

		public override void AddRecipes() {
			CreateRecipe().AddIngredient<FundamentalBrickWall>(4).AddTile(TileID.WorkBenches).Register();
		}
	}
}
