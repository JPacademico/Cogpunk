using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// Firework Cannon (Canhão de Fogos), one of Jadey's three weapons (user-set 2026-11-17: "mage weapon that shoots quick
	/// firework missiles that deal small contact damage but high area damage with a chance to stun basic enemies, should also
	/// blow up dealing area damage upon hitting a wall or after traveling 22 tiles, and should consume 21 mana"): a cinnabar
	/// lacquered launch tube in gilt bands with a jade dragon at the muzzle. Each shot is a <see cref="FireworkRocket"/>:
	/// <see cref="FireworkRocket.ContactShare"/> of the damage on the enemy it strikes, then a burst of the full damage on
	/// everything within <see cref="FireworkRocket.BurstRadius"/> px (that enemy too), each enemy stunned 1 time in
	/// <see cref="FireworkRocket.StunOneIn"/> for <see cref="FireworkRocket.StunTicks"/> ticks if it can be
	/// (<see cref="Mechanist.Buffs.StunnedNPC.CanStun"/>: basic enemies only, never bosses or mini-bosses).
	/// <para>Balance (D3; docs/balance/weapons.csv; T4): anchor the Flamelash (decompiled 1.4.4 <c>Item.SetDefaults</c> 218: 32
	/// damage, 30 use, 21 mana, 6.5 knockback; Hellstone tier): <see cref="Damage"/> burst + its contact share every
	/// <see cref="UseTime"/> ticks on one target, the user's 21 mana. Art: art/bosses/jadey/make_jadey_loot_art.py.</para>
	/// </summary>
	public class FireworkCannon : CogpunkItem
	{
		public const int Damage = 30;                      // the burst's (the contact deals ContactShare of it); 28 until the user's
		                                                   // "increase the damage of the firework canon" (2026-11-17): 30 is
		                                                   // +21.8% on the anchor, inside D3's +25% with its trade-offs (31: +25.8%)
		public const int UseTime = 30;
		public const int ManaCost = 21;                    // user-set
		public const float Knockback = 4f;
		public const float ShootSpeed = 14f;               // "quick": 22 tiles in 25 ticks
		public const float MuzzleDistance = 36f;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(FireworkRocket.RangeTiles,
			100 / FireworkRocket.StunOneIn, FireworkRocket.StunTicks / 60f);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 52;
			Item.height = 24;
			Item.DamageType = DamageClass.Magic;
			Item.damage = Damage;
			Item.mana = ManaCost;
			Item.knockBack = Knockback;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.noMelee = true;
			Item.autoReuse = true;
			Item.shoot = ModContent.ProjectileType<FireworkRocket>();
			Item.shootSpeed = ShootSpeed;
			Item.UseSound = SoundID.Item61 with { Pitch = 0.35f, Volume = 0.8f };
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = ItemRarityID.Orange;
		}

		public override Vector2? HoldoutOffset() => new Vector2(-6f, 0f);

		/// <summary>From the muzzle, unless a wall stands between the hand and it (vanilla's guns do the same).</summary>
		public override void ModifyShootStats(Player player, ref Vector2 position, ref Vector2 velocity, ref int type, ref int damage, ref float knockback) {
			Vector2 muzzle = velocity.SafeNormalize(Vector2.Zero) * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
		}
	}
}
