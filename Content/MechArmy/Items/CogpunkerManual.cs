using System.Collections.Generic;
using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Items
{
	/// <summary>
	/// Cogpunker Manual (user-set 2026-10-28), dropped by the Jaeger 1 time in 4: a consumable read once per character
	/// (<see cref="SteamDashPlayer.HasManual"/>, saved with the player). It permanently adds
	/// <see cref="SteamDashPlayer.ManualSteamMax"/> steam capacity and teaches the steam dash (<see cref="SteamDashPlayer"/>:
	/// <see cref="SteamDashPlayer.SteamCost"/> steam, a 4 s cooldown, projectiles pass through). Used like vanilla's
	/// permanent upgrades (ExampleMod 1.4.4 <c>ExampleLifeFruit</c>): <see cref="CanUseItem"/> refuses a second reading, and
	/// the effect is applied in <see cref="UseItem"/> on the reading player's client. Balance: docs/balance/accessories.csv.
	/// Art: art/mecharmy/make_jaeger_armor.py.
	/// </summary>
	public class CogpunkerManual : CogpunkItem
	{
		private static LocalizedText readText, alreadyReadText, keyText, unboundText;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SteamDashPlayer.ManualSteamMax, SteamDashPlayer.SteamCost,
			SteamDashPlayer.CooldownTicks / 60);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
			readText = this.GetLocalization("Learned");
			alreadyReadText = this.GetLocalization("AlreadyRead");
			keyText = this.GetLocalization("DashKey");
			unboundText = this.GetLocalization("DashKeyUnbound");
		}

		public override void Unload() {
			readText = alreadyReadText = keyText = unboundText = null;
		}

		public override void SetDefaults() {
			Item.width = 26;
			Item.height = 28;
			Item.useStyle = ItemUseStyleID.HoldUp;
			Item.useTime = 30;
			Item.useAnimation = 30;
			Item.UseSound = SoundID.Item4;
			Item.consumable = true;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Orange;
		}

		public override bool CanUseItem(Player player) {
			return !player.GetModPlayer<SteamDashPlayer>().HasManual;
		}

		public override bool? UseItem(Player player) {
			SteamDashPlayer dash = player.GetModPlayer<SteamDashPlayer>();
			if (dash.HasManual) {
				return null;                                 // never consumed twice
			}
			dash.HasManual = true;
			if (player.whoAmI == Main.myPlayer && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item34 with { Pitch = 0.4f, Volume = 0.6f }, player.Center);
				if (readText != null) {
					CombatText.NewText(player.getRect(), new Color(238, 241, 243), readText.Value);
				}
			}
			return true;
		}

		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			if (keyText == null) {
				return;
			}
			List<string> keys = SteamDashSystem.Keybind?.GetAssignedKeys();
			string key = keys != null && keys.Count > 0 ? keys[0] : unboundText.Value;
			tooltips.Add(new TooltipLine(Mod, "DashKey", keyText.Format(key)));
			if (Main.LocalPlayer.GetModPlayer<SteamDashPlayer>().HasManual) {
				tooltips.Add(new TooltipLine(Mod, "AlreadyRead", alreadyReadText.Value) { OverrideColor = new Color(190, 120, 120) });
			}
		}
	}
}
