using Cogpunk.Content.Bosses.Jadey.Buffs;
using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Safety;
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
	/// Incense Mace (Maça de Incenso), one of Jadey's four weapons (user-set 2026-11-18: "a mechanist class (5 steam) mace like
	/// weapon that deals great damage (has to be slightly better than any pre hardmode mace) and on the right click it should
	/// emit a quick incense aura effect around the player (25 tile area) that buffs allies that were on the area (+10% damage
	/// and attackspeed for 35 seconds) at the cost of 20 steam (30 seconds cooldown). the base art of the weapon is on the image
	/// prompt"): a gilt censer, pierced with crosses, on a gilt chain from a turned oak handle (the user's art,
	/// art/bosses/jadey/make_incense_mace_art.py).
	/// <list type="bullet">
	/// <item><b>Left click</b>: a flail (<see cref="IncenseMaceHead"/>, vanilla's flail AI as ExampleMod 1.4.4's
	/// <c>ExampleFlail</c>: hold to spin it, release to throw it; thrown into an enemy it hits for double, as vanilla's flails,
	/// <c>ItemID.Sets.ToolTipDamageMultiplier</c> 2). <see cref="SwingSteam"/> steam a use.</item>
	/// <item><b>Right click</b>: <see cref="IncenseAura"/> rolls out from the wielder: every ally within
	/// <see cref="AuraRadiusTiles"/> tiles of it as it reaches them (the wielder too) is blessed (<see cref="IncenseBlessing"/>:
	/// +<see cref="DamageBonus"/> damage and attack speed for <see cref="BlessingTicks"/> ticks); then the censer needs
	/// <see cref="CooldownTicks"/> ticks to rekindle (<see cref="IncenseBurntOut"/>), and the right click waits for it.
	/// <see cref="AuraSteam"/> steam.</item>
	/// </list>
	/// <para>Balance (D3; docs/balance/weapons.csv; T4, Jadey's drop): anchor the Sunfury, the strongest pre-Hardmode flail
	/// (decompiled 1.4.4 <c>Item.SetDefaults</c> 220: 32 damage, 45 use, 6.75 knockback, 7 crit; the Blue Moon 27, the Meatball
	/// 17, the Ball O' Hurt 15, the Mace 9): <see cref="Damage"/> every <see cref="UseTime"/> ticks with the base crit, +11% on
	/// it ("slightly better"), paid in steam. My calls: the damage, knockback 7, the flail's speeds (the Sunfury's, in
	/// <see cref="IncenseMaceHead"/>), "25 tile area" read as 25 tiles from the wielder, allies = everyone not an enemy in PvP.</para>
	/// <para>D2: the owner pays and throws (MechanistWeapon, <c>Shoot</c>); the aura is an ordinary synced projectile and each
	/// client blesses its own player if that player is in reach when the aura arrives (<see cref="IncenseAura"/>), so no packet
	/// is needed and a buff is never set on someone else's player. D0: spawns through SafeSpawn; one head out at a time.</para>
	/// </summary>
	public class IncenseMace : MechanistWeapon
	{
		public const int Damage = 38;                            // my call: "slightly better than any pre-hardmode mace"
		public const int UseTime = 45;                           // vanilla's flails'
		public const float Knockback = 7f;
		public const float ShootSpeed = 12f;                     // vanilla's flails'
		public const int SwingSteam = 5, AuraSteam = 20;         // user-set
		public const int BlessingTicks = 35 * 60;                // user-set: 35 s
		public const int CooldownTicks = 30 * 60;                // user-set: 30 s
		public const float AuraRadiusTiles = 25f;                // user-set "25 tile area" (my reading: within 25 tiles)
		public const float AuraRadius = AuraRadiusTiles * 16f;
		public const float DamageBonus = 0.10f, SpeedBonus = 0.10f;   // user-set

		public override int SteamCost => SwingSteam;

		public override int SteamCostFor(Player player) => player.altFunctionUse == 2 ? AuraSteam : SwingSteam;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs((int)AuraRadiusTiles, (int)System.Math.Round(DamageBonus * 100f),
			BlessingTicks / 60, CooldownTicks / 60, AuraSteam);

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			ItemID.Sets.ToolTipDamageMultiplier[Type] = 2f;      // thrown into an enemy the head hits for double (vanilla's flails)
		}

		public override void SetDefaults() {
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.damage = Damage;
			Item.crit = 0;                                       // the player's base 4%
			Item.knockBack = Knockback;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.channel = true;                                 // the flail spins while the button is held
			Item.noMelee = true;
			Item.noUseGraphic = true;                            // the head and its chain are the projectile's
			Item.shoot = ModContent.ProjectileType<IncenseMaceHead>();
			Item.shootSpeed = ShootSpeed;
			Item.UseSound = SoundID.Item1;
			Item.width = 30;
			Item.height = 30;
			Item.rare = ItemRarityID.Orange;
			Item.value = Item.sellPrice(gold: 2, silver: 50);
		}

		public override bool AltFunctionUse(Player player) => true;

		/// <summary>The right click: only once the censer has rekindled. The left: one head out at a time.</summary>
		protected override bool CanUseMechanist(Player player) {
			if (player.altFunctionUse == 2) {
				return !player.HasBuff<IncenseBurntOut>();
			}
			return player.ownedProjectileCounts[Item.shoot] < 1;
		}

		/// <summary>The owner: the right click rolls out the aura (and puts out the censer); the left throws the head.</summary>
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			if (player.altFunctionUse == 2) {
				player.AddBuff(ModContent.BuffType<IncenseBurntOut>(), CooldownTicks);
				if (!SafeSpawn.TryNewProjectile(source, player.Center, Vector2.Zero, ModContent.ProjectileType<IncenseAura>(), 0, 0f, out _, player.whoAmI)) {
					IncenseAura.Bless(player);                   // no room for the aura: the wielder still gets theirs
				}
				SoundEngine.PlaySound(SoundID.Item44 with { Pitch = -0.2f, Volume = 0.7f }, player.Center);
				return false;
			}
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			return false;
		}
	}
}
