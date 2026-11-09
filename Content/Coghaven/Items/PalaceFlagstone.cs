using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>The block (see <see cref="Tiles.PalaceFlagstoneTile"/>): mined in Coghaven, or cut from stone at a Heavy Work
	/// Bench; four of its wall make one back at a Work Bench.</summary>
	public class PalaceFlagstone : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.PalaceFlagstoneTile>());
			Item.value = Item.sellPrice(copper: 20);
		}

		public override void AddRecipes() {
			CreateRecipe(2).AddIngredient(ItemID.StoneBlock, 2).AddTile(TileID.HeavyWorkBench).Register();
			CreateRecipe().AddIngredient<PalaceFlagstoneWall>(4).AddTile(TileID.WorkBenches).Register();
		}
	}
}
