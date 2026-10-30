using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Armor
{
	/// <summary>Jaeger Chestplate (user-set 2026-10-28): <see cref="Defense"/> defense and -<see cref="ContactReduction"/>%
	/// damage taken from touching enemies (not from projectiles; <see cref="JaegerArmorPlayer"/>). Set bonus:
	/// <see cref="JaegerHelmet"/>.</summary>
	[AutoloadEquip(EquipType.Body)]
	public class JaegerChestplate : CogpunkItem
	{
		public const int Defense = 10;
		public const int ContactReduction = 15;         // percent

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ContactReduction);

		public override void SetDefaults() {
			Item.width = 26;
			Item.height = 24;
			Item.value = Item.sellPrice(gold: 1, silver: 20);
			Item.rare = ItemRarityID.Green;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetModPlayer<JaegerArmorPlayer>().ContactDamageTaken -= ContactReduction / 100f;
		}
	}
}
