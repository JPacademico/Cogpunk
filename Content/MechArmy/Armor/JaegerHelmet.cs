using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Armor
{
	/// <summary>
	/// Jaeger Helmet (user-set 2026-10-28), one of the three pieces the Jaeger drops (1 in 4, one piece at a time):
	/// <see cref="Defense"/> defense and +<see cref="MeleeDamage"/>% melee damage. Owns the set bonus
	/// (<see cref="JaegerArmorPlayer"/>): knockback immunity, +<see cref="KnockbackBonus"/>% knockback, a ram that deals
	/// <see cref="JaegerArmorPlayer.RamDamage"/> melee damage to every enemy the wearer touches, and
	/// -<see cref="MoveSpeedPenalty"/>% movement speed. Balance: docs/balance/armor.csv (anchor: Molten armor, 8/9/8).
	/// Art: art/mecharmy/make_jaeger_armor.py.
	/// </summary>
	[AutoloadEquip(EquipType.Head)]
	public class JaegerHelmet : CogpunkItem
	{
		public const int Defense = 6;
		public const int MeleeDamage = 10;              // percent
		public const int KnockbackBonus = 50;           // percent, every class (my call: "increased knockback")
		public const int MoveSpeedPenalty = 12;         // percent

		public static LocalizedText SetBonusText { get; private set; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MeleeDamage);

		public override void SetStaticDefaults() {
			SetBonusText = this.GetLocalization("SetBonus").WithFormatArgs(KnockbackBonus, JaegerArmorPlayer.RamDamage, MoveSpeedPenalty);
		}

		public override void Unload() {
			SetBonusText = null;
		}

		public override void SetDefaults() {
			Item.width = 24;
			Item.height = 22;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Green;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetDamage(DamageClass.Melee) += MeleeDamage / 100f;
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return body.type == ModContent.ItemType<JaegerChestplate>() && legs.type == ModContent.ItemType<JaegerGreaves>();
		}

		public override void UpdateArmorSet(Player player) {
			player.setBonus = SetBonusText.Value;
			player.noKnockback = true;
			player.GetKnockback(DamageClass.Generic) += KnockbackBonus / 100f;
			player.moveSpeed -= MoveSpeedPenalty / 100f;
			player.GetModPlayer<JaegerArmorPlayer>().Ram = true;
		}
	}
}
