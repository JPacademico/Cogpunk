using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>The placeable wall (see <see cref="Walls.PalaceFlagstoneWallTile"/>): four from a Palace Flagstone at a Work
	/// Bench.</summary>
	public class PalaceFlagstoneWall : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 400;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableWall(ModContent.WallType<Walls.PalaceFlagstoneWallTile>());
		}

		public override void AddRecipes() {
			CreateRecipe(4).AddIngredient<PalaceFlagstone>().AddTile(TileID.WorkBenches).Register();
		}
	}
}
