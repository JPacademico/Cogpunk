using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Items
{
	/// <summary>
	/// Large Jade (Jade Grande), the "big gem" of the default gem crafts (user, 2026-11-09): 15 <see cref="Jade"/> at an
	/// anvil, as vanilla's Large Emerald (decompiled 1.4.4 <c>Recipe</c>: 15 gems, tile 16; <c>Item.SetDefaults</c> 1525:
	/// 20x20, Blue rarity, no value). It behaves as vanilla's Capture the Gem gems do (<see cref="LargeJadePlayer"/>): while
	/// carried it hovers over its bearer's head, and a softcore or journey character who dies drops it.
	/// </summary>
	public class LargeJade : CogpunkItem
	{
		public const int JadeCost = 15;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 20;
			Item.height = 20;
			Item.rare = ItemRarityID.Blue;
		}

		public override void AddRecipes() {
			CreateRecipe().AddIngredient<Jade>(JadeCost).AddTile(TileID.Anvils).Register();
		}
	}
}
