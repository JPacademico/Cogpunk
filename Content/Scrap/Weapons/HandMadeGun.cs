using System;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Weapons
{
	/// <summary>
	/// Hand-made Gun (user-set 2026-11-27: "a ranged weapon crafted using a rusted cog and 4 copper/tin. it should shoot a
	/// quick precise bullet that bounces once and deal 18 damage, but has a chance to whiff and shoot a spark instead (10%)"):
	/// a crude pipe pistol held together by a brass cog and wire. Fires <see cref="HandMadeBullet"/> straight along the cursor
	/// line with one wall ricochet, except 1 shot in 10 (<see cref="WhiffChance"/>) misfires with a sputter and coughs out a
	/// short-lived Wand of Sparking spark instead.
	/// <para>D2: the misfire roll runs on the owner's client in <see cref="Shoot"/> and syncs through the spawned projectile.
	/// Balance: docs/balance/weapons.csv (anchor the Platinum Bow, +2.8%).</para>
	/// </summary>
	public class HandMadeGun : CogpunkItem
	{
		public const int Damage = 18;                             // user-set
		public const int UseTime = 32;
		public const float Knockback = 3f;
		public const float ShotSpeed = 14f;                       // x2 updates = 28 px/tick
		public const float WhiffChance = 0.10f;                   // user-set: 10%
		public const float WhiffDamageMultiplier = 0.5f;
		public const float WhiffSparkSpeed = 7f;
		public const float MuzzleDistance = 26f;
		public const int CogCost = 1, BarCost = 4;                // user-set

		private static readonly SoundStyle WhiffSound = SoundID.Item11 with { Pitch = -0.55f, Volume = 0.75f };

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs((int)Math.Round(WhiffChance * 100f));

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.knockBack = Knockback;
			Item.DamageType = DamageClass.Ranged;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<HandMadeBullet>();
			Item.shootSpeed = ShotSpeed;
			Item.useAmmo = AmmoID.Bullet;
			Item.UseSound = SoundID.Item11 with { Pitch = 0.15f };
			Item.width = 36;
			Item.height = 22;
			Item.value = Item.sellPrice(silver: 8);
			Item.rare = ItemRarityID.White;
		}

		public override Vector2? HoldoutOffset() => new Vector2(-4f, 0f);

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 dir = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 muzzle = dir * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
			if (Main.rand.NextFloat() < WhiffChance) {
				int sparkDamage = Math.Max(1, (int)MathF.Round(damage * WhiffDamageMultiplier));
				Vector2 sparkVel = dir * WhiffSparkSpeed + new Vector2(0f, -0.8f);
				if (SafeSpawn.TryNewProjectile(source, position, sparkVel, ProjectileID.WandOfSparkingSpark, sparkDamage,
						knockback * 0.5f, out Projectile spark, player.whoAmI)) {
					spark.DamageType = DamageClass.Ranged;
				}
				if (!Main.dedServ) {
					SoundEngine.PlaySound(WhiffSound, position);
					if (CogpunkClientConfig.RollEffect()) {
						for (int i = 0; i < 6; i++) {
							if (SafeSpawn.TryNewDust(position - new Vector2(4f), 8, 8, DustID.Smoke, out Dust puff)) {
								puff.velocity = dir * Main.rand.NextFloat(0.8f, 2.5f) + new Vector2(0f, -0.6f);
								puff.scale = 1.05f;
							}
						}
					}
				}
				return false;
			}
			Vector2 bulletVel = dir * Math.Max(1f, velocity.Length());
			SafeSpawn.TryNewProjectile(source, position, bulletVel, ModContent.ProjectileType<HandMadeBullet>(), damage, knockback, out _, player.whoAmI);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>(CogCost)
				.AddRecipeGroup(VanillaRecipeGroups.CopperBar, BarCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
