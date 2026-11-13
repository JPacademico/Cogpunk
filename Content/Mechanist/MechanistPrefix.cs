using System;
using System.Collections.Generic;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// The Mechanist's reforges (user, 2026-11-12: "add new balanced cohesive reforge tiers to the mechanist weapons class;
	/// verify the already existing tiers for the default terraria class weapons (like mythical or legendary) for reference").
	/// <para>Built on vanilla's own class sets (decompiled <c>Item.TryGetPrefixStatMultipliersForItem</c>, 1.4.4): every
	/// class has a set where one stat is its own (mana for magic: Mystic, Adept, Masterful, Inept, Ignorant, Deranged,
	/// Intense, Taboo, Celestial, Furious, Manic, and Mythical at the top; size for melee, velocity for ranged), and the
	/// universal weapon prefixes on top. The Mechanist's own stat is the steam a use costs, so these twelve are the magic
	/// set line for line with steam in mana's place: the same damage, speed, crit and knockback numbers and the same steam
	/// steps as vanilla's mana ones. The best, <see cref="Overclocked"/>, is Mythical's twin (+15% damage, +10% speed,
	/// +5% crit, +15% knockback, -10% steam), matching Legendary and Unreal in strength and value.</para>
	/// <para>How they roll (decompiled <c>PrefixLoader.Roll</c>): a Mechanist weapon's damage class isn't melee, ranged or
	/// magic, so vanilla gives it the universal weapon category (<c>ModItem.WeaponPrefix</c>); these sit in that category
	/// and <see cref="CanRoll"/> only for Mechanist weapons, so a Mechanist weapon rolls from the universal set plus these
	/// twelve, each weighted 1 like a vanilla prefix, exactly as a magic weapon rolls from the universal and magic sets.</para>
	/// <para>Steam: <see cref="Apply"/> puts the multiplier on the item (<see cref="MechanistWeapon.PrefixSteamMultiplier"/>,
	/// rounded like vanilla's mana); a prefix whose steam step wouldn't change the cost is refused, as vanilla refuses a
	/// mana prefix that rounds to nothing (<see cref="AllStatChangesHaveEffectOn"/>), so a 2-steam weapon simply rolls
	/// another. Value: vanilla's formula plus the steam term the way it has the mana one (<c>(2 - mult)</c>), so rarity
	/// moves the same way (decompiled <c>Item.Prefix</c>). Localization: <c>Mods.Cogpunk.Prefixes.&lt;Name&gt;.DisplayName</c>.</para>
	/// </summary>
	public abstract class MechanistPrefix : ModPrefix
	{
		private static LocalizedText steamLine;

		/// <summary>Damage, use speed (vanilla's <c>spd</c>: a use-time multiplier, 0.9 = 10% faster), crit, knockback and
		/// steam cost multipliers.</summary>
		public abstract float Damage { get; }
		public virtual float UseTime => 1f;
		public virtual int Crit => 0;
		public virtual float Knockback => 1f;
		public abstract float Steam { get; }

		public override PrefixCategory Category => PrefixCategory.AnyWeapon;

		public override void SetStaticDefaults() {
			steamLine ??= Mod.GetLocalization("Prefixes.SteamCostLine");
		}

		public override void Unload() {
			steamLine = null;
		}

		public override bool CanRoll(Item item) {
			return item.ModItem is MechanistWeapon && item.DamageType.CountsAsClass<MechanistDamage>();
		}

		public override float RollChance(Item item) => 1f;   // like each vanilla prefix in the pool

		public override void SetStats(ref float damageMult, ref float knockbackMult, ref float useTimeMult, ref float scaleMult,
			ref float shootSpeedMult, ref float manaMult, ref int critBonus) {
			damageMult *= Damage;
			knockbackMult *= Knockback;
			useTimeMult *= UseTime;
			critBonus += Crit;
		}

		/// <summary>Refused (re-rolled) when the steam step rounds to nothing on this weapon, as vanilla does for mana.</summary>
		public override bool AllStatChangesHaveEffectOn(Item item) {
			if (Steam == 1f) {
				return true;
			}
			if (item.ModItem is not MechanistWeapon weapon) {
				return false;
			}
			int cost = weapon.CombinedSteamCost > 0 ? weapon.CombinedSteamCost : weapon.SteamCost;
			return cost > 0 && MechanistWeapon.ApplyPrefix(cost, Steam) != cost;
		}

		public override void Apply(Item item) {
			if (item.ModItem is MechanistWeapon weapon) {
				weapon.PrefixSteamMultiplier = Steam;
			}
		}

		public override void ModifyValue(ref float valueMult) {
			valueMult *= 2f - Steam;                     // vanilla's mana term: (2 - mcst)
		}

		public override IEnumerable<TooltipLine> GetTooltipLines(Item item) {
			if (Steam == 1f || steamLine == null) {
				yield break;
			}
			int percent = (int)Math.Round((Steam - 1f) * 100f);
			yield return new TooltipLine(Mod, "PrefixSteamCost", steamLine.Format((percent > 0 ? "+" : "") + percent)) {
				IsModifier = true,
				IsModifierBad = percent > 0,
			};
		}
	}

	// The set, with the vanilla magic prefix each one mirrors (stats from decompiled Item.TryGetPrefixStatMultipliersForItem).

	/// <summary>Mythical's twin: the top tier.</summary>
	public class Overclocked : MechanistPrefix
	{
		public override float Damage => 1.15f;
		public override float UseTime => 0.9f;
		public override int Crit => 5;
		public override float Knockback => 1.15f;
		public override float Steam => 0.9f;
	}

	/// <summary>Mystic's twin.</summary>
	public class Calibrated : MechanistPrefix
	{
		public override float Damage => 1.1f;
		public override float Steam => 0.85f;
	}

	/// <summary>Adept's twin.</summary>
	public class Efficient : MechanistPrefix
	{
		public override float Damage => 1f;
		public override float Steam => 0.85f;
	}

	/// <summary>Masterful's twin.</summary>
	public class Engineered : MechanistPrefix
	{
		public override float Damage => 1.15f;
		public override float Knockback => 1.05f;
		public override float Steam => 0.85f;
	}

	/// <summary>Inept's twin.</summary>
	public class Leaky : MechanistPrefix
	{
		public override float Damage => 1f;
		public override float Steam => 1.1f;
	}

	/// <summary>Ignorant's twin.</summary>
	public class Corroded : MechanistPrefix
	{
		public override float Damage => 0.9f;
		public override float Steam => 1.2f;
	}

	/// <summary>Deranged's twin.</summary>
	public class Jammed : MechanistPrefix
	{
		public override float Damage => 0.9f;
		public override float Knockback => 0.9f;
		public override float Steam => 1f;
	}

	/// <summary>Intense's twin.</summary>
	public class Pressurized : MechanistPrefix
	{
		public override float Damage => 1.1f;
		public override float Steam => 1.15f;
	}

	/// <summary>Taboo's twin.</summary>
	public class Hissing : MechanistPrefix
	{
		public override float Damage => 1f;
		public override float UseTime => 0.9f;
		public override float Knockback => 1.1f;
		public override float Steam => 1.1f;
	}

	/// <summary>Celestial's twin.</summary>
	public class Geared : MechanistPrefix
	{
		public override float Damage => 1.1f;
		public override float UseTime => 1.1f;
		public override float Knockback => 1.1f;
		public override float Steam => 0.9f;
	}

	/// <summary>Furious's twin.</summary>
	public class Overdriven : MechanistPrefix
	{
		public override float Damage => 1.15f;
		public override float Knockback => 1.15f;
		public override float Steam => 1.2f;
	}

	/// <summary>Manic's twin.</summary>
	public class Rattling : MechanistPrefix
	{
		public override float Damage => 0.9f;
		public override float UseTime => 0.9f;
		public override float Steam => 0.9f;
	}
}
