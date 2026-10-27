using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Armor
{
	/// <summary>Polished Pants (user-set 2026-10-27): <see cref="Defense"/> defense, +<see cref="MoveSpeedBonus"/>% movement
	/// speed (piston knees). Set bonus: <see cref="PolishedHelmet"/>.</summary>
	[AutoloadEquip(EquipType.Legs)]
	public class PolishedPants : CogpunkItem
	{
		public const int Defense = 5;
		public const int MoveSpeedBonus = 10;              // percent
		public const int MetalCost = 12;
		public const int TarCost = 5;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MoveSpeedBonus);

		public override void SetDefaults() {
			Item.width = 22;
			Item.height = 18;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Blue;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.moveSpeed += MoveSpeedBonus / 100f;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<PolishedMetal>(MetalCost)
				.AddIngredient<TarDrop>(TarCost)
				.AddTile<RustPolisherTile>()
				.Register();
		}
	}
}
