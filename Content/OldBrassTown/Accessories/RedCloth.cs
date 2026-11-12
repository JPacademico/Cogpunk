using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Accessories
{
	/// <summary>
	/// Red Cloth (Pano Vermelho), a matador's muleta (user-set 2026-11-10b: "a new accessory that can be dropped by the
	/// mechanical bull enemy at a 10% chance called red cloth; it should make so the next contact damage the player takes is
	/// dodged every 12 seconds (gives 0.7 second of eye frame after dodging it)"). The Mechanical Bull drops it 1 time in
	/// <see cref="DropOneIn"/>. Worn, the next enemy that touches the wearer is sidestepped: no damage, no knockback,
	/// <see cref="ImmuneTicks"/> ticks of immunity, then it recharges for <see cref="RechargeTicks"/> ticks
	/// (<see cref="RedClothCooldown"/> shows the wait). Only an enemy's touch: projectiles, falls and the like still hurt.
	/// The rules live in <see cref="RedClothPlayer"/>.
	/// <para>Balance: docs/balance/accessories.csv (anchor the Brain of Confusion and Shadow Dodge: a free hit now and then).
	/// Art: art/oldbrasstown/make_red_cloth_art.py.</para>
	/// </summary>
	public class RedCloth : CogpunkItem
	{
		public const int DropOneIn = 10;                    // user-set: 10%
		public const int RechargeTicks = 12 * 60;           // user-set: every 12 seconds
		public const int ImmuneTicks = 42;                  // user-set: 0.7 s after the dodge

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(RechargeTicks / 60, ImmuneTicks / 60f);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.accessory = true;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Orange;                // Westworld's drops' rarity (the Law Hat, the Sheriff's Badge)
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetModPlayer<RedClothPlayer>().Cloth = true;
		}
	}
}
