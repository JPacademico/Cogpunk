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
	/// The Diamond Cutter (Mechanist; user-set 2026-11-11b: "add a new mechanist weapon called diamond cutter, it should be
	/// crafted using a diamond and some platinum/gold bars. it should fire a precise instantaneous thin laser that can pierce
	/// up to 3 enemies with 12% crit chance but 19 damage and 30 use time (8 steam per attack), it should not consume ammo
	/// and should ignore 20% of enemy defense"). A jeweller's steam cutter with a cut diamond for a lens. Each use fires one
	/// <see cref="DiamondCutterBeam"/>: a hitscan line from the diamond's point to the first wall (at most
	/// <see cref="DiamondCutterBeam.Range"/>) that strikes the first <see cref="DiamondCutterBeam.MaxTargets"/> enemies along
	/// it in the tick it is fired, ignoring <see cref="DiamondCutterBeam.ArmorIgnore"/> of their defense. No ammo: steam only.
	/// <para>Recipe (my calls for the counts): <see cref="Diamonds"/> Diamond and <see cref="Bars"/> Gold or Platinum Bars at
	/// an anvil (vanilla's Diamond Staff takes 8 Diamonds and Platinum). D2: the owner aims, pays and fires (vanilla runs
	/// <c>Shoot</c> on the owner's client); the beam's length rides <c>ai[0]</c>, so every client draws the same line.
	/// Balance: docs/balance/weapons.csv.</para>
	/// </summary>
	public class DiamondCutter : MechanistWeapon
	{
		public const int Cost = 8, Damage = 19, UseTime = 30;      // user-set
		public const int CritBonus = 8;                            // + the player's base 4% = 12% (user-set)
		public const int Diamonds = 1, Bars = 10;                  // "a diamond and some platinum/gold bars"
		public const float Knockback = 2f;
		/// <summary>The hand (the gun's grip) to the diamond's point along the barrel, game px.</summary>
		public const float MuzzleDistance = 44f;

		/// <summary>The hand holds the grip 8 px in from the gun's back, its middle 2 px below the arm (vanilla's
		/// <c>HoldoutOffset</c>).</summary>
		public static readonly Vector2 Holdout = new(-8f, 2f);

		public override int SteamCost => Cost;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(DiamondCutterBeam.MaxTargets,
			(int)System.Math.Round(DiamondCutterBeam.ArmorIgnore * 100f));

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = CritBonus;
			Item.knockBack = Knockback;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.UseSound = SoundID.Item12 with { Pitch = 0.45f, Volume = 0.75f };   // a thin, high laser
			Item.shoot = ModContent.ProjectileType<DiamondCutterBeam>();
			Item.shootSpeed = 1f;                                  // a direction only: the beam is instant
			Item.width = 56;
			Item.height = 28;
			Item.value = Item.sellPrice(silver: 60);
			Item.rare = ItemRarityID.Blue;
		}

		public override Vector2? HoldoutOffset() => Holdout;

		/// <summary>The owner: the beam leaves the diamond's point (from the player's centre if a wall is in the way), its length
		/// measured now (<see cref="DiamondCutterBeam.Measure"/>) and sent with it.</summary>
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 dir = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 muzzle = dir * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
			float length = DiamondCutterBeam.Measure(position, dir);
			SafeSpawn.TryNewProjectile(source, position, dir, type, damage, knockback, out _, player.whoAmI, length);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.Diamond, Diamonds)
				.AddRecipeGroup(VanillaRecipeGroups.GoldBar, Bars)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
