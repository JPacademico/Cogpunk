using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Content.Scrap.Items;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Accessories
{
	/// <summary>
	/// Brass Container (user-set 2026-10-27): the <see cref="GlassContainer"/> caged in brass and fitted with a pressure
	/// valve: +15 steam capacity and +4% mechanist damage. Crafted at the Rust Polisher from a Glass Container, 8 Polished
	/// Metal and 18 Rusted Cogs.
	/// </summary>
	public class BrassContainer : SteamContainer
	{
		public const int Capacity = 20;                // 15, +5 (user, 2026-11-26: "increase amount of max steam that all max steam increasing itens give in 5 points")
		public const int DamagePercent = 4;
		public const int MetalCost = 8;
		public const int CogCost = 22;                     // 18 -> 22, x1.2 rounded (user, 2026-11-26)

		public override int SteamCapacity => Capacity;

		public override LocalizedText Tooltip => this.GetLocalization(nameof(Tooltip)).WithFormatArgs(Capacity, DamagePercent);

		public override void SetDefaults() {
			Item.width = 32;
			Item.height = 32;
			Item.accessory = true;
			Item.value = Item.sellPrice(silver: 60);
			Item.rare = ItemRarityID.Green;
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			base.UpdateAccessory(player, hideVisual);
			player.GetDamage<MechanistDamage>() += DamagePercent / 100f;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<GlassContainer>()
				.AddIngredient<PolishedMetal>(MetalCost)
				.AddIngredient<RustedCog>(CogCost)
				.AddTile<RustPolisherTile>()
				.Register();
		}
	}
}
