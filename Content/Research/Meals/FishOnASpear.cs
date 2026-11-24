using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Meals
{
	// --- the melee meal: "fish on a spear using 2 of any fish + a mushroom and a stick ... (3% for melee stats + 20 max health,
	// lasting 20 minutes)" (the fish: vanilla's "any fish" group of the Seafood Dinner; the stick: any wood)

	public class FishOnASpear : ProperMealItem
	{
		protected override int MealBuff => ModContent.BuffType<FishOnASpearBuff>();

		public override void AddRecipes() {
			CreateRecipe()
				.AddRecipeGroup(RecipeGroupID.FishForDinner, 2)
				.AddIngredient(ItemID.Mushroom)
				.AddRecipeGroup(RecipeGroupID.Wood)
				.AddTile(TileID.CookingPots)
				.Register();
		}
	}

	public class FishOnASpearBuff : ProperMealBuff
	{
		public override void Update(Player player, ref int buffIndex) {
			player.GetDamage(DamageClass.Melee) += Bonus;
			player.GetCritChance(DamageClass.Melee) += Bonus * 100f;
			player.GetAttackSpeed(DamageClass.Melee) += Bonus;
			player.GetKnockback(DamageClass.Melee) += Bonus;
			player.statLifeMax2 += Pool;
		}
	}
}
