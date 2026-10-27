using Cogpunk.Content.Bosses.TrashTr0m.Buffs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// Tetanus (Trash-Tr0m drop, melee): a long, thin, rusted needle of a lance reaching <see cref="ReachTiles"/> tiles
	/// (8.5, user-set 2026-10-27). Every attack goes where the player aims, in any direction: the lance follows the cursor
	/// while it is out, and holding the button keeps thrusting.
	/// <list type="bullet">
	/// <item><b>Left click</b>: a quick thrust (<see cref="TetanusProjectile"/>, mode <see cref="TetanusProjectile.Quick"/>)
	/// that hits on the way out and again on the way back, like the <c>Screwdriver</c>.</item>
	/// <item><b>Right click, held</b>: the lance is drawn back and charges, +<see cref="ChargeStepPercent"/>% damage per
	/// <see cref="ChargeStepTicks"/> ticks held (0.5 s), up to +<see cref="MaxChargePercent"/>%; letting go lunges it out in
	/// one piercing strike that also hits twice, going out and coming back (user-set 2026-10-27).</item>
	/// </list>
	/// Every hit gives the target <see cref="TetanusDebuff"/> (+<see cref="TetanusDebuff.DamageTakenPercent"/>% damage
	/// taken) for <see cref="DebuffTicks"/> ticks. Balance: docs/balance/weapons.csv (anchor: The Rotted Fork).
	/// </summary>
	public class Tetanus : CogpunkItem
	{
		public const int UseTime = 24;
		public const float ReachTiles = 8.5f;
		public const int ChargeStepTicks = 30;          // +20% per 0.5 s held
		public const int ChargeStepPercent = 20;
		public const int MaxChargeSteps = 5;            // +100% at 2.5 s
		public const int MaxChargePercent = ChargeStepPercent * MaxChargeSteps;
		public const int DebuffTicks = 120;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ChargeStepPercent, MaxChargePercent, TetanusDebuff.DamageTakenPercent);

		public override void SetStaticDefaults() {
			ItemID.Sets.Spears[Type] = true;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 27;
			Item.crit = 0;                               // + the player's base 4% = 4%
			Item.knockBack = 5.5f;
			Item.DamageType = DamageClass.Melee;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;                       // hold to keep thrusting, re-aimed every time
			Item.noMelee = true;                         // the lance does the hitting and plays the sounds (every client sees it)
			Item.noUseGraphic = true;
			Item.shoot = ModContent.ProjectileType<TetanusProjectile>();
			Item.shootSpeed = 1f;                        // only the direction is used
			Item.width = 56;
			Item.height = 56;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Blue;
		}

		public override bool AltFunctionUse(Player player) => true;

		// One lance at a time, like every vanilla spear.
		public override bool CanUseItem(Player player) {
			return player.ownedProjectileCounts[Item.shoot] < 1;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			float mode = player.altFunctionUse == 2 ? TetanusProjectile.Charging : TetanusProjectile.Quick;
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI, ai0: mode);
			return false;
		}
	}
}
