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
	/// Tar Bone Staff (user-set 2026-10-30): a femur wrapped in tar with a little tyrant skull on top. It looses a slow,
	/// homing tyrant skull (<see cref="TyrantSkullBolt"/>, "like the Book of Skulls": the same speed, homing and steering)
	/// that bites the first enemy it reaches and bursts there, hurting every other enemy within a 5-tile circle.
	/// <see cref="SkullSpeed"/> is the Book of Skulls' (decompiled 1.4.4 <c>Item.SetDefaults</c> case 1313: shootSpeed 3.5).
	/// Balance: docs/balance/weapons.csv (anchor: Book of Skulls).
	/// </summary>
	public class TarBoneStaff : CogpunkItem
	{
		public const int UseTime = 28;
		public const float SkullSpeed = 3.5f;
		private const float MuzzleDistance = 34f;          // from the hand to the skull at the staff's top

		public override void SetStaticDefaults() {
			Item.staff[Type] = true;                       // held and aimed like a staff (the sprite points to the top right)
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 33;                              // user-set
			Item.crit = 3;                                 // + the player's base 4% = 7% (user-set)
			Item.knockBack = 3.5f;
			Item.DamageType = DamageClass.Magic;
			Item.mana = 19;                                // user-set
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.UseSound = SoundID.Item8 with { Pitch = -0.3f };
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<TyrantSkullBolt>();
			Item.shootSpeed = SkullSpeed;
			Item.width = 44;
			Item.height = 44;
			Item.value = Item.sellPrice(gold: 1, silver: 50);
			Item.rare = ItemRarityID.Orange;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 muzzle = velocity.SafeNormalize(Vector2.UnitX * player.direction) * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;                        // leave from the skull, unless that is inside a wall
			}
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.Bone, 25)
				.AddIngredient<CondensedTar>(8)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
