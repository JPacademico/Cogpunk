using System.Collections.Generic;
using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Weapons
{
	/// <summary>
	/// The Sheriff's Revolver (user-set 2026-11-04), found in Old Brass Town's locked Brass Strongbox: 33 damage with a Musket
	/// Ball (<see cref="Damage"/> + the bullet's 7), <see cref="UseTime"/> use time, 6% crit (vanilla's 4% + <c>Item.crit</c> 2). A polished brass magnum (redrawn
	/// 2026-11-05, user: "a polished brass powerful magnum revolver"); the left click is precise, within
	/// <see cref="AimSpread"/> degree of the aim (user-set 2026-11-05). It fires a fast brass bullet
	/// (<see cref="SheriffsBullet"/>) that bounces once off a wall (never off an enemy since 2026-11-19), and always bounces
	/// towards an enemy when one is in sight.
	/// <list type="bullet">
	/// <item><b>Six chambers</b>: after <see cref="SheriffsRevolverPlayer.Chambers"/> shots it must reload for
	/// <see cref="SheriffsRevolverPlayer.ReloadTicks"/> ticks (1.5 s), the user's price for a weapon stronger than its tier.
	/// The rounds left are the player's, not the gun's (<see cref="SheriffsRevolverPlayer"/>): swapping weapons never
	/// refills it, and a reload keeps running while the gun is put away.</item>
	/// <item><b>Right click</b>: fans every round left in the cylinder, one every <see cref="BurstInterval"/> ticks (all six
	/// inside a third of a second: user, 2026-11-05, "the burst should be faster, 0.33 seconds"), for <see cref="BurstSteamCost"/> steam (a steam skill, <see cref="ISteamSkill"/>: a Mechanist
	/// weapon's rules, and the Spring Gloves count it); the reload follows at once.</item>
	/// </list>
	/// <b>Bullets</b> (user, 2026-11-09: "the sheriff revolver should use ammo to be affected by the new law hat"; it loaded
	/// none until then): every shot takes a bullet (<c>useAmmo = AmmoID.Bullet</c>, vanilla's ammo rules), and whatever the
	/// bullet it fires the magnum's own ricocheting round with the bullet's damage and knockback added (a special bullet's
	/// own effects don't carry over). The weapon's damage was the user's 33 with no ammo; it is <see cref="Damage"/> now, so a
	/// Musket Ball (+7, the anchor's own) gives the same 33 and better bullets more, as vanilla's guns. D2: only the owner
	/// shoots; the rounds and the reload are the owner's (nobody else needs them). Balance: docs/balance/weapons.csv.
	/// </summary>
	public class SheriffsRevolver : CogpunkItem, ISteamSkill
	{
		public const int Damage = 26, UseTime = 23;                // user-set 33 with no ammo = 26 + a Musket Ball's 7 (2026-11-09)
		public const int BurstSteamCost = 20;                       // user-set
		public const int BurstInterval = 4;                         // six shots span 20 ticks: "0.33 seconds of burst" (user-set 2026-11-05)
		public const float AimSpread = 1f;                          // degrees either way, the left click (user-set 2026-11-05)
		public const float ShotSpeed = 16f;                         // px per update: 32 px/tick (the bullet updates twice a tick)
		public const float BurstSpread = 0.05f;                     // radians each way: a fanned hammer isn't a rifle
		public const float MuzzleDistance = 34f;                    // the bore of the 44 px magnum (52 px until 2026-11-05b)

		public int SkillSteamCost => BurstSteamCost;

		/// <summary>The alt use is the burst: its shots count its steam for the Spring Gloves.</summary>
		public int SteamForUse(Player player) => player.altFunctionUse != 0 ? player.GetModPlayer<SteamPlayer>().GetCost(BurstSteamCost) : 0;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SheriffsRevolverPlayer.Chambers, SheriffsRevolverPlayer.ReloadTicks / 60f,
			BurstSteamCost);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = 2;                                          // + the player's base 4% = 6% (user-set)
			Item.knockBack = 3.5f;
			Item.DamageType = DamageClass.Ranged;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<SheriffsBullet>();
			Item.shootSpeed = ShotSpeed;
			Item.useAmmo = AmmoID.Bullet;                           // 2026-11-09 (user): bullets, so the Law Hat counts it
			Item.UseSound = SoundID.Item41 with { Pitch = -0.15f };
			Item.width = 44;                                // 2026-11-05b (user: "decrease a bit the size... on the player hand")
			Item.height = 24;
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = ItemRarityID.Orange;
		}

		public override bool AltFunctionUse(Player player) => true;

		public override bool CanUseItem(Player player) {
			SheriffsRevolverPlayer cylinder = player.GetModPlayer<SheriffsRevolverPlayer>();
			if (cylinder.Reloading || cylinder.Rounds <= 0) {
				return false;
			}
			if (player.altFunctionUse == 2 && player.whoAmI == Main.myPlayer) {
				return player.GetModPlayer<SteamPlayer>().CanPayAttack(BurstSteamCost);   // the hint or the overheat when it can't
			}
			return true;
		}

		// The burst: every round left, one every BurstInterval ticks, in one use (vanilla fires a use's shots each time its
		// useTime runs out within its useAnimation, decompiled Player.ItemCheck_OwnerOnlyCode).
		public override float UseTimeMultiplier(Player player) => player.altFunctionUse == 2 ? BurstInterval / (float)UseTime : 1f;

		public override float UseAnimationMultiplier(Player player) {
			if (player.altFunctionUse != 2) {
				return 1f;
			}
			int rounds = System.Math.Max(1, player.GetModPlayer<SheriffsRevolverPlayer>().Rounds);
			return BurstInterval * rounds / (float)UseTime;
		}

		public override Vector2? HoldoutOffset() => new Vector2(-4f, 0f);

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			SheriffsRevolverPlayer cylinder = player.GetModPlayer<SheriffsRevolverPlayer>();
			if (cylinder.Rounds <= 0) {
				return false;                                       // the cylinder ran dry mid-burst
			}
			bool burst = player.altFunctionUse == 2;
			type = ModContent.ProjectileType<SheriffsBullet>();     // any bullet: the magnum's own round, the bullet's damage added
			if (burst && player.ItemUsesThisAnimation == 1) {
				player.GetModPlayer<SteamPlayer>().Spend(BurstSteamCost);   // CanUseItem checked it as the burst began
			}
			Vector2 direction = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 muzzle = direction * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
			if (!burst) {
				velocity = velocity.RotatedBy(Main.rand.NextFloat(-1f, 1f) * MathHelper.ToRadians(AimSpread));   // owner-only: synced with the shot
			}
			if (burst) {
				velocity = velocity.RotatedByRandom(BurstSpread);
				if (player.ItemUsesThisAnimation > 1) {
					Terraria.Audio.SoundEngine.PlaySound(SoundID.Item41 with { Pitch = 0.1f, MaxInstances = 4 }, position);
				}
			}
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			cylinder.Fired();
			return false;
		}

		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			SteamSkillTooltip.AddNoTankLine(Mod, tooltips, BurstSteamCost);
			SheriffsRevolverPlayer cylinder = Main.LocalPlayer.GetModPlayer<SheriffsRevolverPlayer>();
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Knockback");
			TooltipLine rounds = new(Mod, "Rounds", Language.GetTextValue("Mods.Cogpunk.Items.SheriffsRevolver.Rounds", cylinder.Rounds, SheriffsRevolverPlayer.Chambers));
			if (index >= 0) {
				tooltips.Insert(index + 1, rounds);
			}
			else {
				tooltips.Add(rounds);
			}
		}
	}
}
