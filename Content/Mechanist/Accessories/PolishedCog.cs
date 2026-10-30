using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Accessories
{
	/// <summary>
	/// Polished Cog (user-set 2026-10-28): +<see cref="OverheatSpeedBonus"/>% movement speed while the wearer is
	/// <see cref="Overheat"/>ed, so the forced run of a venting boiler carries them out of trouble. A Scrappy Trunk trinket
	/// (<see cref="CogpunkSets.ScrappyTrunkTrinket"/>), or crafted at the Rust Polisher from <see cref="CogCost"/> Rusted Cogs.
	/// <para>It reads the Overheat buff, which vanilla syncs, rather than <see cref="SteamPlayer.Overheated"/> (owner-only),
	/// so the speed is right on every side (D2). Balance: docs/balance/accessories.csv (anchor: Anklet of the Wind).</para>
	/// </summary>
	public class PolishedCog : CogpunkItem
	{
		public const int OverheatSpeedBonus = 20;          // percent
		public const int CogCost = 50;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(OverheatSpeedBonus);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
			CogpunkSets.ScrappyTrunkTrinket[Type] = true;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.accessory = true;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Blue;
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			if (player.HasBuff<Overheat>()) {
				player.moveSpeed += OverheatSpeedBonus / 100f;
			}
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>(CogCost)
				.AddTile<RustPolisherTile>()
				.Register();
		}
	}
}
