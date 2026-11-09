using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>The block (see <see cref="Tiles.CinnabarLacquerTile"/>): mined in Coghaven. Four of its wall make one back at a Work Bench.</summary>
	public class CinnabarLacquer : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.CinnabarLacquerTile>());
			Item.value = Item.sellPrice(copper: 20);
		}
		public override void AddRecipes() {
			CreateRecipe().AddIngredient<CinnabarPanelWall>(4).AddTile(TileID.WorkBenches).Register();
		}
	}
}
