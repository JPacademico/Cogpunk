using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Ocean.Items
{
	/// <summary>
	/// Shark Eye (user-set 2026-11-04): the <see cref="NPCs.Cogtuna"/>'s porthole eye worn as an accessory (1 in 10 from
	/// it): +<see cref="MeleeCrit"/>% melee critical strike chance. Not a Scrappy Trunk trinket: it has its own user-set drop
	/// (SKILL 3.3). Balance: docs/balance/accessories.csv (anchor: the Chicken Snapper's +5% melee crit, which also gives +5%
	/// melee speed).
	/// </summary>
	public class SharkEye : CogpunkItem
	{
		public const int MeleeCrit = 5;                  // user-set

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MeleeCrit);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.accessory = true;
			Item.value = Item.sellPrice(silver: 75);
			Item.rare = ItemRarityID.Green;
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetCritChance(DamageClass.Melee) += MeleeCrit;
		}
	}
}
