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
	/// Spare Helmet (user-set 2026-11-27: "spare helmet crafted using wood helmet + 2 rusted cog. it should give +3% damage and
	/// crit ... as strong as iron armor ... the full set bonus should be that when taking damage it releases damaging spark"):
	/// a Wooden Helmet reinforced with a spinning brass ear cog and leather brow strap.
	/// <para>Balance: docs/balance/armor.csv (3/3/3 = 9 defense, matching Iron armor's 9 total).</para>
	/// </summary>
	[AutoloadEquip(EquipType.Head)]
	public class SpareHelmet : CogpunkItem
	{
		public const int Defense = 3;
		public const int DamageBonus = 3;             // user-set: +3% damage
		public const int CritBonus = 3;               // user-set: +3% crit
		public const int CogCost = 2;                 // user-set
		public const int CogFrames = 4;
		public const int CogTicksPerFrame = 8;

		public static LocalizedText SetBonusText { get; private set; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(DamageBonus, CritBonus);

		public override void Load() {
			AnimatedEquip.Register(this, EquipType.Head, CogFrames, CogTicksPerFrame);
		}

		public override void Unload() {
			SetBonusText = null;
		}

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
			SetBonusText = this.GetLocalization("SetBonus").WithFormatArgs(SpareArmorPlayer.SparkDamage);
		}

		public override void SetDefaults() {
			Item.width = 24;
			Item.height = 22;
			Item.value = Item.sellPrice(silver: 4);
			Item.rare = ItemRarityID.White;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetDamage(DamageClass.Generic) += DamageBonus / 100f;
			player.GetCritChance(DamageClass.Generic) += CritBonus;
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return body.type == ModContent.ItemType<SpareVest>() && legs.type == ModContent.ItemType<SpareBoots>();
		}

		public override void UpdateArmorSet(Player player) {
			player.setBonus = SetBonusText.Value;
			player.GetModPlayer<SpareArmorPlayer>().SparkOnHurt = true;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.WoodHelmet)
				.AddIngredient<RustedCog>(CogCost)
				.AddTile(TileID.WorkBenches)
				.Register();
		}
	}
}
