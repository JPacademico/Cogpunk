using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// Tar-Shower (user-set 2026-10-30): a polished-metal tar sprayer, flamethrower-like. Gel is its ammo, one per use like
	/// vanilla's flamethrowers (decompiled 1.4.4 <c>Item.SetDefaults</c> case 506: useAnimation 30, useTime 6,
	/// <c>consumeAmmoOnFirstShotOnly</c>); its bursts are fewer and harder (<see cref="UseTime"/> 8, four a use), so the
	/// charge's "up to 300% of the weapon damage" is worth having.
	/// <list type="bullet">
	/// <item><b>Left click</b>: a mid-range spray of tar (<see cref="TarSpray"/>, four bursts a use, ~16 tiles) that coats
	/// what it touches in the Tar Plague.</item>
	/// <item><b>Right click, held</b>: a ball of tar swells at the nozzle (<see cref="TarShowerCharge"/>), up to
	/// x<see cref="MaxChargeMultiplier"/> damage at <see cref="MaxChargeTicks"/> ticks (2.5 s); let go and it flies. At full
	/// charge it is the big glob (<see cref="TarShowerBigGlob"/>): it falls on an arc, goes through every enemy in its way and
	/// leaves a <see cref="TarStain"/> 6 tiles wide where it lands, plaguing every enemy that touches it; a lesser charge
	/// throws a smaller glob (<see cref="TarShowerGlob"/>) for its share of the damage.</item>
	/// </list>
	/// Only the owner fires (D2). Balance: docs/balance/weapons.csv (anchor: Bee's Knees).
	/// </summary>
	public class TarShower : CogpunkItem
	{
		public const int UseTime = 8, UseAnimationTicks = 32;
		public const int MaxChargeTicks = 150;            // 2.5 s (user-set)
		public const float MaxChargeMultiplier = 3f;      // "up to 300% of the weapon damage" (user-set)
		public const float SpraySpeed = 9.3f;             // ~16 tiles over TarSpray.Lifetime at its drag (user, 2026-11-03: +4 tiles; 7 was ~12)
		public const float SpraySpread = 0.07f;           // radians each way
		public const float MuzzleDistance = 36f;          // from the hand to the nozzle

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MaxChargeTicks / 60f, (int)(MaxChargeMultiplier * 100f), TarStain.WidthTiles);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 8;
			Item.crit = 0;                                 // + the player's base 4% = 4%
			Item.knockBack = 0.5f;
			Item.DamageType = DamageClass.Ranged;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseAnimationTicks;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.useAmmo = AmmoID.Gel;
			Item.consumeAmmoOnFirstShotOnly = true;
			Item.shoot = ModContent.ProjectileType<TarSpray>();
			Item.shootSpeed = SpraySpeed;
			Item.width = 52;
			Item.height = 28;
			Item.value = Item.sellPrice(gold: 1, silver: 50);
			Item.rare = ItemRarityID.Orange;
		}

		public override bool AltFunctionUse(Player player) => true;

		// One charge at a time; the alt use only spawns it (one shot a use, see UseTimeMultiplier) and the charge holds the gun.
		public override bool CanUseItem(Player player) {
			return player.altFunctionUse != 2 || player.ownedProjectileCounts[ModContent.ProjectileType<TarShowerCharge>()] < 1;
		}

		public override float UseTimeMultiplier(Player player) => player.altFunctionUse == 2 ? UseAnimationTicks / (float)UseTime : 1f;

		/// <summary>The barrel runs along the sprite's middle rows, so vanilla's gun drawing keeps it at arm level; the hand sits
		/// on the grip under the pump (decompiled <c>PlayerDrawLayers</c> useStyle 5: X replaces the default 10).</summary>
		public override Vector2? HoldoutOffset() => new Vector2(-6f, 2f);

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 direction = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			if (player.altFunctionUse == 2) {
				SafeSpawn.TryNewProjectile(source, player.MountedCenter, direction, ModContent.ProjectileType<TarShowerCharge>(), damage, knockback,
					out _, player.whoAmI);
				return false;
			}
			Vector2 muzzle = direction * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;                        // from the nozzle, unless that is inside a wall
			}
			if (player.ItemUsesThisAnimation == 1 && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item13 with { Pitch = -0.55f, Volume = 0.55f, MaxInstances = 3 }, position);
			}
			Vector2 spray = direction.RotatedByRandom(SpraySpread) * SpraySpeed * Main.rand.NextFloat(0.9f, 1.1f);
			SafeSpawn.TryNewProjectile(source, position, spray, type, damage, knockback, out _, player.whoAmI);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<CondensedTar>(8)
				.AddIngredient<PolishedMetal>(14)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
