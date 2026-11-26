using Cogpunk.Core.Combat;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Items
{
	/// <summary>
	/// Jade Phaseblade (Lâmina de Fase de Jade), the phaseblade of the default gem crafts (user, 2026-11-09: "phase saber";
	/// vanilla's gems make a Phaseblade, upgraded to a Phasesaber in Hardmode, so jade makes both: <see cref="JadePhasesaber"/>).
	/// 15 Meteorite Bars and 10 <see cref="Jade"/> at an anvil, with vanilla's numbers (decompiled 1.4.4 <c>Recipe</c>: item
	/// 117 x15 + 10 gems, tile 16; <c>Item.SetDefaults</c> 198-203: 26 damage, use time 18, knockback 3, 40x40, the beam's
	/// hum, Blue rarity, value 27000). Drawn at full brightness and lighting its swing, as vanilla's are
	/// (<c>Item.GetAlpha</c> returns white for them; <c>Player.ItemCheck</c> lights the item: a jade green here).
	/// Balance: docs/balance/weapons.csv. Art: art/gems/make_jade_art.py.
	/// </summary>
	public class JadePhaseblade : CogpunkItem
	{
		public const int Damage = 26, UseTime = 18;
		public const int MeteoriteCost = 15, JadeCost = 10;
		public static readonly Vector3 Light = new(0.08f, 0.5f, 0.32f);   // jade green (vanilla's emerald blade: 0.05, 0.5, 0.1)

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
			Item.UseSound = SoundID.Item15;
			Item.rare = ItemRarityID.Blue;
			Item.value = 27000;
		}

		// --- the swing (0.2.3: directional, user rule 2026-11-26: "our melee weapons for the mod must have directional swings that
		// actualy track cursor position"; Core/Combat/DirectionalSwing). The sprite measured along its diagonal from the corner the
		// game draws it from (game px at scale 1): the hilt to 16, the jade blade from 16 to the tip at 52, 4 px either side (JadePhaseblade.png, 40 x 40;
		// a little wider to hit, as vanilla's phaseblades)
		public const float GripFromCorner = 6f, BladeFrom = 16f, BladeTo = 52f, BladeRadius = 8f;

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
			Lighting.AddLight(player.itemLocation + new Vector2(6f + player.velocity.X, -14f), Light);
		}

		public override void MeleeEffects(Player player, Rectangle hitbox) {
			Lighting.AddLight(hitbox.Center.ToVector2(), Light);
		}

		public override void AddRecipes() {
			CreateRecipe().AddIngredient(ItemID.MeteoriteBar, MeteoriteCost).AddIngredient<Jade>(JadeCost).AddTile(TileID.Anvils).Register();
		}
	}
}
