using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// The kitchen and the alchemy bench of the research tree (user, 2026-11-24):
	/// <list type="bullet">
	/// <item><b>Alchemy Initiate</b>: "10% chance to double the potion when crafting (so instead of crafting one it crafts two
	/// despite costing like one)": a potion (<see cref="IsPotion"/>) made at a Placed Bottle or an Alchemy Table (any recipe
	/// needing <c>TileID.Bottles</c>; the table counts as one, decompiled 1.4.4 <c>Player.AdjTiles</c>) comes out with its
	/// recipe's stack again on top, <see cref="ResearchNodes.PotionDoubleChance"/> of the time
	/// (<see cref="OnCreated"/>: vanilla clones the result, takes the ingredients, then calls it before the stack reaches the
	/// cursor, decompiled <c>Main.CraftItem</c>; never past the cursor's room).</item>
	/// <item><b>Fulfilling Concoction</b>: "after drinking a potion the player gets the well fed buff for 5 minutes": every
	/// potion drunk (<see cref="OnConsumeItem"/>), unless a better meal (Plenty Satisfied, Exquisitely Stuffed) is on: vanilla's
	/// <c>AddBuff</c> clears every fed state before adding one (decompiled <c>BuffID.Sets.IsFedState</c>), so it would take the
	/// better one away.</item>
	/// <item><b>Seasoning</b>: "cooking has a 10% chance to not consume the itens used for the recipe": a recipe made at a
	/// Cooking Pot (or a Cauldron, its other style) takes nothing, <see cref="ResearchNodes.SeasoningChance"/> of the time
	/// (<see cref="SeasonIngredient"/>, added to those recipes by <see cref="ResearchRecipes"/>; vanilla asks it for each
	/// ingredient in order, decompiled <c>Recipe.Create</c>, so the first one rolls for the whole craft).</item>
	/// </list>
	/// <para>D2: crafting and drinking happen on the player's own client (vanilla syncs the inventory and the buff); the rolls
	/// are that client's. D1: none of this runs per tick.</para>
	/// </summary>
	public sealed class ResearchCrafting : GlobalItem
	{
		private static bool seasoned;

		/// <summary>A potion: drunk (<c>ItemUseStyleID.DrinkLiquid</c>), used up, not a food or a drink (vanilla's
		/// <c>ItemID.Sets.IsFood</c>: ale, coffee, milkshakes), and it heals, restores mana or gives a buff (healing and mana
		/// potions, buff potions, flasks).</summary>
		public static bool IsPotion(Item item) {
			return item != null && !item.IsAir && item.consumable && item.useStyle == ItemUseStyleID.DrinkLiquid
				&& item.type < ItemID.Sets.IsFood.Length && !ItemID.Sets.IsFood[item.type]
				&& (item.buffType > 0 || item.healLife > 0 || item.healMana > 0);
		}

		/// <summary>A food: vanilla's food and drinks (<c>ItemID.Sets.IsFood</c>), or anything that feeds (a fed state's buff).</summary>
		public static bool IsFood(Item item) {
			if (item == null || item.IsAir) {
				return false;
			}
			if (item.type < ItemID.Sets.IsFood.Length && ItemID.Sets.IsFood[item.type]) {
				return true;
			}
			return item.buffType > 0 && item.buffType < BuffID.Sets.IsFedState.Length && BuffID.Sets.IsFedState[item.buffType];
		}

		/// <summary>Only drinkable things are worth a look (the potion test again in the hooks).</summary>
		public override bool AppliesToEntity(Item entity, bool lateInstantiation) {
			return lateInstantiation && entity.consumable && entity.useStyle == ItemUseStyleID.DrinkLiquid;
		}

		/// <summary>A brew: a recipe made at a Placed Bottle (the Alchemy Table stands in for one).</summary>
		private static bool IsBrew(Recipe recipe) {
			if (recipe?.requiredTile == null) {
				return false;
			}
			foreach (int tile in recipe.requiredTile) {
				if (tile == TileID.Bottles || tile == TileID.AlchemyTable) {
					return true;
				}
			}
			return false;
		}

		public override void OnCreated(Item item, ItemCreationContext context) {
			if (Main.dedServ || context is not RecipeItemCreationContext craft || !IsPotion(item) || !IsBrew(craft.Recipe)) {
				return;
			}
			Player player = Main.LocalPlayer;
			if (player == null || !player.active || !player.GetModPlayer<ResearchPlayer>().Has(ResearchNodes.AlchemyInitiate)
				|| Main.rand.NextFloat() >= ResearchNodes.PotionDoubleChance) {
				return;
			}
			int extra = craft.Recipe.createItem?.stack ?? 1;
			Item cursor = craft.DestinationStack;
			int held = cursor != null && !cursor.IsAir && cursor.type == item.type ? cursor.stack : 0;
			int room = item.maxStack - item.stack - held;
			if (room <= 0 || extra <= 0) {
				return;                                          // the cursor's stack is full: nothing to add (D0: no overflow)
			}
			item.stack += System.Math.Min(extra, room);
			CombatText.NewText(player.getRect(), new Color(140, 228, 88), Language.GetTextValue("Mods.Cogpunk.Research.DoubleBrew"));
			SoundEngine.PlaySound(SoundID.Item86 with { Pitch = 0.4f, Volume = 0.6f }, player.Center);
		}

		public override void OnConsumeItem(Item item, Player player) {
			if (player == null || player.whoAmI != Main.myPlayer || !IsPotion(item)
				|| !player.GetModPlayer<ResearchPlayer>().Has(ResearchNodes.FulfillingConcoction)) {
				return;
			}
			int ticks = ResearchNodes.ConcoctionWellFedTicks;
			for (int i = 0; i < player.buffType.Length; i++) {
				int buff = player.buffType[i];
				if (buff > 0 && buff != BuffID.WellFed && buff < BuffID.Sets.IsFedState.Length && BuffID.Sets.IsFedState[buff]) {
					return;                                      // a better meal: AddBuff would clear it
				}
			}
			int index = player.FindBuffIndex(BuffID.WellFed);
			if (index >= 0 && player.buffTime[index] >= ticks) {
				return;                                          // already fed for longer
			}
			player.AddBuff(BuffID.WellFed, ticks);
		}

		/// <summary>Seasoning, on every recipe made at a Cooking Pot (<see cref="ResearchRecipes"/>): the craft's first ingredient
		/// rolls; on a success every ingredient of that craft is kept. Never for shimmer decrafting.</summary>
		public static void SeasonIngredient(Recipe recipe, int type, ref int amount, bool isDecrafting) {
			if (isDecrafting || Main.dedServ || recipe?.requiredItem == null || recipe.requiredItem.Count == 0) {
				return;
			}
			if (type == recipe.requiredItem[0].type) {          // vanilla takes the ingredients in order: a new craft begins
				Player player = Main.LocalPlayer;
				seasoned = player != null && player.active && player.GetModPlayer<ResearchPlayer>().Has(ResearchNodes.Seasoning)
					&& Main.rand.NextFloat() < ResearchNodes.SeasoningChance;
				if (seasoned) {
					CombatText.NewText(player.getRect(), new Color(223, 185, 78), Language.GetTextValue("Mods.Cogpunk.Research.Seasoned"));
				}
			}
			if (seasoned) {
				amount = 0;
			}
		}

		public override void Unload() {
			seasoned = false;
		}
	}
}
