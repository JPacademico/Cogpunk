using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Minions
{
	/// <summary>
	/// Alarm Head (user-set 2026-10-28), the Annoy-o-tron's beacon head (<see cref="AlarmHeadDrop"/>: 1 in 10, 1 in 100
	/// once one has dropped in the world): a summon item for an <see cref="AlarmoboMinion"/>, one minion slot. The little
	/// alarm box follows its owner and never fights; every player within <see cref="NPCs.AnnoyOTron.AlarmRange"/> of it moves
	/// <see cref="AlarmPlayer.MoveSpeedPerAlarm"/>% faster and attacks <see cref="AlarmPlayer.AttackSpeedPerAlarm"/>% faster,
	/// stacking with every Alarmobô in range (<see cref="AlarmPlayer"/>). Set up like the Mice-bot (ExampleMod 1.4.4
	/// <c>ExampleSimpleMinionItem</c>), spawned through SafeSpawn (D0). No damage: it is pure support.
	/// Balance: docs/balance/weapons.csv (anchor: the Bewitching Table's +1 minion slot, an equal-tier support pick).
	/// </summary>
	public class AlarmHead : CogpunkItem
	{
		public const int ManaCost = 10;

		/// <summary>World flag: an Alarm Head has dropped in this world (the drop falls to 1 in 100).</summary>
		public static int DroppedFlag { get; private set; } = -1;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(AlarmPlayer.MoveSpeedPerAlarm, AlarmPlayer.AttackSpeedPerAlarm,
			(int)(NPCs.AnnoyOTron.AlarmRange / 16f));

		public override void Load() {
			DroppedFlag = WorldFlagSystem.Register("DroppedAlarmHead");
		}

		public override void SetStaticDefaults() {
			ItemID.Sets.GamepadWholeScreenUseRange[Type] = true;
			ItemID.Sets.LockOnIgnoresCollision[Type] = true;
			ItemID.Sets.StaffMinionSlotsRequired[Type] = AlarmoboMinion.MinionSlots;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 0;
			Item.knockBack = 0f;
			Item.mana = ManaCost;
			Item.DamageType = DamageClass.Summon;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = 36;
			Item.useAnimation = 36;
			Item.UseSound = SoundID.Item44;
			Item.noMelee = true;
			Item.buffType = ModContent.BuffType<AlarmoboBuff>();
			Item.shoot = ModContent.ProjectileType<AlarmoboMinion>();
			Item.width = 32;
			Item.height = 32;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Green;
		}

		public override void ModifyShootStats(Player player, ref Vector2 position, ref Vector2 velocity, ref int type, ref int damage, ref float knockback) {
			position = Main.MouseWorld;                  // set down at the cursor, within reach
			player.LimitPointToPlayerReachableArea(ref position);
			velocity = Vector2.Zero;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			player.AddBuff(Item.buffType, 2);
			SafeSpawn.TryNewProjectile(source, position, velocity, type, 0, 0f, out _, player.whoAmI);
			return false;
		}
	}
}
