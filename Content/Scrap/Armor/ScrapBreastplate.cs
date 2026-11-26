using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Armor
{
	/// <summary>Scrap armor body: 5% damage (all classes), a spinning chest cog. Set bonus: <see cref="ScrapHelmet"/>.</summary>
	[AutoloadEquip(EquipType.Body)]
	public class ScrapBreastplate : CogpunkItem
	{
		public const int DamageBonus = 5;           // percent, generic

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(DamageBonus);

		public override void Load() {
			AnimatedEquip.Register(this, EquipType.Body, ScrapHelmet.CogFrames, ScrapHelmet.CogTicksPerFrame);
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 20;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.White;
			Item.defense = 6;
		}

		public override void UpdateEquip(Player player) {
			player.GetDamage(DamageClass.Generic) += DamageBonus / 100f;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>(8)                           // 7 -> 8, x1.2 rounded (user, 2026-11-26)
				.AddRecipeGroup(RecipeGroupID.IronBar, 8)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
