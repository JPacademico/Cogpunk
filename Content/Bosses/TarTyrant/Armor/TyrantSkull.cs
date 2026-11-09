using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Armor
{
	/// <summary>
	/// Tyrant Skull, a piece of the Tyrant armor, the set Tar Tyrant drops (at least one piece a kill,
	/// <see cref="TarTyrantLoot"/>). Reworked 2026-11-06 into a summoner-mage set (user: "the skull should give +12% summon and
	/// mage damage and +1 minion slot; the set bonus should maintain the tar claw effect but the buff numbers should be +6%
	/// summon and mage crit"; it was a mage set until 2026-11-03, then a summoner set): <see cref="Defense"/> defense,
	/// +<see cref="Damage"/>% summon and magic damage, +<see cref="MinionSlots"/> minion slot.
	/// <para>Owns the set bonus: the tar claw (<see cref="TyrantArmorPlayer"/>: every 4 s a claw erupts under the closest
	/// enemy for 100 magic damage), +<see cref="SetCrit"/>% summon and magic critical strike chance (summon crit counts for
	/// minions that can crit: Cogpunk's own, or any with the Cursed Conductor's Bottle of Lost Souls), and the Tar Plague the
	/// wearer gives enemies lasts <see cref="PlagueBonusTicks"/> ticks longer (<see cref="TarPlayer.PlagueBonusTicks"/>, kept
	/// from the 2026-11-03 set; the whip speed it had moved to the cape). Balance: docs/balance/armor.csv (anchor: the
	/// Obsidian armor, 4/6/5, +8% / +1 minion / +8%, set +15% summon damage, +30% whip range, +15% whip speed). Art:
	/// art/bosses/tartyrant/make_tyrant_armor.py (2026-10-30, the berserker redesign).</para>
	/// </summary>
	[AutoloadEquip(EquipType.Head)]
	public class TyrantSkull : CogpunkItem
	{
		public const int Defense = 5;
		public const int Damage = 12;                   // percent, summon and magic (user-set)
		public const int MinionSlots = 1;               // user-set
		public const int SetCrit = 6;                   // percent, summon and magic, set bonus (user-set)
		public const int PlagueBonusTicks = 90;         // set bonus: +1.5 s of Tar Plague on enemies (2026-11-03, kept)

		public static LocalizedText SetBonusText { get; private set; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(Damage, MinionSlots);

		public override void SetStaticDefaults() {
			SetBonusText = this.GetLocalization("SetBonus").WithFormatArgs(TyrantArmorPlayer.ClawInterval / 60, TyrantArmorPlayer.ClawDamage,
				SetCrit, PlagueBonusTicks / 60f);
		}

		public override void Unload() {
			SetBonusText = null;
		}

		public override void SetDefaults() {
			Item.width = 38;
			Item.height = 28;
			Item.value = Item.sellPrice(gold: 1, silver: 50);
			Item.rare = ItemRarityID.Orange;            // Deerclops' drops (T3)
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetDamage(DamageClass.Summon) += Damage / 100f;
			player.GetDamage(DamageClass.Magic) += Damage / 100f;
			player.maxMinions += MinionSlots;
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return body.type == ModContent.ItemType<TyrantCape>() && legs.type == ModContent.ItemType<TyrantSandals>();
		}

		public override void UpdateArmorSet(Player player) {
			player.setBonus = SetBonusText.Value;
			player.GetModPlayer<TyrantArmorPlayer>().ClawSet = true;
			player.GetCritChance(DamageClass.Summon) += SetCrit;
			player.GetCritChance(DamageClass.Magic) += SetCrit;
			player.GetModPlayer<TarPlayer>().PlagueBonusTicks += PlagueBonusTicks;
		}
	}
}
