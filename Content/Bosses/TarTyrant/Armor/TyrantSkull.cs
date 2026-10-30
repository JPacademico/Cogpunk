using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Armor
{
	/// <summary>
	/// Tyrant Skull (user-set 2026-10-29), a piece of the Tyrant armor, the mage set Tar Tyrant drops (at least one piece a
	/// kill, <see cref="TarTyrantLoot"/>): <see cref="Defense"/> defense, +<see cref="MagicDamage"/>% magic damage and
	/// +<see cref="MagicCrit"/>% magic critical strike chance. Owns the set bonus (<see cref="TyrantArmorPlayer"/>): every
	/// 4 s a tar claw like the boss's own erupts out of the ground under the closest enemy. Balance:
	/// docs/balance/armor.csv (anchors: Necro armor, the T3 set, 6/7/6; Meteor armor, the pre-Hardmode mage set, 5/6/5).
	/// Art: art/bosses/tartyrant/make_tyrant_armor.py (2026-10-30, the berserker redesign: horns on the skull, a brow
	/// horn swept back over the head with its pair behind and a nose horn).
	/// </summary>
	[AutoloadEquip(EquipType.Head)]
	public class TyrantSkull : CogpunkItem
	{
		public const int Defense = 5;
		public const int MagicDamage = 15;              // percent
		public const int MagicCrit = 5;                 // percent

		public static LocalizedText SetBonusText { get; private set; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MagicDamage, MagicCrit);

		public override void SetStaticDefaults() {
			SetBonusText = this.GetLocalization("SetBonus").WithFormatArgs(TyrantArmorPlayer.ClawInterval / 60, TyrantArmorPlayer.ClawDamage);
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
			player.GetDamage(DamageClass.Magic) += MagicDamage / 100f;
			player.GetCritChance(DamageClass.Magic) += MagicCrit;
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return body.type == ModContent.ItemType<TyrantCape>() && legs.type == ModContent.ItemType<TyrantSandals>();
		}

		public override void UpdateArmorSet(Player player) {
			player.setBonus = SetBonusText.Value;
			player.GetModPlayer<TyrantArmorPlayer>().ClawSet = true;
		}
	}
}
