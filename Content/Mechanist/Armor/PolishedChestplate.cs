using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Armor
{
	/// <summary>Polished Chestplate (user-set 2026-10-27): <see cref="Defense"/> defense, +<see cref="SteamCapacity"/> steam
	/// capacity (the boiler on its back). Set bonus: <see cref="PolishedHelmet"/>.</summary>
	[AutoloadEquip(EquipType.Body)]
	public class PolishedChestplate : CogpunkItem
	{
		public const int Defense = 7;
		public const int SteamCapacity = 30;
		public const int MetalCost = 16;
		public const int TarCost = 12;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SteamCapacity);

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 22;
			Item.value = Item.sellPrice(silver: 60);
			Item.rare = ItemRarityID.Blue;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetModPlayer<SteamPlayer>().SteamMaxBonus += SteamCapacity;
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
