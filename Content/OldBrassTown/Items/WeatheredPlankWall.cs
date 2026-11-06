using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>The placeable wall (see <see cref="Walls.WeatheredPlankWallTile"/>): four from a block at a Work Bench, and back.</summary>
	public class WeatheredPlankWall : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 400;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableWall(ModContent.WallType<Walls.WeatheredPlankWallTile>());
		}

		public override void AddRecipes() {
			CreateRecipe(4).AddIngredient<WeatheredPlank>().AddTile(TileID.WorkBenches).Register();
		}
	}
}
