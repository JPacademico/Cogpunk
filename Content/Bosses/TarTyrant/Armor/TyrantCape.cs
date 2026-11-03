using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Armor
{
	/// <summary>Tyrant Cape: <see cref="Defense"/> defense, +<see cref="MinionSlots"/> minion slot (user-set 2026-11-03,
	/// the summoner rework; the Obsidian Shirt's own bonus) and +<see cref="SummonDamage"/>% summon damage. Until
	/// 2026-11-03 it cut mana and steam costs 10% (the mage set). Set bonus: <see cref="TyrantSkull"/>.
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
		public const int MinionSlots = 1;               // user-set
		public const int SummonDamage = 5;              // percent
		public const string CapeEquipName = "TyrantCapeBack";
		public const string CapeTexture = "Cogpunk/Content/Bosses/TarTyrant/Armor/TyrantCape_Back";

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MinionSlots, SummonDamage);

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
			player.maxMinions += MinionSlots;
			player.GetDamage(DamageClass.Summon) += SummonDamage / 100f;
		}
	}
}
