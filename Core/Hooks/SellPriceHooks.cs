using System;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Hooks
{
	/// <summary>
	/// Selling pays <see cref="SellFactor"/> of vanilla's price (user, 2026-11-25: "reduce sell cost by 60% also"; the shops'
	/// prices are +60%, <see cref="Content.Economy.ShopPrices"/>).
	/// <para>Why this lives in Core/Hooks: tModLoader 1.4.4 has no hook for a sell price. Vanilla works it out in
	/// <c>Player.GetItemExpectedPrice</c> (decompiled: its <c>calcForSelling</c>, which <c>Player.SellItem</c> divides by 5 and
	/// multiplies by the stack, and which the item tooltip shows as "Sell"), so this detours that one method and scales only
	/// the selling price of coin-priced items (not the buying price, not another currency). If the detour can't be applied
	/// (a tModLoader update renamed it), one error is logged and selling simply pays vanilla's price (D0 rule 14).
	/// tModLoader removes <c>On_</c> detours itself when the mod unloads.</para>
	/// <para>D2: selling is the seller's client's (vanilla); every client shows the same price. D1: one multiply per call.</para>
	/// </summary>
	public sealed class SellPriceHooks : ModSystem
	{
		/// <summary>60% less (user-set).</summary>
		public const double SellFactor = 0.4;

		public override void Load() {
			try {
				On_Player.GetItemExpectedPrice += LowerSellPrice;
			}
			catch (Exception e) {
				SafeLog.Error("Hooks.SellPrice", e);
			}
		}

		private static void LowerSellPrice(On_Player.orig_GetItemExpectedPrice orig, Player self, Item item, out long calcForSelling,
			out long calcForBuying) {
			orig(self, item, out calcForSelling, out calcForBuying);
			if (item != null && item.shopSpecialCurrency == -1 && calcForSelling > 0) {
				calcForSelling = Math.Max(1L, (long)Math.Round(calcForSelling * SellFactor));
			}
		}
	}
}
