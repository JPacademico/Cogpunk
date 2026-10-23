using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Armor
{
	/// <summary>Scrap armor legs: half fall damage, a spinning hip cog. Set bonus: <see cref="ScrapHelmet"/>.</summary>
	[AutoloadEquip(EquipType.Legs)]
	public class ScrapLeggings : CogpunkItem
	{
		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs((int)(ScrapArmorPlayer.FallDamageReduction * 100));

		public override void Load() {
			AnimatedEquip.Register(this, EquipType.Legs, ScrapHelmet.CogFrames, ScrapHelmet.CogTicksPerFrame);
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 14;
			Item.value = Item.sellPrice(silver: 40);
			Item.rare = ItemRarityID.White;
			Item.defense = 5;
		}

		public override void UpdateEquip(Player player) {
			player.GetModPlayer<ScrapArmorPlayer>().SoftLanding = true;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>(6)
				.AddRecipeGroup(VanillaRecipeGroups.CopperBar, 6)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
