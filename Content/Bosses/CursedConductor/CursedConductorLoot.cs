using Cogpunk.Content.Bosses.CursedConductor.Items;
using Cogpunk.Content.Bosses.CursedConductor.Weapons;
using Cogpunk.Content.OldBrassTown.Items;
using Terraria.GameContent.ItemDropRules;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor
{
	/// <summary>
	/// The Cursed Conductor's loot (my calls, 2026-11-04), shared by the boss (<see cref="CursedConductor.ModifyNPCLoot"/>)
	/// and its <see cref="CursedConductorBag"/> (Expert and Master only, one per player, D3 rule 0):
	/// <see cref="MinBars"/>-<see cref="MaxBars"/> Tarnished Brass Bars and one of his weapons (<see cref="Weapon"/>, as
	/// vanilla's bosses drop one weapon of their set: the <see cref="CursedLantern"/>, user-set 2026-11-06, or since
	/// 2026-11-09 the <see cref="CursedTrainWhistle"/>, user-set: "a new weapon to the cursed conductor weapon pool"); the bag always holds the
	/// <see cref="BottleOfLostSouls"/> (his Expert item, user-set 2026-11-06) and adds the coins of his value, as vanilla
	/// bags do. Lesser loot goes through <see cref="CursedConductor.BossLoot"/> (Healing Potions). Refights:
	/// Friendobô sells the <see cref="CursedWhistle"/> once he is beaten (the rule for every boss's summon).
	/// </summary>
	public static class CursedConductorLoot
	{
		public const int MinBars = 20, MaxBars = 35;

		/// <summary>One of his weapons, every kill (each player gets their own from their bag).</summary>
		private static IItemDropRule Weapon() {
			return ItemDropRule.OneFromOptions(1, ModContent.ItemType<CursedLantern>(), ModContent.ItemType<CursedTrainWhistle>());
		}

		public static void AddClassic(LeadingConditionRule classic) {
			classic.OnSuccess(ItemDropRule.Common(ModContent.ItemType<TarnishedBrassBar>(), 1, MinBars, MaxBars));
			classic.OnSuccess(Weapon());
		}

		public static void AddBagContents(ILoot loot) {
			loot.Add(ItemDropRule.Common(ModContent.ItemType<TarnishedBrassBar>(), 1, MinBars, MaxBars));
			loot.Add(Weapon());
			loot.Add(ItemDropRule.Common(ModContent.ItemType<BottleOfLostSouls>()));
			loot.Add(ItemDropRule.CoinsBasedOnNPCValue(ModContent.NPCType<CursedConductor>()));
		}
	}
}
