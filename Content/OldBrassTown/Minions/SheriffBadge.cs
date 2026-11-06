using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Minions
{
	/// <summary>
	/// Sheriff Badge (user-set 2026-11-04: "a summon weapon that summons the flying sheriff stars to hover above the player
	/// and attack enemies, 1 summon slot each"), the <see cref="NPCs.Sheriff"/>'s drop (1 in
	/// <see cref="NPCs.Sheriff.BadgeOdds"/>). Each use pins on another <see cref="SheriffStarMinion"/> (one minion slot).
	/// Set up like ExampleMod 1.4.4's <c>ExampleSimpleMinionItem</c> (the minion through SafeSpawn, its
	/// <c>originalDamage</c> set here as vanilla's staffs do); the stars crit at the usual 4%, and since summon weapons hide
	/// the crit line, <see cref="ModifyTooltips"/> adds it back (as the Mice-bot does). Balance: docs/balance/weapons.csv
	/// (anchor: the Hornet Staff).
	/// </summary>
	public class SheriffBadge : CogpunkItem
	{
		public const int Damage = 15;

		public override void SetStaticDefaults() {
			ItemID.Sets.GamepadWholeScreenUseRange[Type] = true;
			ItemID.Sets.LockOnIgnoresCollision[Type] = true;
			ItemID.Sets.StaffMinionSlotsRequired[Type] = SheriffStarMinion.MinionSlots;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.knockBack = 3f;
			Item.mana = 10;
			Item.DamageType = DamageClass.Summon;
			Item.useStyle = ItemUseStyleID.HoldUp;           // the badge held up: deputized
			Item.useTime = 30;
			Item.useAnimation = 30;
			Item.UseSound = SoundID.Item44;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.buffType = ModContent.BuffType<SheriffStarBuff>();
			Item.shoot = ModContent.ProjectileType<SheriffStarMinion>();
			Item.width = 28;
			Item.height = 28;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Orange;                 // the Hornet Staff's
		}

		public override void ModifyShootStats(Player player, ref Vector2 position, ref Vector2 velocity, ref int type, ref int damage, ref float knockback) {
			position = player.Top - new Vector2(0f, 24f);    // pinned on over the head, where the stars ride
			velocity = Vector2.Zero;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			player.AddBuff(Item.buffType, 2);
			if (SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out Projectile star, player.whoAmI)) {
				star.originalDamage = Item.damage;
			}
			return false;
		}

		// Summon damage hides the vanilla crit line (SummonDamageClass.ShowStatTooltipLine), but these stars do crit.
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
