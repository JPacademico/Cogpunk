using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// The Barrel Gun (Mechanist; user-set 2026-11-11b, with a reference image of a red-staved, iron-hooped barrel on a dark
	/// gun frame: "add a new mechanist weapon that can be found in wood crates (5%). it should be called barrel gun and shoot
	/// fish at 24 use time 4 steam each, dealing 20 damage and with a chance to stun enemies (only stun basic enemies, not
	/// bosses or mini bosses) it can't crit and gains 50% more damage and homing when it's raining or underwater"). A fish
	/// barrel on a steam frame. Each use flings one fish (<see cref="BarrelGunFish"/>: a bass, a trout or a snapper, the
	/// owner's pick) in a shallow arc; a fish that hits may stun its enemy (<see cref="BarrelGunFish.StunChance"/>, for
	/// <see cref="BarrelGunFish.StunTicks"/>; basic enemies only, <see cref="Buffs.StunnedNPC.CanStun"/>). It never crits.
	/// While it rains where the wielder stands (the surface or the sky) or the wielder is under water,
	/// <see cref="Empowered"/>: x<see cref="EmpoweredDamage"/> damage (the tooltip shows it) and the fish swim straight and
	/// home in on the nearest enemy.
	/// <para>Found in Wooden and Pearlwood Crates, 1 in <see cref="CrateChance"/> (<see cref="BarrelGunCrateLoot"/>). D2: the
	/// owner aims, pays and picks the fish and the empowerment, which ride the fish's <c>ai[]</c>; its hits and stun rolls
	/// are the owner's (the stun's buff is synced by vanilla). Balance: docs/balance/weapons.csv.</para>
	/// </summary>
	public class BarrelGun : MechanistWeapon
	{
		public const int Cost = 4, Damage = 20, UseTime = 24;      // user-set
		public const float EmpoweredDamage = 1.5f;                 // user-set: +50% in rain or under water
		public const int CrateChance = 20;                         // user-set: 5%
		public const float ShotSpeed = 10f, Knockback = 3.5f;
		public const float MuzzleDistance = 36f;                   // the hand to the barrel's mouth

		/// <summary>The hand holds the grip 14 px in from the gun's back, 2 px below the arm (vanilla's <c>HoldoutOffset</c>).</summary>
		public static readonly Vector2 Holdout = new(-14f, 2f);

		public override int SteamCost => Cost;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs((int)System.Math.Round(BarrelGunFish.StunChance * 100f),
			(int)System.Math.Round((EmpoweredDamage - 1f) * 100f));

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.knockBack = Knockback;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.UseSound = SoundID.Item61 with { Pitch = -0.35f, Volume = 0.7f };   // a hollow, wet thunk
			Item.shoot = ModContent.ProjectileType<BarrelGunFish>();
			Item.shootSpeed = ShotSpeed;
			Item.width = 60;
			Item.height = 32;
			Item.value = Item.sellPrice(silver: 40);
			Item.rare = ItemRarityID.Blue;
		}

		/// <summary>Rain over the wielder (it only falls on the surface and in the sky) or water round them (not lava, honey or
		/// shimmer).</summary>
		public static bool Empowered(Player player) {
			bool rain = Main.raining && (player.ZoneOverworldHeight || player.ZoneSkyHeight);
			bool water = player.wet && !player.lavaWet && !player.honeyWet && !player.shimmerWet;
			return rain || water;
		}

		public override void ModifyWeaponDamage(Player player, ref StatModifier damage) {
			if (Empowered(player)) {
				damage *= EmpoweredDamage;
			}
		}

		public override Vector2? HoldoutOffset() => Holdout;

		/// <summary>The owner: one fish from the barrel's mouth (from the player's centre if a wall is in the way), its kind
		/// and whether it is empowered in its <c>ai[]</c>.</summary>
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 muzzle = velocity.SafeNormalize(Vector2.UnitX * player.direction) * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
			float empowered = Empowered(player) ? 1f : 0f;
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI, empowered,
				Main.rand.Next(BarrelGunFish.Kinds));
			return false;
		}

		/// <summary>No critical strike line: it can't crit (the tooltip says so).</summary>
		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			base.ModifyTooltips(tooltips);
			for (int k = tooltips.Count - 1; k >= 0; k--) {
				if (tooltips[k].Mod == "Terraria" && tooltips[k].Name == "CritChance") {
					tooltips.RemoveAt(k);
				}
			}
		}
	}

	/// <summary>The Barrel Gun in Wooden Crates and their Hardmode Pearlwood Crates, 1 in <see cref="BarrelGun.CrateChance"/>
	/// (user-set 5%), rolled on its own beside the crate's own loot (vanilla opens crates on the opener's client through the
	/// item loot database).</summary>
	public sealed class BarrelGunCrateLoot : GlobalItem
	{
		public override bool AppliesToEntity(Item entity, bool lateInstantiation) => entity.type == ItemID.WoodenCrate || entity.type == ItemID.WoodenCrateHard;

		public override void ModifyItemLoot(Item item, ItemLoot itemLoot) {
			itemLoot.Add(ItemDropRule.Common(ModContent.ItemType<BarrelGun>(), BarrelGun.CrateChance));
		}
	}
}
