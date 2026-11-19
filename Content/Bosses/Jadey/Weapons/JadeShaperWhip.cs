using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// Jade-shaper Whip (Chicote da Molda-Jade), one of Jadey's three weapons (user-set 2026-11-17: "her whip weapon, it should
	/// deal bonus damage (50%) to jade petrified enemies, and be slightly better than all pre hardmode whips in basic
	/// attributes"): her rope dart on a red cord, a gilt handle (<see cref="JadeShaperWhipProjectile"/>). Every lash deals
	/// x<see cref="JadeShaperWhipProjectile.PetrifiedBonus"/> to an enemy turned to jade (the jade curse,
	/// <see cref="Gems.JadeCurseNPC.Petrified"/>) and tags (<see cref="JadeShaperWhipDebuff"/>).
	/// <para>Slightly better than every pre-Hardmode whip (decompiled 1.4.4 <c>Item.SetDefaults</c>: Leather Whip
	/// <c>DefaultToWhip(841, 14, 1f, 4f)</c>, range x0.75, tag +4, -50% a further enemy; Snapthorn <c>(914, 18, 1.5f, 4f)</c>, x1,
	/// tag +6, -40%; Spinal Tap <c>(952, 27, 2f, 5f)</c>, x0.95, tag +7, -10%; Cogpunk's own Tar Whip 29, 2.5, 5, x1, +7, -10%; the
	/// Firecracker and the Cool Whip are Hardmode, Light Red): <see cref="Damage"/> damage, <see cref="Knockback"/> knockback, speed
	/// <see cref="ShootSpeed"/> at range x<see cref="JadeShaperWhipProjectile.RangeMultiplier"/>, tag
	/// +<see cref="JadeShaperWhipDebuff.TagDamage"/>, -<c>8%</c> a further enemy, every whip's 30-tick swing. Set up like
	/// ExampleMod 1.4.4's <c>ExampleWhip</c>. Balance: docs/balance/weapons.csv. Art: art/bosses/jadey/make_jadey_loot_art.py.</para>
	/// </summary>
	public class JadeShaperWhip : CogpunkItem
	{
		public const int Damage = 31;
		public const float Knockback = 2.75f;
		public const float ShootSpeed = 5f;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(JadeShaperWhipDebuff.TagDamage,
			(int)System.Math.Round((JadeShaperWhipProjectile.PetrifiedBonus - 1f) * 100f));

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToWhip(ModContent.ProjectileType<JadeShaperWhipProjectile>(), Damage, Knockback, ShootSpeed);
			Item.width = 36;
			Item.height = 36;
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = ItemRarityID.Orange;              // Coghaven's tier (T4), as Jadey's other drops
		}

		public override bool MeleePrefix() => true;
	}
}
