using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
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
	/// A wand welded together from scrap, with a topaz at the tip. Each use fires a burst of <see cref="BurstShots"/>
	/// <see cref="ScrappyWandBolt"/>s, <see cref="ShotDelay"/> ticks apart, for <see cref="ManaPerBurst"/> mana; only the
	/// first bolt flies where the wand points, the others stray up to <see cref="SpreadDegrees"/> degrees.
	/// <para>Burst mechanics are vanilla's: <c>useTime</c> = the gap between bolts, <c>useAnimation</c> = the whole cycle
	/// (26, "Average speed" in the tooltip), <c>useLimitPerAnimation</c> = 3. Mana is paid once, when the animation starts
	/// (decompiled <c>Player.ItemCheck_CheckCanUse</c>), so the tooltip's "Uses 9 mana" is the burst's cost.
	/// Balance: docs/balance/weapons.csv (anchor: Wand of Sparking; flagged over budget, numbers set by the user).</para>
	/// </summary>
	public class ScrappyWand : CogpunkItem
	{
		public const int BurstShots = 3;
		public const int ShotDelay = 4;
		public const int CycleTime = 26;
		public const int ManaPerBurst = 9;
		public const float SpreadDegrees = 9f;
		public const float BoltSpeed = 13f;
		private const float MuzzleDistance = 40f;       // from the hand to the topaz at the wand's tip

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(BurstShots);

		public override void SetStaticDefaults() {
			Item.staff[Type] = true;                     // held and aimed like a staff (sprite points top-right)
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 18;
			Item.crit = 4;                               // + the player's base 4% = 8%
			Item.knockBack = 1.5f;
			Item.DamageType = DamageClass.Magic;
			Item.mana = ManaPerBurst;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useAnimation = CycleTime;
			Item.useTime = ShotDelay;
			Item.useLimitPerAnimation = BurstShots;
			Item.autoReuse = true;
			Item.UseSound = SoundID.Item12 with { Pitch = 0.5f, Volume = 0.55f };
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<ScrappyWandBolt>();
			Item.shootSpeed = BoltSpeed;
			Item.width = 32;
			Item.height = 32;
			Item.value = Item.sellPrice(silver: 30);
			Item.rare = ItemRarityID.Blue;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			// ItemUsesThisAnimation already counts this bolt: decompiled Player.ItemCheck_Shoot calls ApplyItemTime (which
			// raises it) before the Shoot hook, so the first bolt of the burst sees 1.
			if (player.ItemUsesThisAnimation > 1) {
				velocity = velocity.RotatedByRandom(MathHelper.ToRadians(SpreadDegrees));
			}
			Vector2 muzzle = velocity.SafeNormalize(Vector2.UnitX * player.direction) * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;                      // leave from the topaz, unless that is inside a wall
			}
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>()
				.AddIngredient(ItemID.Topaz)
				.AddIngredient<RustedMetal>(4)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
