using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Meals
{
	// --- the mage's meal: "blue star fruit ... gives +3% mage damage and crit +3% mana regen -3% mana consumption and +20 max
	// mana (can pass the limit) for 20 minutes and uses one of any fruit item and a mana star" (the star read as a Fallen Star)

	public class BlueStarFruit : ProperMealItem
	{
		protected override int MealBuff => ModContent.BuffType<BlueStarFruitBuff>();

		public override void AddRecipes() {
			CreateRecipe()
				.AddRecipeGroup(RecipeGroupID.Fruit)
				.AddIngredient(ItemID.FallenStar)
				.AddTile(TileID.CookingPots)
				.Register();
		}
	}

	public class BlueStarFruitBuff : ProperMealBuff
	{
		public override void Update(Player player, ref int buffIndex) {
			player.GetDamage(DamageClass.Magic) += Bonus;
			player.GetCritChance(DamageClass.Magic) += Bonus * 100f;
			// +3% mana regeneration: 3% of vanilla's regeneration base (decompiled Player.UpdateManaRegen: max mana / 3 + 1)
			player.manaRegenBonus += System.Math.Max(1, (int)((player.statManaMax2 / 3 + 1) * Bonus + 0.5f));
			player.manaCost -= Bonus;
			player.statManaMax2 += Pool;                      // past the 200 of the Mana Crystals: max mana has no cap of its own
		}
	}
}
