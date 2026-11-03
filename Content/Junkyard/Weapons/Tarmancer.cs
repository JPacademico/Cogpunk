using System.Collections.Generic;
using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// Tarmancer (user-set 2026-10-30): a claw of tar that summons <see cref="TarSlimeMinion"/>s, one minion slot each, which
	/// hop after the summoner and spit globs of tar (<see cref="TarSlimeShot"/>, the item's damage, low knockback) at enemies
	/// as often as the Hornet Staff's hornets sting; every glob coats its target in the Tar Plague. Crafted from a Slime Staff
	/// and Condensed Tar. Set up like <c>MiceBot</c> (ExampleMod 1.4.4 <c>ExampleSimpleMinionItem</c>, spawned through SafeSpawn,
	/// <c>originalDamage</c> set here, the crit line added back). Balance: docs/balance/weapons.csv (anchor: Hornet Staff).
	/// </summary>
	public class Tarmancer : CogpunkItem
	{
		public override void SetStaticDefaults() {
			ItemID.Sets.GamepadWholeScreenUseRange[Type] = true;
			ItemID.Sets.LockOnIgnoresCollision[Type] = true;
			ItemID.Sets.StaffMinionSlotsRequired[Type] = TarSlimeMinion.MinionSlots;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 11;                              // user-set
			Item.knockBack = 2f;                           // low (the Hornet Staff's)
			Item.mana = 10;
			Item.DamageType = DamageClass.Summon;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = 28;
			Item.useAnimation = 28;
			Item.UseSound = SoundID.Item44;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.buffType = ModContent.BuffType<TarSlimeBuff>();
			Item.shoot = ModContent.ProjectileType<TarSlimeMinion>();
			Item.width = 44;
			Item.height = 44;
			Item.value = Item.sellPrice(gold: 2, silver: 50);
			Item.rare = ItemRarityID.LightRed;
		}

		public override void ModifyShootStats(Player player, ref Vector2 position, ref Vector2 velocity, ref int type, ref int damage, ref float knockback) {
			position = Main.MouseWorld;                    // dropped at the cursor, within reach
			player.LimitPointToPlayerReachableArea(ref position);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			player.AddBuff(Item.buffType, 2);
			if (SafeSpawn.TryNewProjectile(source, position, Vector2.Zero, type, damage, knockback, out Projectile slime, player.whoAmI)) {
				slime.originalDamage = Item.damage;
			}
			return false;
		}

		// Summon damage hides vanilla's crit line, but the tar slimes' globs do crit (TarSlimeShot.ModifyHitNPC).
		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Damage");
			if (index >= 0) {
				tooltips.Insert(index + 1, new TooltipLine(Mod, "CritChance", Main.LocalPlayer.GetWeaponCrit(Item) + Lang.tip[41].Value));
			}
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.SlimeStaff)
				.AddIngredient<CondensedTar>(8)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
