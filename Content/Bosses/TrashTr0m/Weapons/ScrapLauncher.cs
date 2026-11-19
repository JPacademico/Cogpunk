using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// Scrap Launcher (Trash-Tr0m drop): Trash-Tr0m's own jaw and grinder turned into a hand cannon, a Mechanist weapon since
	/// 2026-11-17 (user: "make the scrap launcher a mechanist class weapon now instead of ranged class"; it ate bullets as a
	/// ranged gun before): it burns steam like every Mechanist weapon (<see cref="MechanistWeapon"/>: <see cref="ChunkSteam"/> a
	/// chunk, <see cref="BallSteam"/> a ball; my calls, the Barrel Gun's 4 for a shot of its size) and fires what the boss spits
	/// (user-set 2026-10-27):
	/// <list type="bullet">
	/// <item><b>Left click</b>: a lump of chewed scrap (<see cref="ScrapLauncherChunk"/>, the item's damage) that flies
	/// dead straight, no gravity, across a whole screen.</item>
	/// <item><b>Right click</b>: the big scrap ball (<see cref="ScrapLauncherBall"/>, x<see cref="BigShotMultiplier"/>
	/// damage and x<see cref="BigShotKnockback"/> knockback) on a gravity arc, every <see cref="BigShotUseTime"/> ticks.</item>
	/// </list>
	/// Both burst on impact (<see cref="ScrapImpact"/>). Only the owner fires (D2).
	/// Balance: docs/balance/weapons.csv (anchor: The Undertaker / Musket; Mechanist since 2026-11-17).
	/// </summary>
	public class ScrapLauncher : MechanistWeapon
	{
		public const int ChunkSteam = 4, BallSteam = 9;  // my calls (2026-11-17)

		public const int UseTime = 20;
		public const int BigShotUseTime = 31;
		public const float BigShotMultiplier = 2.5f;
		public const float BigShotKnockback = 1.6f;
		public const float ChunkSpeed = 14f;
		public const float BallSpeed = 11f;
		private const float MuzzleDistance = 30f;       // from the hand to the jaw at the gun's front

		public override int SteamCost => ChunkSteam;

		public override int SteamCostFor(Player player) => player.altFunctionUse == 2 ? BallSteam : ChunkSteam;

		public override void SetDefaults() {
			Item.damage = 20;
			Item.crit = 0;                               // + the player's base 4% = 4%
			Item.knockBack = 6.5f;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<ScrapLauncherChunk>();
			Item.shootSpeed = ChunkSpeed;
			Item.width = 52;
			Item.height = 28;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Blue;
		}

		public override bool AltFunctionUse(Player player) => true;

		// Right click: the slower big shot. A multiplier, not a change to Item.useTime (D2 rule 8).
		public override float UseTimeMultiplier(Player player) => player.altFunctionUse == 2 ? BigShotUseTime / (float)UseTime : 1f;

		public override float UseAnimationMultiplier(Player player) => UseTimeMultiplier(player);

		/// <summary>Vanilla draws a gun with its sprite's vertical centre on the player's MountedCenter and the point
		/// HoldoutOffset.X px from its left end on the hand (decompiled Player.ItemCheck_ApplyUseStyle_Inner and
		/// PlayerDrawLayers useStyle 5; X replaces the default 10, Y is added). The old 72x40 sprite had the gun body in
		/// its top half, so it was drawn up over the head (user, 2026-10-27). The 52x24 sprite runs the barrel along its
		/// centre line with the grip hanging below, and the hand sits 6 px from the butt, on the grip.</summary>
		public override Vector2? HoldoutOffset() => new Vector2(-6f, 0f);

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			bool big = player.altFunctionUse == 2;
			Vector2 direction = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 muzzle = direction * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;                      // leave from the jaw, unless that is inside a wall
			}
			// The projectiles play their own launch sound on their first tick, so every client hears it.
			if (big) {
				SafeSpawn.TryNewProjectile(source, position, direction * BallSpeed, ModContent.ProjectileType<ScrapLauncherBall>(),
					(int)(damage * BigShotMultiplier), knockback * BigShotKnockback, out _, player.whoAmI);
			}
			else {
				SafeSpawn.TryNewProjectile(source, position, direction * ChunkSpeed, ModContent.ProjectileType<ScrapLauncherChunk>(),
					damage, knockback, out _, player.whoAmI);
			}
			return false;
		}
	}
}
