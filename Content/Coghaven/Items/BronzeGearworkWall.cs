using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>The placeable wall (see <see cref="Walls.BronzeGearworkWallTile"/>): four from a Bronze Gearwork block at a Work Bench.</summary>
	public class BronzeGearworkWall : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 400;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableWall(ModContent.WallType<Walls.BronzeGearworkWallTile>());
		}

		public override void AddRecipes() {
			CreateRecipe(4).AddIngredient<BronzeGearwork>().AddTile(TileID.WorkBenches).Register();
		}
	}
}
