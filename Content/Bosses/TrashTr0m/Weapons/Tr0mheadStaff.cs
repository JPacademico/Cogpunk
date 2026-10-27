using System;
using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// Tr0mhead (Trash-Tr0m drop, summon; class name kept from the "Tr0mhead Staff" so saved items still load): the item is
	/// only the little Tr0m head, held up to place it (user-set 2026-10-27: not a staff). It places a
	/// <see cref="Tr0mheadSentry"/>, a small copy of Trash-Tr0m's head on a scrap tripod, on the ground under the cursor (vanilla's sentry placement: <c>Player.FindSentryRestingSpot</c>,
	/// ExampleMod 1.4.4 <c>ExampleSentryItem</c>). It takes a sentry slot and lasts the vanilla 10 minutes.
	/// <para>Like the <c>Mice-bot</c>, it crits at the usual 4% (summon damage skips vanilla's crit roll, so the sentry
	/// rolls it, D3 rule 9), and <see cref="ModifyTooltips"/> shows the crit line. Balance: docs/balance/weapons.csv
	/// (anchor: Lightning Aura Rod).</para>
	/// </summary>
	public class Tr0mheadStaff : CogpunkItem
	{
		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(Tr0mheadSentry.SuckTicks / 60, Tr0mheadSentry.RestTicks / 60f);

		public override void SetStaticDefaults() {
			ItemID.Sets.GamepadWholeScreenUseRange[Type] = true;
			ItemID.Sets.LockOnIgnoresCollision[Type] = true;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 15;
			Item.knockBack = 0f;
			Item.mana = 10;
			Item.DamageType = DamageClass.Summon;
			Item.sentry = true;
			Item.useStyle = ItemUseStyleID.HoldUp;      // the head is held up, not swung like a staff
			Item.useTime = 30;
			Item.useAnimation = 30;
			Item.UseSound = SoundID.Item46;
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<Tr0mheadSentry>();
			Item.width = 40;
			Item.height = 44;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Blue;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			player.FindSentryRestingSpot(type, out int worldX, out int worldY, out _);
			int halfHeight = (int)Math.Ceiling(Tr0mheadSentry.HitboxHeight / 2f);
			Vector2 at = new(worldX, worldY - halfHeight);
			if (SafeSpawn.TryNewProjectile(source, at, Vector2.Zero, type, damage, knockback, out Projectile sentry, player.whoAmI)) {
				sentry.originalDamage = Item.damage;
			}
			player.UpdateMaxTurrets();                     // removes the oldest sentries past the player's limit
			return false;
		}

		// Summon damage hides the vanilla crit line, but this sentry does crit (see MiceBot).
		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Damage");
			if (index < 0) {
				return;
			}
			int crit = Main.LocalPlayer.GetWeaponCrit(Item);
			tooltips.Insert(index + 1, new TooltipLine(Mod, "CritChance", crit + Lang.tip[41].Value));
		}
	}
}
