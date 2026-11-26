using Cogpunk.Core.Combat;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Items
{
	/// <summary>
	/// Jade Phasesaber (Sabre de Fase de Jade), the Hardmode step of the <see cref="JadePhaseblade"/> (user, 2026-11-09:
	/// "phase saber"): the phaseblade and 25 Crystal Shards at a Mythril or Orichalcum Anvil, with vanilla's numbers
	/// (decompiled 1.4.4 <c>Recipe</c>: the phaseblade + item 502 x25, tile 134; <c>Item.SetDefaults</c> 3764-3769: 48 damage,
	/// use time 16, knockback 3, 40x40, auto swing, turns with the cursor, Light Red rarity, sells for 1 gold). Full
	/// brightness and a jade light, as the phaseblade. Balance: docs/balance/weapons.csv. Art: art/gems/make_jade_art.py.
	/// </summary>
	public class JadePhasesaber : CogpunkItem
	{
		public const int Damage = 48, UseTime = 16;
		public const int CrystalCost = 25;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.DamageType = DamageClass.Melee;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.knockBack = 3f;
			Item.width = 40;
			Item.height = 40;
			Item.autoReuse = true;
			Item.useTurn = false;                           // 0.2.3: a directional swing faces the cursor (a turn mid-swing would mirror it)
			Item.UseSound = SoundID.Item15;
			Item.rare = ItemRarityID.LightRed;
			Item.value = Item.sellPrice(gold: 1);
		}

		// --- the swing (0.2.3: directional, user rule 2026-11-26: "our melee weapons for the mod must have directional swings that
		// actualy track cursor position"; Core/Combat/DirectionalSwing). The sprite measured along its diagonal from the corner the
		// game draws it from (game px at scale 1): the hilt and guard to 16, the jade blade from 16 to the tip at 54, 9 px either side with the guard
		// (JadePhasesaber.png, 40 x 40)
		public const float GripFromCorner = 6f, BladeFrom = 16f, BladeTo = 54f, BladeRadius = 9f;

		/// <summary>Vanilla's arc turned to the cursor (<see cref="DirectionalSwing"/>): the wielder turned to the cursor's side as
		/// each swing starts, the arm along the blade, the grip in the hand; the game still draws the sprite. Every side, from the
		/// synced use and aim.</summary>
		public override void UseStyle(Player player, Rectangle heldItemFrame) {
			float aim = DirectionalSwing.Aim(player);
			DirectionalSwing.PoseHeld(player, DirectionalSwing.VanillaArc(DirectionalSwing.Done(player)) + aim, GripFromCorner,
				player.GetAdjustedItemScale(Item));
			DirectionalSwing.Note(player);
		}

		/// <summary>The drawn blade's bounds (vanilla cuts grass and pots with it); the hits are <see cref="CanMeleeAttackCollideWithNPC"/>.</summary>
		public override void UseItemHitbox(Player player, ref Rectangle hitbox, ref bool noHitbox) {
			float scale = player.GetAdjustedItemScale(Item);
			if (DirectionalSwing.HeldBladeBounds(player, BladeFrom * scale, BladeTo * scale, BladeRadius * scale, out Rectangle bounds)) {
				hitbox = bounds;
			}
			else {
				noHitbox = true;
			}
		}

		/// <summary>The blade as drawn, swept from the last tick.</summary>
		public override bool? CanMeleeAttackCollideWithNPC(Rectangle meleeAttackHitbox, Player player, NPC target) {
			float scale = player.GetAdjustedItemScale(Item);
			return DirectionalSwing.HeldBladeSweepHits(player, BladeFrom * scale, BladeTo * scale, BladeRadius * scale, target.Hitbox);
		}

		public override Color? GetAlpha(Color lightColor) => Color.White;

		public override void HoldItem(Player player) {
			Lighting.AddLight(player.itemLocation + new Vector2(6f + player.velocity.X, -14f), JadePhaseblade.Light);
		}

		public override void MeleeEffects(Player player, Rectangle hitbox) {
			Lighting.AddLight(hitbox.Center.ToVector2(), JadePhaseblade.Light);
		}

		public override void AddRecipes() {
			CreateRecipe().AddIngredient<JadePhaseblade>().AddIngredient(ItemID.CrystalShard, CrystalCost).AddTile(TileID.MythrilAnvil).Register();
		}
	}
}
