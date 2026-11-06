using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>
	/// Tarnished Brass Bar (2026-11-03): Old Brass Town's metal, smelted from <see cref="TarnishedBrassOre"/> (3 a bar at a
	/// Furnace, like vanilla's gold). A material for the town's gear to come; rolled into <see cref="TarnishedBrassPlating"/>.
	/// </summary>
	public class TarnishedBrassBar : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 25;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 20;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(silver: 4);
			Item.rare = ItemRarityID.Green;
		}

		public override void AddRecipes() {
			CreateRecipe().AddIngredient<TarnishedBrassOre>(3).AddTile(TileID.Furnaces).Register();
		}
	}
}
