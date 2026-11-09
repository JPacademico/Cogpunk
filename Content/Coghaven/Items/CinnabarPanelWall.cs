using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>The placeable wall (see <see cref="Walls.CinnabarPanelWallTile"/>): four from a Cinnabar Lacquer block at a Work Bench.</summary>
	public class CinnabarPanelWall : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 400;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableWall(ModContent.WallType<Walls.CinnabarPanelWallTile>());
		}

		public override void AddRecipes() {
			CreateRecipe(4).AddIngredient<CinnabarLacquer>().AddTile(TileID.WorkBenches).Register();
		}
	}
}
