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

		public ResearchItemCost(Func<Item, bool> matches, int count, string labelKey) {
			Matches = matches;
			Count = count;
			LabelKey = labelKey;
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
			Slimed = "Slimed", Calcified = "Calcified";
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
		public const float HeatManagementResist = 0.10f;       // user-set: 10% damage resistance while overheated
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
				// "gives the player 10% damage resistance while it is overheated. costs a knowledge point" (ResearchPlayer.ModifyHurt)
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
