using System.Collections.Generic;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Minions
{
	/// <summary>
	/// Summon weapon: a wound-up clockwork mouse that becomes a <see cref="MiceBotMinion"/> (half a minion slot, so a
	/// summoner fields two per slot). Set up like ExampleMod 1.4.4's <c>ExampleSimpleMinionItem</c>, except that the minion
	/// is spawned through SafeSpawn (D0) and gets its <c>originalDamage</c> here, as vanilla's own staffs do (decompiled
	/// <c>Player.ItemCheck_Shoot</c>). Minions crit at the usual 4% (see <see cref="MiceBotMinion.ModifyHitNPC"/>), and since
	/// summon weapons hide the crit line, <see cref="ModifyTooltips"/> adds it back.
	/// Balance: docs/balance/weapons.csv (anchor: Finch Staff).
	/// </summary>
	public class MiceBot : CogpunkItem
	{
		public override void SetStaticDefaults() {
			ItemID.Sets.GamepadWholeScreenUseRange[Type] = true;
			ItemID.Sets.LockOnIgnoresCollision[Type] = true;
			ItemID.Sets.StaffMinionSlotsRequired[Type] = MiceBotMinion.MinionSlots;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 8;
			Item.knockBack = 0f;
			Item.mana = 10;
			Item.DamageType = DamageClass.Summon;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = 36;
			Item.useAnimation = 36;
			Item.UseSound = SoundID.Item44;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.buffType = ModContent.BuffType<MiceBotBuff>();
			Item.shoot = ModContent.ProjectileType<MiceBotMinion>();
			Item.width = 32;
			Item.height = 32;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Blue;
		}

		public override void ModifyShootStats(Player player, ref Vector2 position, ref Vector2 velocity, ref int type, ref int damage, ref float knockback) {
			position = Main.MouseWorld;                  // released at the cursor, within reach
			player.LimitPointToPlayerReachableArea(ref position);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			player.AddBuff(Item.buffType, 2);
			if (SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out Projectile mouse, player.whoAmI)) {
				mouse.originalDamage = Item.damage;
			}
			return false;
		}

		// Summon damage hides the vanilla "N% critical strike chance" line (SummonDamageClass.ShowStatTooltipLine), but this
		// minion does crit; show the line after the damage line, worded and computed like vanilla's own (Lang.tip[41]).
		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Damage");
			if (index < 0) {
				return;
			}
			int crit = Main.LocalPlayer.GetWeaponCrit(Item);
			tooltips.Insert(index + 1, new TooltipLine(Mod, "CritChance", crit + Lang.tip[41].Value));
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>(10)                          // 8 -> 10, x1.2 rounded (user, 2026-11-26)
				.AddRecipeGroup(VanillaRecipeGroups.CopperBar, 6)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
