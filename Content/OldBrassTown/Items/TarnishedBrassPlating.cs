using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>Tarnished Brass Plating, the block (see <see cref="Tiles.TarnishedBrassPlatingTile"/>).</summary>
	public class TarnishedBrassPlating : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.TarnishedBrassPlatingTile>());
			Item.value = 0;
		}

		public override void AddRecipes() {
			CreateRecipe(5).AddIngredient<TarnishedBrassBar>().AddTile(TileID.Furnaces).Register();
		}
	}
}
