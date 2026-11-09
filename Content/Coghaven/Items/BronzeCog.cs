using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>Bronze Cog, the placeable (see <see cref="Tiles.BronzeCogTile"/>): a 6x6 cog that turns on two tiles. Found on
	/// Coghaven; crafted at a Tinkerer's Workshop from 12 Bronze Gearwork and a Jade Brick.</summary>
	public class BronzeCog : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.BronzeCogTile>());
			Item.width = 32;
			Item.height = 32;
			Item.rare = ItemRarityID.Green;
			Item.value = Item.sellPrice(silver: 30);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<BronzeGearwork>(12)
				.AddIngredient<JadeBrick>()
				.AddTile(TileID.TinkerersWorkbench)
				.Register();
		}
	}
}
