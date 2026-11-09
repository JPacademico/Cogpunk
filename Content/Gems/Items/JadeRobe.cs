using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Items
{
	/// <summary>
	/// Jade Robe (Manto de Jade), the gem robe of the default gem crafts (user, 2026-11-09): a Robe and 10 <see cref="Jade"/>
	/// at a loom, as vanilla's Emerald Robe, whose numbers it has since jade sits at the Emerald's rarity (decompiled 1.4.4
	/// <c>Recipe</c>: item 262 + 10 gems at tile 86; <c>Item.SetDefaults</c> 1285: 2 defense, Blue rarity, a sell price of 50
	/// silver x 4; <c>Player.GrantArmorBenefits</c>: +60 max mana, -11% mana cost). Like vanilla's gem robes it completes the
	/// Wizard Hat (+10% magic critical strike chance) and the Magic Hat (+60 max mana) sets: vanilla checks its own robes'
	/// body slots (decompiled <c>Player.UpdateArmorSets</c>), so the robe answers for those sets itself
	/// (<see cref="IsArmorSet"/>; tModLoader asks every worn piece's ModItem, decompiled <c>ItemLoader.UpdateArmorSet</c>).
	/// <para>A robe (ExampleMod 1.4.4's <c>ExampleRobe</c>): the body sheet plus a skirt drawn over the legs
	/// (<c>JadeRobe_Legs</c>, registered in <see cref="Load"/>, swapped in by <see cref="SetMatch"/>). Balance:
	/// docs/balance/armor.csv. Art: art/gems/make_jade_art.py.</para>
	/// </summary>
	[AutoloadEquip(EquipType.Body)]
	public class JadeRobe : CogpunkItem
	{
		public const int Defense = 2, ManaBonus = 60, ManaCostReduction = 11;   // the Emerald Robe's
		public const int WizardCrit = 10, MagicHatMana = 60;                    // vanilla's two robe sets
		public const int JadeCost = 10;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ManaBonus, ManaCostReduction);

		public override void Load() {
			if (Main.netMode == NetmodeID.Server) {
				return;
			}
			EquipLoader.AddEquipTexture(Mod, $"{Texture}_{EquipType.Legs}", EquipType.Legs, this);
		}

		public override void SetStaticDefaults() {
			ArmorIDs.Body.Sets.HidesHands[Item.bodySlot] = false;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 18;
			Item.height = 14;
			Item.defense = Defense;
			Item.value = Item.sellPrice(silver: 50) * 4;
			Item.rare = ItemRarityID.Blue;
		}

		public override void UpdateEquip(Player player) {
			player.statManaMax2 += ManaBonus;
			player.manaCost -= ManaCostReduction / 100f;
		}

		public override void SetMatch(bool male, ref int equipSlot, ref bool robes) {
			robes = true;
			int legs = EquipLoader.GetEquipSlot(Mod, Name, EquipType.Legs);
			if (legs > 0) {
				equipSlot = legs;
			}
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return head.type == ItemID.WizardHat || head.type == ItemID.MagicHat;
		}

		public override void UpdateArmorSet(Player player) {
			if (player.armor[0].type == ItemID.WizardHat) {
				player.setBonus = Language.GetTextValue("ArmorSetBonus.Wizard");
				player.GetCritChance(DamageClass.Magic) += WizardCrit;
			}
			else {
				player.setBonus = Language.GetTextValue("ArmorSetBonus.MagicHat");
				player.statManaMax2 += MagicHatMana;
			}
		}

		public override void AddRecipes() {
			CreateRecipe().AddIngredient(ItemID.Robe).AddIngredient<Jade>(JadeCost).AddTile(TileID.Loom).Register();
		}
	}
}
