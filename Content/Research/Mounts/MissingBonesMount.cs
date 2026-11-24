using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Mounts
{
	/// <summary>
	/// Missing Bones (Ossos Perdidos), a mount (user, 2026-11-24: "a raptor skeleton that is fast and make the player imune to tar
	/// poisoning (a way to reach the fundamental stone under the pool)"): a raptor rebuilt from bones held together with the
	/// Junkyard's tar, ridden on its hips. It runs fast (<see cref="RunSpeed"/> / <see cref="DashSpeed"/>: between the Bunny's
	/// 4 / 7.8 and the Hardmode Unicorn's 4 / 12, decompiled 1.4.4 <c>Mount.SetupMounts</c>), leaps well, falls softly; its rider
	/// can't catch the Tar Plague (<see cref="MissingBonesBuff"/>), and bones don't float: in a liquid it sinks to the bottom and
	/// walks there, and it paddles up while jump is held (<see cref="MissingBonesPlayer"/>), so it can take its rider down the
	/// tar pit to the Fundamental Stone on its floor and back up. Breath is the rider's own (a Gills Potion for the deep pits).
	/// <para>Art (art/research/make_missing_bones_art.py): a side view facing right, <see cref="Frames"/> frames of
	/// <see cref="FrameWidth"/> x <see cref="FrameHeight"/> game px stacked in <c>MissingBonesMount_Back.png</c>: 0 standing,
	/// 1-8 the run, 9 in the air. Vanilla draws a mount frame with its middle at the hitbox's middle plus
	/// (<see cref="Mount.MountData.xOffset"/> x the facing, <see cref="Mount.MountData.yOffset"/>), the hitbox grown up by
	/// <see cref="HeightBoost"/>, and the rider <see cref="Mount.MountData.playerYOffsets"/> px up (decompiled <c>Mount.Draw</c>,
	/// <c>PlayerDrawSet.HeightOffsetVisual</c>), so the frame's bottom row is the ground when its height is 42 + the boost.</para>
	/// <para>D0: the sizes come from these constants, never from the texture (a missing sheet must not throw at load). D2: a
	/// vanilla mount (its buff synced by vanilla); the liquid moves are computed from synced controls on every side.</para>
	/// </summary>
	public class MissingBonesMount : ModMount
	{
		public const int FrameWidth = 100, FrameHeight = 72, Frames = 10;
		public const int HeightBoost = FrameHeight - 42;         // 30: the sheet's bottom row on the ground
		public const int RiderOffset = 24;                       // the rider's feet 24 px up: their hips on its back
		public const float RunSpeed = 6f, DashSpeed = 10f, Acceleration = 0.14f;
		public const int JumpTiles = 14;
		public const float JumpVelocity = 6.51f;
		public const int RunFrameDelay = 14;                     // px of travel a run frame (vanilla's mount frame clock)
		/// <summary>The rider's bob in the run (game px, the art's own: the hips rise as a foot pushes off).</summary>
		private static readonly int[] Bob = { 0, 0, 2, 2, 0, 0, 2, 2, 0, 0 };

		public override void SetStaticDefaults() {
			MountData.buff = ModContent.BuffType<MissingBonesBuff>();
			MountData.spawnDust = DustID.Bone;
			MountData.heightBoost = HeightBoost;
			MountData.fallDamage = 0.4f;
			MountData.runSpeed = RunSpeed;
			MountData.dashSpeed = DashSpeed;
			MountData.acceleration = Acceleration;
			MountData.jumpHeight = JumpTiles;
			MountData.jumpSpeed = JumpVelocity;
			MountData.flightTimeMax = 0;
			MountData.fatigueMax = 0;
			MountData.constantJump = false;
			MountData.blockExtraJumps = false;
			MountData.totalFrames = Frames;
			int[] offsets = new int[Frames];
			for (int k = 0; k < Frames; k++) {
				offsets[k] = RiderOffset + Bob[k];
			}
			MountData.playerYOffsets = offsets;
			MountData.xOffset = 0;
			MountData.yOffset = 0;
			MountData.playerHeadOffset = RiderOffset;
			MountData.bodyFrame = 3;                             // the rider's legs astride (vanilla's riding frame)
			MountData.standingFrameStart = 0;
			MountData.standingFrameCount = 1;
			MountData.standingFrameDelay = 12;
			MountData.runningFrameStart = 1;
			MountData.runningFrameCount = 8;
			MountData.runningFrameDelay = RunFrameDelay;
			MountData.dashingFrameStart = 1;
			MountData.dashingFrameCount = 8;
			MountData.dashingFrameDelay = RunFrameDelay;
			MountData.flyingFrameStart = 9;
			MountData.flyingFrameCount = 1;
			MountData.flyingFrameDelay = 12;
			MountData.inAirFrameStart = 9;
			MountData.inAirFrameCount = 1;
			MountData.inAirFrameDelay = 12;
			MountData.idleFrameStart = 0;
			MountData.idleFrameCount = 1;
			MountData.idleFrameDelay = 12;
			MountData.idleFrameLoop = false;
			MountData.swimFrameStart = 1;                         // under the tar it keeps walking
			MountData.swimFrameCount = 8;
			MountData.swimFrameDelay = RunFrameDelay;
			MountData.textureWidth = FrameWidth;
			MountData.textureHeight = FrameHeight * Frames;
		}

		/// <summary>Clients: bone dust kicked up at a run.</summary>
		public override void UpdateEffects(Player player) {
			if (Main.dedServ || Math.Abs(player.velocity.X) < RunSpeed || player.velocity.Y != 0f || !Main.rand.NextBool(6)
				|| !CogpunkClientConfig.RollEffect()) {
				return;
			}
			if (SafeSpawn.TryNewDust(player.Bottom + new Vector2(-8f, -4f), 16, 4, DustID.Bone, out Dust d)) {
				d.velocity = new Vector2(-player.velocity.X * 0.15f, -Main.rand.NextFloat(0.5f, 1.5f));
				d.scale = 0.8f;
			}
		}
	}

	/// <summary>
	/// Missing Bones in a liquid (2026-11-24, my call, so it is "a way to reach the fundamental stone under the pool"): a skeleton
	/// doesn't float, so in water (the Junkyard's tar is water drawn as tar) it sinks at <see cref="SinkSpeed"/>
	/// (<see cref="SinkFast"/> holding down) and paddles up at <see cref="RiseSpeed"/> while jump is held, instead of vanilla's
	/// slow bob (a player in water falls at most 5 a tick and moves at half its velocity, decompiled <c>Player.Update</c> and
	/// <c>WaterCollision</c>; these are velocities, so halved too: 4, 8 and 6 px a tick). Runs in <c>PreUpdateMovement</c>, after
	/// vanilla's jump and gravity and before the collision (decompiled order), on every side from the synced controls (D2). Lava,
	/// honey and shimmer are left to vanilla.
	/// </summary>
	public sealed class MissingBonesPlayer : ModPlayer
	{
		public const float SinkSpeed = 8f, SinkFast = 16f, RiseSpeed = 12f, SinkAccel = 0.4f, RiseAccel = 0.6f;

		public override void PreUpdateMovement() {
			if (!Player.mount.Active || Player.mount.Type != ModContent.MountType<MissingBonesMount>() || !Player.wet || Player.lavaWet
				|| Player.honeyWet || Player.shimmerWet) {
				return;
			}
			if (Player.controlJump) {
				Player.velocity.Y = Math.Max(Player.velocity.Y - RiseAccel, -RiseSpeed);
			}
			else {
				float down = Player.controlDown ? SinkFast : SinkSpeed;
				Player.velocity.Y = Math.Min(Player.velocity.Y + SinkAccel, down);
			}
			Player.fallStart = (int)(Player.position.Y / 16f);         // no fall damage from a long sink (vanilla: water already)
		}
	}
}
