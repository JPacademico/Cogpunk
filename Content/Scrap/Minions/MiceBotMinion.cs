using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Minions
{
	/// <summary>
	/// The Mice-bot: a small, very fast clockwork mouse on wheels that runs along the ground and bites what it touches
	/// (contact damage, <see cref="HitCooldown"/> ticks of local immunity per enemy, no knockback). Half a minion slot.
	/// <para>Targeting follows ExampleMod 1.4.4's <c>ExampleSimpleMinion</c>: the owner's whip/right-click target first, then
	/// the nearest chaseable enemy that is in sight <b>or behind at most <see cref="MaxBurrowTiles"/> tiles of solid ground</b>
	/// (measured along the straight line it would dig, so a diagonal through a thin floor counts its real length). The
	/// choice is re-evaluated every <see cref="RetargetInterval"/> ticks (D1).</para>
	/// <para>Modes (<c>ai[0]</c>, synced; changed by the owner's client only, every client runs the same movement, D2):
	/// <list type="bullet">
	/// <item><b>Run</b>: a ground runner like the Scrappybot pet: gravity, steps up one-tile ledges, jumps when blocked or when
	/// the owner is above, pounces just high enough at a target above it.</item>
	/// <item><b>Burrow</b>: digs straight through a wall or floor (no tile collision, hidden while underground, tile dust)
	/// when the target is behind one at most <see cref="MaxBurrowTiles"/> tiles thick, and pops out on the far side.</item>
	/// <item><b>Zip</b>: a spring-loaded dash back to the owner through walls, when it falls far behind or cannot make
	/// progress while following, or stays underground too long.</item>
	/// </list>
	/// A no-progress detector (distance to the goal not shrinking for <see cref="NoProgressTicks"/> ticks) catches every
	/// stuck case: it burrows if a thin wall is in the way, ignores a target it cannot reach for a few seconds (a flier out
	/// of pounce range, a thick wall), and zips home when following. The burrow never changes tiles (D0, D2).
	/// Constants are mirrored in tools/sim/scrap_arsenal_sim.py.</para>
	/// </summary>
	public class MiceBotMinion : CogpunkProjectile
	{
		private enum Mode { Run, Zip, Burrow }

		// MiceBotMinion.png: 8 frames of 32x22 (16x11 art), facing right; the bottom 2 px are padding under the wheels.
		private const int FrameCount = 8;
		private const int FrameIdle = 0;                // 2 frames: the wind-up key turning
		private const int FrameRun = 2;                 // 4 frames
		private const int FrameJump = 6;
		private const int FrameBite = 7;
		private const int FootPadding = 2;

		public const float MinionSlots = 0.5f;
		public const int HitCooldown = 15;              // 0.25 s between bites on the same enemy
		public const float RunSpeed = 9f;               // chasing (the player's base run speed is 3)
		public const float FollowSpeed = 6f;
		public const float CatchUpSpeed = 10f;
		public const float Acceleration = 0.6f;
		public const float JumpSpeed = 8f;              // about 5 tiles high
		public const float JumpReach = JumpSpeed * JumpSpeed / (2f * Gravity);   // 80 px
		public const float Gravity = 0.4f;
		public const float MaxFallSpeed = 10f;
		public const float RunAnimDistance = 6f;        // pixels per run frame
		public const int MaxBurrowTiles = 4;            // thickest wall or floor it digs through
		public const float BurrowSpeed = 6f;
		public const int MaxBurrowTicks = 150;          // still underground after this: zip home
		public const int NoProgressTicks = 45;
		public const int IgnoreTargetTicks = 180;
		public const int RetargetInterval = 10;
		private const float ProgressStep = 8f;          // the goal must get this much closer to count as progress
		private const float ArrivedDistance = 40f;
		private const float TargetRange = 640f;         // from the mouse
		private const float OwnerTargetRange = 1000f;   // targets also stay this close to the owner
		private const float CloseRange = 100f;          // closer than this, no line of sight needed
		private const float ZipStartDistance = 600f;
		private const float ZipStopDistance = 96f;
		private const float ZipMaxSpeed = 15f;
		private const float TeleportDistance = 2000f;
		private const int LineSampleStep = 4;           // px between samples when measuring solid ground on a line
		private const int MaxLineSamples = 256;
		private const float BurrowLengthLimit = MaxBurrowTiles + LineSampleStep / 16f;   // one sample of tolerance
		private const int IdleTicksPerFrame = 30;
		private const int BiteFrameTicks = 8;

		private Mode State {
			get => (Mode)(int)Projectile.ai[0];
			set => Projectile.ai[0] = (float)value;
		}

		private ref float RunDistance => ref Projectile.localAI[1];
		private ref float BiteTicks => ref Projectile.localAI[2];

		// Per-instance and not synced: physics flags from OnTileCollide, target cache and stuck detection. Every client
		// keeps its own copy; the owner's decisions reach the others through ai[0].
		private bool onGround;
		private bool hitWall;
		private Mode lastState;
		private int targetIndex = -1;
		private int retargetTimer;
		private int ignoredTarget = -1;
		private int ignoreTimer;
		private float bestGoalDistance = float.MaxValue;
		private int stalledTicks;
		private int burrowTicks;
		private bool dugIn;
		private bool wasInside;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = FrameCount;
			Main.projPet[Type] = true;
			CogpunkSets.RollsOwnCrit[Type] = true;          // its ModifyHitNPC rolls CritChance (the Bottle of Lost Souls skips it)
			ProjectileID.Sets.MinionTargettingFeature[Type] = true;
			ProjectileID.Sets.MinionSacrificable[Type] = true;
			ProjectileID.Sets.CultistIsResistantTo[Type] = true;
		}

		public override void SetDefaults() {
			Projectile.width = 20;
			Projectile.height = 14;
			Projectile.friendly = true;
			Projectile.minion = true;
			Projectile.minionSlots = MinionSlots;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;               // stays very fast in water
			Projectile.netImportant = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = HitCooldown;
		}

		public override bool? CanCutTiles() {
			return false;
		}

		public override bool MinionContactDamage() {
			return true;
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			if (!CheckActive(owner)) {
				return;
			}
			bool isOwner = Projectile.owner == Main.myPlayer;
			bool grounded = onGround;
			bool blocked = hitWall;
			onGround = false;
			hitWall = false;
			if (BiteTicks > 0f) {
				BiteTicks--;
			}
			if (State != lastState) {                    // a mode change arrived (ours or synced): start it fresh
				lastState = State;
				ResetProgress();
				burrowTicks = 0;
				dugIn = false;
			}

			float ownerDistanceSq = Vector2.DistanceSquared(owner.Center, Projectile.Center);
			if (isOwner && ownerDistanceSq > TeleportDistance * TeleportDistance) {
				Projectile.Center = owner.Center;
				Projectile.velocity = Vector2.Zero;
				ChangeState(Mode.Run, isOwner);
				Projectile.netUpdate = true;
			}

			NPC target = AcquireTarget(owner);
			Projectile.friendly = target != null;        // no stray bites while just following
			switch (State) {
				case Mode.Zip:
					UpdateZip(owner, isOwner);
					break;
				case Mode.Burrow:
					UpdateBurrow(owner, isOwner, target);
					break;
				default:
					UpdateRun(owner, isOwner, grounded, blocked, target, ownerDistanceSq);
					break;
			}
			SpreadOut();

			// D0: never let NaN movement through (it makes the minion vanish and breaks drawing).
			MathSafety.Sanitize(ref Projectile.velocity);
			if (!MathSafety.IsFinite(Projectile.position)) {
				Projectile.Center = owner.Center;
			}
			UpdateFrame(grounded);
		}

		private bool CheckActive(Player owner) {
			int buff = ModContent.BuffType<MiceBotBuff>();
			if (!owner.active || owner.dead) {
				owner.ClearBuff(buff);
				return false;
			}
			if (owner.HasBuff(buff)) {
				Projectile.timeLeft = 2;
			}
			return true;
		}

		// --- Run ------------------------------------------------------------------------------------------------------

		private void UpdateRun(Player owner, bool isOwner, bool grounded, bool blocked, NPC target, float ownerDistanceSq) {
			Projectile.tileCollide = true;
			float goalX;
			float maxSpeed;
			if (target != null) {
				goalX = target.Center.X;
				maxSpeed = RunSpeed;
			}
			else {
				goalX = owner.Center.X - owner.direction * (28f + Projectile.minionPos * 22f);
				maxSpeed = Math.Abs(goalX - Projectile.Center.X) > 160f ? CatchUpSpeed : FollowSpeed;
			}
			float dx = goalX - Projectile.Center.X;
			bool wantsToMove = Math.Abs(dx) > (target != null ? 6f : 16f);
			if (wantsToMove) {
				Projectile.velocity.X = MathHelper.Clamp(Projectile.velocity.X + Math.Sign(dx) * Acceleration, -maxSpeed, maxSpeed);
				Projectile.spriteDirection = Math.Sign(dx);
			}
			else {
				Projectile.velocity.X *= 0.8f;
				if (Math.Abs(Projectile.velocity.X) < 0.05f) {
					Projectile.velocity.X = 0f;
				}
				Vector2 facing = target != null ? target.Center : owner.Center;
				Projectile.spriteDirection = facing.X >= Projectile.Center.X ? 1 : -1;
			}

			Collision.StepUp(ref Projectile.position, ref Projectile.velocity, Projectile.width, Projectile.height, ref Projectile.stepSpeed, ref Projectile.gfxOffY);
			if (grounded) {
				bool targetAbove = target != null && target.Bottom.Y < Projectile.Bottom.Y - 20f && Math.Abs(dx) < 160f;
				bool ownerAbove = target == null && owner.velocity.Y == 0f && owner.Bottom.Y < Projectile.Bottom.Y - 40f && Math.Abs(dx) < 160f;
				if ((wantsToMove && blocked) || ownerAbove) {
					Projectile.velocity.Y = -JumpSpeed;
				}
				else if (targetAbove) {
					// Pounce just high enough to reach the target's middle: v = sqrt(2gh), capped at a full jump.
					float height = Projectile.Bottom.Y - target.Center.Y;
					Projectile.velocity.Y = -Math.Min(JumpSpeed, (float)Math.Sqrt(2f * Gravity * Math.Max(height, 0f)));
				}
			}
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);

			if (!isOwner) {
				return;                                  // mode decisions belong to the owner's client
			}
			if (target == null) {
				Vector2 home = new(goalX, owner.Bottom.Y - Projectile.height * 0.5f);
				bool stalled = TrackProgress(home);
				if (ownerDistanceSq > ZipStartDistance * ZipStartDistance || stalled) {
					ChangeState(Mode.Zip, isOwner);
				}
				return;
			}

			// A target behind a wall or under the floor: dig as soon as the mouse is up against it.
			bool walled = !Collision.CanHitLine(Projectile.position, Projectile.width, Projectile.height, target.position, target.width, target.height);
			bool targetBelow = target.Top.Y > Projectile.Bottom.Y + 8f && Math.Abs(dx) < 32f;
			if (walled && (blocked || (grounded && targetBelow)) && TryStartBurrow(target, isOwner)) {
				return;
			}
			if (TrackProgress(target.Center)) {
				if (!TryStartBurrow(target, isOwner)) {
					bool withinPounce = Projectile.Bottom.Y - target.Bottom.Y < JumpReach;
					if (walled || !withinPounce) {
						IgnoreTarget(target);                // a thick wall, or a flier out of reach: try others for a while
					}
					else {
						ResetProgress();                     // reachable by pouncing: keep at it
					}
				}
			}
		}

		/// <summary>Burrow if the straight line to the target crosses some solid ground, but no more than <see cref="MaxBurrowTiles"/> tiles of it.</summary>
		private bool TryStartBurrow(NPC target, bool isOwner) {
			float wall = SolidLengthOnLine(Projectile.Center, target.Center);
			if (wall <= 0f || wall > BurrowLengthLimit) {
				return false;
			}
			ChangeState(Mode.Burrow, isOwner);
			return true;
		}

		// --- Burrow ---------------------------------------------------------------------------------------------------

		private void UpdateBurrow(Player owner, bool isOwner, NPC target) {
			Projectile.tileCollide = false;
			Vector2 goal = target != null ? target.Center : owner.Center;
			Vector2 direction = (goal - Projectile.Center).SafeNormalize(Vector2.UnitX * Projectile.spriteDirection);
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, direction * BurrowSpeed, 0.3f);
			if (Math.Abs(Projectile.velocity.X) > 0.2f) {
				Projectile.spriteDirection = Math.Sign(Projectile.velocity.X);
			}
			bool inside = Collision.SolidCollision(Projectile.position, Projectile.width, Projectile.height);
			if (inside) {
				dugIn = true;
			}
			burrowTicks++;

			if (!Main.dedServ) {
				if (inside != wasInside) {
					SoundEngine.PlaySound(SoundID.Dig with { Volume = 0.5f, Pitch = 0.4f }, Projectile.Center);
				}
				if (inside && Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()) {
					Point at = Projectile.Center.ToTileCoordinates();
					SafeSpawn.TryTileDust(at.X, at.Y);
				}
			}
			wasInside = inside;

			if (!isOwner) {
				return;
			}
			if (!inside && (dugIn || target == null)) {
				ChangeState(Mode.Run, isOwner);          // out on the far side
			}
			else if (burrowTicks > MaxBurrowTicks) {
				ChangeState(Mode.Zip, isOwner);          // lost underground: dash home
			}
		}

		// --- Zip ------------------------------------------------------------------------------------------------------

		// Spring-loaded dash back to the owner, through walls.
		private void UpdateZip(Player owner, bool isOwner) {
			Projectile.tileCollide = false;
			Vector2 goal = owner.Center + new Vector2(-owner.direction * 32f, -24f);
			Vector2 toGoal = goal - Projectile.Center;
			float speed = Math.Min(toGoal.Length() / 10f + 3f, ZipMaxSpeed);
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, toGoal.SafeNormalize(Vector2.Zero) * speed, 0.12f);
			if (Math.Abs(Projectile.velocity.X) > 0.2f) {
				Projectile.spriteDirection = Math.Sign(Projectile.velocity.X);
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect() && Main.rand.NextBool(3)
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Electric, out Dust spark, 0f, 0f)) {
				spark.noGravity = true;
				spark.scale = 0.5f;
				spark.velocity *= 0.3f;
			}
			if (Vector2.DistanceSquared(owner.Center, Projectile.Center) < ZipStopDistance * ZipStopDistance
				&& !Collision.SolidCollision(Projectile.position, Projectile.width, Projectile.height)) {
				ChangeState(Mode.Run, isOwner);
			}
		}

		/// <summary>Only the owner decides; the change reaches the server and other clients through ai[] (D2).</summary>
		private void ChangeState(Mode next, bool isOwner) {
			if (!isOwner || State == next) {
				return;
			}
			State = next;
			Projectile.netUpdate = true;
		}

		// --- Stuck detection --------------------------------------------------------------------------------------------

		/// <summary>True once the goal has not come <see cref="ProgressStep"/> px closer for <see cref="NoProgressTicks"/>
		/// ticks while still farther than <see cref="ArrivedDistance"/>.</summary>
		private bool TrackProgress(Vector2 goal) {
			float distance = Vector2.Distance(Projectile.Center, goal);
			if (distance < ArrivedDistance || distance < bestGoalDistance - ProgressStep) {
				bestGoalDistance = Math.Min(bestGoalDistance, distance);
				stalledTicks = 0;
				return false;
			}
			return ++stalledTicks > NoProgressTicks;
		}

		private void ResetProgress() {
			bestGoalDistance = float.MaxValue;
			stalledTicks = 0;
		}

		private void IgnoreTarget(NPC target) {
			ignoredTarget = target.whoAmI;
			ignoreTimer = IgnoreTargetTicks;
			targetIndex = -1;
			retargetTimer = 0;
			ResetProgress();
		}

		// --- Targeting ------------------------------------------------------------------------------------------------

		/// <summary>The cached target, re-chosen every <see cref="RetargetInterval"/> ticks or as soon as it stops being valid.</summary>
		private NPC AcquireTarget(Player owner) {
			if (ignoreTimer > 0 && --ignoreTimer == 0) {
				ignoredTarget = -1;
			}
			if (--retargetTimer <= 0 || !IsValidTarget(targetIndex, owner)) {
				retargetTimer = RetargetInterval;
				int found = SearchTarget(owner);
				if (found != targetIndex) {
					targetIndex = found;
					ResetProgress();
				}
			}
			return targetIndex >= 0 ? Main.npc[targetIndex] : null;
		}

		private bool IsValidTarget(int index, Player owner) {
			if (index < 0 || index >= Main.maxNPCs || index == ignoredTarget) {
				return false;
			}
			NPC npc = Main.npc[index];
			return npc.CanBeChasedBy(Projectile) && Vector2.DistanceSquared(npc.Center, owner.Center) < OwnerTargetRange * OwnerTargetRange;
		}

		/// <summary>The owner's whip/right-click target if valid, else the nearest chaseable enemy in sight or behind a wall
		/// thin enough to dig through. Allocation-free; the line checks only run for enemies closer than the best so far.</summary>
		private int SearchTarget(Player owner) {
			int forced = owner.MinionAttackTargetNPC;
			if (IsValidTarget(forced, owner)) {
				return forced;
			}
			int best = -1;
			float bestSq = TargetRange * TargetRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.whoAmI == ignoredTarget || !npc.CanBeChasedBy(Projectile)) {
					continue;
				}
				float distanceSq = Vector2.DistanceSquared(npc.Center, Projectile.Center);
				if (distanceSq >= bestSq || Vector2.DistanceSquared(npc.Center, owner.Center) > OwnerTargetRange * OwnerTargetRange) {
					continue;
				}
				bool reachable = distanceSq < CloseRange * CloseRange
					|| Collision.CanHitLine(Projectile.position, Projectile.width, Projectile.height, npc.position, npc.width, npc.height)
					|| SolidLengthOnLine(Projectile.Center, npc.Center) <= BurrowLengthLimit;
				if (reachable) {
					best = npc.whoAmI;
					bestSq = distanceSq;
				}
			}
			return best;
		}

		/// <summary>
		/// How many tiles of solid ground the straight line between two points crosses: the line is sampled every
		/// <see cref="LineSampleStep"/> px (at most <see cref="MaxLineSamples"/> samples, D0) and each solid sample counts
		/// for its share of a tile. Stops once past <see cref="BurrowLengthLimit"/>. Platforms and actuated blocks don't
		/// count. Allocation-free.
		/// </summary>
		public static float SolidLengthOnLine(Vector2 from, Vector2 to) {
			Vector2 delta = to - from;
			float length = delta.Length();
			int samples = Math.Clamp((int)(length / LineSampleStep) + 1, 1, MaxLineSamples);
			float perSample = length / samples / 16f;     // tiles of line per sample
			float solid = 0f;
			for (int k = 0; k <= samples; k++) {
				Vector2 point = from + delta * (k / (float)samples);
				if (TileSafety.TryGetTile((int)(point.X / 16f), (int)(point.Y / 16f), out Tile tile) && tile.HasTile && !tile.IsActuated
					&& Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType]) {
					solid += perSample;
					if (solid > BurrowLengthLimit) {
						return solid;
					}
				}
			}
			return solid;
		}

		// Mice of the same owner nudge apart instead of stacking into one sprite.
		private void SpreadOut() {
			foreach (Projectile other in Main.ActiveProjectiles) {
				if (other.whoAmI == Projectile.whoAmI || other.owner != Projectile.owner || other.type != Projectile.type) {
					continue;
				}
				float dx = Projectile.Center.X - other.Center.X;
				if (Math.Abs(dx) < Projectile.width && Math.Abs(Projectile.Center.Y - other.Center.Y) < Projectile.height) {
					Projectile.velocity.X += dx != 0f ? Math.Sign(dx) * 0.1f : (Projectile.whoAmI < other.whoAmI ? -0.1f : 0.1f);
				}
			}
		}

		// --- Visuals and hits -------------------------------------------------------------------------------------------

		private void UpdateFrame(bool grounded) {
			if (BiteTicks > 0f) {
				Projectile.frame = FrameBite;
				return;
			}
			if (State != Mode.Run || (!grounded && Math.Abs(Projectile.velocity.Y) > 0.5f)) {
				Projectile.frame = FrameJump;
				return;
			}
			float speed = Math.Abs(Projectile.velocity.X);
			if (speed > 0.3f) {
				if (Projectile.frame < FrameRun || Projectile.frame >= FrameRun + 4) {
					Projectile.frame = FrameRun;
				}
				RunDistance += speed;
				if (RunDistance >= RunAnimDistance) {
					RunDistance = 0f;
					Projectile.frame = FrameRun + ((Projectile.frame - FrameRun + 1) % 4);
				}
				return;
			}
			Projectile.frame = FrameIdle + (int)(Main.GameUpdateCount / IdleTicksPerFrame % 2);
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			modifiers.DisableKnockback();               // the bites never push enemies, whatever knockback bonuses say
			// Summon damage skips vanilla's crit roll (SummonDamageClass.UseStandardCritCalcs is false), but tModLoader still
			// keeps CritChance current for minions: the player's 4% base plus summon/generic bonuses (decompiled
			// Projectile.Update). Rolling it here gives the mouse the same crit odds as any other weapon. This runs on the
			// client that deals the damage (the owner), so the roll is the owner's (D2).
			if (Main.rand.Next(100) < Projectile.CritChance) {
				modifiers.SetCrit();
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			BiteTicks = BiteFrameTicks;                 // jaw open for a moment (owner's client, visual only)
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Projectile.velocity.X != oldVelocity.X) {
				hitWall = true;
			}
			if (Projectile.velocity.Y != oldVelocity.Y && oldVelocity.Y > 0f) {
				onGround = true;
			}
			return false;
		}

		// Drawn by hand: anchored to the hitbox bottom (wheels on the ground), flipped by direction, snapped to whole
		// pixels and never rotated, so the pixel art stays crisp (D4). Hidden while it is inside the blocks it digs through.
		public override bool PreDraw(ref Color lightColor) {
			if (State == Mode.Burrow && Collision.SolidCollision(Projectile.position, Projectile.width, Projectile.height)) {
				return false;
			}
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frameHeight = texture.Height / FrameCount;
			int frame = Math.Clamp(Projectile.frame, 0, FrameCount - 1);
			Rectangle source = new(0, frame * frameHeight, texture.Width, frameHeight);
			Vector2 origin = new(texture.Width * 0.5f, frameHeight - FootPadding);
			Vector2 position = (Projectile.Bottom + new Vector2(0f, Projectile.gfxOffY) - Main.screenPosition).Floor();
			SpriteEffects effects = Projectile.spriteDirection == -1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), 0f, origin, 1f, effects);
			return false;
		}
	}
}
