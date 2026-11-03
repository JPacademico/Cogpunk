using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// Tar Whip (user-set 2026-11-03: "a tar whip crafted using the obsidian whip + 4 condensed tar, slightly better than the
	/// obsidian whip"). Vanilla has no Obsidian whip (1.4.4 or the 1.4.5 wiki), so it is crafted from the Spinal Tap, the
	/// bone whip of the same tier (post-Skeletron, like Tar Tyrant's T3) and the one that fits a tar-soaked spine: a whip of
	/// tar-stained vertebrae with a tyrant's fang for a tip (<see cref="TarWhipProjectile"/>). Slightly better than the
	/// Spinal Tap (decompiled 1.4.4 <c>Item.SetDefaults</c> case 5074: <c>DefaultToWhip(952, 27, 2f, 5f)</c>; its whip:
	/// range x0.95, -10% per extra enemy, +7 tag damage): <see cref="Damage"/> damage, range x1, the same tag
	/// (<see cref="TarWhipDebuff"/>) and every lash coats the enemy in the Tar Plague for
	/// <see cref="TarWhipProjectile.PlagueTicks"/> ticks (the Tyrant set adds 1.5 s, <see cref="TarPlague.InflictOn"/>).
	/// Set up like ExampleMod 1.4.4's <c>ExampleWhip</c> (DefaultToWhip, melee prefixes). Balance: docs/balance/weapons.csv.
	/// </summary>
	public class TarWhip : CogpunkItem
	{
		public const int Damage = 29;
		public const float Knockback = 2.5f;
		public const float ShootSpeed = 5f;             // the Spinal Tap's

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(TarWhipDebuff.TagDamage, TarWhipProjectile.PlagueTicks / 60f);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToWhip(ModContent.ProjectileType<TarWhipProjectile>(), Damage, Knockback, ShootSpeed);
			Item.width = 32;
			Item.height = 32;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Orange;             // Condensed Tar's (Tar Tyrant, T3)
		}

		// Whips take melee prefixes (ExampleMod 1.4.4 ExampleWhip).
		public override bool MeleePrefix() => true;

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.BoneWhip)                // the Spinal Tap
				.AddIngredient<CondensedTar>(4)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
