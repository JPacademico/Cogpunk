using System;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	/// <summary>
	/// What Trash-Tr0m does to players, applied from the boss's synced state (D2: a player's movement belongs to its own
	/// client, so nothing here is decided by the server; every side runs the same math so other clients predict it too).
	/// <list type="bullet">
	/// <item><b>Suction</b> (<see cref="TrashTr0m.GetPull"/>): a conveyor. The pull is added to the player's velocity right
	/// before vanilla moves and collides them (<see cref="PreUpdateMovement"/>) and taken off again afterwards
	/// (<see cref="PostUpdate"/>, scaled by how much of it collision let through), so it never builds up: it simply
	/// subtracts <see cref="TrashTr0m.MaxPull"/> (5.4 px/tick) from their own speed. Walls and slopes still stop them.
	/// Near the mouth it also lifts them towards it.</item>
	/// <item><b>Swallowed</b> (<see cref="TrashTr0m.HeldPlayer"/>): locked in the mouth, hidden, controls off, immune to
	/// everything. On the spit tick the owning client throws them up (<see cref="TrashTr0m.SpitLaunchSpeed"/>) and back
	/// over the boss (<see cref="TrashTr0m.SpitSideSpeed"/>), out of any tile the mouth may be in.</item>
	/// <item><b>Spat</b>: vanilla only resets <c>fallStart</c> on the ground or while jumping (decompiled Player.Update), so
	/// a launch would count the fall from the mouth. While rising we move <c>fallStart</c> up with the player (as a jump
	/// does), and while falling we never let the fall exceed <see cref="TrashTr0m.MaxSpitFallTiles"/> + extraFall tiles:
	/// at most (45 - 25) x 10 = 200 damage, less with fall protection (Lucky Horseshoe, wings and Featherfall negate it,
	/// a double jump or a hook breaks it).</item>
	/// <item><b>Burst</b>: when it erupts from the heap, players near the cache are thrown back once.</item>
	/// </list>
	/// </summary>
	public sealed class TrashTr0mPlayer : ModPlayer
	{
		public const float BurstKnockRange = 16f * 16f;
		public const int SpatTimeout = 600;               // stop tracking a spat player after 10 s whatever happens

		private float addedPull;
		private float pulledVelocity;
		private bool held;
		private int heldBy = -1;
		private int spatTicks;
		private int knockedBy = -1;

		public bool IsHeld => held;

		public override void PreUpdate() {
			bool hasBoss = TrashTr0mSystem.TryGetBoss(out TrashTr0m boss);
			UpdateHeld(hasBoss ? boss : null);
			if (Player.whoAmI == Main.myPlayer) {
				UpdateSpat();
				if (hasBoss) {
					TryBurstKnockback(boss);
				}
			}
		}

		private void UpdateHeld(TrashTr0m boss) {
			bool nowHeld = boss != null && !Player.dead && boss.HeldPlayer == Player.whoAmI;
			if (held && !nowHeld) {
				Release(boss);
			}
			held = nowHeld;
			if (held) {
				heldBy = boss.NPC.whoAmI;
				LockInMouth(boss);
			}
		}

		private void LockInMouth(TrashTr0m boss) {
			Vector2 mouth = boss.MouthWorld();
			Player.position = mouth - Player.Size * 0.5f;
			Player.velocity = Vector2.Zero;
			Player.fallStart = (int)(Player.position.Y / 16f);
			Player.fallStart2 = Player.fallStart;
			Player.gravDir = 1f;
		}

		/// <summary>The spit (or a release when the boss died or let go). Only the owner moves its player.</summary>
		private void Release(TrashTr0m boss) {
			held = false;
			int by = heldBy;
			heldBy = -1;
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			NudgeOutOfTiles();
			if (boss == null || boss.NPC.whoAmI != by || !boss.IsSpitting(Player.whoAmI)) {
				return;                                    // let go without a spit (it died): just drop
			}
			float launch = TrashTr0m.SpitLaunchSpeed(Player.Bottom.Y, boss.RigOrigin.Y, Player.gravity);
			Player.velocity = new Vector2(-boss.NPC.spriteDirection * TrashTr0m.SpitSideSpeed, -launch);   // out behind it
			Player.fallStart = (int)(Player.position.Y / 16f);
			spatTicks = 1;
		}

		/// <summary>The mouth can be inside terrain if the boss is against a wall: climb out (at most 24 steps, D0).</summary>
		private void NudgeOutOfTiles() {
			for (int i = 0; i < 24 && Collision.SolidCollision(Player.position, Player.width, Player.height); i++) {
				Player.position.Y -= 8f;
			}
		}

		private void UpdateSpat() {
			if (spatTicks <= 0) {
				return;
			}
			if (Player.dead || ++spatTicks > SpatTimeout) {
				spatTicks = 0;
				return;
			}
			int tileY = (int)(Player.position.Y / 16f);
			if (Player.velocity.Y < 0f) {
				Player.fallStart = tileY;                 // rising: the fall will be measured from the top of the arc
			}
			else {
				int lowest = tileY - (TrashTr0m.MaxSpitFallTiles + Player.extraFall);
				if (Player.fallStart < lowest) {
					Player.fallStart = lowest;             // never more than 200 fall damage
				}
				if (Player.velocity.Y == 0f && spatTicks > 2) {
					spatTicks = 0;                         // landed (this tick's fall check uses the capped start)
				}
			}
		}

		private void TryBurstKnockback(TrashTr0m boss) {
			if (!boss.FromHeap || boss.NPC.ai[1] < TrashTr0m.BurstTick) {
				if (!boss.IsEmerging) {
					knockedBy = -1;
				}
				return;
			}
			if (knockedBy == boss.NPC.whoAmI || boss.NPC.ai[1] > TrashTr0m.BurstTick + 6 || Player.dead) {
				return;
			}
			knockedBy = boss.NPC.whoAmI;
			Vector2 centre = boss.NPC.Bottom - new Vector2(0f, 64f);
			Vector2 away = Player.Center - centre;
			float dist = away.Length();
			if (dist > BurstKnockRange) {
				return;
			}
			float power = MathHelper.Lerp(1f, 0.45f, dist / BurstKnockRange);
			float side = away.X >= 0f ? 1f : -1f;
			Player.velocity = new Vector2(side * 11f * power, -8.5f * power);
			Player.fallStart = (int)(Player.position.Y / 16f);
		}

		public override void PreUpdateMovement() {
			addedPull = 0f;
			if (held) {
				if (TrashTr0mSystem.TryGetBoss(out TrashTr0m holder) && holder.NPC.whoAmI == heldBy) {
					LockInMouth(holder);
				}
				return;
			}
			if (!TrashTr0mSystem.TryGetBoss(out TrashTr0m boss) || !boss.GetPull(Player, out float convey, out float lift, out bool lifting)) {
				return;
			}
			if (lifting) {
				Player.velocity.Y = MathHelper.Lerp(Player.velocity.Y, lift, 0.25f);
				Player.fallStart = (int)(Player.position.Y / 16f);
			}
			if (convey != 0f && MathSafety.IsFinite(new Vector2(convey, 0f))) {
				addedPull = convey;
				Player.velocity.X += convey;
				pulledVelocity = Player.velocity.X;
			}
		}

		public override void PostUpdate() {
			if (held && TrashTr0mSystem.TryGetBoss(out TrashTr0m holder) && holder.NPC.whoAmI == heldBy) {
				LockInMouth(holder);
			}
			if (addedPull == 0f) {
				return;
			}
			// Take the conveyor back off: all of it if the player moved freely, the part collision let through otherwise
			// (a wall that stopped them leaves them stopped).
			float kept = pulledVelocity != 0f ? MathHelper.Clamp(Player.velocity.X / pulledVelocity, 0f, 1f) : 0f;
			Player.velocity.X -= addedPull * kept;
			addedPull = 0f;
		}

		public override void SetControls() {
			if (!held) {
				return;
			}
			Player.controlLeft = Player.controlRight = Player.controlUp = Player.controlDown = false;
			Player.controlJump = Player.controlUseItem = Player.controlUseTile = Player.controlHook = false;
			Player.controlMount = Player.controlThrow = Player.controlQuickHeal = Player.controlQuickMana = false;
		}

		public override bool ImmuneTo(PlayerDeathReason damageSource, int cooldownCounter, bool dodgeable) {
			return held;                                   // nothing reaches a player inside the boss
		}

		public override void HideDrawLayers(PlayerDrawSet drawInfo) {
			if (!held) {
				return;
			}
			var layers = PlayerDrawLayerLoader.Layers;
			for (int i = 0; i < layers.Count; i++) {
				layers[i].Hide();
			}
		}

		public override void OnRespawn() {
			held = false;
			heldBy = -1;
			spatTicks = 0;
		}
	}
}
