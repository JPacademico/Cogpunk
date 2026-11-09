using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Weapons
{
	/// <summary>
	/// Cursed Lantern (Lanterna Amaldiçoada), a mage weapon the Cursed Conductor drops (user-set 2026-11-06: "a new mage
	/// weapon called cursed lantern that should fire slow moving homing soul fire projectiles; the projectiles should only
	/// home in on the closest enemy inside a 10 tile area around the projectile and stay floating slowly if there's no enemy
	/// close"). Held out in the hand toward the cursor, as vanilla's spell tomes are (user, 2026-11-09: "the lantern mage
	/// weapon should not be used on the player head! the player should use on the hand (smaller lantern) like default
	/// terraria books are used"; it was held up over the head, and redrawn smaller), it lets a soul go at the cursor from
	/// its glass: a <see cref="SoulFire"/>.
	/// <para>The Conductor is fought at the Wall of Flesh's tier (T5 in docs/balance; its anchor the Laser Rifle: 29 damage, 12
	/// use time, 8 mana): <see cref="Damage"/> damage, <see cref="UseTime"/> use time, <see cref="Mana"/> mana, the base 4%
	/// crit. Balance: docs/balance/weapons.csv. Art: art/bosses/cursedconductor/make_cursed_lantern_art.py.</para>
	/// </summary>
	public class CursedLantern : CogpunkItem
	{
		public const int Damage = 40, UseTime = 18, Mana = 10;
		public const float SoulSpeed = 3.5f;                // "slow moving"
		private const float GlassReach = 18f;               // from the hand's pivot out along the aim to the lantern's glass
		private static readonly Vector2 Holdout = new(-2f, 0f);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.knockBack = 3f;
			Item.DamageType = DamageClass.Magic;
			Item.mana = Mana;
			Item.useStyle = ItemUseStyleID.Shoot;          // held out toward the cursor, like vanilla's spell tomes
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.UseSound = SoundID.Item8 with { Pitch = 0.3f, Volume = 0.7f };
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<SoulFire>();
			Item.shootSpeed = SoulSpeed;
			Item.width = 20;
			Item.height = 28;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.LightRed;              // the Wall of Flesh's drops' rarity
		}

		public override Vector2? HoldoutOffset() => Holdout;

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 lantern = position + velocity.SafeNormalize(Vector2.UnitX * player.direction) * GlassReach;
			if (Collision.CanHit(position, 0, 0, lantern, 0, 0)) {
				position = lantern;                         // the soul leaves the lantern's glass, unless that is inside a wall
			}
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			return false;
		}
	}
}
