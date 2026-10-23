using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Weapons
{
	/// <summary>
	/// An old, sharpened screwdriver used like a spear: a <see cref="ScrewdriverProjectile"/> thrusts out to 6.5 tiles and
	/// back once per use, hitting on the way out and again on the way back, and deals <see cref="MechanicalBonus"/>% more
	/// damage to NPCs in <see cref="CogpunkSets.Mechanical"/>. Balance: docs/balance/weapons.csv (anchor: Platinum
	/// Broadsword; flagged over budget, numbers set by the user).
	/// </summary>
	public class Screwdriver : CogpunkItem
	{
		public const int MechanicalBonus = 50;          // percent
		public const int UseTime = 31;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MechanicalBonus);

		public override void SetStaticDefaults() {
			ItemID.Sets.Spears[Type] = true;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 20;
			Item.crit = 0;                               // + the player's base 4% = 4%
			Item.knockBack = 5f;
			Item.DamageType = DamageClass.Melee;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.UseSound = SoundID.Item1;
			Item.noMelee = true;                         // the projectile does the hitting
			Item.noUseGraphic = true;
			Item.shoot = ModContent.ProjectileType<ScrewdriverProjectile>();
			Item.shootSpeed = 1f;                        // only the direction is used
			Item.width = 32;
			Item.height = 32;
			Item.value = Item.sellPrice(silver: 40);
			Item.rare = ItemRarityID.White;
		}

		// One thrust at a time, like every vanilla spear.
		public override bool CanUseItem(Player player) {
			return player.ownedProjectileCounts[Item.shoot] < 1;
		}

		// Spawn through SafeSpawn instead of letting vanilla call Projectile.NewProjectile (D0).
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddRecipeGroup(RecipeGroupID.IronBar, 12)
				.AddRecipeGroup(VanillaRecipeGroups.CopperBar, 8)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
