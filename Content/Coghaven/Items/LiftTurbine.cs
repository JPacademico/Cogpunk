using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>Lift Turbine, the placeable (see <see cref="Tiles.LiftTurbineTile"/>): hangs under a ceiling of solid blocks,
	/// 4 wide. Found on Coghaven's underside; crafted at a Tinkerer's Workshop from 10 Bronze Gearwork, 5 Jade Bricks and a
	/// Steampunk Boiler's worth of brass (8 Tarnished Brass Bars), so builders can make their own floating islands.</summary>
	public class LiftTurbine : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.LiftTurbineTile>());
			Item.width = 24;
			Item.height = 32;
			Item.rare = ItemRarityID.Green;
			Item.value = Item.sellPrice(silver: 50);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<BronzeGearwork>(10)
				.AddIngredient<JadeBrick>(5)
				.AddIngredient<OldBrassTown.Items.TarnishedBrassBar>(8)
				.AddTile(TileID.TinkerersWorkbench)
				.Register();
		}
	}
}
