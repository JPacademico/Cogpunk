using System.Collections.Generic;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// Base for every Mechanist weapon (ExampleMod 1.4.4 <c>ExampleCustomResourceWeapon</c>: check in <c>CanUseItem</c>, pay in
	/// <c>UseItem</c>). Each use costs <see cref="SteamCost"/> steam (scaled by the player's cost multiplier). Using one
	/// without enough steam doesn't fire: it <see cref="Overheat"/>s the player instead. A player whose whole tank is
	/// smaller than the cost (no Mechanist gear: the base capacity is 0) can't fire it at all and doesn't overheat, since
	/// no refill could ever pay; the tooltip and a hint say a steam tank is needed.
	/// <para>Derived weapons set <c>Item.DamageType = ModContent.GetInstance&lt;MechanistDamage&gt;()</c> and override
	/// <see cref="CanUseMechanist"/> instead of <c>CanUseItem</c>. D2: only the owner checks and pays (decompiled
	/// <c>Player.ApplyItemTime</c> calls <c>UseItem</c> once per use, on every client that runs the player's item check);
	/// other clients just play the use.</para>
	/// </summary>
	public abstract class MechanistWeapon : CogpunkItem
	{
		private static LocalizedText steamCostText;
		private static LocalizedText noTankTooltip;

		/// <summary>Steam spent per use, before the player's cost multiplier.</summary>
		public abstract int SteamCost { get; }

		/// <summary>The steam the use <paramref name="player"/> is starting costs, before the multiplier: <see cref="SteamCost"/>,
		/// unless the weapon's alternate use costs more (the Firesaw's fire, 2026-11-09).</summary>
		public virtual int SteamCostFor(Player player) => SteamCost;

		public override void SetStaticDefaults() {
			steamCostText ??= Language.GetOrRegister("Mods.Cogpunk.Mechanist.SteamCost");
			noTankTooltip ??= Language.GetOrRegister("Mods.Cogpunk.Mechanist.NoTankTooltip");
			Item.ResearchUnlockCount = 1;
		}

		public override void Unload() {
			steamCostText = null;
			noTankTooltip = null;
		}

		/// <summary>Extra conditions for the weapon (one projectile at a time...), checked before the steam.</summary>
		protected virtual bool CanUseMechanist(Player player) => true;

		public sealed override bool CanUseItem(Player player) {
			if (!CanUseMechanist(player)) {
				return false;
			}
			if (player.whoAmI != Main.myPlayer) {
				return true;                                   // the owner decided (D2)
			}
			return player.GetModPlayer<SteamPlayer>().CanPayAttack(SteamCostFor(player));   // the hint or the overheat when it can't
		}

		public override bool? UseItem(Player player) {
			if (player.whoAmI == Main.myPlayer) {
				player.GetModPlayer<SteamPlayer>().Spend(SteamCostFor(player));
			}
			return null;
		}

		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			if (steamCostText == null) {
				return;
			}
			SteamPlayer steam = Main.LocalPlayer.GetModPlayer<SteamPlayer>();
			int cost = steam.GetCost(SteamCost);
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Knockback");
			TooltipLine line = new(Mod, "SteamCost", steamCostText.Format(cost));
			if (index >= 0) {
				tooltips.Insert(index + 1, line);
			}
			else {
				tooltips.Add(line);
			}
			if (steam.SteamMax < cost && noTankTooltip != null) {
				tooltips.Insert(tooltips.IndexOf(line) + 1, new TooltipLine(Mod, "NoTank", noTankTooltip.Value) { OverrideColor = new Color(190, 70, 50) });
			}
		}
	}
}
