using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// The red "Needs a steam tank" tooltip line for a weapon whose skill costs steam (<see cref="ISteamSkill"/>), shown when
	/// the local player's whole tank is smaller than the skill's cost (the base capacity is 0: only gear grants a tank), the
	/// way <see cref="MechanistWeapon"/> shows it. Tooltips only (UI, not a hot path).
	/// </summary>
	public static class SteamSkillTooltip
	{
		public static void AddNoTankLine(Mod mod, List<TooltipLine> tooltips, int baseCost) {
			SteamPlayer steam = Main.LocalPlayer.GetModPlayer<SteamPlayer>();
			if (steam.SteamMax >= steam.GetCost(baseCost)) {
				return;
			}
			int index = tooltips.FindLastIndex(static line => line.Mod == "Terraria" && line.Name.StartsWith("Tooltip"));
			TooltipLine noTank = new(mod, "NoTank", Language.GetTextValue("Mods.Cogpunk.Mechanist.NoTankTooltip")) {
				OverrideColor = new Color(190, 70, 50)
			};
			if (index >= 0) {
				tooltips.Insert(index + 1, noTank);         // under the item's own lines, where the skill is described
			}
			else {
				tooltips.Add(noTank);
			}
		}
	}
}
