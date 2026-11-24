using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Meals
{
	// --- the ranged meal (my design, "follow the same logic"): Deadeye Chili, a bowl of fireblossom chili with mushrooms

	public class DeadeyeChili : ProperMealItem
	{
		protected override int MealBuff => ModContent.BuffType<DeadeyeChiliBuff>();

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.Bowl)
				.AddIngredient(ItemID.Fireblossom)
				.AddIngredient(ItemID.Mushroom)
				.AddTile(TileID.CookingPots)
				.Register();
		}
	}

	public class DeadeyeChiliBuff : ProperMealBuff
	{
		public override void Update(Player player, ref int buffIndex) {
			player.GetDamage(DamageClass.Ranged) += Bonus;
			player.GetCritChance(DamageClass.Ranged) += Bonus * 100f;
			player.GetAttackSpeed(DamageClass.Ranged) += Bonus;
			player.GetModPlayer<ProperMealPlayer>().AmmoSaver = true;      // 3% chance not to use a round
			player.statLifeMax2 += Pool;
		}
	}
}
