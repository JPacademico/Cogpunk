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
	/// <summary>Brass Chestplate (2026-11-09): <see cref="Defense"/> defense (Molten Breastplate's), +<see cref="DamageBonus"/>%
	/// Mechanist damage (its +7% melee damage) and a bigger boiler, +<see cref="SteamCapacity"/> steam capacity (the Polished
	/// Chestplate holds 30; Mechanist armor is the class's tank, as mage armor carries mana). Set bonus: <see cref="BrassHelmet"/>.</summary>
	[AutoloadEquip(EquipType.Body)]
	public class BrassChestplate : CogpunkItem
	{
		public const int Defense = 9;
		public const int DamageBonus = 7;
		public const int SteamCapacity = 40;
		public const int BarCost = 20, MetalCost = 8;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(DamageBonus, SteamCapacity);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 22;
			Item.value = 30000;                            // Molten Breastplate's
			Item.rare = ItemRarityID.Orange;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetDamage<MechanistDamage>() += DamageBonus / 100f;
			player.GetModPlayer<SteamPlayer>().SteamMaxBonus += SteamCapacity;
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
