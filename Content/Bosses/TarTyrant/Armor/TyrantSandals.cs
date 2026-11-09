using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Armor
{
	/// <summary>Tyrant Sandals: <see cref="Defense"/> defense and immunity to fall damage (user-set 2026-11-06, the
	/// summoner-mage rework: vanilla's <c>noFallDmg</c>, the Lucky Horseshoe's; from 2026-11-03 they gave +15% summon damage
	/// and +10% movement speed, before that +10% speed and jump height for the mage set). Set bonus: <see cref="TyrantSkull"/>.
	/// <para>Berserker look (user, 2026-10-30: "the pants only an underwear and sandals"): a tar loincloth on a belt of
	/// vertebrae and bone-soled sandals; the legs between are the wearer's own skin (vanilla draws it under leg armor:
	/// <c>ArmorIDs.Legs.Sets.HidesBottomSkin</c> is false by default).</para></summary>
	[AutoloadEquip(EquipType.Legs)]
	public class TyrantSandals : CogpunkItem
	{
		public const int Defense = 5;

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 20;
			Item.value = Item.sellPrice(gold: 1, silver: 20);
			Item.rare = ItemRarityID.Orange;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.noFallDmg = true;
		}
	}
}
