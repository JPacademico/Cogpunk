using System.Collections.Generic;
using System.IO;
using Cogpunk.Core.Networking;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// "Consumerism" (user-set 2026-11-27, 0.4.0: "makes so when a player obtain a must have/rare non boss accessory (like
	/// hermes boots, cloud in a bottle, horse shoe, baloon, ninja belt) the merchant starts to sell then, for other players to
	/// obtain"):
	/// <list type="bullet">
	/// <item>Curates 22 iconic pre-Hardmode and Dungeon exploration accessories (all non-boss) plus recognizes their direct
	/// tinkered upgrades (e.g. Spectre/Lightning/Frostspark/Terraspark Boots unlock Hermes Boots, Master Ninja Gear unlocks
	/// Black Belt, Tabi, Climbing Claws and Shoe Spikes).</item>
	/// <item>Saved by item internal name on both the character and the world (D0 rule 9: never save numeric IDs or raw bit
	/// positions), packed into a 32-bit runtime mask for O(1) per-tick and network checks (D1).</item>
	/// <item>Once any player in the world has researched Consumerism, accessories found by players in that world (including ones
	/// the researcher already obtained earlier) are synced to <see cref="ResearchWorld"/> and added to the Merchant's active
	/// shop into free slots only, never exceeding <c>Chest.maxItems</c> (40, D0).</item>
	/// </list>
	/// </summary>
	public static class ResearchConsumerism
	{
		public static readonly int[] StockItems = {
			ItemID.HermesBoots,
			ItemID.FlurryBoots,
			ItemID.SailfishBoots,
			ItemID.SandBoots,
			ItemID.CloudinaBottle,
			ItemID.BlizzardinaBottle,
			ItemID.SandstorminaBottle,
			ItemID.TsunamiInABottle,
			ItemID.LuckyHorseshoe,
			ItemID.ShinyRedBalloon,
			ItemID.BlackBelt,
			ItemID.Tabi,
			ItemID.ClimbingClaws,
			ItemID.ShoeSpikes,
			ItemID.Aglet,
			ItemID.AnkletoftheWind,
			ItemID.WaterWalkingBoots,
			ItemID.IceSkates,
			ItemID.LavaCharm,
			ItemID.FeralClaws,
			ItemID.BandofRegeneration,
			ItemID.CobaltShield,
		};

		public static uint ValidMask => (1u << StockItems.Length) - 1u;

		/// <summary>Bitmask of <see cref="StockItems"/> unlocked by owning <paramref name="itemType"/> (0 when unrelated).</summary>
		public static uint BitsForItem(int itemType) {
			if (itemType <= ItemID.None) {
				return 0u;
			}
			for (int i = 0; i < StockItems.Length; i++) {
				if (StockItems[i] == itemType) {
					return 1u << i;
				}
			}
			return itemType switch {
				ItemID.SpectreBoots => BitOf(ItemID.HermesBoots),
				ItemID.LightningBoots => BitOf(ItemID.HermesBoots) | BitOf(ItemID.Aglet) | BitOf(ItemID.AnkletoftheWind),
				ItemID.FrostsparkBoots => BitOf(ItemID.HermesBoots) | BitOf(ItemID.Aglet) | BitOf(ItemID.AnkletoftheWind) | BitOf(ItemID.IceSkates),
				ItemID.LavaWaders => BitOf(ItemID.WaterWalkingBoots) | BitOf(ItemID.LavaCharm),
				ItemID.TerrasparkBoots => BitOf(ItemID.HermesBoots) | BitOf(ItemID.Aglet) | BitOf(ItemID.AnkletoftheWind)
					| BitOf(ItemID.IceSkates) | BitOf(ItemID.WaterWalkingBoots) | BitOf(ItemID.LavaCharm),
				ItemID.CloudinaBalloon => BitOf(ItemID.CloudinaBottle) | BitOf(ItemID.ShinyRedBalloon),
				ItemID.BlueHorseshoeBalloon => BitOf(ItemID.CloudinaBottle) | BitOf(ItemID.ShinyRedBalloon) | BitOf(ItemID.LuckyHorseshoe),
				ItemID.BlizzardinaBalloon => BitOf(ItemID.BlizzardinaBottle) | BitOf(ItemID.ShinyRedBalloon),
				ItemID.WhiteHorseshoeBalloon => BitOf(ItemID.BlizzardinaBottle) | BitOf(ItemID.ShinyRedBalloon) | BitOf(ItemID.LuckyHorseshoe),
				ItemID.SandstorminaBalloon => BitOf(ItemID.SandstorminaBottle) | BitOf(ItemID.ShinyRedBalloon),
				ItemID.YellowHorseshoeBalloon => BitOf(ItemID.SandstorminaBottle) | BitOf(ItemID.ShinyRedBalloon) | BitOf(ItemID.LuckyHorseshoe),
				ItemID.BundleofBalloons => BitOf(ItemID.CloudinaBottle) | BitOf(ItemID.BlizzardinaBottle)
					| BitOf(ItemID.SandstorminaBottle) | BitOf(ItemID.ShinyRedBalloon),
				ItemID.HorseshoeBundle => BitOf(ItemID.CloudinaBottle) | BitOf(ItemID.BlizzardinaBottle)
					| BitOf(ItemID.SandstorminaBottle) | BitOf(ItemID.ShinyRedBalloon) | BitOf(ItemID.LuckyHorseshoe),
				ItemID.TigerClimbingGear => BitOf(ItemID.ClimbingClaws) | BitOf(ItemID.ShoeSpikes),
				ItemID.MasterNinjaGear => BitOf(ItemID.BlackBelt) | BitOf(ItemID.Tabi) | BitOf(ItemID.ClimbingClaws) | BitOf(ItemID.ShoeSpikes),
				ItemID.PowerGlove or ItemID.MechanicalGlove or ItemID.FireGauntlet or ItemID.BerserkerGlove => BitOf(ItemID.FeralClaws),
				ItemID.CharmofMyths => BitOf(ItemID.BandofRegeneration),
				ItemID.ObsidianShield or ItemID.AnkhShield => BitOf(ItemID.CobaltShield),
				ItemID.ObsidianHorseshoe => BitOf(ItemID.LuckyHorseshoe),
				_ => 0u,
			};
		}

		private static uint BitOf(int stockType) {
			for (int i = 0; i < StockItems.Length; i++) {
				if (StockItems[i] == stockType) {
					return 1u << i;
				}
			}
			return 0u;
		}

		public static List<string> ToSavedNames(uint mask) {
			List<string> list = new();
			for (int i = 0; i < StockItems.Length; i++) {
				if ((mask & (1u << i)) != 0 && ItemID.Search.TryGetName(StockItems[i], out string name)) {
					list.Add(name);
				}
			}
			return list;
		}

		public static uint FromSavedNames(IList<string> names) {
			if (names == null) {
				return 0u;
			}
			uint mask = 0u;
			int max = names.Count < 64 ? names.Count : 64;
			for (int k = 0; k < max; k++) {
				string s = names[k];
				if (!string.IsNullOrEmpty(s) && ItemID.Search.TryGetId(s, out int id)) {
					mask |= BitsForItem(id);
				}
			}
			return mask & ValidMask;
		}

		/// <summary>Inserts unlocked Consumerism accessories into free slots of the Merchant's active shop before pricing runs.</summary>
		public static void FillMerchantShop(Item[] items) {
			uint mask = ResearchWorld.ConsumerismMask;
			if (Main.myPlayer >= 0 && Main.myPlayer < Main.maxPlayers && Main.LocalPlayer != null && Main.LocalPlayer.active) {
				ResearchPlayer local = Main.LocalPlayer.GetModPlayer<ResearchPlayer>();
				if (local.Has(ResearchNodes.Consumerism) || ResearchWorld.ConsumerismActive) {
					mask |= local.ConsumerismSeen;
				}
			}
			mask &= ValidMask;
			if (mask == 0u || items == null) {
				return;
			}
			int nextSlot = 0;
			for (int i = 0; i < StockItems.Length; i++) {
				if ((mask & (1u << i)) == 0) {
					continue;
				}
				int itemType = StockItems[i];
				if (ShopContains(items, itemType)) {
					continue;
				}
				while (nextSlot < items.Length && items[nextSlot] != null && !items[nextSlot].IsAir) {
					nextSlot++;
				}
				if (nextSlot >= items.Length) {
					break;                                           // D0: Chest.maxItems (40) reached; stop cleanly
				}
				items[nextSlot] ??= new Item();
				items[nextSlot].SetDefaults(itemType);
				if (items[nextSlot].value <= 0) {
					items[nextSlot].value = Item.buyPrice(gold: 5);
				}
				nextSlot++;
			}
		}

		private static bool ShopContains(Item[] items, int type) {
			for (int i = 0; i < items.Length; i++) {
				if (items[i] != null && !items[i].IsAir && items[i].type == type) {
					return true;
				}
			}
			return false;
		}
	}

	/// <summary>Client -> Server: reports newly obtained Consumerism accessory bits so the Merchant stocks them for all players.</summary>
	public sealed class ConsumerismPacket : CogpunkPacket
	{
		public void Send(uint mask) {
			if (Main.netMode != NetmodeID.MultiplayerClient || mask == 0u) {
				return;
			}
			ModPacket packet = Begin();
			packet.Write(mask & ResearchConsumerism.ValidMask);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			uint mask = reader.ReadUInt32();
			if (Main.netMode != NetmodeID.Server || sender < 0 || sender >= Main.maxPlayers || !Main.player[sender].active) {
				return;                                              // D0 rule 7: validate sender and netMode
			}
			Player player = Main.player[sender];
			if (!ResearchWorld.ConsumerismActive && !player.GetModPlayer<ResearchPlayer>().Has(ResearchNodes.Consumerism)) {
				return;
			}
			ResearchWorld.UnlockConsumerism(mask);
		}
	}
}
