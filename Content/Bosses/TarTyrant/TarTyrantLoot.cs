using Cogpunk.Content.Bosses.TarTyrant.Armor;
using Cogpunk.Content.Bosses.TarTyrant.Items;
using Cogpunk.Content.Junkyard.Items;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant
{
	/// <summary>
	/// Tar Tyrant's loot (user-set 2026-10-29), shared by the boss (<see cref="TarTyrant.ModifyNPCLoot"/>) and its
	/// <see cref="TarTyrantBag"/> (Expert and Master only, one per player, D3 rule 0): <see cref="MinBones"/>-
	/// <see cref="MaxBones"/> Bones, <see cref="MinTar"/>-<see cref="MaxTar"/> Tar Drops and at least one piece of the
	/// Tyrant armor (user: "at least one piece"; my call: 1 in <see cref="SecondPieceOdds"/> it is two different pieces,
	/// so a full set takes about four kills, not five and a half); the bag always holds the <see cref="SereneTear"/> (its
	/// Expert item) and the coins of the boss's value, as vanilla bags do. Lesser loot goes through
	/// <see cref="TarTyrant.BossLoot"/> (Healing Potions, Deerclops').
	/// </summary>
	public static class TarTyrantLoot
	{
		public const int MinBones = 15, MaxBones = 55;
		public const int MinTar = 15, MaxTar = 55;
		public const int SecondPieceOdds = 3;

		/// <summary>Two different pieces 1 in <see cref="SecondPieceOdds"/>, one otherwise (vanilla's
		/// <c>FewFromOptionsNotScaledWithLuckDropRule</c> draws without repeats; a failed roll falls through to the one).</summary>
		private static IItemDropRule ArmorPiece() {
			int[] pieces = { ModContent.ItemType<TyrantSkull>(), ModContent.ItemType<TyrantCape>(), ModContent.ItemType<TyrantSandals>() };
			IItemDropRule two = ItemDropRule.FewFromOptionsNotScalingWithLuck(2, SecondPieceOdds, pieces);
			two.OnFailedRoll(ItemDropRule.OneFromOptionsNotScalingWithLuck(1, pieces));
			return two;
		}

		public static void AddClassic(LeadingConditionRule classic) {
			classic.OnSuccess(ItemDropRule.Common(ItemID.Bone, 1, MinBones, MaxBones));
			classic.OnSuccess(ItemDropRule.Common(ModContent.ItemType<TarDrop>(), 1, MinTar, MaxTar));
			classic.OnSuccess(ArmorPiece());
		}

		public static void AddBagContents(ILoot loot) {
			loot.Add(ItemDropRule.Common(ItemID.Bone, 1, MinBones, MaxBones));
			loot.Add(ItemDropRule.Common(ModContent.ItemType<TarDrop>(), 1, MinTar, MaxTar));
			loot.Add(ArmorPiece());
			loot.Add(ItemDropRule.Common(ModContent.ItemType<SereneTear>()));
			loot.Add(ItemDropRule.CoinsBasedOnNPCValue(ModContent.NPCType<TarTyrant>()));
		}
	}
}
