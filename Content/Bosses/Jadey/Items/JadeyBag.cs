using Cogpunk.Core.Templates;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Items
{
	/// <summary>Treasure Bag (Jadey): Expert and Master, one per player (vanilla <c>ItemDropRule.BossBag</c>); contents in
	/// <see cref="JadeyLoot"/>. Set up like ExampleMod 1.4.4's <c>MinionBossBag</c>; pre-Hardmode (Coghaven is T4).</summary>
	public class JadeyBag : CogpunkItem
	{
		public override void SetStaticDefaults() {
			ItemID.Sets.BossBag[Type] = true;
			ItemID.Sets.PreHardmodeLikeBossBag[Type] = true;
			Item.ResearchUnlockCount = 3;
		}

		public override void SetDefaults() {
			Item.maxStack = Item.CommonMaxStack;
			Item.consumable = true;
			Item.width = 32;
			Item.height = 32;
			Item.rare = ItemRarityID.Purple;
			Item.expert = true;
		}

		public override bool CanRightClick() => true;

		public override void ModifyItemLoot(ItemLoot itemLoot) {
			JadeyLoot.AddBagContents(itemLoot);
		}
	}

	/// <summary>
	/// Jadey's loot (user-set 2026-11-17): one of her weapons (<see cref="WeaponPool"/>: the Jade-shaper Whip, the Jade Cursed
	/// Glaives, the Firework Cannon and, since 2026-11-18, the Incense Mace), <see cref="MinJade"/>-<see cref="MaxJade"/> Jade ("1-10 jades and not 15-25") and a
	/// Large Jade; the bag adds her Expert item, the <see cref="JadeShaperPendant"/> ("Jadey should give from her bag the
	/// Jade-shaper pendant"), and her coins. Her Jade-shaper Manual drops beside the bag, one per player, on her first defeat
	/// (<see cref="Manuals.ManualDrop"/>).
	/// </summary>
	public static class JadeyLoot
	{
		public const int MinJade = 1, MaxJade = 10;        // user-set 2026-11-17

		/// <summary>One of her four weapons, one per class she suits (summoner, melee, mage and, since 2026-11-18, mechanist:
		/// user, "add a new weapon to Jadey weapon pool called Incense mace").</summary>
		public static int[] WeaponPool() => new[] {
			ModContent.ItemType<Weapons.JadeShaperWhip>(),
			ModContent.ItemType<Weapons.JadeCursedGlaives>(),
			ModContent.ItemType<Weapons.FireworkCannon>(),
			ModContent.ItemType<Weapons.IncenseMace>(),
		};

		public static void AddClassic(LeadingConditionRule classic) {
			classic.OnSuccess(ItemDropRule.OneFromOptionsNotScalingWithLuck(1, WeaponPool()));
			classic.OnSuccess(ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), 1, MinJade, MaxJade));
			classic.OnSuccess(ItemDropRule.Common(ModContent.ItemType<Gems.Items.LargeJade>()));
		}

		public static void AddBagContents(ILoot loot) {
			loot.Add(ItemDropRule.OneFromOptionsNotScalingWithLuck(1, WeaponPool()));
			loot.Add(ItemDropRule.Common(ModContent.ItemType<JadeShaperPendant>()));
			loot.Add(ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), 1, MinJade, MaxJade));
			loot.Add(ItemDropRule.Common(ModContent.ItemType<Gems.Items.LargeJade>()));
			loot.Add(ItemDropRule.CoinsBasedOnNPCValue(ModContent.NPCType<Jadey>()));
		}
	}
}
