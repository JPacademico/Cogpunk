using Cogpunk.Content.Furniture;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Stations
{
	/// <summary>
	/// Steam Injection (Injeção de Vapor), the <see cref="SteamInjectorTile"/>'s buff (user, 2026-11-12: "+10 max steam and
	/// -5% steam consumption"): <see cref="SteamMaxBonus"/> on the tank (<see cref="SteamPlayer.SteamMaxBonus"/>, so it gives a
	/// small tank of its own to a player who has none) and <see cref="CostReductionPercent"/>% off every steam cost
	/// (<see cref="SteamPlayer.SteamCostMultiplier"/>, the same field the Polished set lowers). Like every buff station's
	/// since the same request, it lasts until death (<see cref="BuffStationRules.MakeUntilDeath"/>). D2: steam is the
	/// owner's; the buff itself syncs like any buff. Balance: docs/balance/accessories.csv.
	/// </summary>
	public class SteamInjection : CogpunkBuff
	{
		public const int SteamMaxBonus = 15;           // 10, +5 (user, 2026-11-26: "increase amount of max steam that all max steam increasing itens give in 5 points")
		public const int CostReductionPercent = 5;

		public override LocalizedText Description => base.Description.WithFormatArgs(SteamMaxBonus, CostReductionPercent);

		public override void SetStaticDefaults() {
			Main.buffNoSave[Type] = false;
			BuffStationRules.MakeUntilDeath(Type);
		}

		public override void Update(Player player, ref int buffIndex) {
			SteamPlayer steam = player.GetModPlayer<SteamPlayer>();
			steam.SteamMaxBonus += SteamMaxBonus;
			steam.SteamCostMultiplier -= CostReductionPercent / 100f;
		}
	}
}
