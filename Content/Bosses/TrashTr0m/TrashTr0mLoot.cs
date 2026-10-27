using Cogpunk.Content.Bosses.TrashTr0m.Items;
using Cogpunk.Content.Bosses.TrashTr0m.Weapons;
using Cogpunk.Content.Scrap.Items;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	/// <summary>
	/// Trash-Tr0m's loot (user-set 2026-10-26), shared by the boss (<see cref="TrashTr0m.ModifyNPCLoot"/>) and its
	/// <see cref="TrashTr0mBag"/>:
	/// <list type="bullet">
	/// <item>the <see cref="LostKey"/>, on the <b>first</b> kill in a world only (<see cref="FirstKillCondition"/>);</item>
	/// <item>Expert and Master: a <see cref="TrashTr0mBag"/> per player (vanilla <c>ItemDropRule.BossBag</c>) holding
	/// <see cref="MinScrap"/>-<see cref="MaxScrap"/> Rusted Scrap, <see cref="MinGold"/>-<see cref="MaxGold"/> Gold Coins and
	/// one weapon from <see cref="WeaponPool"/>;</item>
	/// <item>Classic: the same scrap and weapon dropped directly (the coins come from <c>NPC.value</c>, as for every
	/// vanilla boss).</item>
	/// </list>
	/// </summary>
	public static class TrashTr0mLoot
	{
		public const int MinScrap = 10, MaxScrap = 30;
		public const int MinGold = 1, MaxGold = 5;

		/// <summary>One of the four Trash-Tr0m weapons, one per vanilla class.</summary>
		public static int[] WeaponPool() => new[] {
			ModContent.ItemType<Tetanus>(),
			ModContent.ItemType<ScrapLauncher>(),
			ModContent.ItemType<Scrapmancer>(),
			ModContent.ItemType<Tr0mheadStaff>(),
		};

		/// <summary>The bag's rules (built once at load: allocation is fine here).</summary>
		public static void AddBagContents(ILoot loot) {
			loot.Add(ItemDropRule.OneFromOptionsNotScalingWithLuck(1, WeaponPool()));
			loot.Add(ItemDropRule.Common(ModContent.ItemType<RustedScrap>(), 1, MinScrap, MaxScrap));
			loot.Add(ItemDropRule.Common(ItemID.GoldCoin, 1, MinGold, MaxGold));
		}
	}

	/// <summary>
	/// True until Trash-Tr0m has been defeated once in this world. Decompiled <c>NPC.NPCLoot</c>: the drop rules run
	/// (<c>NPCLoot_DropItems</c>) before <c>NPCLoader.OnKill</c>, where <see cref="TrashTr0m.OnKill"/> sets the downed flag,
	/// so the first kill still sees it clear. Read on the server (or singleplayer), where loot is rolled.
	/// </summary>
	public sealed class FirstKillCondition : IItemDropRuleCondition
	{
		public bool CanDrop(DropAttemptInfo info) => !TrashTr0mSystem.Downed;

		public bool CanShowItemDropInUI() => true;

		public string GetConditionDescription() => Language.GetTextValue("Mods.Cogpunk.DropConditions.TrashTr0mFirstKill");
	}
}
