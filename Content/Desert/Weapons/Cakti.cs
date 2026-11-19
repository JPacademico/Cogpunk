using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Desert.Weapons
{
	/// <summary>
	/// Cak-ti (user-set 2026-11-17: "ranged, a very fast cactus weapon that shoots thin cacti spikes that stick on the enemy for 5
	/// seconds and when the enemy dies it shoots the spikes that were on him everywhere. It should consume bullets and deal 8
	/// base damage with a 11 use time and 5% base crit with high precision and a 33% chance to not consume ammo. It should be
	/// crafted using cactus and rusted cogs"): a gun grown from a flowering cactus on an oak stock, a rusted cog at its joint.
	/// It eats any bullet and fires a <see cref="CaktiSpike"/> in its place (the bullet's damage and speed added, vanilla's ammo
	/// rules), dead straight (no spread), and saves the bullet 1 time in 3 (<see cref="CanConsumeAmmo"/>, the Minishark's rate).
	/// <para>Balance (D3; docs/balance/weapons.csv; T0, crafted early): anchor the Minishark (decompiled 1.4.4
	/// <c>Item.SetDefaults</c> 98: 6 damage, use 8, bullets, the same 33% ammo save): <see cref="Damage"/> every
	/// <see cref="UseTime"/> ticks at 5% crit; its spikes' burst on a kill is its edge. Recipe: <see cref="CactusCost"/> Cactus and
	/// <see cref="CogCost"/> Rusted Cogs at a Work Bench (my calls). Art: art/desert/make_cakti_art.py.</para>
	/// </summary>
	public class Cakti : CogpunkItem
	{
		public const int Damage = 10;                       // 8 user-set; 10 since 2026-11-18 (user: "only 5% worse than mini shark")
		public const int UseTime = 11;                      // user-set
		public const int CritBonus = 1;                     // user-set: 5% with the player's own 4%
		public const float AmmoSaveChance = 0.33f;          // user-set: 33% not to use a bullet
		public const float ShootSpeed = 11f;
		public const float Knockback = 1f;
		public const float MuzzleDistance = 30f;
		public const int CactusCost = 20, CogCost = 6;      // my calls

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(CaktiSpike.StickTicks / 60, (int)System.Math.Round(AmmoSaveChance * 100f));

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 52;
			Item.height = 26;
			Item.DamageType = DamageClass.Ranged;
			Item.damage = Damage;
			Item.crit = CritBonus;
			Item.knockBack = Knockback;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.noMelee = true;
			Item.autoReuse = true;
			Item.useAmmo = AmmoID.Bullet;
			Item.shoot = ProjectileID.Bullet;                // any bullet: replaced by a spike in ModifyShootStats
			Item.shootSpeed = ShootSpeed;
			Item.UseSound = SoundID.Item11 with { Pitch = 0.45f, Volume = 0.7f };
			Item.value = Item.sellPrice(silver: 60);
			Item.rare = ItemRarityID.Blue;
		}

		public override Vector2? HoldoutOffset() => new Vector2(-4f, 0f);

		public override bool CanConsumeAmmo(Item ammo, Player player) => Main.rand.NextFloat() >= AmmoSaveChance;

		/// <summary>A spike in the bullet's place, from the muzzle unless a wall is in the way; no spread ("high precision").</summary>
		public override void ModifyShootStats(Player player, ref Vector2 position, ref Vector2 velocity, ref int type, ref int damage, ref float knockback) {
			type = ModContent.ProjectileType<CaktiSpike>();
			Vector2 muzzle = velocity.SafeNormalize(Vector2.Zero) * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.Cactus, CactusCost)
				.AddIngredient<RustedCog>(CogCost)
				.AddTile(TileID.WorkBenches)
				.Register();
		}
	}
}
