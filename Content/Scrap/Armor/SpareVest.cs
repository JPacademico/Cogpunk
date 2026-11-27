using Cogpunk.Content.Mechanist;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Armor
{
	/// <summary>
	/// Spare Vest (user-set 2026-11-27: "spare vest crafted using wood chest + 4 rusted cogs. it should give +10 max
	/// mana/steam capacity"): a Wooden Breastplate strapped with a brass cog and small copper pressure vessel, giving early
	/// mages and Mechanists alike a +10 resource boost (an immediate starter steam tank for the <see cref="Mechanist.Weapons.Sparkler"/>).
	/// </summary>
	[AutoloadEquip(EquipType.Body)]
	public class SpareVest : CogpunkItem
	{
		public const int Defense = 3;
		public const int ManaBonus = 10;              // user-set: +10 max mana
		public const int SteamBonus = 10;             // user-set: +10 steam capacity
		public const int CogCost = 4;                 // user-set

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ManaBonus, SteamBonus);

		public override void Load() {
			AnimatedEquip.Register(this, EquipType.Body, SpareHelmet.CogFrames, SpareHelmet.CogTicksPerFrame);
		}

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 20;
			Item.value = Item.sellPrice(silver: 6);
			Item.rare = ItemRarityID.White;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.statManaMax2 += ManaBonus;
			player.GetModPlayer<SteamPlayer>().SteamMaxBonus += SteamBonus;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.WoodBreastplate)
				.AddIngredient<RustedCog>(CogCost)
				.AddTile(TileID.WorkBenches)
				.Register();
		}
	}
}
