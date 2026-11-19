using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// Recipes a research node unlocks (user, 2026-11-18: nodes "unlocking crafting recipes that were locked before"): every
	/// recipe that makes an item in a node's <see cref="ResearchNode.Recipes"/> gets a condition (tModLoader's
	/// <c>Recipe.AddCondition</c>) that the crafting player has unlocked that node, shown in the recipe's tooltip as the node's
	/// name. None of the first three nodes unlocks a recipe; the hook is here for the ones to come.
	/// </summary>
	public sealed class ResearchRecipes : ModSystem
	{
		private static bool[] gemWeapons;
		public const int GemWeaponPasses = 6;                  // D0: the "made from a gem weapon" chain is followed this deep

		/// <summary>"Gem Power" (user, 2026-11-18): a weapon "that use gem or other gem weapons on crafting recipe": a gem or a
		/// gem weapon in any of its recipes (vanilla's gem staves, phaseblades and phasesabers, the Jade Staff...).</summary>
		public static bool IsGemWeapon(Item item) {
			return item != null && !item.IsAir && gemWeapons != null && item.type > 0 && item.type < gemWeapons.Length && gemWeapons[item.type];
		}

		public override void Unload() {
			gemWeapons = null;
		}

		private static void FindGemWeapons() {
			gemWeapons = new bool[ItemLoader.ItemCount];
			bool[] gem = new bool[ItemLoader.ItemCount];
			int[] gems = { ItemID.Amethyst, ItemID.Topaz, ItemID.Sapphire, ItemID.Emerald, ItemID.Ruby, ItemID.Diamond, ItemID.Amber,
				ItemID.LargeAmethyst, ItemID.LargeTopaz, ItemID.LargeSapphire, ItemID.LargeEmerald, ItemID.LargeRuby, ItemID.LargeDiamond,
				ItemID.LargeAmber, ModContent.ItemType<Gems.Items.Jade>(), ModContent.ItemType<Gems.Items.LargeJade>() };
			foreach (int g in gems) {
				if (g > 0 && g < gem.Length) {
					gem[g] = true;
				}
			}
			for (int pass = 0; pass < GemWeaponPasses; pass++) {
				bool changed = false;
				for (int k = 0; k < Recipe.numRecipes; k++) {
					Recipe recipe = Main.recipe[k];
					Item result = recipe?.createItem;
					if (result == null || result.IsAir || result.type >= gemWeapons.Length || gemWeapons[result.type] || !IsWeapon(result)) {
						continue;
					}
					foreach (Item part in recipe.requiredItem) {
						int t = part?.type ?? 0;
						if (t > 0 && t < gem.Length && (gem[t] || gemWeapons[t])) {
							gemWeapons[result.type] = true;
							changed = true;
							break;
						}
					}
				}
				if (!changed) {
					break;
				}
			}
		}

		private static bool IsWeapon(Item item) => item.damage > 0 && item.useStyle != 0 && item.ammo == 0 && item.pick == 0 && item.axe == 0
			&& item.hammer == 0 && !item.accessory;

		public override void PostAddRecipes() {
			FindGemWeapons();
			foreach (ResearchNode node in ResearchNodes.All) {
				if (node.Recipes.Length == 0) {
					continue;
				}
				string name = node.Name;
				Condition researched = new(Language.GetText("Mods.Cogpunk.Research.RecipeCondition").WithFormatArgs(node.DisplayName),
					() => Main.LocalPlayer.GetModPlayer<ResearchPlayer>().Has(name));
				for (int k = 0; k < Recipe.numRecipes; k++) {
					Recipe recipe = Main.recipe[k];
					if (recipe == null || recipe.createItem == null || recipe.createItem.IsAir) {
						continue;
					}
					foreach (int type in node.Recipes) {
						if (recipe.createItem.type == type) {
							recipe.AddCondition(researched);
							break;
						}
					}
				}
			}
		}
	}
}
