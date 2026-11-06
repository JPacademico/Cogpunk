using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Desert.Items
{
	/// <summary>
	/// Hawk Eye (user-set 2026-11-04): the <see cref="NPCs.Coghawk"/>'s brass lens worn as an accessory (1 in 10 from it):
	/// +<see cref="RangedCrit"/>% ranged critical strike chance. Not a Scrappy Trunk trinket: it has its own user-set drop
	/// (SKILL 3.3). Balance: docs/balance/accessories.csv (anchor: the Chicken Snapper's +5% melee crit, which also gives +5%
	/// melee speed).
	/// </summary>
	public class HawkEye : CogpunkItem
	{
		public const int RangedCrit = 5;                 // user-set

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(RangedCrit);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.accessory = true;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Blue;
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetCritChance(DamageClass.Ranged) += RangedCrit;
		}
	}
}
