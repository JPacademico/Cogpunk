using Cogpunk.Content.Bosses.CursedConductor.Items;
using Cogpunk.Content.OldBrassTown.Items;
using Terraria.GameContent.ItemDropRules;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor
{
	/// <summary>
	/// The Cursed Conductor's loot (my calls, 2026-11-04: the user named no drops yet), shared by the boss
	/// (<see cref="CursedConductor.ModifyNPCLoot"/>) and its <see cref="CursedConductorBag"/> (Expert and Master only, one
	/// per player, D3 rule 0): <see cref="MinBars"/>-<see cref="MaxBars"/> Tarnished Brass Bars; the bag adds the coins of his
	/// value, as vanilla bags do. Lesser loot goes through <see cref="CursedConductor.BossLoot"/> (Healing Potions). Refights:
	/// Friendobô sells the <see cref="CursedWhistle"/> once he is beaten (the rule for every boss's summon).
	/// </summary>
	public static class CursedConductorLoot
	{
		public const int MinBars = 20, MaxBars = 35;

		public static void AddClassic(LeadingConditionRule classic) {
			classic.OnSuccess(ItemDropRule.Common(ModContent.ItemType<TarnishedBrassBar>(), 1, MinBars, MaxBars));
		}

		public static void AddBagContents(ILoot loot) {
			loot.Add(ItemDropRule.Common(ModContent.ItemType<TarnishedBrassBar>(), 1, MinBars, MaxBars));
			loot.Add(ItemDropRule.CoinsBasedOnNPCValue(ModContent.NPCType<CursedConductor>()));
		}
	}
}
