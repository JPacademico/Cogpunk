using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>
	/// Law Hat (Chapéu da Lei), an accessory the <see cref="NPCs.Sheriff"/> drops 1 time in <see cref="DropOdds"/> (user-set
	/// 2026-11-09: "a new accessory that can be dropped by the sheriff mini boss (20% chance) called law hat; it should give
	/// +10% ranged crit to weapons that consume bullets"): +<see cref="BulletCrit"/>% critical strike chance for every weapon
	/// that uses bullets as ammo (<c>useAmmo == AmmoID.Bullet</c>: the guns; bows, launchers and the Sheriff's own Revolver,
	/// which loads no ammo, are not). Not a Scrappy Trunk trinket (its own drop, SKILL 3.3). Worn as an accessory, it doesn't
	/// show on the player. Balance: docs/balance/accessories.csv. Art: art/oldbrasstown/make_law_hat_art.py.
	/// </summary>
	public class LawHat : CogpunkItem
	{
		public const int BulletCrit = 10;               // user-set
		public const int DropOdds = 5;                  // user-set: 20%

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(BulletCrit);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 36;
			Item.height = 18;
			Item.accessory = true;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Orange;             // the Sheriff Badge's
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetModPlayer<LawHatPlayer>().Worn = true;
		}
	}

	/// <summary>The <see cref="LawHat"/>'s crit for bullet weapons (on whatever side computes the weapon's crit: the owner).</summary>
	public sealed class LawHatPlayer : ModPlayer
	{
		public bool Worn;

		public override void ResetEffects() {
			Worn = false;
		}

		public override void ModifyWeaponCrit(Item item, ref float crit) {
			if (Worn && item.useAmmo == AmmoID.Bullet) {
				crit += LawHat.BulletCrit;
			}
		}
	}
}
