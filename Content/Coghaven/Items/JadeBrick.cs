using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>The block (see <see cref="Tiles.JadeBrickTile"/>): no longer part of Coghaven (since 2026-11-06 the palace's
	/// floors are Palace Flagstone and its jade is the roofs'), so it is made at a Furnace: ten from ten stone and an emerald;
	/// four of its wall make one back at a Work Bench.</summary>
	public class JadeBrick : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.JadeBrickTile>());
			Item.value = Item.sellPrice(copper: 20);
		}
		public override void AddRecipes() {
			CreateRecipe(10).AddIngredient(ItemID.StoneBlock, 10).AddIngredient(ItemID.Emerald).AddTile(TileID.Furnaces).Register();
			CreateRecipe().AddIngredient<JadeBrickWall>(4).AddTile(TileID.WorkBenches).Register();
		}
	}
}
