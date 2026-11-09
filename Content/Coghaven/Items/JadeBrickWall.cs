using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>The placeable wall (see <see cref="Walls.JadeBrickWallTile"/>): four from a Jade Brick block at a Work Bench.</summary>
	public class JadeBrickWall : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 400;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableWall(ModContent.WallType<Walls.JadeBrickWallTile>());
		}

		public override void AddRecipes() {
			CreateRecipe(4).AddIngredient<JadeBrick>().AddTile(TileID.WorkBenches).Register();
		}
	}
}
