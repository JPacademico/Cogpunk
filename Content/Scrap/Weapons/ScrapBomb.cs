using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Weapons
{
	/// <summary>
	/// Thrown, consumable pipe bomb. It arcs under gravity and explodes on the first surface or enemy it touches:
	/// a direct hit deals <see cref="DirectDamage"/>, then the blast deals <see cref="ExplosionDamage"/> to
	/// everything within <see cref="ExplosionRadiusTiles"/> tiles, including the target hit directly.
	/// Never destroys tiles. Balance: docs/balance/weapons.csv (anchor: Grenade).
	/// </summary>
	public class ScrapBomb : CogpunkItem
	{
		public const int DirectDamage = 43;
		public const int ExplosionDamage = 32;
		public const float ExplosionRadiusTiles = 5f;   // one tile past the Grenade's 8x8-tile square (4 tiles each way)
		public const int UseTime = 45;                  // same as the Grenade
		public const float ThrowSpeed = 6f;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ExplosionDamage, (int)ExplosionRadiusTiles);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 99;
		}

		public override void SetDefaults() {
			Item.damage = DirectDamage;
			Item.DamageType = DamageClass.Ranged;  // vanilla throwables (Grenade) have been Ranged since 1.4
			Item.knockBack = 6f;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.UseSound = SoundID.Item1;
			Item.noUseGraphic = true;
			Item.noMelee = true;
			Item.consumable = true;
			Item.maxStack = Item.CommonMaxStack;
			Item.shoot = ModContent.ProjectileType<ScrapBombProjectile>();
			Item.shootSpeed = ThrowSpeed;
			Item.width = 24;
			Item.height = 12;
			Item.value = Item.sellPrice(copper: 15);
			Item.rare = ItemRarityID.White;
		}

		// Spawn through SafeSpawn instead of letting vanilla call Projectile.NewProjectile (D0).
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe(5)
				.AddIngredient<RustedCog>()
				.AddRecipeGroup(VanillaRecipeGroups.CopperBar)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
