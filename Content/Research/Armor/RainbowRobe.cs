using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Armor
{
	/// <summary>
	/// The Rainbow Robe (Manto Arco-Íris), unlocked by the research node "RGBT" (user, 2026-11-24: "unlocks (one knowledge point)
	/// the crafting of the rainbow robe a powerfull mage chest piece that should be slightly stronger than all other pre hardmode
	/// mage chest pieces and make so while using any gem mage weapon it fires a extra projectile without extra mana cost"): the
	/// Jade Robe's cut in bands of every gem.
	/// <list type="bullet">
	/// <item>Its numbers (my calls, "slightly stronger than all"; vanilla decompiled 1.4.4, <c>Player.GrantArmorBenefits</c> and
	/// <c>Item.SetDefaults</c>): <see cref="Defense"/> defense (the Meteor Suit's and Jungle Shirt's 6, the Diamond Robe's 3),
	/// +<see cref="ManaBonus"/> max mana and -<see cref="ManaCostReduction"/>% mana cost (between the Ruby Robe's 60 / 13% and the
	/// Diamond Robe's 80 / 15%), +<see cref="MagicDamage"/>% magic damage (the Meteor Suit's is 7%, the Mystic Robe's 6%).</item>
	/// <item>With a gem mage weapon (a magic weapon made from gems or another gem weapon: <see cref="ResearchRecipes.IsGemWeapon"/>)
	/// every shot sends one more of its projectile, a little to one side or the other in turn, paid by nothing
	/// (<see cref="RainbowRobePlayer"/>).</item>
	/// <item>Like vanilla's gem robes it completes the Wizard Hat and Magic Hat sets (<see cref="IsArmorSet"/>).</item>
	/// </list>
	/// <para>Recipe (my call): any gem robe and <see cref="GemCost"/> of each gem (vanilla's seven and jade) at a loom, locked until
	/// the node is researched (<see cref="ResearchRecipes"/>). D2: the stats on every side; the extra shot on the owner (vanilla
	/// runs <c>Shoot</c> there; the projectile is synced by vanilla). Art: art/research/make_rainbow_robe_art.py. Balance:
	/// docs/balance/armor.csv.</para>
	/// </summary>
	[AutoloadEquip(EquipType.Body)]
	public class RainbowRobe : CogpunkItem
	{
		public const int Defense = 6, ManaBonus = 60, ManaCostReduction = 12, MagicDamage = 5;
		public const int WizardCrit = 10, MagicHatMana = 60;   // vanilla's two robe sets
		public const int GemCost = 3;
		public const float ExtraSpread = 0.1f;                 // radians either side, in turn

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ManaBonus, ManaCostReduction, MagicDamage);

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
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Orange;
		}

		public override void UpdateEquip(Player player) {
			player.statManaMax2 += ManaBonus;
			player.manaCost -= ManaCostReduction / 100f;
			player.GetDamage(DamageClass.Magic) += MagicDamage / 100f;
			player.GetModPlayer<RainbowRobePlayer>().Worn = true;
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
			CreateRecipe()
				.AddRecipeGroup(ResearchRecipes.GemRobes)
				.AddIngredient(ItemID.Amethyst, GemCost)
				.AddIngredient(ItemID.Topaz, GemCost)
				.AddIngredient(ItemID.Sapphire, GemCost)
				.AddIngredient(ItemID.Emerald, GemCost)
				.AddIngredient(ItemID.Ruby, GemCost)
				.AddIngredient(ItemID.Diamond, GemCost)
				.AddIngredient(ItemID.Amber, GemCost)
				.AddIngredient<Gems.Items.Jade>(GemCost)
				.AddTile(TileID.Loom)
				.Register();
		}
	}

	/// <summary>The Rainbow Robe's extra shot: the owner, as a gem mage weapon fires, sends one more of the shot's projectile
	/// (the shot's own type, damage and knockback), turned <see cref="RainbowRobe.ExtraSpread"/> to one side, then the other.
	/// No mana: the use already paid. D0: through <see cref="SafeSpawn"/>; one projectile per shot, never from a projectile.</summary>
	public sealed class RainbowRobePlayer : ModPlayer
	{
		public bool Worn;
		private bool side;

		public override void ResetEffects() {
			Worn = false;
		}

		public override bool Shoot(Item item, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			if (!Worn || Player.whoAmI != Main.myPlayer || type <= ProjectileID.None || item == null
				|| !item.DamageType.CountsAsClass(DamageClass.Magic) || !ResearchRecipes.IsGemWeapon(item)) {
				return true;
			}
			side = !side;
			Vector2 turned = velocity.RotatedBy(side ? RainbowRobe.ExtraSpread : -RainbowRobe.ExtraSpread);
			SafeSpawn.TryNewProjectile(source, position, turned, type, damage, knockback, out _, Player.whoAmI);
			return true;
		}
	}
}
