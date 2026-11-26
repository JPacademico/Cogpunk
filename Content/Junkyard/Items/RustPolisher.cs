using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Items
{
	/// <summary>
	/// Places a <see cref="RustPolisherTile"/>, the Junkyard's crafting station (ExampleMod 1.4.4 <c>ExampleWorkbench</c>).
	/// Recipe (anvil, user-set 2026-10-26): the <see cref="PolisherSchematic"/> (needed, never consumed: the ingredient
	/// callback keeps it, and shimmer decrafting is off so it can't be duplicated) + <see cref="BarCost"/> Copper or Tin
	/// Bars + <see cref="CogCost"/> Rusted Cogs + <see cref="SandCost"/> sand blocks of any kind.
	/// </summary>
	public class RustPolisher : CogpunkItem
	{
		public const int BarCost = 30;
		public const int CogCost = 42;                     // 35 -> 42, x1.2 (user, 2026-11-26)
		public const int SandCost = 50;

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<RustPolisherTile>());
			Item.width = 48;
			Item.height = 40;
			Item.value = Item.sellPrice(silver: 60);
			Item.rare = ItemRarityID.Blue;
		}

		public override void ModifyResearchSorting(ref ContentSamples.CreativeHelper.ItemGroup itemGroup) {
			itemGroup = ContentSamples.CreativeHelper.ItemGroup.CraftingObjects;
		}

		public override void AddRecipes() {
			int schematic = ModContent.ItemType<PolisherSchematic>();
			CreateRecipe()
				.AddIngredient(schematic)
				.AddRecipeGroup(VanillaRecipeGroups.CopperBar, BarCost)
				.AddIngredient<RustedCog>(CogCost)
				.AddRecipeGroup(RecipeGroupID.Sand, SandCost)
				.AddTile(TileID.Anvils)
				.AddConsumeIngredientCallback((Recipe recipe, int type, ref int amount, bool isDecrafting) => {
					if (type == schematic) {
						amount = 0;                    // the blueprint stays in the inventory
					}
				})
				.DisableDecraft()
				.Register();
		}
	}
}
