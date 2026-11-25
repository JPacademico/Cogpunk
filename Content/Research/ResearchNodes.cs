using System;
using System.Collections.Generic;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research
{
	/// <summary>An item a node takes from the inventory when it is unlocked: any item that <see cref="Matches"/>, up to
	/// <see cref="Count"/> in all (user, 2026-11-18: "consume the required amount from the player inventory when unlocked (from
	/// left to right top to bottom ...)").</summary>
	public sealed class ResearchItemCost
	{
		public readonly Func<Item, bool> Matches;
		public readonly int Count;
		public readonly string LabelKey;                      // Mods.Cogpunk.Research.Costs.<LabelKey>, "{0}" = Count
		/// <summary><see cref="Count"/> different kinds, one of each (user, 2026-11-24: "costs 5 different potions to unlock (any
		/// potion but has to be different not 5 of the same)"): the first kinds met left to right, top to bottom, one item
		/// taken from each.</summary>
		public readonly bool Distinct;

		public ResearchItemCost(Func<Item, bool> matches, int count, string labelKey, bool distinct = false) {
			Matches = matches;
			Count = count;
			LabelKey = labelKey;
			Distinct = distinct;
		}
	}

	/// <summary>
	/// One node of the research tree (user, 2026-11-18). Shown at (<see cref="Column"/>, <see cref="Row"/>), row 0 at the bottom
	/// ("nodes (from bottom-up order)"), with an item's sprite as its icon (<see cref="IconItem"/>: "any in game block or object
	/// that matches; if it's a recipe unlocking node it should have the item sprite as icon"); its name and text are
	/// <c>Mods.Cogpunk.Research.Nodes.&lt;Name&gt;.DisplayName / Description</c>. Unlocked once, for good, per player, when
	/// everything it asks for is met: its <see cref="Cost"/> in knowledge points, the nodes it <see cref="Requires"/>, its
	/// <see cref="Condition"/> (a step in the world) and its <see cref="Items"/> (taken from the inventory). It may be hidden
	/// until <see cref="Reveal"/> holds ("secret" nodes; once seen, it stays). It gives a <see cref="Passive"/> bonus (every
	/// tick while unlocked) and/or unlocks the recipes of <see cref="Recipes"/> (locked until then: <see cref="ResearchRecipes"/>).
	/// Lines are drawn only to the nodes in <see cref="Links"/> (user: "Nodes should only be connected if i specify").
	/// </summary>
	public sealed class ResearchNode
	{
		public string Name { get; init; }
		public int Column { get; init; }
		public int Row { get; init; }
		public int Cost { get; init; }
		public int IconItem { get; init; }
		public string[] Requires { get; init; } = Array.Empty<string>();
		public string[] Links { get; init; } = Array.Empty<string>();
		public ResearchItemCost[] Items { get; init; } = Array.Empty<ResearchItemCost>();
		/// <summary>A step the player must have made (null: none). <see cref="ConditionText"/> describes it with its progress.</summary>
		public Func<Player, bool> Condition { get; init; }
		public Func<Player, string> ConditionText { get; init; }
		/// <summary>Hidden until this holds for the player (null: always shown).</summary>
		public Func<Player, bool> Reveal { get; init; }
		/// <summary>Applied every tick while unlocked (ModPlayer.PostUpdateEquips, every side).</summary>
		public Action<Player> Passive { get; init; }
		/// <summary>Items whose recipes this node unlocks.</summary>
		public int[] Recipes { get; init; } = Array.Empty<int>();
		/// <summary>A secret shown as a question mark before <see cref="Reveal"/> holds (user, 2026-11-19: "nodes that have a
		/// question mark and get revealed once you kill a base game boss"); other secrets don't show at all until then.</summary>
		public bool Teaser { get; init; }
		/// <summary>The hint a <see cref="Teaser"/> gives while it is a question mark: <c>Mods.Cogpunk.Research.Hints.&lt;key&gt;</c>
		/// (null: the general "a great foe must fall first").</summary>
		public string TeaserHint { get; init; }
		/// <summary>A progress line under a teaser's hint (2026-11-25: Bad Luck Protection's kills); null: none.</summary>
		public Func<Player, string> TeaserProgress { get; init; }
		/// <summary>The window's tab the node sits in (user, 2026-11-24: "a new tab ... called "mystery of the past" ... a
		/// different node set"): <see cref="ResearchNodes.MainTab"/> or <see cref="ResearchNodes.MysteryTab"/>.</summary>
		public int Tab { get; init; }
		/// <summary>A Fundamental Stone glyph (an index into <c>FundamentalRunes.png</c>) drawn as the icon instead of an item
		/// (the Mystery of the Past's sigils); -1: <see cref="IconItem"/>.</summary>
		public int IconGlyph { get; init; } = -1;
		/// <summary>A texture of its own drawn as the icon (an asset path, 2x art, up to 32 x 32 game px), instead of an item
		/// (2026-11-25: "Who is he?"'s circled Ghedalari); null: <see cref="IconItem"/> or <see cref="IconGlyph"/>.</summary>
		public string IconTexture { get; init; }
		/// <summary>Money it takes, in copper (user, 2026-11-25: "it should cost 10 gold coins to unlock"): paid like a purchase,
		/// from the inventory and the banks (vanilla's <c>Player.BuyItem</c>); 0: none.</summary>
		public long Coins { get; init; }

		/// <summary>Index in <see cref="ResearchNodes.All"/> (the sync bit).</summary>
		public int Index { get; internal set; }

		public LocalizedText DisplayName => Language.GetText("Mods.Cogpunk.Research.Nodes." + Name + ".DisplayName");
		public LocalizedText Description => Language.GetText("Mods.Cogpunk.Research.Nodes." + Name + ".Description");
	}

	/// <summary>
	/// The research tree's nodes (user, 2026-11-18: "add 3 nodes to begin with"), registered in a fixed order: a node's index
	/// is its sync bit, so the order must be the same on every side (it is: this list). Saved by name (D0 rule 9).
	/// <list type="number">
	/// <item><b>The Basics</b>: "a obligatory initial node it should not have knowledge points requirement but requires the
	/// player to have collected at least one of every base pre hardmode minerals (the nuggets not the bars, hellstone/demonite
	/// not included), and rewards with + 5% mining speed". My reading: the four tiers of ore, either of each pair (copper or
	/// tin, iron or lead, silver or tungsten, gold or platinum: a world only has one of each); "obligatory initial": every
	/// other node needs it first (without a line: none was asked for).</item>
	/// <item><b>Mine and Craft</b>: "requires 10 of any ore and gives the player a chance to double nugget while mining any ore
	/// (10%)" (<see cref="ResearchGlobalTile"/>). The 10 ores are taken (any ore items, mixed). Cost: 1 knowledge point (my
	/// call: the user gave none).</item>
	/// <item><b>Jogger</b>: "requires the player to have reached both edge biomes of the world (ocean and junkyard) and gives
	/// +3% speed when unlocked". Cost: 1 knowledge point (my call).</item>
	/// </list>
	/// <para>Layout (user, 2026-11-18: "the secret nodes ... should not be on top of the main progression arch of nodes on the
	/// research menu they should always be at the side or down"): the main arch grows up from The Basics (columns -1..1, rows
	/// 0 and up); secret nodes sit beside it (columns -3 and 3) or below row 0, never above it. Each source of secrets keeps
	/// its own column: the Scrap Manual's on the right, the world's (Just the Tip, Bundle Up!) on the left.</para>
	/// </summary>
	public sealed class ResearchNodes : ModSystem
	{
		public const string TheBasics = "TheBasics", MineAndCraft = "MineAndCraft", Jogger = "Jogger", Cogpunker = "Cogpunker",
			GemPower = "GemPower", InACaveWithScraps = "InACaveWithScraps", HitTheJoints = "HitTheJoints", Mandacaru = "Mandacaru",
			CausesAutism = "CausesAutism", Squire = "Squire", JustTheTip = "JustTheTip", BundleUp = "BundleUp",
			HeatManagement = "HeatManagement", BringAKnife = "BringAKnife", TriggerFinger = "TriggerFinger", DilatedPupils = "DilatedPupils",
			Slimed = "Slimed", Calcified = "Calcified",
			// 2026-11-24
			AlchemyInitiate = "AlchemyInitiate", FulfillingConcoction = "FulfillingConcoction", EfficientFuel = "EfficientFuel",
			Reconstructed = "Reconstructed", Seasoning = "Seasoning", ProperMeal = "ProperMeal", GreenIsGood = "GreenIsGood",
			GreenDiamond = "GreenDiamond", MadScience = "MadScience",
			SigilFleur = "SigilFleur", SigilSun = "SigilSun", SigilMountain = "SigilMountain", SigilCross = "SigilCross", SigilWave = "SigilWave",
			// 2026-11-24 (second message)
			Rgbt = "Rgbt", JadeMenagerie = "JadeMenagerie",
			// 2026-11-25 (the alpha: quality of life at the demon altar, and the Last Ghedalari's arrival)
			LaceUp = "LaceUp", UnholyCarpentry = "UnholyCarpentry", BadLuckProtection = "BadLuckProtection",
			CrateExpectations = "CrateExpectations", WhoIsHe = "WhoIsHe";
		public const int BadLuckKills = 300;                   // user-set: "a "?" until you kill 300 enemies"
		public const long WhoIsHeCoins = 10L * 100L * 100L;    // user-set: "it should cost 10 gold coins to unlock" (in copper)
		/// <summary>The window's tabs (user, 2026-11-24): the main tree, and the Mystery of the Past once a Fundamental Stone has
		/// been touched (<see cref="ResearchPlayer.MysteryTab"/>).</summary>
		public const int MainTab = 0, MysteryTab = 1, TabCount = 2;
		public const int AlchemyDaybloom = 5, AlchemyMushrooms = 5;       // user-set: "requires 5 daybloom and 5 mushroom"
		public const float PotionDoubleChance = 0.10f;         // user-set: "10% chance to double the potion when crafting"
		public const int ConcoctionPotions = 5;                // user-set: "5 different potions"
		public const int ConcoctionWellFedTicks = 5 * 60 * 60; // user-set: "the well fed buff for 5 minutes"
		public const float EfficientFuelSaving = 0.05f;        // user-set: "decreses steam consuption in 5%"
		public const int SeasoningFoods = 5;                   // user-set: "5 diferent food itens"
		public const float SeasoningChance = 0.10f;            // user-set: "10% chance to not consume the itens"
		public const int GreenIsGoodHeal = 20;                 // user-set: "heal when killing a jade petrified enemy (20 health)"
		public const float GreenIsGoodResistance = 0.20f;      // user-set: "damage resistance when jade petrified by an enemy (20%)"
		public const float MadScienceSpeed = 0.05f;            // user-set: "increase the attack speed of combined weapons by 5%"
		/// <summary>The Mystery of the Past's sigils (my calls, placeholders until the user designs the puzzle's rewards): the
		/// fleur +1 life regeneration (a Band of Regeneration's), the sun a soft light about you, the mountain +2 defense, the
		/// cross +5% movement speed, the wave +50% breath.</summary>
		public const int SigilFleurRegen = 1, SigilMountainDefense = 2;
		public const float SigilCrossSpeed = 0.05f, SigilWaveBreath = 0.5f;
		public static readonly Microsoft.Xna.Framework.Vector3 SigilSunLight = new(0.45f, 0.40f, 0.22f);
		public const float BasicsMiningSpeed = 0.05f;          // user-set: +5% mining speed
		public const float DoubleOreChance = 0.10f;            // user-set: 10%
		public const int MineAndCraftOres = 10;                // user-set
		public const float JoggerSpeed = 0.03f;                // user-set: +3% speed
		public const int CogpunkerSteam = 10;                  // user-set: +10 steam capacity
		public const float GemPowerBonus = 0.03f;              // user-set: +3% damage, crit, attack speed, -3% mana cost
		public const float HitTheJointsBonus = 0.10f;          // user-set: +10% damage against machines
		public const int SquireDefense = 1;                    // user-set: +1 defense
		public const float JustTheTipBonus = 0.25f;            // user-set: +25% spear damage at full reach
		/// <summary>"Just the Tip"'s window: the last thrust frames and the first frames of the pull back ("ending frames of the
		/// thrust or initial frame of the return motion"; my call: 3 and 1).</summary>
		public const int TipThrustFrames = 3, TipReturnFrames = 1;
		public const float TriggerFingerBonus = 0.25f;         // user-set: +25% a missed shot, on the next hit
		public const int TriggerFingerStacks = 4;              // user-set: up to 4 times
		public const float DilatedPupilsCrit = 5f;             // user-set: +5% crit at night, -5% by day
		public const int SlimedGel = 200;                      // user-set: 200 gel
		public const int SlimedTicks = 300;                    // my call: an enemy stays slimed 5 s
		public const int CalcifiedDamage = 40;                 // user-set: the bone deals 40
		public const int MaxNodes = 256;                       // D0: the sync carries at most this many bits

		private static readonly List<ResearchNode> all = new();
		private static readonly Dictionary<string, ResearchNode> byName = new();

		public static IReadOnlyList<ResearchNode> All => all;

		public static ResearchNode Get(string name) => name != null && byName.TryGetValue(name, out ResearchNode n) ? n : null;

		public override void PostSetupContent() {
			ResearchGlobalTile.BuildOreTable();
			all.Clear();
			byName.Clear();
			Add(new ResearchNode {
				Name = TheBasics, Column = 0, Row = 0, Cost = 0, IconItem = ItemID.CopperPickaxe,
				Condition = static p => p.GetModPlayer<ResearchPlayer>().AllOreTiers,
				ConditionText = static p => ResearchPlayer.OreTiersText(p),
				Passive = static p => p.pickSpeed -= BasicsMiningSpeed,
			});
			Add(new ResearchNode {
				Name = MineAndCraft, Column = -1, Row = 1, Cost = 1, IconItem = ItemID.IronOre,
				Requires = new[] { TheBasics },
				Items = new[] { new ResearchItemCost(static item => ResearchItems.IsOre(item), MineAndCraftOres, "AnyOre") },
			});
			Add(new ResearchNode {
				Name = Jogger, Column = 1, Row = 1, Cost = 1, IconItem = ItemID.HermesBoots,
				Requires = new[] { TheBasics },
				Condition = static p => p.GetModPlayer<ResearchPlayer>().ReachedBothEdges,
				ConditionText = static p => ResearchPlayer.EdgesText(p),
				Passive = static p => p.moveSpeed += JoggerSpeed,
			});
			// 2026-11-18 (second research request)
			Add(new ResearchNode {
				Name = Cogpunker, Column = 0, Row = 1, Cost = 1, IconItem = ModContent.ItemType<Mechanist.Accessories.BrassContainer>(),
				Requires = new[] { TheBasics },
				Passive = static p => p.GetModPlayer<Mechanist.SteamPlayer>().SteamMaxInnate += CogpunkerSteam,
			});
			Add(new ResearchNode {
				Name = GemPower, Column = -1, Row = 2, Cost = 0, IconItem = ItemID.Diamond,
				Requires = new[] { TheBasics },
				Items = GemCosts(),
				Passive = static p => {
					if (ResearchRecipes.IsGemWeapon(p.HeldItem)) {
						p.GetDamage(DamageClass.Generic) += GemPowerBonus;
						p.GetCritChance(DamageClass.Generic) += GemPowerBonus * 100f;
						p.GetAttackSpeed(DamageClass.Generic) += GemPowerBonus;
						p.manaCost -= GemPowerBonus;
					}
				},
			});
			Add(new ResearchNode {
				Name = CausesAutism, Column = 1, Row = 2, Cost = 1, IconItem = ModContent.ItemType<Bosses.TrashTr0m.Items.TetanusShot>(),
				Requires = new[] { TheBasics },
				Recipes = new[] { ModContent.ItemType<Bosses.TrashTr0m.Items.TetanusShot>() },
			});
			// secret: revealed by reading Trash-Tr0m's Scrap Manual (user: "add a first set of secret nodes that get revealed when
			// consuming the trashtr0m manual item")
			Add(new ResearchNode {
				Name = InACaveWithScraps, Column = 3, Row = 0, Cost = 1, IconItem = ModContent.ItemType<Scrap.Armor.ScrapHelmet>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.ScrapManual)),
				Recipes = new[] { ModContent.ItemType<Scrap.Armor.ScrapHelmet>(), ModContent.ItemType<Scrap.Armor.ScrapBreastplate>(),
					ModContent.ItemType<Scrap.Armor.ScrapLeggings>() },
			});
			Add(new ResearchNode {
				Name = HitTheJoints, Column = 3, Row = 1, Cost = 2, IconItem = ModContent.ItemType<Scrap.Items.RustedCog>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.ScrapManual)),
			});
			Add(new ResearchNode {
				Name = Mandacaru, Column = 3, Row = 2, Cost = 1, IconItem = ModContent.ItemType<Desert.Weapons.Cakti>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.ScrapManual)),
				Recipes = new[] { ModContent.ItemType<Desert.Weapons.Cakti>() },
			});
			// 2026-11-18 (third research request); appended (a node's index is its sync bit)
			Add(new ResearchNode {
				// "requires a zombie, slime, or eye banner and gives a permanent +1 to defense" (any one of the three, taken)
				Name = Squire, Column = 0, Row = 2, Cost = 0, IconItem = ItemID.SquireGreatHelm,
				Requires = new[] { TheBasics },
				Items = new[] { new ResearchItemCost(static item => item.type == ItemID.ZombieBanner || item.type == ItemID.SlimeBanner
					|| item.type == ItemID.DemonEyeBanner, 1, "SquireBanner") },
				Passive = static p => p.statDefense += SquireDefense,
			});
			Add(new ResearchNode {
				// secret: "appears when the player visits a marble biome"; the spear bonus is in ResearchPlayer.ModifyHitNPCWithProj
				Name = JustTheTip, Column = -3, Row = 0, Cost = 1, IconItem = ItemID.Spear,
				Requires = new[] { TheBasics },
				Reveal = static p => p.ZoneMarble || p.GetModPlayer<ResearchPlayer>().Earned(KnowledgeTasks.Marble),
			});
			Add(new ResearchNode {
				// secret: "appears when a any player has obtained all pre hardmode gem staffs (globally)" (ResearchWorld.AllGemStaffs)
				Name = BundleUp, Column = -3, Row = 1, Cost = 1, IconItem = ModContent.ItemType<Weapons.BundleOfWands>(),
				Requires = new[] { TheBasics },
				Reveal = static p => ResearchWorld.AllGemStaffs,
				Recipes = new[] { ModContent.ItemType<Weapons.BundleOfWands>() },
			});
			// 2026-11-19; appended (a node's index is its sync bit)
			eyeKey = KnowledgeTasks.Boss(NPCID.EyeofCthulhu);
			slimeKey = KnowledgeTasks.Boss(NPCID.KingSlime);
			skeletronKey = KnowledgeTasks.Boss(NPCID.SkeletronHead);
			Add(new ResearchNode {
				// user, 2026-11-23 (replacing 2026-11-19's 10% resistance): "gives the player ability to stay still when overheated
				// (not obligatory to move). costs a knowledge point" (Mechanist.SteamPlayer.SetControls)
				Name = HeatManagement, Column = 0, Row = 3, Cost = 1, IconItem = ItemID.ObsidianSkull,
				Requires = new[] { TheBasics },
			});
			// secret: the Sheriff's Law Book (the Cursed Conductor's manual) "should now reveal 2 secret nodes when consumed"
			Add(new ResearchNode {
				Name = BringAKnife, Column = 4, Row = 0, Cost = 1, IconItem = ModContent.ItemType<Weapons.BanditsDream>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.SheriffsLawBook)),
				Recipes = new[] { ModContent.ItemType<Weapons.BanditsDream>() },
			});
			Add(new ResearchNode {
				Name = TriggerFinger, Column = 4, Row = 1, Cost = 1, IconItem = ModContent.ItemType<OldBrassTown.Weapons.SheriffsRevolver>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.SheriffsLawBook)),
			});
			// question marks until a vanilla boss falls (user, 2026-11-19)
			Add(new ResearchNode {
				// "+5% crit at night and -5% crit at day and costs 1 black lens. reveals when eye of cthullu is killed"
				Name = DilatedPupils, Column = -4, Row = 0, Cost = 0, IconItem = ItemID.BlackLens, Teaser = true,
				Requires = new[] { TheBasics }, Reveal = static p => BossDown(p, NPC.downedBoss1, eyeKey),
				Items = new[] { new ResearchItemCost(static item => item.type == ItemID.BlackLens, 1, "BlackLens") },
				Passive = static p => p.GetCritChance(DamageClass.Generic) += Main.dayTime ? -DilatedPupilsCrit : DilatedPupilsCrit,
			});
			Add(new ResearchNode {
				// "reveals after king slime and makes so the player apply slimed effect to enemy upon contact. costs 200 slime"
				Name = Slimed, Column = -4, Row = 1, Cost = 0, IconItem = ItemID.Gel, Teaser = true,
				Requires = new[] { TheBasics }, Reveal = static p => BossDown(p, NPC.downedSlimeKing, slimeKey),
				Items = new[] { new ResearchItemCost(static item => item.type == ItemID.Gel, SlimedGel, "Gel") },
			});
			Add(new ResearchNode {
				// "reveals after skeletron and makes so every enemy killed launches a small bone flying that deals 40 damage if it
				// hits another enemy. costs a research point"
				Name = Calcified, Column = -4, Row = 2, Cost = 1, IconItem = ItemID.Bone, Teaser = true,
				Requires = new[] { TheBasics }, Reveal = static p => BossDown(p, NPC.downedBoss3, skeletronKey),
			});
			// 2026-11-24; appended (a node's index is its sync bit)
			Add(new ResearchNode {
				// "requires 5 daybloom and 5 mushroom and makes so the player has 10% chance to double the potion when crafting"
				// (ResearchCrafting.OnCreated); on the arch beside Heat Management
				Name = AlchemyInitiate, Column = -1, Row = 3, Cost = 0, IconItem = ItemID.LesserHealingPotion,
				Requires = new[] { TheBasics },
				Items = new[] {
					new ResearchItemCost(static item => item.type == ItemID.Daybloom, AlchemyDaybloom, "Daybloom"),
					new ResearchItemCost(static item => item.type == ItemID.Mushroom, AlchemyMushrooms, "Mushroom"),
				},
			});
			Add(new ResearchNode {
				// "connected to this ... an interrogation ... reveals only when the player finds a alchemy table (gets within crafting
				// range, or gets one in the inventory), its called "fulfilling concoction" and makes so after drinking a potion the
				// player gets the well fed buff for 5 minutes, and costs 5 diferent potions" (ResearchCrafting.OnConsumeItem); a
				// secret, so beside the arch
				Name = FulfillingConcoction, Column = -2, Row = 3, Cost = 0, IconItem = ItemID.AlchemyTable, Teaser = true,
				TeaserHint = "AlchemyTable", Requires = new[] { AlchemyInitiate }, Links = new[] { AlchemyInitiate },
				Reveal = static p => p.GetModPlayer<ResearchPlayer>().FoundAlchemyTable,
				Items = new[] { new ResearchItemCost(static item => ResearchCrafting.IsPotion(item), ConcoctionPotions, "Potions", distinct: true) },
			});
			Add(new ResearchNode {
				// secret, the Sticky Pages (the Tar Tyrant's manual): "efficient fuel costs 1 knowledge point and decreses steam
				// consuption in 5%"; a new source of secrets, its own column (5)
				Name = EfficientFuel, Column = 5, Row = 0, Cost = 1, IconItem = ModContent.ItemType<Junkyard.Items.CondensedTar>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.StickyPages)),
				Passive = static p => p.GetModPlayer<Mechanist.SteamPlayer>().SteamCostMultiplier -= EfficientFuelSaving,
			});
			Add(new ResearchNode {
				// "reconstructed costs a knowledge point and unlocks the crafting recipe for a new mount called "missing bones""
				Name = Reconstructed, Column = 5, Row = 1, Cost = 1, IconItem = ModContent.ItemType<Mounts.MissingBones>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.StickyPages)),
				Recipes = new[] { ModContent.ItemType<Mounts.MissingBones>() },
			});
			Add(new ResearchNode {
				// "an interrogation and gets revealed when the player finds a cooking pot (gets into use range or gets one on the
				// inventory), called "seasoning" it requires a 5 diferent food itens and makes so cooking has a 10% chance to not
				// consume the itens used for the recipe" (ResearchRecipes' cooking callback)
				Name = Seasoning, Column = 2, Row = 2, Cost = 0, IconItem = ItemID.CookingPot, Teaser = true, TeaserHint = "CookingPot",
				Requires = new[] { TheBasics }, Reveal = static p => p.GetModPlayer<ResearchPlayer>().FoundCookingPot,
				Items = new[] { new ResearchItemCost(static item => ResearchCrafting.IsFood(item), SeasoningFoods, "Foods", distinct: true) },
			});
			Add(new ResearchNode {
				// "connected to the "seasoning" node called "propper meal" that costs a knowledge point and unlocks crafting recipes
				// for 4 new meals"; shown with Seasoning (the same reveal), above it
				Name = ProperMeal, Column = 2, Row = 3, Cost = 1, IconItem = ModContent.ItemType<Meals.FishOnASpear>(),
				Requires = new[] { Seasoning }, Links = new[] { Seasoning },
				Reveal = static p => p.GetModPlayer<ResearchPlayer>().FoundCookingPot,
				Recipes = new[] { ModContent.ItemType<Meals.BlueStarFruit>(), ModContent.ItemType<Meals.FishOnASpear>(),
					ModContent.ItemType<Meals.DeadeyeChili>(), ModContent.ItemType<Meals.FireflyJelly>() },
			});
			Add(new ResearchNode {
				// secret, the Jade-shaper Manual (Jadey's): "green = good" heals on killing a jade petrified enemy and resists damage
				// while petrified (ResearchPlayer); its own column (-5)
				Name = GreenIsGood, Column = -5, Row = 0, Cost = 1, IconItem = ModContent.ItemType<Gems.Items.Jade>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.JadeShaperManual)),
				Passive = static p => {
					if (p.GetModPlayer<Gems.JadeCursePlayer>().Petrified) {
						p.endurance += GreenIsGoodResistance;
					}
				},
			});
			Add(new ResearchNode {
				// "green diamond costs a knowlegde point and unlocks the "jade refractor" mechanist weapon"
				Name = GreenDiamond, Column = -5, Row = 1, Cost = 1, IconItem = ModContent.ItemType<Weapons.JadeRefractor>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.JadeShaperManual)),
				Recipes = new[] { ModContent.ItemType<Weapons.JadeRefractor>() },
			});
			Add(new ResearchNode {
				// "a new hardmode node that is an interrogation and reveals when the player first crafts a combined weapon from the
				// combinator, it should be called "mad science" and increase the attack speed of combined weapons by 5% and cost 2
				// reasearch points" (the Combinator's own knowledge task is paid as a weapon is combined)
				Name = MadScience, Column = 2, Row = 0, Cost = 2, IconItem = ModContent.ItemType<Combinator.Items.TheCombinator>(),
				Teaser = true, TeaserHint = "Combinator", Requires = new[] { TheBasics },
				Reveal = static p => p.GetModPlayer<ResearchPlayer>().Earned(KnowledgeTasks.Combinator),
				Passive = static p => {
					if (Combinator.Combination.CombinedWeapon.IsCombined(p.HeldItem)) {
						p.GetAttackSpeed(DamageClass.Generic) += MadScienceSpeed;
					}
				},
			});
			// The Mystery of the Past (user, 2026-11-24: "a new tab that appears once the player has interacted with a
			// fundamental stone ... have a different node set to unlock based on the fundamental stones puzzle"): one sigil per
			// stone, laid out as the five points of a star, each a question mark until its stone has been read (the reading is
			// the price: no points). Their bonuses are my placeholders (SigilFleurRegen...).
			AddSigil(SigilFleur, FundamentalStonesIndex.Fleur, -1, 0, static p => p.lifeRegen += SigilFleurRegen);
			AddSigil(SigilSun, FundamentalStonesIndex.Sun, 1, 0, static p => {
				if (!Main.dedServ) {
					Lighting.AddLight(p.Center, SigilSunLight);
				}
			});
			AddSigil(SigilMountain, FundamentalStonesIndex.Mountain, 2, 1, static p => p.statDefense += SigilMountainDefense);
			AddSigil(SigilCross, FundamentalStonesIndex.Cross, 0, 2, static p => p.moveSpeed += SigilCrossSpeed);
			AddSigil(SigilWave, FundamentalStonesIndex.Wave, -2, 1, static p => p.breathMax += (int)(p.breathMax * SigilWaveBreath));
			// 2026-11-24 (second message); appended (a node's index is its sync bit)
			Add(new ResearchNode {
				// "a new node called "rgbt" it should be connected to the gem mage node but show only an "?" until the player has
				// obtained at leat one gem robe (any). and unlocks (one knowledge point) the crafting of the rainbow robe"; beside
				// Gem Power, on its row
				Name = Rgbt, Column = -2, Row = 2, Cost = 1, IconItem = ModContent.ItemType<Armor.RainbowRobe>(), Teaser = true,
				TeaserHint = "GemRobe", Requires = new[] { GemPower }, Links = new[] { GemPower },
				Reveal = static p => p.GetModPlayer<ResearchPlayer>().FoundGemRobe,
				Recipes = new[] { ModContent.ItemType<Armor.RainbowRobe>() },
			});
			Add(new ResearchNode {
				// secret, the Jade-shaper Manual: "a new node that is unlocked by the jade manual that unlocks the crafting of a new
				// summon weapon called "jade coin" using a platinum coin + 8 jades"; under Green Diamond in the manual's column
				Name = JadeMenagerie, Column = -5, Row = 2, Cost = 1, IconItem = ModContent.ItemType<Summons.JadeCoin>(),
				Requires = new[] { TheBasics }, Reveal = static p => ReadManual(p, nameof(Manuals.Items.JadeShaperManual)),
				Recipes = new[] { ModContent.ItemType<Summons.JadeCoin>() },
			});
			// 2026-11-25 (the alpha); appended (a node's index is its sync bit). The quality-of-life recipes (user: "add the quality
			// of life crafting recipes from calamity ... This quality of life crafts can only be crafting with a demon altar (or the
			// new demon table)"; Altar/AltarRecipes): one row under The Basics (a cluster of the altar's crafts; secrets go
			// beside or below the arch, never above it), the Demon Table in the middle
			Add(new ResearchNode {
				// "craft for the anklet of the wind and aglet (1 knowledge point, available at any time)": Calamity's two recipes,
				// at the altar. Not through Recipes: another mod's own Aglet recipe (Calamity's, at an anvil) must stay as it is
				Name = LaceUp, Column = -1, Row = -1, Cost = 1, IconItem = ItemID.AnkletoftheWind,
				Requires = new[] { TheBasics },
			});
			Add(new ResearchNode {
				// "be able to craft a demon table (demon/crimson altar crafting station but without spreading corruption or scarying
				// npcs) ... add a node for it that costs a voodoo doll and stays "?" until a crimson or corruption heart is broken on
				// the world" (either voodoo doll; vanilla's world flag, synced with the world data)
				Name = UnholyCarpentry, Column = 0, Row = -1, Cost = 0, IconItem = ModContent.ItemType<Altar.DemonTable>(),
				Teaser = true, TeaserHint = "EvilHeart", Requires = new[] { TheBasics },
				Reveal = static p => WorldGen.shadowOrbSmashed || p.GetModPlayer<ResearchPlayer>().Earned(KnowledgeTasks.EvilHeart),
				Items = new[] { new ResearchItemCost(static item => item.type == ItemID.GuideVoodooDoll || item.type == ItemID.ClothierVoodooDoll,
					1, "VoodooDoll") },
				Recipes = new[] { ModContent.ItemType<Altar.DemonTable>() },
			});
			Add(new ResearchNode {
				// "be able to craft a rare drop from the enemy using the enemy banner (add a node for it that is a "?" until you kill
				// 300 enemies and costs 1 knowledge point)" (the kills: ResearchPlayer.Kills)
				Name = BadLuckProtection, Column = 1, Row = -1, Cost = 1, IconItem = ItemID.ZombieBanner, Teaser = true, TeaserHint = "Kills",
				TeaserProgress = static p => Language.GetTextValue("Mods.Cogpunk.Research.Hints.KillsProgress",
					Math.Min(BadLuckKills, p.GetModPlayer<ResearchPlayer>().Kills), BadLuckKills),
				Requires = new[] { TheBasics }, Reveal = static p => p.GetModPlayer<ResearchPlayer>().Kills >= BadLuckKills,
			});
			Add(new ResearchNode {
				// "craft a fishing box item using 5 of the same fishing box that the item can come from (a node for this that costs 1
				// knowledge point, reveals after fishing a crate for the first time)"
				Name = CrateExpectations, Column = 2, Row = -1, Cost = 1, IconItem = ItemID.WoodenCrate, Teaser = true, TeaserHint = "Crate",
				Requires = new[] { TheBasics }, Reveal = static p => p.GetModPlayer<ResearchPlayer>().FishedCrate,
			});
			Add(new ResearchNode {
				// "make so our main mod npc the last ghedalari can only appear after unlocking a node on the mystery of the past tab of
				// the research table. this node should be called "who is he?" and reveal after interacting with a fundamental stone
				// (globaly) and the icon for it should be the npc miniature with a red circle and arrow arround it (like the "who is
				// he?" meme). it should cost 10 gold coins to unlock" (ResearchWorld.GhedalariInvited); the middle of the sigils' star
				Name = WhoIsHe, Tab = MysteryTab, Column = 0, Row = 1, Cost = 0, Coins = WhoIsHeCoins,
				IconItem = ModContent.ItemType<Secrets.Ruins.Items.FundamentalRune>(), IconTexture = "Cogpunk/Content/Research/UI/WhoIsHe",
				Teaser = true, TeaserHint = "WhoIsHe", Requires = new[] { TheBasics },
				Reveal = static p => ResearchWorld.StoneTouched || p.GetModPlayer<ResearchPlayer>().TouchedStone,
			});
		}

		/// <summary>The Fundamental Stones' numbers (their styles: <see cref="Secrets.FundamentalStones"/>) by their sigil.</summary>
		private static class FundamentalStonesIndex
		{
			public const int Fleur = 0, Sun = 1, Mountain = 2, Cross = 3, Wave = 4;
		}

		private static void AddSigil(string name, int stone, int column, int row, Action<Player> passive) {
			Add(new ResearchNode {
				Name = name, Tab = MysteryTab, Column = column, Row = row, Cost = 0, IconGlyph = stone,
				IconItem = ModContent.ItemType<Secrets.Ruins.Items.FundamentalRune>(), Teaser = true, TeaserHint = "Stone",
				Requires = new[] { TheBasics }, Reveal = p => p.GetModPlayer<ResearchPlayer>().Earned(KnowledgeTasks.StoneKey(stone)),
				Passive = passive,
			});
		}

		private static bool ReadManual(Player p, string manual) => p.GetModPlayer<Manuals.ManualPlayer>().Knows(manual);

		// The vanilla bosses' task keys, built once (the reveals run every frame the window is open: no string building, D1)
		private static string eyeKey, slimeKey, skeletronKey;

		/// <summary>A vanilla boss down for this player: the world has it (<paramref name="downed"/>), or the character was
		/// paid for its first kill somewhere (<see cref="KnowledgeTasks.Boss"/>).</summary>
		private static bool BossDown(Player p, bool downed, string key) => downed || p.GetModPlayer<ResearchPlayer>().Earned(key);

		/// <summary>"requires one of each gem (jade included)": one of each of vanilla's seven gems and a Jade, taken.</summary>
		private static ResearchItemCost[] GemCosts() {
			int[] gems = { ItemID.Amethyst, ItemID.Topaz, ItemID.Sapphire, ItemID.Emerald, ItemID.Ruby, ItemID.Diamond, ItemID.Amber,
				ModContent.ItemType<Gems.Items.Jade>() };
			string[] labels = { "Amethyst", "Topaz", "Sapphire", "Emerald", "Ruby", "Diamond", "Amber", "Jade" };
			ResearchItemCost[] costs = new ResearchItemCost[gems.Length];
			for (int k = 0; k < gems.Length; k++) {
				int type = gems[k];
				costs[k] = new ResearchItemCost(item => item.type == type, 1, labels[k]);
			}
			return costs;
		}

		private static void Add(ResearchNode node) {
			if (all.Count >= MaxNodes || node.Name == null || byName.ContainsKey(node.Name)) {
				return;
			}
			node.Index = all.Count;
			all.Add(node);
			byName[node.Name] = node;
		}

		public override void Unload() {
			all.Clear();
			byName.Clear();
		}
	}

	/// <summary>Which items are ores (any item that places a tile vanilla flags as an ore, <c>TileID.Sets.Ore</c>: vanilla's and
	/// other mods' ores alike), and the four base pre-Hardmode tiers for <see cref="ResearchNodes.TheBasics"/>.</summary>
	public static class ResearchItems
	{
		public static bool IsOre(Item item) {
			if (item == null || item.IsAir) {
				return false;
			}
			int t = item.createTile;
			return t >= 0 && t < TileID.Sets.Ore.Length && TileID.Sets.Ore[t];
		}

		/// <summary>The base tier (0 copper/tin, 1 iron/lead, 2 silver/tungsten, 3 gold/platinum) of an ore item, or -1.</summary>
		public static int BaseTier(int type) => type switch {
			ItemID.CopperOre or ItemID.TinOre => 0,
			ItemID.IronOre or ItemID.LeadOre => 1,
			ItemID.SilverOre or ItemID.TungstenOre => 2,
			ItemID.GoldOre or ItemID.PlatinumOre => 3,
			_ => -1,
		};
	}
}
