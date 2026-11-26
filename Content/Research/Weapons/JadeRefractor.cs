using Cogpunk.Content.Mechanist;
using Cogpunk.Content.Mechanist.Weapons;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Weapons
{
	/// <summary>
	/// The Jade Refractor (Refrator de Jade; Mechanist), unlocked by the research node "Green Diamond" (user, 2026-11-24: "unlocks
	/// the "jade refractor" mechanist weapon crafted using the diamond cutter weapon + jade + glass. A direct upgrade for the
	/// diamond cutter that should shoot a continuous thin jade colored laser that aply jade curse and deal 50% more damage to jade
	/// petrified enemies"). The <see cref="DiamondCutter"/>'s cutter rebuilt round a jade lens in a glass refracting housing.
	/// Held down, it keeps one thin jade beam (<see cref="JadeRefractorBeam"/>) on the cursor: every
	/// <see cref="JadeRefractorBeam.HitInterval"/> ticks it cuts the first <see cref="DiamondCutterBeam.MaxTargets"/> enemies along
	/// it, ignoring <see cref="DiamondCutterBeam.ArmorIgnore"/> of their defense (the cutter's, kept: "a direct upgrade"), lays
	/// the jade curse (on an enemy's first hit and every <see cref="JadeRefractorBeam.CurseEvery"/>rd after) and deals x<see cref="PetrifiedBonus"/>
	/// to an enemy turned to jade. Each use (<see cref="UseTime"/> ticks, repeated while held) costs <see cref="Cost"/> steam, but
	/// the beam first winds up for <see cref="JadeRefractorBeam.WindUpTicks"/> ticks (0.2.2, user 2026-11-26: "jade refractor is to
	/// instant, add a 1 second wind up animation before the laser comes out (no steam cost for the wind up)"), and its uses
	/// cost nothing (<see cref="SteamCostFor"/>).
	/// <para>Recipe (the amounts my calls): the Diamond Cutter, <see cref="JadeCost"/> Jade and <see cref="GlassCost"/> Glass at
	/// an anvil, locked until the node is researched (<see cref="ResearchRecipes"/>). Balance (D3; docs/balance/weapons.csv):
	/// T4 (after Jadey, whose manual teaches it). A far-range Mechanist weapon (user, 2026-11-24: "mechanist weapons should be
	/// balanced differently depending if it is a far ranged weapon or a close quarter one"; SKILL D3 rule 10): 10-25% under the
	/// tier's melee anchor (the Night's Edge, 99.8 eff DPS), the reach being its safety. Nerfed the same day (user: "kinda
	/// strong ... it has to still be one of the strongest pre-hardmode mechanist high range weapons"): <see cref="Damage"/>
	/// six times a second at 12% crit is 87.4, -12.4% (15 a hit before: 100.8), the curse every 3rd hit (every 2nd before);
	/// still the strongest far-range Mechanist weapon before Hardmode on one target, and the only one cutting three. D2: the
	/// owner aims and pays; the beam is the owner's projectile (its aim synced); every client draws it. Art:
	/// art/mechanist/make_jade_refractor_art.py.</para>
	/// </summary>
	public class JadeRefractor : MechanistWeapon
	{
		public const int Cost = 1, Damage = 16, UseTime = 12;       // 15, 13 after the 2026-11-24 nerf; 2026-11-26 (user): 1 steam, +20% (15.6)
		public const int CritBonus = 8;                            // + the player's base 4% = 12% (the Diamond Cutter's)
		public const float PetrifiedBonus = 1.5f;                  // user-set: "deal 50% more damage to jade petrified enemies"
		public const int JadeCost = 10, GlassCost = 15;
		public const float Knockback = 1.5f;
		/// <summary>Where the hand holds the sprite (game px in the 64x32 texture: the art's grip, (7, 10) at 1x), and the lens's
		/// point from there (the art's TIP, (31, 7)), in the gun's own frame (x along the barrel, y down; flipped when aiming
		/// left). art/mechanist/make_jade_refractor_art.py.</summary>
		public static readonly Vector2 GripOrigin = new(15f, 21f);
		public static readonly Vector2 MuzzleOffset = new(48f, -6f);

		/// <summary>The lens's point in the world for a hand at <paramref name="hand"/> aiming along the unit <paramref name="dir"/>.</summary>
		public static Vector2 Muzzle(Vector2 hand, Vector2 dir) {
			float side = dir.X < 0f ? -MuzzleOffset.Y : MuzzleOffset.Y;          // the sprite is flipped vertically aiming left
			Vector2 normal = new(-dir.Y, dir.X);
			return hand + dir * MuzzleOffset.X + normal * side;
		}

		public override int SteamCost => Cost;

		/// <summary>The wind-up is free (user, 2026-11-26, 0.2.2: "add a 1 second wind up animation before the laser comes out (no
		/// steam cost for the wind up)"): the uses before the beam is out cost nothing (<see cref="JadeRefractorBeam.WindingUp"/>).</summary>
		public override int SteamCostFor(Player player) => JadeRefractorBeam.WindingUp(player) ? 0 : Cost;

		/// <summary>The owner: a wind-up only starts (or goes on) when the tank could pay the shots after it: no tank, the hint;
		/// too little steam, the overheat (as before the wind-up, when the first use paid).</summary>
		protected override bool CanUseMechanist(Player player) {
			if (player.whoAmI != Main.myPlayer || !JadeRefractorBeam.WindingUp(player)) {
				return true;
			}
			return player.GetModPlayer<SteamPlayer>().CanPayAttack(ApplyPrefix(Cost, PrefixSteamMultiplier));
		}

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(DiamondCutterBeam.MaxTargets,
			(int)System.Math.Round(DiamondCutterBeam.ArmorIgnore * 100f), (int)System.Math.Round((PetrifiedBonus - 1f) * 100f));

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = CritBonus;
			Item.knockBack = Knockback;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.channel = true;
			Item.noMelee = true;
			Item.noUseGraphic = true;                              // the beam draws the refractor in the hand
			Item.shoot = ModContent.ProjectileType<JadeRefractorBeam>();
			Item.shootSpeed = 1f;                                  // a direction only
			Item.width = 64;
			Item.height = 32;
			Item.value = Item.sellPrice(gold: 4);
			Item.rare = ItemRarityID.Orange;
		}

		/// <summary>The owner: the beam the first use lights; the uses after it only pay its steam (one beam a player).</summary>
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			if (player.ownedProjectileCounts[type] > 0) {
				return false;
			}
			Vector2 dir = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			SafeSpawn.TryNewProjectile(source, player.MountedCenter, dir, type, damage, knockback, out _, player.whoAmI);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<DiamondCutter>()
				.AddIngredient<Gems.Items.Jade>(JadeCost)
				.AddIngredient(ItemID.Glass, GlassCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
