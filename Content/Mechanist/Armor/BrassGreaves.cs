using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Armor
{
	/// <summary>Brass Greaves (2026-11-09): <see cref="Defense"/> defense (Molten Greaves'), +<see cref="SpeedBonus"/>% Mechanist
	/// attack speed (their +7% melee speed). Set bonus: <see cref="BrassHelmet"/>.</summary>
	[AutoloadEquip(EquipType.Legs)]
	public class BrassGreaves : CogpunkItem
	{
		public const int Defense = 8;
		public const int SpeedBonus = 7;
		public const int BarCost = 15, MetalCost = 6;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SpeedBonus);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 22;
			Item.height = 18;
			Item.value = 30000;                            // Molten Greaves'
			Item.rare = ItemRarityID.Orange;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetAttackSpeed<MechanistDamage>() += SpeedBonus / 100f;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<TarnishedBrassBar>(BarCost)
				.AddIngredient<PolishedMetal>(MetalCost)
				.AddTile<RustPolisherTile>()
				.Register();
		}
	}
}
