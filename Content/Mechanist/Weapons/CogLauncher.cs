using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Content.Scrap.Items;
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
	/// The Cog-launcher (Mechanist; user-set 2026-11-05: "a mechanist class weapon that shoots a spinning cog, like the scrap
	/// armor does but without the bullet drop gravity, consuming 7 steam per shot; the cog should pierce up to 2 times and
	/// bounce up to 3 times on walls, dealing 31 damage with a fast 24 use time and 5% crit; subsequent hits from the same cog
	/// on the same enemy deal 50% more damage; crafted from a musket + 8 brass bars + 4 polished metal + 23 rusted cogs at an
	/// anvil"). Redrawn 2026-11-05b (user: "it should look like a brass gun with a clocked cog that is shot with a piston, and
	/// not a classic gunpowder gun"): a brass steam piston gun, a Rusted Cog clocked into the cup at its front and a steel ram
	/// behind it. It fires that Rusted Cog (<see cref="CogLauncherCog"/>, spinning like the Scrap armor's) straight ahead,
	/// which passes through <see cref="CogLauncherCog.Pierce"/> enemies, rebounds off <see cref="CogLauncherCog.MaxBounces"/>
	/// walls, and hits an enemy it already hit for <see cref="CogLauncherCog.RepeatBonus"/>x.
	/// <para>While it fires the game draws <see cref="CogLauncherLayer"/>'s frames instead of the item sprite
	/// (<c>noUseGraphic</c>): the ram punched forward through the empty cup, back with the next cog dropping in, loaded.</para>
	/// <para><see cref="Cost"/> steam a shot (a Mechanist weapon: no tank, no shot; an empty tank overheats). Recipe: the
	/// Musket, or The Undertaker in a Crimson world (my call: vanilla's twin of the Musket; a Crimson world has none).
	/// D2: the owner shoots and pays; the cog is the owner's projectile. Balance: docs/balance/weapons.csv.</para>
	/// </summary>
	public class CogLauncher : MechanistWeapon
	{
		public const int Cost = 7, Damage = 31, UseTime = 24;      // user-set
		public const int BrassBars = 8, PolishedMetals = 4, RustedCogs = 28;   // user-set; the cogs 23 -> 28, x1.2 rounded (user, 2026-11-26)
		public const float ShotSpeed = 13f;
		public const float MuzzleDistance = 34f;                   // the hand to the cog's hub in the cup

		/// <summary>The hand holds the grip 12 px in from the gun's back, its middle 2 px below the arm (vanilla's
		/// <c>HoldoutOffset</c>, read by <see cref="CogLauncherLayer"/> too).</summary>
		public static readonly Vector2 Holdout = new(-12f, 2f);

		public override int SteamCost => Cost;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(CogLauncherCog.Pierce, CogLauncherCog.MaxBounces,
			(int)System.Math.Round((CogLauncherCog.RepeatBonus - 1f) * 100f));

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = 1;                                         // + the player's base 4% = 5% (user-set)
			Item.knockBack = 4f;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.noUseGraphic = true;                              // CogLauncherLayer draws the piston's frames
			Item.UseSound = SoundID.Item61 with { Pitch = 0.25f, Volume = 0.8f };
			Item.shoot = ModContent.ProjectileType<CogLauncherCog>();
			Item.shootSpeed = ShotSpeed;
			Item.width = 60;
			Item.height = 32;
			Item.value = Item.sellPrice(gold: 1, silver: 50);
			Item.rare = ItemRarityID.Orange;
		}

		public override Vector2? HoldoutOffset() => Holdout;

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 muzzle = velocity.SafeNormalize(Vector2.UnitX * player.direction) * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddRecipeGroup(VanillaRecipeGroups.Musket)
				.AddIngredient<TarnishedBrassBar>(BrassBars)
				.AddIngredient<PolishedMetal>(PolishedMetals)
				.AddIngredient<RustedCog>(RustedCogs)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
