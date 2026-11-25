using System;
using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Altar
{
	/// <summary>
	/// The quality-of-life recipes of the alpha (user, 2026-11-25: "add the quality of life crafting recipes from calamity for our
	/// mod to ensure better player experience ... This quality of life crafts can only be crafting with a demon altar (or the new
	/// demon table)"). Every one is made only at a Demon or Crimson Altar (vanilla's tile 26, both styles), which the
	/// <see cref="DemonTableTile"/> counts as, and only once its research node is unlocked:
	/// <list type="bullet">
	/// <item><b>Lace Up</b> (<see cref="ResearchNodes.LaceUp"/>): Calamity's own two recipes (calamitymod.wiki.gg, "Vanilla item
	/// recipes", read 2026-11-25): the Aglet from any Copper Bar x5 (copper or tin), the Anklet of the Wind from Jungle Spores x15,
	/// Cloud x5 and Pink Gel x5. Added beside any other recipe for them (another mod's Aglet at an anvil stays as it is).</item>
	/// <item><b>Bad Luck Protection</b> (<see cref="ResearchNodes.BadLuckProtection"/>; user, 2026-11-25: "unlocks the crafting
	/// recipes from banners like calamity mod also has (craft a item that is a rare drop from a enemy using one or two bannner of
	/// that enemy as recipe on the demon altar/table) ... banner shoud maintain the default terraria banner rules"): read from
	/// vanilla's own drop database (every mod's loot included: tModLoader fills it with every <c>ModifyNPCLoot</c> before recipes
	/// are added, decompiled <c>ItemDropDatabase.Populate</c>), every banner gets a recipe for each rare drop of the enemies it
	/// counts (a chance of <see cref="RareChance"/> or less): one banner, or two for the rarest (rarer than 1 in
	/// <see cref="TwoBannerOdds"/>). Banners themselves are vanilla's, untouched (50 kills each). A drop's game-mode, Hardmode,
	/// mechanical-boss, Plantera and world-evil conditions become the recipe's; a drop tied to anything else (events, seeds, the
	/// Blood Moon, a statue) is left out.</item>
	/// <item><b>Crate Expectations</b> (<see cref="ResearchNodes.CrateExpectations"/>; "craft a fishing box item using 5 of the
	/// same fishing box that the item can come from"): every fishing crate (<c>ItemID.Sets.IsFishingCrate</c>, any mod's) gets a
	/// recipe for each piece of equipment it can hold (an item that doesn't stack: accessories, weapons, tools, mounts; ores,
	/// potions and coins aren't "the item"), from <see cref="CratesPerItem"/> of that crate, with the drop's conditions as above.</item>
	/// </list>
	/// <para>D0: the generated recipes are read from foreign data at load time, so each generator is a boundary in a try/catch
	/// (a failure logs once and leaves those recipes out); every type is range-checked. D1: load time only.</para>
	/// </summary>
	public sealed class AltarRecipes : ModSystem
	{
		public const string AnyCopperBar = "Cogpunk:AnyCopperBar", EvilBar = "Cogpunk:EvilBar", EvilStone = "Cogpunk:EvilStone",
			EvilChunk = "Cogpunk:EvilChunk";
		/// <summary>"A rare drop": a 5% chance or less (my call).</summary>
		public const float RareChance = 0.05f;
		/// <summary>A drop rarer than 1 in this many takes two banners, else one (user: "one or two bannner"; the line is my call).</summary>
		public const int TwoBannerOdds = 50;
		/// <summary>User-set: "using 5 of the same fishing box".</summary>
		public const int CratesPerItem = 5;
		/// <summary>Calamity's Aglet and Anklet of the Wind (calamitymod.wiki.gg).</summary>
		public const int AgletCopper = 5, AnkletSpores = 15, AnkletClouds = 5, AnkletPinkGel = 5;

		/// <summary>How many recipes each generator made (for the log and the report).</summary>
		public static int BannerRecipeCount { get; private set; }
		public static int CrateRecipeCount { get; private set; }

		public override void AddRecipeGroups() {
			// the names are the game's own, in the player's language: vanilla's "Any <item>" (LegacyMisc.37, as its Any Iron Bar),
			// and "<item> or <item>" for the two evils' materials
			RecipeGroup.RegisterGroup(AnyCopperBar, new RecipeGroup(() => Language.GetTextValue("LegacyMisc.37") + " " + Lang.GetItemNameValue(ItemID.CopperBar),
				ItemID.CopperBar, ItemID.TinBar));
			RecipeGroup.RegisterGroup(EvilBar, new RecipeGroup(() => Either(ItemID.DemoniteBar, ItemID.CrimtaneBar), ItemID.DemoniteBar, ItemID.CrimtaneBar));
			RecipeGroup.RegisterGroup(EvilStone, new RecipeGroup(() => Either(ItemID.EbonstoneBlock, ItemID.CrimstoneBlock), ItemID.EbonstoneBlock, ItemID.CrimstoneBlock));
			RecipeGroup.RegisterGroup(EvilChunk, new RecipeGroup(() => Either(ItemID.RottenChunk, ItemID.Vertebrae), ItemID.RottenChunk, ItemID.Vertebrae));
		}

		private static string Either(int a, int b) => Language.GetTextValue("Mods.Cogpunk.Research.Groups.Either", Lang.GetItemNameValue(a), Lang.GetItemNameValue(b));

		public override void AddRecipes() {
			Condition laceUp = ResearchRecipes.NodeCondition(ResearchNodes.LaceUp);
			Recipe.Create(ItemID.Aglet)
				.AddRecipeGroup(AnyCopperBar, AgletCopper)
				.AddTile(TileID.DemonAltar)
				.AddCondition(laceUp)
				.Register();
			Recipe.Create(ItemID.AnkletoftheWind)
				.AddIngredient(ItemID.JungleSpores, AnkletSpores)
				.AddIngredient(ItemID.Cloud, AnkletClouds)
				.AddIngredient(ItemID.PinkGel, AnkletPinkGel)
				.AddTile(TileID.DemonAltar)
				.AddCondition(laceUp)
				.Register();
			try {
				BannerRecipeCount = BannerRecipes(ResearchRecipes.NodeCondition(ResearchNodes.BadLuckProtection));
			}
			catch (Exception e) {
				SafeLog.Error("AltarRecipes.Banners", e);
			}
			try {
				CrateRecipeCount = CrateRecipes(ResearchRecipes.NodeCondition(ResearchNodes.CrateExpectations));
			}
			catch (Exception e) {
				SafeLog.Error("AltarRecipes.Crates", e);
			}
			Mod.Logger.Info($"Altar recipes: {BannerRecipeCount} from banners, {CrateRecipeCount} from crates.");
		}

		/// <summary>Banner -> rare drop recipes (see the class summary); returns how many.</summary>
		private static int BannerRecipes(Condition node) {
			Dictionary<(int banner, int item), Found> best = new();
			List<DropRateInfo> infos = new();
			for (int id = NPCID.NegativeIDCount + 1; id < NPCLoader.NPCCount; id++) {      // -65..: vanilla's variants (Pinky...) too
				if (id == 0) {
					continue;
				}
				int bannerItem = BannerItemOf(id);
				if (bannerItem <= 0) {
					continue;
				}
				infos.Clear();
				DropRateInfoChainFeed feed = new(1f);
				foreach (IItemDropRule rule in Main.ItemDropsDB.GetRulesForNPCID(id, includeGlobalDrops: false)) {
					rule.ReportDroprates(infos, feed);
				}
				foreach (DropRateInfo info in infos) {
					if (!Wanted(info.itemId, equipmentOnly: false) || !(info.dropRate > 0f) || info.dropRate > RareChance
						|| !MapConditions(info.conditions, out Condition[] conditions)) {
						continue;
					}
					var key = (bannerItem, info.itemId);
					if (!best.TryGetValue(key, out Found have) || info.dropRate > have.Rate) {
						best[key] = new Found(info.dropRate, Math.Max(1, info.stackMin), conditions);
					}
				}
			}
			int made = 0;
			foreach (var pair in best) {
				int banner = pair.Key.banner;
				int banners = pair.Value.Rate < 1f / TwoBannerOdds ? 2 : 1;
				Recipe recipe = Recipe.Create(pair.Key.item, pair.Value.Stack)
					.AddIngredient(banner, banners)
					.AddTile(TileID.DemonAltar)
					.AddCondition(node);
				foreach (Condition c in pair.Value.Conditions) {
					recipe.AddCondition(c);
				}
				recipe.Register();
				made++;
			}
			return made;
		}

		/// <summary>Crate -> equipment recipes (see the class summary); returns how many.</summary>
		private static int CrateRecipes(Condition node) {
			HashSet<(int crate, int item)> done = new();
			List<DropRateInfo> infos = new();
			int made = 0;
			for (int crate = 1; crate < ItemLoader.ItemCount; crate++) {
				if (crate >= ItemID.Sets.IsFishingCrate.Length || !ItemID.Sets.IsFishingCrate[crate]) {
					continue;
				}
				infos.Clear();
				DropRateInfoChainFeed feed = new(1f);
				foreach (IItemDropRule rule in Main.ItemDropsDB.GetRulesForItemID(crate)) {
					rule.ReportDroprates(infos, feed);
				}
				foreach (DropRateInfo info in infos) {
					if (!Wanted(info.itemId, equipmentOnly: true) || !(info.dropRate > 0f) || !done.Add((crate, info.itemId))
						|| !MapConditions(info.conditions, out Condition[] conditions)) {
						continue;
					}
					Recipe recipe = Recipe.Create(info.itemId)
						.AddIngredient(crate, CratesPerItem)
						.AddTile(TileID.DemonAltar)
						.AddCondition(node);
					foreach (Condition c in conditions) {
						recipe.AddCondition(c);
					}
					recipe.Register();
					made++;
				}
			}
			return made;
		}

		/// <summary>The banner item that counts kills of <paramref name="npcNetId"/> (vanilla's tables, any mod's banner), or 0.</summary>
		private static int BannerItemOf(int npcNetId) {
			int banner = Item.NPCtoBanner(npcNetId);
			if (banner <= 0) {
				return 0;
			}
			int item = Item.BannerToItem(banner);
			return item > ItemID.None && item < ItemLoader.ItemCount ? item : 0;
		}

		/// <summary>An item worth a recipe: a real item (no coins, hearts or stars), and for crates one that doesn't stack and
		/// isn't used up (equipment).</summary>
		private static bool Wanted(int type, bool equipmentOnly) {
			if (type <= ItemID.None || type >= ItemLoader.ItemCount || !ContentSamples.ItemsByType.TryGetValue(type, out Item sample)) {
				return false;
			}
			if ((type < ItemID.Sets.CommonCoin.Length && ItemID.Sets.CommonCoin[type])
				|| (type < ItemID.Sets.ItemsThatShouldNotBeInInventory.Length && ItemID.Sets.ItemsThatShouldNotBeInInventory[type])) {
				return false;
			}
			return !equipmentOnly || (sample.maxStack == 1 && !sample.consumable);
		}

		/// <summary>A drop's conditions as recipe conditions: game modes, Hardmode, the mechanical bosses, Plantera and the world's
		/// evil carry over; "not from a statue" and "not Expert/Master" need none (banners and crates come from real kills and
		/// catches, and an item's other branch covers the other modes); anything else (events, seeds, moons, specific AIs) makes
		/// the drop unwanted (false).</summary>
		private static bool MapConditions(List<IItemDropRuleCondition> source, out Condition[] mapped) {
			mapped = Array.Empty<Condition>();
			if (source == null || source.Count == 0) {
				return true;
			}
			List<Condition> list = new();
			foreach (IItemDropRuleCondition c in source) {
				switch (c) {
					case null:
					case Conditions.NotFromStatue:
					case Conditions.NotExpert:
					case Conditions.NotMasterMode:
						break;
					case Conditions.IsExpert:
						list.Add(Condition.InExpertMode);
						break;
					case Conditions.IsMasterMode:
						list.Add(Condition.InMasterMode);
						break;
					case Conditions.IsHardmode:
						list.Add(Condition.Hardmode);
						break;
					case Conditions.IsPreHardmode:
						list.Add(Condition.PreHardmode);
						break;
					case Conditions.DownedPlantera:
						list.Add(Condition.DownedPlantera);
						break;
					case Conditions.DownedAllMechBosses:
						list.Add(Condition.DownedMechBossAll);
						break;
					case Conditions.BeatAnyMechBoss:
						list.Add(Condition.DownedMechBossAny);
						break;
					case Conditions.IsCrimson:
					case Conditions.IsCrimsonAndNotExpert:
						list.Add(Condition.CrimsonWorld);
						break;
					case Conditions.IsCorruption:
					case Conditions.IsCorruptionAndNotExpert:
						list.Add(Condition.CorruptWorld);
						break;
					default:
						return false;
				}
			}
			mapped = list.ToArray();
			return true;
		}

		private readonly struct Found
		{
			public readonly float Rate;
			public readonly int Stack;
			public readonly Condition[] Conditions;

			public Found(float rate, int stack, Condition[] conditions) {
				Rate = rate;
				Stack = stack;
				Conditions = conditions;
			}
		}
	}
}
