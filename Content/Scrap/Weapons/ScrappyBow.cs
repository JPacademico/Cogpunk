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
	/// A bow welded from rusted plate and strung with cobweb. Each use looses <see cref="MinArrows"/>-<see cref="MaxArrows"/>
	/// arrows at once (rolled by the owner, uniform) and consumes one arrow; the first flies true, the rest stray up to
	/// <see cref="SpreadDegrees"/> degrees and lose a little speed. Every arrow is the ammo's own projectile, with its
	/// damage and effects. Balance: docs/balance/weapons.csv (anchor: Platinum Bow; flagged over budget, numbers set by
	/// the user).
	/// </summary>
	public class ScrappyBow : CogpunkItem
	{
		public const int MinArrows = 1;
		public const int MaxArrows = 5;
		public const float SpreadDegrees = 5f;
		public const float ArrowSpeed = 7f;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MinArrows, MaxArrows);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToBow(30, ArrowSpeed);           // ranged, Arrow ammo, use style Shoot, Item5 sound, no auto-reuse
			Item.damage = 20;
			Item.crit = 0;                               // + the player's base 4% = 4%
			Item.knockBack = 1f;
			Item.width = 16;
			Item.height = 32;
			Item.value = Item.sellPrice(silver: 30);
			Item.rare = ItemRarityID.Blue;
		}

		// One volley per use, spawned through SafeSpawn (D0); vanilla already took one arrow from the ammo slots.
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			int arrows = Main.rand.Next(MinArrows, MaxArrows + 1);
			for (int i = 0; i < arrows; i++) {
				Vector2 shot = velocity;
				if (i > 0) {
					shot = velocity.RotatedByRandom(MathHelper.ToRadians(SpreadDegrees)) * Main.rand.NextFloat(0.9f, 1f);
				}
				if (!SafeSpawn.TryNewProjectile(source, position, shot, type, damage, knockback, out _, player.whoAmI)) {
					break;                               // projectile array nearly full: the rest of the volley is dropped
				}
			}
			return false;
		}

		public override Vector2? HoldoutOffset() {
			return new Vector2(-2f, 0f);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.Cobweb, 10)
				.AddIngredient<RustedCog>(2)
				.AddIngredient<RustedMetal>(6)                         // 5 -> 6, x1.2 (user, 2026-11-26; the 2 cogs stay: 2.4 rounds to 2)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
