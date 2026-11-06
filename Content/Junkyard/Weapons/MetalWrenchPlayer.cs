using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The Metal Wrench's parry and riposte (user-set 2026-10-30), on the owning client.
	/// <list type="bullet">
	/// <item><b>Guard</b>: a right click with the wrench in hand, idle, under the same conditions vanilla checks before a
	/// right-click feature (decompiled <c>Player.ItemCheck_ManageRightClickFeatures</c>: not over the UI, no tile or NPC
	/// interaction this tick, a fresh press), and not cooling down; it costs <see cref="MetalWrench.ParrySteamCost"/> steam
	/// (user, 2026-11-04: <see cref="SteamPlayer.TryPayAttack"/>, a Mechanist weapon's rules: no tank, no parry and a hint;
	/// too little steam, an overheat), and the click is used up either way so a refusal can't repeat every tick. It lasts
	/// <see cref="MetalWrench.ParryTicks"/>; a <see cref="MetalWrenchGuard"/> shows it to everyone.</item>
	/// <item><b>Parry</b>: vanilla asks the hit player's own client before every dodgeable hit (decompiled
	/// <c>Player.Hurt</c>: <c>PlayerLoader.FreeDodge</c> only when <c>whoAmI == Main.myPlayer</c>), which is where contact
	/// and hostile projectile hits on a player are decided. A hit from an NPC or a hostile projectile during the guard is
	/// refused: a <see cref="MetalClash"/> where it struck, the riposte buff, the cooldown, and vanilla's usual hurt
	/// immunity (40 ticks, 80 with a Cross Necklace) so the same enemy can't land a second later.</item>
	/// <item><b>Riposte</b>: the next swing (<see cref="MetalWrench.UseItem"/>) carries it to its end, whether it lands or
	/// not; every NPC it hits takes x<see cref="MetalWrench.RiposteMultiplier"/>, plus the Spring Gloves' bonus for the steam
	/// the parry took (<see cref="RiposteSteam"/>); the first boss or mini-boss it hits sets off a boss clash
	/// (<see cref="MetalClash"/> mode 1: every side slows down when it arrives).</item>
	/// </list>
	/// D2: the state is the owner's; others see the guard projectile, the clash projectile and the two buffs (vanilla
	/// sends the local player's buff list whenever it changes, decompiled <c>Main</c>: <c>NetMessage.SendData(50)</c>).
	/// D1: a few ints and bools; nothing allocates.
	/// </summary>
	public sealed class MetalWrenchPlayer : ModPlayer
	{
		private const int ClashDistance = 22;           // the clash shows this far from the player towards the attacker

		private int guardTicks;
		private int guardProjectile = -1;
		private int guardSteam;

		/// <summary>The steam the parry behind the ready riposte took (after discounts): what the Spring Gloves count for the
		/// riposte swing (owner).</summary>
		public int RiposteSteam { get; private set; }

		/// <summary>The swing in progress carries the riposte (owner).</summary>
		public bool RiposteSwing { get; private set; }

		private bool riposteClashed;
		private bool riposteShown;

		public bool Guarding => guardTicks > 0;

		public override void PreUpdate() {
			if (Player.whoAmI != Main.myPlayer) {
				guardTicks = 0;
				return;
			}
			if (guardTicks > 0 && (Player.dead || Player.CCed || Player.noItems || Player.HeldItem.ModItem is not MetalWrench)) {
				EndGuard();
			}
		}

		// Just before the item check, right where vanilla handles its own right-click features.
		public override bool PreItemCheck() {
			if (Player.whoAmI != Main.myPlayer || guardTicks > 0 || Player.HeldItem.ModItem is not MetalWrench) {
				return true;
			}
			bool rightClick = Player.controlUseTile && Main.mouseRightRelease && !Player.tileInteractionHappened && Player.releaseUseItem
				&& !Player.controlUseItem && !Player.mouseInterface && !Main.HoveringOverAnNPC && !Main.SmartInteractShowingGenuine;
			if (!rightClick || Player.itemAnimation > 0 || Player.CCed || Player.noItems || Player.dead || Player.HasBuff<WrenchParryCooldown>()) {
				return true;
			}
			Main.mouseRightRelease = false;                 // the click is used up, as vanilla does with its own
			if (!Player.GetModPlayer<SteamPlayer>().TryPayAttack(MetalWrench.ParrySteamCost, out guardSteam)) {
				return true;                                // no tank (a hint) or too little steam (an overheat): no guard
			}
			guardTicks = MetalWrench.ParryTicks;
			guardProjectile = -1;
			if (SafeSpawn.TryNewProjectile(Player.GetSource_ItemUse(Player.HeldItem), Player.Center, Vector2.Zero,
				ModContent.ProjectileType<MetalWrenchGuard>(), 0, 0f, out Projectile guard, Player.whoAmI)) {
				guardProjectile = guard.whoAmI;
			}
			return true;
		}

		public override void PostItemCheck() {
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			if (RiposteSwing && Player.itemAnimation <= 0) {
				EndRiposte();                                 // the riposte swing is over, landed or not
			}
		}

		private void EndRiposte() {
			RiposteSwing = false;
			RiposteSteam = 0;
			riposteClashed = riposteShown = false;
			Player.ClearBuff(ModContent.BuffType<WrenchRiposteBuff>());
		}

		public override void PostUpdate() {
			if (Player.whoAmI == Main.myPlayer && guardTicks > 0 && --guardTicks == 0) {
				EndGuard();
			}
		}

		public override void UpdateDead() {
			guardTicks = 0;
			guardSteam = 0;
			RiposteSteam = 0;
			RiposteSwing = false;
			riposteClashed = riposteShown = false;
		}

		/// <summary>Owner: a swing starts (<see cref="MetalWrench.UseItem"/>); it carries the riposte if one is ready.</summary>
		public void BeginSwing() {
			if (RiposteSwing) {
				EndRiposte();                                 // autoswing began the next swing on the tick the riposte's ended: it is spent
			}
			if (Player.HasBuff<WrenchRiposteBuff>()) {
				RiposteSwing = true;
				riposteClashed = riposteShown = false;
			}
		}

		/// <summary>Owner (melee hits are the attacker's): the riposte's clash, once per swing, on a boss or mini-boss.</summary>
		public void OnSwingHit(NPC target) {
			if (!RiposteSwing || Player.whoAmI != Main.myPlayer) {
				return;
			}
			bool boss = !riposteClashed && CogpunkSets.IsBossOrMiniboss(target);
			if (!boss && riposteShown) {
				return;                                       // one clash a swing, plus the boss's
			}
			Vector2 at = target.Hitbox.ClosestPointInRect(Vector2.Lerp(Player.Center, target.Center, 0.5f));
			riposteShown = true;
			if (boss) {
				riposteClashed = true;
			}
			SafeSpawn.TryNewProjectile(Player.GetSource_ItemUse(Player.HeldItem), at, Vector2.Zero, ModContent.ProjectileType<MetalClash>(), 0, 0f,
				out _, Player.whoAmI, ai0: boss ? MetalClash.BossMode : MetalClash.HitMode);
		}

		public override bool FreeDodge(Player.HurtInfo info) {
			if (guardTicks <= 0 || !FromEnemy(info.DamageSource, out Vector2 attacker)) {
				return false;
			}
			Vector2 toward = (attacker - Player.Center).SafeNormalize(Vector2.UnitX * Player.direction);
			SafeSpawn.TryNewProjectile(Player.GetSource_FromThis(), Player.Center + toward * ClashDistance, Vector2.Zero,
				ModContent.ProjectileType<MetalClash>(), 0, 0f, out _, Player.whoAmI, ai0: MetalClash.ParryMode);
			Player.SetImmuneTimeForAllTypes(Player.longInvince ? 80 : 40);
			Player.AddBuff(ModContent.BuffType<WrenchRiposteBuff>(), MetalWrench.RiposteBuffTicks);
			RiposteSteam = guardSteam;
			EndGuard();
			return true;
		}

		/// <summary>An NPC's touch or a hostile projectile; out: where it came from. Indices validated (D0).</summary>
		private static bool FromEnemy(PlayerDeathReason source, out Vector2 at) {
			at = Vector2.Zero;
			if (source == null) {
				return false;
			}
			int npc = source.SourceNPCIndex;
			if (npc >= 0 && npc < Main.maxNPCs && Main.npc[npc].active) {
				at = Main.npc[npc].Center;
				return true;
			}
			int proj = source.SourceProjectileLocalIndex;
			if (proj >= 0 && proj < Main.maxProjectiles && Main.projectile[proj].active && Main.projectile[proj].hostile) {
				at = Main.projectile[proj].Center;
				return true;
			}
			return false;
		}

		/// <summary>Owner: the guard is over (parried or timed out): the cooldown starts and the guard pose goes.</summary>
		private void EndGuard() {
			guardTicks = 0;
			Player.AddBuff(ModContent.BuffType<WrenchParryCooldown>(), MetalWrench.CooldownTicks);
			int index = guardProjectile;
			guardProjectile = -1;
			if (index >= 0 && index < Main.maxProjectiles && Main.projectile[index].active && Main.projectile[index].owner == Player.whoAmI
				&& Main.projectile[index].type == ModContent.ProjectileType<MetalWrenchGuard>()) {
				Main.projectile[index].Kill();
			}
		}
	}
}
