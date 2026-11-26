using System;
using System.Collections.Generic;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
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
		private static LocalizedText manaFallbackText;

		/// <summary>Steam spent per use, before the player's cost multiplier.</summary>
		public abstract int SteamCost { get; }

		/// <summary>The steam cost's multiplier from this item's reforge (<see cref="MechanistPrefix"/>, user, 2026-11-12); 1
		/// without one. An instance field: <c>Item.Prefix</c> runs the prefix's <c>Apply</c> on every load, net receive and
		/// reforge, after <c>SetDefaults</c> made a fresh clone of the template with 1 (decompiled <c>Item.Prefix</c>).</summary>
		public float PrefixSteamMultiplier = 1f;

		/// <summary>A cost set on this one item by the Combinator (half the sum of its two weapons' costs, user-set
		/// 2026-11-12), used instead of <see cref="SteamCostFor"/>; 0 when the item isn't a combination.</summary>
		public int CombinedSteamCost;

		/// <summary>The steam the use <paramref name="player"/> is starting costs, before the multiplier: <see cref="SteamCost"/>,
		/// unless the weapon's alternate use costs more (the Firesaw's fire, 2026-11-09).</summary>
		public virtual int SteamCostFor(Player player) => SteamCost;

		/// <summary>What a use costs before the player's multiplier: <see cref="SteamCostFor"/> (or the Combinator's
		/// <see cref="CombinedSteamCost"/>) with this item's reforge applied, rounded like vanilla's mana prefixes
		/// (decompiled <c>Item.Prefix</c>: <c>(int)Math.Round(mana * mcst)</c>), never below 1. Every payment, check and
		/// tooltip goes through it.</summary>
		public int ItemSteamCost(Player player) {
			int raw = CombinedSteamCost > 0 && player.altFunctionUse != 2 ? CombinedSteamCost : SteamCostFor(player);
			return ApplyPrefix(raw, PrefixSteamMultiplier);
		}

		/// <summary><paramref name="cost"/> after a reforge's steam multiplier (vanilla's mana rounding, 1 at least).</summary>
		public static int ApplyPrefix(int cost, float multiplier) {
			if (cost <= 0 || multiplier == 1f) {
				return cost;
			}
			return Math.Max(1, (int)Math.Round(cost * multiplier));
		}

		public override void SetStaticDefaults() {
			steamCostText ??= Language.GetOrRegister("Mods.Cogpunk.Mechanist.SteamCost");
			noTankTooltip ??= Language.GetOrRegister("Mods.Cogpunk.Mechanist.NoTankTooltip");
			manaFallbackText ??= Language.GetOrRegister("Mods.Cogpunk.Mechanist.SteamManaFallback");
			Item.ResearchUnlockCount = 1;
		}

		public override void Unload() {
			steamCostText = null;
			noTankTooltip = null;
			manaFallbackText = null;
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
			return player.GetModPlayer<SteamPlayer>().CanPayAttack(ItemSteamCost(player));   // the hint or the overheat when it can't
		}

		/// <summary>
		/// The owner pays the steam, once a use. Vanilla calls this on every tick while the player's item time is 0 (decompiled
		/// 1.4.4 <c>Player.ItemCheck_Inner</c>: <c>if (ItemTimeIsZero &amp;&amp; itemAnimation &gt; 0)</c>, until it answers true); a
		/// weapon that shoots reaches it through vanilla's shot instead, which sets the item time, so it is called once a shot.
		/// A swing that shoots nothing never set it: the Cogspring Sword paid its steam every tick of its swing and flipped its
		/// slash back and forth (user, 2026-11-26: "a glitched animation that consumes all the steam"). So a swing pays as its
		/// animation starts and answers true, and vanilla applies its use time once.
		/// </summary>
		public override bool? UseItem(Player player) {
			bool swing = Item.shoot <= ProjectileID.None;
			if (swing && !player.ItemAnimationJustStarted) {
				return null;
			}
			if (player.whoAmI == Main.myPlayer) {
				player.GetModPlayer<SteamPlayer>().Spend(ItemSteamCost(player));
			}
			return swing ? true : null;
		}

		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			if (steamCostText == null) {
				return;
			}
			SteamPlayer steam = Main.LocalPlayer.GetModPlayer<SteamPlayer>();
			int cost = steam.GetCost(ApplyPrefix(CombinedSteamCost > 0 ? CombinedSteamCost : SteamCost, PrefixSteamMultiplier));
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Knockback");
			TooltipLine line = new(Mod, "SteamCost", steamCostText.Format(cost));
			if (index >= 0) {
				tooltips.Insert(index + 1, line);
			}
			else {
				tooltips.Add(line);
			}
			if (steam.SteamAsMana && manaFallbackText != null) {
				// the Serene Tear (user, 2026-11-12): mana pays once the steam runs out, at half the efficiency
				tooltips.Insert(tooltips.IndexOf(line) + 1, new TooltipLine(Mod, "SteamManaFallback", manaFallbackText.Format(SteamPlayer.ManaFor(cost))));
			}
			else if (steam.SteamMax < cost && noTankTooltip != null) {
				tooltips.Insert(tooltips.IndexOf(line) + 1, new TooltipLine(Mod, "NoTank", noTankTooltip.Value) { OverrideColor = new Color(190, 70, 50) });
			}
		}
	}
}
