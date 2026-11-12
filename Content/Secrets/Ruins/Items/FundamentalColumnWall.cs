using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Items
{
	/// <summary>Fundamental Column Wall (2026-11-10b): fluted drums; two side by side make a pillar.</summary>
	public class FundamentalColumnWall : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 400;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableWall(ModContent.WallType<Walls.FundamentalColumnWallTile>());
		}

		public override void AddRecipes() {
			CreateRecipe(4).AddIngredient<FundamentalBrick>().AddTile(TileID.WorkBenches).Register();
		}
	}
}
