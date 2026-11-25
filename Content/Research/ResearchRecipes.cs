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
			nodeConditions.Clear();
		}

		private static readonly System.Collections.Generic.Dictionary<string, Condition> nodeConditions = new();

		/// <summary>A recipe condition "Researched: &lt;node&gt;" for recipes added one by one (2026-11-25: the altar's), built once
		/// per node: the crafting player has unlocked <paramref name="nodeName"/>. Call after <see cref="ResearchNodes"/> is set up
		/// (in <c>AddRecipes</c>).</summary>
		public static Condition NodeCondition(string nodeName) {
			if (nodeConditions.TryGetValue(nodeName, out Condition existing)) {
				return existing;
			}
			ResearchNode node = ResearchNodes.Get(nodeName);
			Condition c = new(Language.GetText("Mods.Cogpunk.Research.RecipeCondition").WithFormatArgs(node?.DisplayName ?? Language.GetText(nodeName)),
				() => Main.LocalPlayer.GetModPlayer<ResearchPlayer>().Has(nodeName));
			nodeConditions[nodeName] = c;
			return c;
		}

		/// <summary>Any gem robe: vanilla's seven and the Jade Robe (2026-11-24: the Rainbow Robe's recipe and RGBT's reveal).</summary>
		public const string GemRobes = "Cogpunk:GemRobes";

		public static readonly int[] VanillaGemRobes = { ItemID.AmethystRobe, ItemID.TopazRobe, ItemID.SapphireRobe, ItemID.EmeraldRobe,
			ItemID.RubyRobe, ItemID.DiamondRobe, ItemID.AmberRobe };

		/// <summary>A gem robe (vanilla's seven or the Jade Robe).</summary>
		public static bool IsGemRobe(int type) {
			if (type == ModContent.ItemType<Gems.Items.JadeRobe>()) {
				return true;
			}
			foreach (int robe in VanillaGemRobes) {
				if (robe == type) {
					return true;
				}
			}
			return false;
		}

		public override void AddRecipeGroups() {
			int[] robes = new int[VanillaGemRobes.Length + 1];
			VanillaGemRobes.CopyTo(robes, 0);
			robes[^1] = ModContent.ItemType<Gems.Items.JadeRobe>();
			RecipeGroup.RegisterGroup(GemRobes, new RecipeGroup(
				() => Language.GetTextValue("Mods.Cogpunk.Research.GemRobeGroup"), robes));
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
			// Seasoning (2026-11-24): every recipe made at a Cooking Pot (ours, vanilla's, any mod's) may keep its ingredients
			for (int k = 0; k < Recipe.numRecipes; k++) {
				Recipe recipe = Main.recipe[k];
				if (recipe?.requiredTile != null && recipe.requiredTile.Contains(TileID.CookingPots)) {
					recipe.AddConsumeIngredientCallback(ResearchCrafting.SeasonIngredient);
				}
			}
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
