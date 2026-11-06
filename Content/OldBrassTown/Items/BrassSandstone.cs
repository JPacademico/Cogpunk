using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>Brass Sandstone, the block (see <see cref="Tiles.BrassSandstoneTile"/>).</summary>
	public class BrassSandstone : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.BrassSandstoneTile>());
			Item.value = 0;
		}

		public override void AddRecipes() {
			CreateRecipe().AddIngredient<BrassSandstoneWall>(4).AddTile(TileID.WorkBenches).Register();
		}
	}
}
