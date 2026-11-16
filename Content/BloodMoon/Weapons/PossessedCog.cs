using Cogpunk.Content.BloodMoon.Projectiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.BloodMoon.Weapons
{
	/// <summary>
	/// Possessed Cog (Engrenagem Possuída), the Mechromancer's drop (user-set 2026-11-16: "a yoyo weapon that pierces instead
	/// of bouncing off enemies dealing moderate continuous damage"): a brass cog with a soul's eye glaring from its hub, on a
	/// string. Thrown and steered like any yoyo (vanilla's yoyo AI, ExampleMod 1.4.4's ExampleYoyo), but its spinning cog
	/// grinds straight through enemies instead of being knocked back off them: it keeps cutting every enemy it overlaps,
	/// each at most once every <see cref="PossessedCogYoyo.HitCooldown"/> ticks (<see cref="PossessedCogYoyo"/>).
	/// <para>Balance (D3; docs/balance/weapons.csv; T3, after Skeletron like its dropper): anchor the Valor, the Dungeon's yoyo
	/// (terraria.wiki.gg 1.4.4: 28 damage, 3.85 knockback, 11 s, 14.06 tiles; on one target it lands a hit every 12.8 ticks
	/// in a replay of the decompiled bounce, 136 effective DPS); <see cref="Damage"/> every 8 ticks is 133 (-3%) on one
	/// target, with the trade of a weaker knockback and a shorter string, and it cuts a crowd at once. Every yoyo's 25-tick
	/// use. Its base lends nothing to the Combinator but its crit and reach (<c>CombinatorTraits.NoPassives</c>): its one
	/// trick is its own projectile's, kept whenever it is the augment.</para>
	/// <para>Art: art/bloodmoon/make_possessed_cog_art.py.</para>
	/// </summary>
	public class PossessedCog : CogpunkItem
	{
		public const int Damage = 17;
		public const float Knockback = 2f;                       // a weak push: it stays in the enemy it grinds
		public const int UseTime = 25;                           // every vanilla yoyo's (ExampleMod 1.4.4)
		public const float ShootSpeed = 16f;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
			ItemID.Sets.Yoyo[Type] = true;                        // vanilla's yoyo set: gamepad range, the Combinator's yoyo rules
			ItemID.Sets.GamepadExtraRange[Type] = 12;             // between the Valor's 10 and the Yelets' 13 (ExampleMod's notes)
			ItemID.Sets.GamepadSmartQuickReach[Type] = true;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.noMelee = true;
			Item.noUseGraphic = true;
			Item.UseSound = SoundID.Item1;
			Item.damage = Damage;
			Item.DamageType = DamageClass.MeleeNoSpeed;
			Item.knockBack = Knockback;
			Item.channel = true;
			Item.rare = ItemRarityID.Green;
			Item.value = Item.sellPrice(gold: 1, silver: 75);     // the Valor's
			Item.shoot = ModContent.ProjectileType<PossessedCogYoyo>();
			Item.shootSpeed = ShootSpeed;
		}
	}
}
