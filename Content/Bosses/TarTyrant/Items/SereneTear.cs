using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Items
{
	/// <summary>
	/// Serene Tear (Gota Serena), Tar Tyrant's Expert item (user-set 2026-10-29), always in its treasure bag:
	/// <list type="bullet">
	/// <item>steam pays for mana: a mana cost is taken from the steam tank first, and from mana once the steam can't cover
	/// it (<see cref="SteamPlayer.SteamAsMana"/>, one steam per point of mana);</item>
	/// <item>immunity to <see cref="Overheat"/> (<see cref="SteamPlayer.OverheatImmune"/>: a Mechanist weapon without
	/// enough steam just doesn't fire, the way a staff without mana doesn't);</item>
	/// <item>+<see cref="RegenBonusPercent"/>% steam regeneration (<see cref="SteamPlayer.SteamRegenMultiplier"/>).</item>
	/// </list>
	/// D2: all of it lives in the owner's <see cref="SteamPlayer"/> (steam and mana are the owner's); the overheat
	/// immunity also sets vanilla's <c>buffImmune</c>, so every client agrees the buff can't be there. Balance:
	/// docs/balance/accessories.csv.
	/// </summary>
	public class SereneTear : CogpunkItem
	{
		public const int RegenBonusPercent = 15;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(RegenBonusPercent);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 24;
			Item.height = 32;
			Item.accessory = true;
			Item.expert = true;
			Item.rare = ItemRarityID.Orange;
			Item.value = Item.sellPrice(gold: 2);
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			SteamPlayer steam = player.GetModPlayer<SteamPlayer>();
			steam.SteamAsMana = true;
			steam.OverheatImmune = true;
			steam.SteamRegenMultiplier += RegenBonusPercent / 100f;
			player.buffImmune[ModContent.BuffType<Overheat>()] = true;
		}
	}
}
