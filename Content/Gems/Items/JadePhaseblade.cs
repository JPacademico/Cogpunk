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
