using System.Collections.Generic;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Meals
{
	/// <summary>
	/// The four meals of the "Proper Meal" research node (user, 2026-11-24: "unlocks crafting recipes for 4 new meals"), each a
	/// class's meal: eaten like vanilla food, cooked at a Cooking Pot, its buff lasting <see cref="BuffTicks"/> (20 minutes,
	/// user-set). One at a time (my call, as vanilla's fed states and flasks replace each other): eating one takes the others'
	/// buffs away. The recipes are locked until the node is researched (<see cref="ResearchRecipes"/>). Art:
	/// art/research/make_meals_art.py.
	/// <para>D2: the buff is added on the eater's client and synced by vanilla; the stats come from the buff on every side.</para>
	/// </summary>
	public abstract class ProperMealItem : CogpunkItem
	{
		public const int BuffTicks = 20 * 60 * 60;            // user-set: "for 20 minutes"

		protected abstract int MealBuff { get; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(BuffTicks / 3600);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 5;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.useStyle = ItemUseStyleID.EatFood;
			Item.useAnimation = 17;                          // vanilla's food (decompiled Item.DefaultToFood)
			Item.useTime = 17;
			Item.useTurn = true;
			Item.UseSound = SoundID.Item2;
			Item.maxStack = Item.CommonMaxStack;
			Item.consumable = true;
			Item.buffType = MealBuff;
			Item.buffTime = BuffTicks;
			Item.rare = ItemRarityID.Green;
			Item.value = Item.sellPrice(silver: 20);
		}

		/// <summary>One proper meal at a time: the other three's buffs go as this one is eaten.</summary>
		public override bool? UseItem(Player player) {
			foreach (int other in ProperMealBuff.All) {
				if (other != MealBuff) {
					player.ClearBuff(other);
				}
			}
			return null;
		}
	}

	/// <summary>A proper meal's buff (<see cref="ProperMealItem"/>): +3% of the class's stats and +20 of a resource
	/// (user-set for the mage and melee meals, "follow the same logic" for the other two).</summary>
	public abstract class ProperMealBuff : CogpunkBuff
	{
		public const float Bonus = 0.03f;                      // user-set: 3%
		public const int Pool = 20;                            // user-set: +20 max mana (mage) / max health (melee)
		/// <summary>The four buffs' types (filled as they load; one meal at a time).</summary>
		public static readonly List<int> All = new();

		public override void SetStaticDefaults() {
			if (!All.Contains(Type)) {
				All.Add(Type);
			}
		}

		public override void Unload() {
			All.Clear();
		}
	}

	/// <summary>The players' side of the meals that has no stat to add to: the Deadeye Chili's ammo saving.</summary>
	public sealed class ProperMealPlayer : ModPlayer
	{
		public bool AmmoSaver;

		public override void ResetEffects() {
			AmmoSaver = false;
		}

		/// <summary>The shooter's client (vanilla asks there before it takes a round).</summary>
		public override bool CanConsumeAmmo(Item weapon, Item ammo) {
			return !AmmoSaver || Main.rand.NextFloat() >= ProperMealBuff.Bonus;
		}
	}
}
