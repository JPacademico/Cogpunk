using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Armor
{
	/// <summary>
	/// Polished Helmet, the first Mechanist armor (user-set 2026-10-27): <see cref="Defense"/> defense and
	/// +<see cref="CritBonus"/>% Mechanist crit. Owns the set bonus: every steam cost -<see cref="SteamCostReduction"/>%.
	/// Crafted at the Rust Polisher from Polished Metal and Tar Drops. Balance: docs/balance/armor.csv (anchor: Gold armor).
	/// Art: art/mechanist/make_mechanist_art.py.
	/// </summary>
	[AutoloadEquip(EquipType.Head)]
	public class PolishedHelmet : CogpunkItem
	{
		public const int Defense = 4;
		public const int CritBonus = 6;
		public const int SteamCostReduction = 10;          // percent
		public const int MetalCost = 6;
		public const int TarCost = 5;

		public static LocalizedText SetBonusText { get; private set; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(CritBonus);

		public override void SetStaticDefaults() {
			SetBonusText = this.GetLocalization("SetBonus").WithFormatArgs(SteamCostReduction);
		}

		public override void Unload() {
			SetBonusText = null;
		}

		public override void SetDefaults() {
			Item.width = 22;
			Item.height = 20;
			Item.value = Item.sellPrice(silver: 40);
			Item.rare = ItemRarityID.Blue;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetCritChance<MechanistDamage>() += CritBonus;
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return body.type == ModContent.ItemType<PolishedChestplate>() && legs.type == ModContent.ItemType<PolishedPants>();
		}

		public override void UpdateArmorSet(Player player) {
			player.setBonus = SetBonusText.Value;
			player.GetModPlayer<SteamPlayer>().SteamCostMultiplier -= SteamCostReduction / 100f;
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
