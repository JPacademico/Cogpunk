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
	/// <summary>
	/// Brass Helmet, the Brass armor's head (user-set 2026-11-09: "a new set of armor called Brass armor for the mechanist
	/// class (T5 balanced, the last armor for the mechanist in pre-hardmode, like the hellstone armor is the last for melee);
	/// its set bonus should reduce any damage taken during overheat by 35%; a cohesive craft (based on other crafts of our
	/// mod) using brass bars"). The Mechanist's Molten armor: the anchor is vanilla's last pre-Hardmode melee set (decompiled
	/// 1.4.4 <c>Item.SetDefaults</c> 231-233: 8/9/8 defense; <c>Player.GrantArmorBenefits</c>: +7% melee crit, +7% melee
	/// damage, +7% melee speed; its set +10% melee damage and fire-block immunity; <c>Recipe</c>: 10/20/15 Hellstone Bars at
	/// an anvil), each melee bonus turned Mechanist. <see cref="Defense"/> defense, +<see cref="CritBonus"/>% Mechanist crit.
	/// Owns the set bonus: while overheated, every hit taken is <see cref="OverheatDamageReduction"/>% smaller
	/// (<see cref="BrassArmorPlayer"/>). Recipes at the Rust Polisher, like the Polished set: Tarnished Brass Bars in
	/// Molten's numbers and Polished Metal. Balance: docs/balance/armor.csv. Art: art/mechanist/make_brass_armor.py.
	/// </summary>
	[AutoloadEquip(EquipType.Head)]
	public class BrassHelmet : CogpunkItem
	{
		public const int Defense = 8;
		public const int CritBonus = 7;
		public const int OverheatDamageReduction = 35;     // percent, user-set
		public const int BarCost = 10, MetalCost = 4;

		public static LocalizedText SetBonusText { get; private set; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(CritBonus);

		public override void SetStaticDefaults() {
			SetBonusText = this.GetLocalization("SetBonus").WithFormatArgs(OverheatDamageReduction);
			Item.ResearchUnlockCount = 1;
		}

		public override void Unload() {
			SetBonusText = null;
		}

		public override void SetDefaults() {
			Item.width = 22;
			Item.height = 22;
			Item.value = 45000;                            // Molten Helmet's
			Item.rare = ItemRarityID.Orange;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetCritChance<MechanistDamage>() += CritBonus;
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return body.type == ModContent.ItemType<BrassChestplate>() && legs.type == ModContent.ItemType<BrassGreaves>();
		}

		public override void UpdateArmorSet(Player player) {
			player.setBonus = SetBonusText.Value;
			player.GetModPlayer<BrassArmorPlayer>().SetBonus = true;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<TarnishedBrassBar>(BarCost)
				.AddIngredient<PolishedMetal>(MetalCost)
				.AddTile<RustPolisherTile>()
				.Register();
		}
	}

	/// <summary>The Brass set bonus (user-set 2026-11-09): while the wearer is overheated, damage taken is cut by
	/// <see cref="BrassHelmet.OverheatDamageReduction"/>%. Runs where vanilla hurts a player: the hurt player's own client,
	/// which also owns the overheat state (<see cref="SteamPlayer.Overheated"/>).</summary>
	public sealed class BrassArmorPlayer : ModPlayer
	{
		public bool SetBonus;

		public override void ResetEffects() {
			SetBonus = false;
		}

		public override void ModifyHurt(ref Player.HurtModifiers modifiers) {
			if (SetBonus && Player.GetModPlayer<SteamPlayer>().Overheated) {
				modifiers.FinalDamage *= 1f - BrassHelmet.OverheatDamageReduction / 100f;
			}
		}
	}
}
