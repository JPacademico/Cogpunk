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
			Item.useTurn = true;
			Item.UseSound = SoundID.Item15;
			Item.rare = ItemRarityID.LightRed;
			Item.value = Item.sellPrice(gold: 1);
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
