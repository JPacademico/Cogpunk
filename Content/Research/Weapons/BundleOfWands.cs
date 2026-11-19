using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Weapons
{
	/// <summary>
	/// Bundle of Wands (Feixe de Varinhas), the seven pre-Hardmode gem staffs bound together (user-set 2026-11-18: "a new mage
	/// weapon called "bundle of wands" ... it should fire a shotgun burst of 5 randon gem staff projectiles at the same time
	/// (each with their propperty) consuming 28 mana with boomstick use time speed it should be slightly better than other
	/// pre-hardmode mage weapons"). Its recipe is locked until the "Bundle Up!" research node (<see cref="ResearchNodes"/>).
	/// <para>Each use fires five of the seven gem bolts at once (never the same gem twice in a burst), each the staff's own: its
	/// projectile, its speed, its share of the damage and its knockback (decompiled 1.4.4 <c>Item.SetDefaults</c> 739-744 and
	/// 3377: Amethyst 15 / 6 / 3.25, Topaz 16 / 6.5 / 3.5, Sapphire 18 / 7.5 / 4, Emerald 19 / 8 / 4.25, Ruby 21 / 9 / 4.75,
	/// Diamond 23 / 9.5 / 5.5, Amber 21 / 9 / 4.75: damage / speed / knockback), spread over +-<see cref="SpreadDegrees"/>.
	/// A bolt deals <see cref="Item.damage"/> x its staff's damage / 19 (the seven's average), so the tooltip's damage is the
	/// average bolt and damage bonuses reach every bolt. The Boomstick's use time (decompiled 964: 40), 28 mana.</para>
	/// <para>Balance (docs/balance/weapons.csv): user-set 2026-11-19, "should be stronger when all five projectiles hit with
	/// at least 112 dps": 15 a bolt on average, 5 bolts every 40 ticks = 118.1 eff DPS when all hit (+69% on the Water Bolt,
	/// 69.7); paid for with 28 mana a shot (42 a second against the Water Bolt's 35) and the spread (bolts miss at range).</para>
	/// <para>D2: the random gems and spread are rolled on the owner's client (<c>Shoot</c> runs there), the bolts are vanilla
	/// projectiles synced as usual. D1: the gem order is shuffled in a reused array.</para>
	/// </summary>
	public class BundleOfWands : CogpunkItem
	{
		public const int Damage = 15, UseTime = 40, Mana = 28, Bolts = 5, RopeCost = 10;   // 15: user-set "at least 112 dps" (2026-11-19)
		public const float Knockback = 4.5f, SpreadDegrees = 9f, AverageStaffDamage = 19f, MuzzleOffset = 44f;

		/// <summary>The seven pre-Hardmode gem staffs (the recipe, and what <see cref="ResearchPlayer"/> watches for).</summary>
		public static readonly int[] StaffItems = { ItemID.AmethystStaff, ItemID.TopazStaff, ItemID.SapphireStaff, ItemID.EmeraldStaff,
			ItemID.RubyStaff, ItemID.DiamondStaff, ItemID.AmberStaff };
		private static readonly int[] boltTypes = { ProjectileID.AmethystBolt, ProjectileID.TopazBolt, ProjectileID.SapphireBolt,
			ProjectileID.EmeraldBolt, ProjectileID.RubyBolt, ProjectileID.DiamondBolt, ProjectileID.AmberBolt };
		private static readonly float[] boltSpeeds = { 6f, 6.5f, 7.5f, 8f, 9f, 9.5f, 9f };
		private static readonly int[] staffDamage = { 15, 16, 18, 19, 21, 23, 21 };
		private static readonly float[] staffKnockback = { 3.25f, 3.5f, 4f, 4.25f, 4.75f, 5.5f, 4.75f };
		private static readonly int[] order = { 0, 1, 2, 3, 4, 5, 6 };

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.DamageType = DamageClass.Magic;
			Item.mana = Mana;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.UseSound = SoundID.Item43 with { Pitch = -0.3f };
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.shoot = ProjectileID.AmethystBolt;             // each bolt's type is picked in Shoot
			Item.shootSpeed = 8f;
			Item.knockBack = Knockback;
			Item.width = 60;
			Item.height = 24;
			Item.value = Item.sellPrice(0, 1);
			Item.rare = ItemRarityID.Green;
		}

		/// <summary>The grip (the wooden club at its left end) in the hand.</summary>
		public override Vector2? HoldoutOffset() => new Vector2(-12f, 2f);

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 dir = velocity.SafeNormalize(new Vector2(player.direction, 0f));
			Vector2 muzzle = dir * MuzzleOffset;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;                             // from the gem tips (not through a wall)
			}
			for (int i = order.Length - 1; i > 0; i--) {         // five of the seven, never the same gem twice in a burst
				int j = Main.rand.Next(i + 1);
				(order[i], order[j]) = (order[j], order[i]);
			}
			for (int k = 0; k < Bolts && k < order.Length; k++) {
				int g = order[k];
				float angle = MathHelper.ToRadians(Main.rand.NextFloat(-SpreadDegrees, SpreadDegrees));
				Vector2 v = dir.RotatedBy(angle) * boltSpeeds[g] * Main.rand.NextFloat(0.94f, 1.06f);
				int dmg = Math.Max(1, (int)Math.Round(damage * staffDamage[g] / AverageStaffDamage));
				float kb = knockback * staffKnockback[g] / Knockback;
				SafeSpawn.TryNewProjectile(source, position, v, boltTypes[g], dmg, kb, out _, player.whoAmI);
			}
			return false;
		}

		public override void AddRecipes() {
			Recipe recipe = CreateRecipe();
			foreach (int staff in StaffItems) {
				recipe.AddIngredient(staff);
			}
			recipe.AddIngredient(ItemID.Rope, RopeCost).AddTile(TileID.WorkBenches).Register();
		}
	}
}
