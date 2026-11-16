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

	/// <summary>Jadey's loot (my call, 2026-11-16; no unique item yet: the user hasn't named one): Jade and a Large Jade,
	/// and in the bag her coins.</summary>
	public static class JadeyLoot
	{
		public const int MinJade = 15, MaxJade = 25;

		public static void AddClassic(LeadingConditionRule classic) {
			classic.OnSuccess(ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), 1, MinJade, MaxJade));
			classic.OnSuccess(ItemDropRule.Common(ModContent.ItemType<Gems.Items.LargeJade>()));
		}

		public static void AddBagContents(ILoot loot) {
			loot.Add(ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), 1, MinJade, MaxJade));
			loot.Add(ItemDropRule.Common(ModContent.ItemType<Gems.Items.LargeJade>()));
			loot.Add(ItemDropRule.CoinsBasedOnNPCValue(ModContent.NPCType<Jadey>()));
		}
	}
}
