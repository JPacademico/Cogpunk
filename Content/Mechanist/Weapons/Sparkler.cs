using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// Sparkler (Mechanist; user-set 2026-11-27: "a mechanist class weapon that costs 2 steam per attack and shots burst of 4
	/// sparks (like a shotgun burst). the 'sparks' should be te spark wand sparks projectile. it should be crafted using 3
	/// rusted cogs and 3 copper or tin bars. it should deal 13 damage (per projectile) and a low 3% base crit chance"): a
	/// stubby copper-and-cog spark blunderbuss. Each blast spends <see cref="Cost"/> steam and fans <see cref="SparkCount"/>
	/// Wand of Sparking sparks (<c>ProjectileID.WandOfSparkingSpark</c>) across a <see cref="SpreadDegrees"/>-degree cone.
	/// <para>D3: <c>Item.crit = -1</c> plus the player's base 4% gives the requested 3% base crit (rule 9); local NPC immunity
	/// lets all four sparks register at close quarters (~11-tile spark range, close-quarter Mechanist rule 10; anchor the T0
	/// Platinum Broadsword, docs/balance/weapons.csv). D2: only the owner spawns and configures the burst in <see cref="Shoot"/>.</para>
	/// </summary>
	public class Sparkler : MechanistWeapon
	{
		public const int Cost = 2;                                // user-set: 2 steam per attack
		public const int Damage = 13;                             // user-set: 13 per projectile
		public const int CritOffset = -1;                         // user-set: 3% base crit (-1 + player's base 4%)
		public const int SparkCount = 4;                          // user-set: burst of 4 sparks
		public const int UseTime = 48;                            // 0.8 s shotgun cadence (+14% at point blank vs T0 anchor)
		public const float SpreadDegrees = 24f;
		public const float ShotSpeed = 7.5f, Knockback = 2f;
		public const float MuzzleDistance = 26f;
		public const int LocalImmunityTicks = 15;
		public const int CogCost = 3, BarCost = 3;                // user-set

		public override int SteamCost => Cost;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SparkCount);

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = CritOffset;
			Item.knockBack = Knockback;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.UseSound = SoundID.Item36 with { Pitch = 0.25f, Volume = 0.8f };
			Item.shoot = ProjectileID.WandOfSparkingSpark;
			Item.shootSpeed = ShotSpeed;
			Item.width = 42;
			Item.height = 22;
			Item.value = Item.sellPrice(silver: 8);
			Item.rare = ItemRarityID.White;
		}

		public override Vector2? HoldoutOffset() => new Vector2(-6f, 0f);

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 dir = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 muzzle = dir * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
			float halfSpread = MathHelper.ToRadians(SpreadDegrees * 0.5f);
			float baseSpeed = velocity.Length();
			for (int i = 0; i < SparkCount; i++) {
				float fraction = SparkCount > 1 ? (i / (float)(SparkCount - 1)) * 2f - 1f : 0f;
				float angle = fraction * halfSpread + Main.rand.NextFloat(-0.035f, 0.035f);
				float speed = baseSpeed * Main.rand.NextFloat(0.92f, 1.08f);
				Vector2 sparkVel = dir.RotatedBy(angle) * speed;
				if (SafeSpawn.TryNewProjectile(source, position, sparkVel, ProjectileID.WandOfSparkingSpark, damage, knockback, out Projectile proj, player.whoAmI)) {
					proj.DamageType = ModContent.GetInstance<MechanistDamage>();
					proj.usesLocalNPCImmunity = true;
					proj.localNPCHitCooldown = LocalImmunityTicks;
				}
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				for (int i = 0; i < 6; i++) {
					if (SafeSpawn.TryNewDust(position - new Vector2(4f), 8, 8, DustID.Torch, out Dust d)) {
						d.velocity = dir.RotatedByRandom(0.5f) * Main.rand.NextFloat(1.5f, 4f);
						d.noGravity = true;
						d.scale = 1.2f;
					}
				}
			}
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
