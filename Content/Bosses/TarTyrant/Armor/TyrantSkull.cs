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
	/// <see cref="TarTyrantLoot"/>). A summoner set since 2026-11-03 (user: "make the tyrant armor a summon class armor, better
	/// than the Obsidian armor; the chest +1 minion slot; the set bonus whip attack speed and +1.5 s of tar poisoning on
	/// enemies"; it was a mage set with a tar-claw set bonus, 2026-10-29): <see cref="Defense"/> defense and
	/// +<see cref="SummonDamage"/>% summon damage. Owns the set bonus: whips swing <see cref="WhipSpeed"/>% faster (vanilla's
	/// own whip-speed stat, the attack speed of <c>DamageClass.SummonMeleeSpeed</c>, as the Obsidian set's +15%: decompiled
	/// <c>Player.UpdateArmorSets</c>) and the Tar Plague the wearer gives enemies lasts <see cref="PlagueBonusTicks"/> ticks
	/// longer (<see cref="TarPlayer.PlagueBonusTicks"/>, read by <see cref="TarPlague.InflictOn"/>). Balance:
	/// docs/balance/armor.csv (anchor: the Obsidian armor, 4/6/5, +8% / +1 minion / +8%, set +15% summon damage, +30% whip
	/// range, +15% whip speed). Art: art/bosses/tartyrant/make_tyrant_armor.py (2026-10-30, the berserker redesign).
	/// </summary>
	[AutoloadEquip(EquipType.Head)]
	public class TyrantSkull : CogpunkItem
	{
		public const int Defense = 5;
		public const int SummonDamage = 15;             // percent
		public const int WhipSpeed = 25;                // percent, set bonus
		public const int PlagueBonusTicks = 90;         // set bonus: +1.5 s of Tar Plague on enemies (user-set)

		public static LocalizedText SetBonusText { get; private set; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SummonDamage);

		public override void SetStaticDefaults() {
			SetBonusText = this.GetLocalization("SetBonus").WithFormatArgs(WhipSpeed, PlagueBonusTicks / 60f);
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
			player.GetDamage(DamageClass.Summon) += SummonDamage / 100f;
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return body.type == ModContent.ItemType<TyrantCape>() && legs.type == ModContent.ItemType<TyrantSandals>();
		}

		public override void UpdateArmorSet(Player player) {
			player.setBonus = SetBonusText.Value;
			player.GetAttackSpeed(DamageClass.SummonMeleeSpeed) += WhipSpeed / 100f;
			player.GetModPlayer<TarPlayer>().PlagueBonusTicks += PlagueBonusTicks;
		}
	}
}
