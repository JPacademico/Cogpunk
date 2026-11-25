using System;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Economy
{
	/// <summary>
	/// Every shop costs more (user, 2026-11-25: "increase all shop prices by 60%, in our mod players have to actualy handle
	/// their money well. we will also add economy related nodes for the player in the future"): as any NPC's shop opens, each
	/// coin price in it is raised by <see cref="Markup"/> (vanilla's vendors, the Travelling Merchant, Cogpunk's and other
	/// mods' alike), except the Tavernkeep's (user, 2026-11-25: "The defender medal cost should be normal so revert the increase
	/// for him specifically"), and any price in another currency. Since 2026-11-25 the Goblin Tinkerer's reforge costs the same
	/// +60% (<see cref="ReforgePrices"/>) and selling pays 60% less (<see cref="Core.Hooks.SellPriceHooks"/>): "increase reforge
	/// cost and reduce sell cost by 60% also". The Nurse's healing is untouched.
	/// <para>How: tModLoader fills a shop from its entries (decompiled <c>Chest.SetupShop(string, NPC)</c>: each entry's item is
	/// cloned, <c>NPCShop.FillShop</c>) and then calls <c>ModifyActiveShop</c> on the shop's items, so the markup is applied to
	/// fresh copies every time a shop opens and never compounds. The price is vanilla's own (<c>Item.GetStoreValue</c>: the
	/// shop's custom price, else the item's value); vanilla then applies happiness and the Discount Card on top of it as usual
	/// (<c>Player.GetItemExpectedPrice</c>). Items sold to a shop come back later at their own value (vanilla adds them after
	/// this hook, <c>Chest.AddItemToShop</c>).</para>
	/// <para>D2: shops are filled on the client that opens them; the price is the same on every client. D0: null and empty
	/// slots skipped, the price clamped to an int. D1: runs once per shop opening, only for NPCs that can have a shop.</para>
	/// </summary>
	public sealed class ShopPrices : GlobalNPC
	{
		/// <summary>+60% (user-set).</summary>
		public const float Markup = 1.6f;

		/// <summary>Only NPCs that can keep a shop: town NPCs and the ones that act like them (the Skeleton Merchant); never the
		/// Tavernkeep (user-set).</summary>
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) =>
			lateInstantiation && entity.isLikeATownNPC && entity.type != NPCID.DD2Bartender;

		public override void ModifyActiveShop(NPC npc, string shopName, Item[] items) {
			if (items == null) {
				return;
			}
			for (int i = 0; i < items.Length; i++) {
				Item item = items[i];
				if (item == null || item.IsAir || item.shopSpecialCurrency != -1) {
					continue;
				}
				int price = item.GetStoreValue();
				if (price <= 0) {
					continue;
				}
				item.shopCustomPrice = Raise(price);
			}
		}

		/// <summary>A coin price with the markup, rounded to the copper and kept inside an int.</summary>
		public static int Raise(int price) => (int)Math.Min(int.MaxValue, Math.Round(price * (double)Markup));
	}

	/// <summary>Reforging costs <see cref="ShopPrices.Markup"/> times vanilla's price (user, 2026-11-25: "increase reforge cost ...
	/// by 60%"): the price after every other mod's change (tModLoader's <c>ReforgePrice</c> hook; the Discount Card and
	/// happiness still apply afterwards). The Goblin Tinkerer's client works it out; D1: once per reforge window update.</summary>
	public sealed class ReforgePrices : GlobalItem
	{
		public override bool ReforgePrice(Item item, ref int reforgePrice, ref bool canApplyDiscount) {
			if (reforgePrice > 0) {
				reforgePrice = ShopPrices.Raise(reforgePrice);
			}
			return true;
		}
	}
}
