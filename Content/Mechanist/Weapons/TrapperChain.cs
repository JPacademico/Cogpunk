using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// Trapper Chain (Mechanist; 5% drop from the jungle's Trapper, user-set 2026-10-27): a length of steel chain with a
	/// dented bear trap on the end. It flings the trap out towards the cursor on its chain
	/// (<see cref="TrapperChainProjectile"/>); the trap snaps shut on the first enemy it reaches, biting every enemy
	/// overlapping it in that moment, and is reeled back in. <b>The next throw is ready the moment the trap is back</b>
	/// (user-set): the trap keeps the use going while it's out, so a bite close by resets faster than a long miss, never
	/// faster than <see cref="MinCycleTicks"/>. One trap out at a time. User-set: <see cref="Cost"/> steam per throw,
	/// 32 damage. Balance: docs/balance/weapons.csv (anchor: Harpoon).
	/// </summary>
	public class TrapperChain : MechanistWeapon
	{
		public const int Cost = 5;
		public const int Damage = 32;
		/// <summary>The fastest a throw can follow the last one (a bite at point-blank range): the cycle is otherwise the
		/// trap's round trip.</summary>
		public const int MinCycleTicks = 20;
		public const float ThrowSpeed = 15f;

		public override int SteamCost => Cost;

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = 0;                                 // + the player's base 4% = 4%
			Item.knockBack = 6f;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = MinCycleTicks;                  // the trap then holds the use until it's back (TrapperChainProjectile)
			Item.useAnimation = MinCycleTicks;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.noUseGraphic = true;                      // the projectile draws the chain from the hand
			Item.UseSound = SoundID.Item1 with { Pitch = -0.3f };
			Item.shoot = ModContent.ProjectileType<TrapperChainProjectile>();
			Item.shootSpeed = ThrowSpeed;
			Item.width = 32;
			Item.height = 32;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Green;
		}

		protected override bool CanUseMechanist(Player player) {
			return player.ownedProjectileCounts[Item.shoot] < 1;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			SafeSpawn.TryNewProjectile(source, player.MountedCenter, velocity, type, damage, knockback, out _, player.whoAmI);
			return false;
		}
	}
}
