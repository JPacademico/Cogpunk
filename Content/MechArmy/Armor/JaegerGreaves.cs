using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Armor
{
	/// <summary>Jaeger Greaves (user-set 2026-10-28): <see cref="Defense"/> defense, a higher jump
	/// (<see cref="JumpSpeedBoost"/> jump speed, the smaller of vanilla's jump-accessory steps; the Frog Leg gives 2.4,
	/// decompiled <c>Player.UpdateJumpHeight</c>) and +<see cref="MeleeCrit"/>% melee critical strike chance. Set bonus:
	/// <see cref="JaegerHelmet"/>.</summary>
	[AutoloadEquip(EquipType.Legs)]
	public class JaegerGreaves : CogpunkItem
	{
		public const int Defense = 8;
		public const float JumpSpeedBoost = 1.6f;
		public const int MeleeCrit = 3;                 // percent

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MeleeCrit);

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 14;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Green;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.jumpSpeedBoost += JumpSpeedBoost;
			player.GetCritChance(DamageClass.Melee) += MeleeCrit;
		}
	}
}
