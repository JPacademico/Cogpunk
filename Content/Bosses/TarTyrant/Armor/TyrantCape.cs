using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Armor
{
	/// <summary>Tyrant Cape: <see cref="Defense"/> defense, +<see cref="WhipSpeed"/>% whip speed (vanilla's own whip-speed
	/// stat, the attack speed of <c>DamageClass.SummonMeleeSpeed</c>) and -<see cref="ManaCost"/>% mana cost (user-set
	/// 2026-11-06, the summoner-mage rework; from 2026-11-03 it gave +1 minion slot and +5% summon damage, before that -10%
	/// mana and steam costs). Set bonus: <see cref="TyrantSkull"/>.
	/// <para>Berserker look (user, 2026-10-30: "make the cape leave the chest naked (bra if female character) only with the
	/// cape"): the body sheet only draws a collar and a bone clasp (and, in the female torso cells, a bra), so vanilla's own
	/// skin shows on the chest and arms (<c>ArmorIDs.Body.Sets.HidesTopSkin</c> is false by default; <c>HidesHands</c>
	/// defaults to true for modded bodies and is turned off here, as ExampleMod 1.4.4's ExampleRobe does). The cape itself is
	/// a back equip (<see cref="CapeTexture"/>, 20 frames drawn with the body frame behind the wearer, decompiled
	/// <c>PlayerDrawLayers.DrawPlayer_10_BackAcc</c>) shown through <c>ArmorIDs.Body.Sets.IncludedCapeBack</c> for both
	/// genders; it takes the body dye and gives way to a back accessory the wearer has on (decompiled
	/// <c>Player.UpdateVisibleAccessories</c>).</para>
	/// <para>D0: the cape's texture is registered on clients only and only if it exists, from a fixed path (not
	/// <c>Texture</c>, which may resolve to the fallback), so a missing file leaves the set without a cape instead of failing
	/// to load.</para></summary>
	[AutoloadEquip(EquipType.Body)]
	public class TyrantCape : CogpunkItem
	{
		public const int Defense = 7;
		public const int WhipSpeed = 12;                // percent, user-set
		public const int ManaCost = 10;                 // percent less, user-set
		public const string CapeEquipName = "TyrantCapeBack";
		public const string CapeTexture = "Cogpunk/Content/Bosses/TarTyrant/Armor/TyrantCape_Back";

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(WhipSpeed, ManaCost);

		public override void Load() {
			if (Main.dedServ || !ModContent.HasAsset(CapeTexture)) {
				return;
			}
			EquipLoader.AddEquipTexture(Mod, CapeTexture, EquipType.Back, name: CapeEquipName);
		}

		public override void SetStaticDefaults() {
			ArmorIDs.Body.Sets.HidesHands[Item.bodySlot] = false;       // bare arms and hands: the wearer's own skin
			int cape = EquipLoader.GetEquipSlot(Mod, CapeEquipName, EquipType.Back);
			if (cape > 0) {
				ArmorIDs.Body.Sets.IncludedCapeBack[Item.bodySlot] = cape;
				ArmorIDs.Body.Sets.IncludedCapeBackFemale[Item.bodySlot] = cape;
			}
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 30;
			Item.value = Item.sellPrice(gold: 1, silver: 80);
			Item.rare = ItemRarityID.Orange;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.GetAttackSpeed(DamageClass.SummonMeleeSpeed) += WhipSpeed / 100f;
			player.manaCost -= ManaCost / 100f;
		}
	}
}
