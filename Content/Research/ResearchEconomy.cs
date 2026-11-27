using System;
using Cogpunk.Core.Hooks;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research
{
	/// <summary>Coins into a bank, as vanilla counts them (Passive Income, 2026-11-26; Real Estate Speculation, 0.4.0).</summary>
	public static class ResearchEconomy
	{
		/// <summary>Coins of a kind that make one of the next (vanilla's <c>Player.DoCoins</c>: 100).</summary>
		public const int CoinsPerNext = 100;
		/// <summary>D0 cap on copper coins generated per second so even modded NPC crowds keep the loop bounded.</summary>
		public const int MaxCopperPerSecond = 100;

		/// <summary>"Real Estate Speculation" (user-set 2026-11-27, 0.4.0: "makes so the piggy bank generates one more copper per
		/// second per housed town npcs (guide, traveling merchant, and pets do not count)"): housed resident town NPCs.</summary>
		public static int HousedResidents() {
			int n = 0;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.homeless && ResearchWorld.IsResident(npc)) {
					n++;
				}
			}
			return n;
		}

		/// <summary>Adds <paramref name="count"/> Copper Coins into <paramref name="bank"/>, rolling stacks of 100 into the next
		/// coin tier and stopping cleanly if the bank fills.</summary>
		public static void AddCopper(Item[] bank, int count) {
			int capped = Math.Clamp(count, 0, MaxCopperPerSecond);
			for (int i = 0; i < capped; i++) {
				if (!AddCoin(bank, ItemID.CopperCoin)) {
					break;
				}
			}
		}

		/// <summary>One coin of <paramref name="coinType"/> (Copper to Platinum) into <paramref name="bank"/>: onto a stack of it
		/// with room, else into an empty slot; a stack of copper, silver or gold that reaches 100 turns into one coin of the next
		/// kind (at most three steps). False when there is no room (nothing changes). No allocation but a new stack's item.</summary>
		public static bool AddCoin(Item[] bank, int coinType) {
			if (bank == null || coinType < ItemID.CopperCoin || coinType > ItemID.PlatinumCoin) {
				return false;
			}
			for (int step = 0; step < 4 && coinType <= ItemID.PlatinumCoin; step++) {
				int partial = -1, empty = -1;
				for (int i = 0; i < bank.Length; i++) {
					Item it = bank[i];
					if (it == null) {
						continue;
					}
					if (it.IsAir) {
						if (empty < 0) {
							empty = i;
						}
					}
					else if (it.type == coinType && it.stack < Math.Max(1, it.maxStack)) {
						partial = i;
						break;
					}
				}
				if (partial < 0) {
					if (empty < 0) {
						return false;                                // a full bank: the coin is not made
					}
					bank[empty].SetDefaults(coinType);
					bank[empty].stack = 1;
					return true;
				}
				Item stack = bank[partial];
				stack.stack++;
				if (coinType == ItemID.PlatinumCoin || stack.stack < CoinsPerNext) {
					return true;
				}
				stack.TurnToAir();                                  // 100 of them: one of the next coin instead
				coinType++;
			}
			return true;
		}
	}

	/// <summary>
	/// The reforge nodes (user-set 2026-11-26): "You broke it!": "makes so itens that are with a negative reforge modifier are 40%
	/// cheaper to reforge" (<see cref="ReforgePrice"/>), and its "?" lifts the first time the player reforges an item
	/// (<see cref="PostReforge"/>); "Build Terraria 2, make no mistakes.": "gives slightly less chance for negative reforges" (a
	/// negative prefix rolled at the Goblin Tinkerer is rolled again <see cref="ResearchNodes.NegativeRerollChance"/> of the time:
	/// <see cref="AllowPrefix"/>; tModLoader rolls up to 50 times, so this can't loop).
	/// <para>A negative prefix: one that lowers its item's value, as vanilla prices prefixes (decompiled <c>Item.Prefix</c>: the
	/// value is scaled by the square of the stats' product, so below 1 is the prefixes vanilla shows a rarity lower; modded
	/// prefixes too, through their own <c>ModifyValue</c>): found once, by putting each prefix on a sample item of a kind that
	/// takes it (<see cref="ResearchPrefixes"/>).</para>
	/// <para>D2: all on the reforging player's own client (the Goblin Tinkerer's window). D1: a table lookup.</para>
	/// </summary>
	public sealed class ResearchReforge : GlobalItem
	{
		private static uint reforgeTick = uint.MaxValue;        // the tick of the reforge under way (Pre -> roll -> Post, one tick)

		private static ResearchPlayer Local => Main.myPlayer >= 0 && Main.myPlayer < Main.maxPlayers ? Main.LocalPlayer.GetModPlayer<ResearchPlayer>() : null;

		public override bool ReforgePrice(Item item, ref int reforgePrice, ref bool canApplyDiscount) {
			ResearchPlayer r = Local;
			if (r != null && r.Has(ResearchNodes.YouBrokeIt) && ResearchPrefixes.IsNegative(item.prefix)) {
				reforgePrice = (int)Math.Round(reforgePrice * (1f - ResearchNodes.BrokenReforgeDiscount));
			}
			return true;
		}

		public override void PreReforge(Item item) {
			reforgeTick = Main.GameUpdateCount;
		}

		public override void PostReforge(Item item) {
			reforgeTick = uint.MaxValue;
			Local?.NoteReforge();
		}

		public override bool AllowPrefix(Item item, int pre) {
			if (reforgeTick != Main.GameUpdateCount || Main.dedServ || !ResearchPrefixes.IsNegative(pre)) {
				return true;
			}
			ResearchPlayer r = Local;
			return r == null || !r.Has(ResearchNodes.BuildTerraria2) || Main.rand.NextFloat() >= ResearchNodes.NegativeRerollChance;
		}
	}

	/// <summary>Which prefixes are negative (<see cref="ResearchReforge"/>), found once after every prefix is loaded.</summary>
	public sealed class ResearchPrefixes : ModSystem
	{
		private static bool[] negative = Array.Empty<bool>();

		/// <summary>The kinds of item each prefix is tried on, in turn, until one takes it: melee, ranged, magic, summon, accessory.</summary>
		private static readonly int[] Samples = { ItemID.IronBroadsword, ItemID.Minishark, ItemID.WandofSparking, ItemID.BlandWhip,
			ItemID.BandofRegeneration };

		public static bool IsNegative(int prefix) => prefix > 0 && prefix < negative.Length && negative[prefix];

		public override void PostSetupContent() {
			int count = Math.Max(PrefixID.Count, PrefixLoader.PrefixCount);
			bool[] table = new bool[count];
			try {
				for (int p = 1; p < count; p++) {
					foreach (int type in Samples) {
						Item sample = new(type);
						int before = sample.value;
						if (before <= 0 || !sample.Prefix(p) || sample.prefix != p) {
							continue;
						}
						table[p] = sample.value < before;
						break;
					}
				}
			}
			catch (Exception e) {
				SafeLog.Error("Research.Prefixes", e);                   // D0: the nodes do nothing rather than break loading
				table = new bool[count];
			}
			negative = table;
		}

		public override void Unload() {
			negative = Array.Empty<bool>();
		}
	}
}
