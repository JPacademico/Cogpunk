using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Underground.Items
{
	/// <summary>
	/// Chicken Snapper (user-set 2026-10-28): the Puxa-frango's pincer claw worn as an accessory (1 in 3 from it):
	/// +<see cref="MeleeCrit"/>% melee critical strike chance and +<see cref="MeleeSpeed"/>% melee attack speed.
	/// Balance: docs/balance/accessories.csv (anchor: Feral Claws, +12% melee speed).
	/// </summary>
	public class ChickenSnapper : CogpunkItem
	{
		public const int MeleeCrit = 5;
		public const int MeleeSpeed = 5;                // percent

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MeleeCrit, MeleeSpeed);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.accessory = true;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Green;
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetCritChance(DamageClass.Melee) += MeleeCrit;
			player.GetAttackSpeed(DamageClass.Melee) += MeleeSpeed / 100f;
		}
	}
}
