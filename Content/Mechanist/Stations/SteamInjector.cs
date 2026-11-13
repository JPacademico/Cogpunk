using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Stations
{
	/// <summary>
	/// Places a <see cref="SteamInjectorTile"/>. Sold by the Friendo-bot for <see cref="PriceGold"/> gold (user, 2026-11-12);
	/// no recipe. Sells back for a fifth, as vanilla items do.
	/// </summary>
	public class SteamInjector : CogpunkItem
	{
		public const int PriceGold = 35;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SteamInjection.SteamMaxBonus, SteamInjection.CostReductionPercent);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<SteamInjectorTile>());
			Item.width = 24;
			Item.height = 40;
			Item.value = Item.buyPrice(gold: PriceGold);
			Item.rare = ItemRarityID.Orange;
		}
	}
}
