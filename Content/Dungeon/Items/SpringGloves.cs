using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Dungeon.Items
{
	/// <summary>
	/// Spring Gloves (user-set 2026-11-03): the <see cref="NPCs.BeatBoxer"/>'s gloves (1 in 5). An attack hits harder and
	/// pushes harder the more steam it consumes: +<see cref="PercentPerSteam"/>% damage and knockback for every point of
	/// steam, counted after the wearer's steam-cost discounts (the steam the attack really takes).
	/// <para>Every attack that consumes steam counts (user, 2026-11-04: "not just Mechanist ... it should also affect weapon
	/// skills/secondary attacks"): a Mechanist weapon's use, a spell whose mana the steam pays (the Serene Tear,
	/// <see cref="SteamPlayer.SteamAsMana"/>), and a weapon skill that costs steam (<see cref="ISteamSkill"/>: the
	/// Tar-Shower's charged glob, the Metal Wrench's riposte after a parry). Uses are read through
	/// <see cref="SteamPlayer.SteamForUse"/> in <see cref="SpringGlovesPlayer"/> (additive with other damage bonuses); a skill
	/// whose payoff isn't an item use applies <see cref="SpringGlovesPlayer.BonusFor"/> to its own hit. Summons count
	/// nothing (the steam pays for the summon, not the minion's attacks).</para>
	/// <para>Not a Scrappy Trunk trinket: it has its own source (SKILL 3.3). Balance: docs/balance/accessories.csv.</para>
	/// </summary>
	public class SpringGloves : CogpunkItem
	{
		public const float PercentPerSteam = 0.5f;      // user-set

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(PercentPerSteam);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 32;
			Item.height = 28;
			Item.accessory = true;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Orange;             // a Dungeon drop (post-Skeletron)
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetModPlayer<SpringGlovesPlayer>().Worn = true;
		}
	}

	/// <summary>
	/// The <see cref="SpringGloves"/>' bonus: in <c>ModifyWeaponDamage</c> / <c>ModifyWeaponKnockback</c> (per use and per
	/// tooltip; D1: field reads) a use gets +<see cref="SpringGloves.PercentPerSteam"/>% per point of the steam it takes
	/// (<see cref="SteamPlayer.SteamForUse"/>). Owner-side numbers; vanilla carries the resulting damage into the hits and
	/// projectiles (D2).
	/// </summary>
	public sealed class SpringGlovesPlayer : ModPlayer
	{
		public bool Worn;

		public override void ResetEffects() {
			Worn = false;
		}

		/// <summary>The bonus (a fraction: 0.05 = +5%) the gloves give an attack that consumed <paramref name="steam"/>
		/// (after discounts); 0 without the gloves. For skills whose payoff isn't an item use (the wrench's riposte).</summary>
		public static float BonusFor(Player player, int steam) {
			if (steam <= 0 || player == null || !player.GetModPlayer<SpringGlovesPlayer>().Worn) {
				return 0f;
			}
			return steam * SpringGloves.PercentPerSteam / 100f;
		}

		private float Bonus(Item item) {
			if (!Worn) {
				return 0f;
			}
			int steam = Player.GetModPlayer<SteamPlayer>().SteamForUse(item);
			return steam * SpringGloves.PercentPerSteam / 100f;
		}

		public override void ModifyWeaponDamage(Item item, ref StatModifier damage) {
			float bonus = Bonus(item);
			if (bonus > 0f) {
				damage += bonus;
			}
		}

		public override void ModifyWeaponKnockback(Item item, ref StatModifier knockback) {
			float bonus = Bonus(item);
			if (bonus > 0f) {
				knockback += bonus;
			}
		}
	}
}
