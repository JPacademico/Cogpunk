using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Meals
{
	// --- the summoner's meal (my design): Firefly Jelly, gel set round a firefly in a bottle's water

	public class FireflyJelly : ProperMealItem
	{
		protected override int MealBuff => ModContent.BuffType<FireflyJellyBuff>();

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.Gel, 3)
				.AddRecipeGroup(RecipeGroupID.Fireflies)
				.AddIngredient(ItemID.BottledWater)
				.AddTile(TileID.CookingPots)
				.Register();
		}
	}

	public class FireflyJellyBuff : ProperMealBuff
	{
		public override void Update(Player player, ref int buffIndex) {
			player.GetDamage(DamageClass.Summon) += Bonus;
			player.GetAttackSpeed(DamageClass.SummonMeleeSpeed) += Bonus;   // whip speed
			player.whipRangeMultiplier += Bonus;
			player.GetKnockback(DamageClass.Summon) += Bonus;
			player.statLifeMax2 += Pool;
		}
	}
}
