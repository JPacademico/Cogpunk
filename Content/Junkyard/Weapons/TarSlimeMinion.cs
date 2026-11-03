using System;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// A tar slime (the <see cref="Tarmancer"/>'s minion, one slot): a Living Tar on the summoner's side that hops after
	/// them and spits a <see cref="TarSlimeShot"/> at the nearest enemy in sight every <see cref="ShotInterval"/> ticks. No
	/// contact damage: it shoots from where it is.
	/// <para>2026-11-03 (user): it looks exactly like the Living Tar enemy (it draws <see cref="NPCs.LivingTar"/>'s own sheet,
	/// cycling its two frames the way vanilla's slimes do: decompiled <c>NPC.VanillaFindFrame</c>, case 1, a counter of 1 a
	/// tick, 2 while moving, a frame every 8), and spits as often as the Imp Staff's imp throws fireballs (decompiled
	/// <c>Projectile.AI_062</c>, type 375: its counter climbs 1 a tick plus 1 one tick in three, from 1 to past 90, so 68
	/// ticks on average). The only extra is a pair of tar wings (<c>TarSlimeMinion_Wings</c>) behind it while it flies home,
	/// as vanilla's Baby Slime sprouts its own.</para>
	/// <para>Modes (<c>ai[0]</c>, synced; decided by the owner's client, every client runs the same movement, D2):
	/// <list type="bullet">
	/// <item><b>Hop</b>: gravity, small hops towards its spot behind the summoner (slimes spread out by
	/// <c>minionPos</c>), a higher hop at a wall.</item>
	/// <item><b>Fly</b>: when it falls more than <see cref="FlyStart"/> px behind, gets stuck or the summoner is far above,
	/// it sprouts two little tar wings and flies through blocks to the summoner, landing again close by.</item>
	/// </list>
	/// <c>ai[1]</c> is the shot cooldown (reset by the owner when it spits, synced then): every client shows the spitting
	/// frame from it. Targets: the owner's whip/right-click target first, then the nearest chaseable enemy in sight within
	/// <see cref="TargetRange"/>, re-chosen every <see cref="RetargetInterval"/> ticks (D1).</para>
	/// </summary>
	public class TarSlimeMinion : CogpunkProjectile
	{
		private enum Mode { Hop, Fly }

		// LivingTar.png: 2 frames of 32x24 (stride 24; squashed, stretched), facing left like every NPC sheet; the body's
		// bottom row is 4 px above the cell's bottom (vanilla draws NPC frames 4 px low). TarSlimeMinion_Wings.png: 2 frames
		// of 64x24 (stride 26; up, down), the slime's cell sitting at (16, 12) in it.
		public const string SheetPath = "Cogpunk/Content/Junkyard/NPCs/LivingTar";
		private const int FrameCount = 2, FrameWidth = 32, FrameHeight = 24, FrameStride = 24, FootPadding = 4;
		private const int FrameSquashed = 0;
		private const int WingFrames = 2, WingWidth = 64, WingHeight = 24, WingStride = 26, WingCellX = 16, WingCellY = 12;
		private const int SlimeFrameCounter = 8;        // vanilla's slime frame step

		public const float MinionSlots = 1f;
		public const int ShotInterval = 68;             // the Imp Staff's imp (user, 2026-11-03; was the Hornet's 45)
		public const float ShotSpeed = 10f;             // a hornet stinger's
		public const float TargetRange = 640f;          // 40 tiles from the slime
		private const float OwnerTargetRange = 1100f;
		public const int RetargetInterval = 10;
		public const float Gravity = 0.35f;
		public const float MaxFallSpeed = 10f;
		public const float HopSpeedX = 3.6f;
		public const float HopSpeedY = 5.6f;
		public const float WallHopSpeedY = 8f;
		public const float FlyStart = 420f;
		public const float FlyStop = 90f;
		public const float FlySpeed = 11f;
		private const float TeleportDistance = 2000f;
		private const int StuckTicks = 90;
		private const int SpitFrameTicks = 8;
		private const int FlyFrameTicks = 6;
		private const int SteamOneIn = 40;              // the Living Tar's wisps of steam

		private static Asset<Texture2D> wings;

		private Mode State {
			get => (Mode)(int)Projectile.ai[0];
			set => Projectile.ai[0] = (float)value;
		}

		private ref float ShotCooldown => ref Projectile.ai[1];

		// not synced: physics flags, the target cache and stuck detection (every client keeps its own; the owner decides)
		private bool onGround;
		private bool hitWall;
		private int targetIndex = -1;
		private int retargetTimer;
		private int stuckTimer;
		private float lastOwnerDistance = float.MaxValue;

		public override string Texture => SheetPath;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = FrameCount;
			wings = DepthLayers.RequestOptional("Cogpunk/Content/Junkyard/Weapons/TarSlimeMinion_Wings");
			Main.projPet[Type] = true;
			ProjectileID.Sets.MinionTargettingFeature[Type] = true;
			ProjectileID.Sets.MinionSacrificable[Type] = true;
			ProjectileID.Sets.CultistIsResistantTo[Type] = true;
		}

		public override void Unload() {
			wings = null;
		}

		public override void SetDefaults() {
			Projectile.width = 24;                          // the Living Tar's (vanilla slime) hitbox
			Projectile.height = 18;
			Projectile.friendly = true;
			Projectile.minion = true;
			Projectile.minionSlots = MinionSlots;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.netImportant = true;
			Projectile.aiStyle = -1;
		}

		public override bool? CanCutTiles() => false;

		public override bool MinionContactDamage() => false;

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
			onGround = hitWall = false;
			if (ShotCooldown > 0f) {
				ShotCooldown--;
			}
			float ownerDistance = Vector2.Distance(owner.Center, Projectile.Center);
			if (isOwner && ownerDistance > TeleportDistance) {
				Projectile.Center = owner.Center;
				Projectile.velocity = Vector2.Zero;
				ChangeState(Mode.Hop, isOwner);
			}
			NPC target = AcquireTarget(owner);
			if (State == Mode.Fly) {
				UpdateFly(owner, isOwner, ownerDistance);
			}
			else {
				UpdateHop(owner, isOwner, grounded, blocked, ownerDistance, target);
			}
			if (target != null) {
				Projectile.spriteDirection = target.Center.X >= Projectile.Center.X ? 1 : -1;
				if (isOwner && ShotCooldown <= 0f) {
					Spit(target);
				}
			}
			MathSafety.Sanitize(ref Projectile.velocity);
			if (!MathSafety.IsFinite(Projectile.position)) {
				Projectile.Center = owner.Center;
			}
			UpdateFrame(grounded);
		}

		private bool CheckActive(Player owner) {
			int buff = ModContent.BuffType<TarSlimeBuff>();
			if (!owner.active || owner.dead) {
				owner.ClearBuff(buff);
				return false;
			}
			if (owner.HasBuff(buff)) {
				Projectile.timeLeft = 2;
			}
			return true;
		}

		// --- Hop --------------------------------------------------------------------------------------------------------

		private void UpdateHop(Player owner, bool isOwner, bool grounded, bool blocked, float ownerDistance, NPC target) {
			Projectile.tileCollide = true;
			float home = owner.Center.X - owner.direction * (34f + Projectile.minionPos * 28f);
			float dx = home - Projectile.Center.X;
			if (grounded) {
				Projectile.velocity.X *= 0.7f;
				if (Math.Abs(dx) > 18f) {
					Projectile.velocity.X = Math.Sign(dx) * HopSpeedX * (Math.Abs(dx) > 200f ? 1.6f : 1f);
					Projectile.velocity.Y = -(blocked ? WallHopSpeedY : HopSpeedY);
				}
				else if (Math.Abs(Projectile.velocity.X) < 0.1f) {
					Projectile.velocity.X = 0f;
				}
				if (target == null && Math.Abs(dx) > 4f) {
					Projectile.spriteDirection = Math.Sign(dx);
				}
			}
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);
			if (!isOwner) {
				return;
			}
			// stuck: the summoner isn't getting closer while far away (a wall, a pit, a ledge out of hop reach)
			if (ownerDistance > 160f && ownerDistance >= lastOwnerDistance - 0.5f) {
				stuckTimer++;
			}
			else {
				stuckTimer = 0;
			}
			lastOwnerDistance = ownerDistance;
			bool ownerAbove = owner.Bottom.Y < Projectile.Bottom.Y - 160f && owner.velocity.Y != 0f;
			if (ownerDistance > FlyStart || stuckTimer > StuckTicks || ownerAbove) {
				stuckTimer = 0;
				ChangeState(Mode.Fly, isOwner);
			}
		}

		// --- Fly --------------------------------------------------------------------------------------------------------

		private void UpdateFly(Player owner, bool isOwner, float ownerDistance) {
			Projectile.tileCollide = false;
			Vector2 goal = owner.Center + new Vector2(-owner.direction * (30f + Projectile.minionPos * 24f), -40f);
			Vector2 toGoal = goal - Projectile.Center;
			float speed = Math.Min(FlySpeed, toGoal.Length() / 12f + 2f);
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, toGoal.SafeNormalize(Vector2.Zero) * speed, 0.1f);
			if (Math.Abs(Projectile.velocity.X) > 0.3f) {
				Projectile.spriteDirection = Math.Sign(Projectile.velocity.X);
			}
			if (isOwner && ownerDistance < FlyStop && !Collision.SolidCollision(Projectile.position, Projectile.width, Projectile.height)) {
				ChangeState(Mode.Hop, isOwner);
			}
		}

		private void ChangeState(Mode next, bool isOwner) {
			if (!isOwner || State == next) {
				return;
			}
			State = next;
			Projectile.netUpdate = true;
		}

		// --- Targeting and spitting ---------------------------------------------------------------------------------

		private NPC AcquireTarget(Player owner) {
			if (--retargetTimer <= 0 || !IsValidTarget(targetIndex, owner)) {
				retargetTimer = RetargetInterval;
				targetIndex = SearchTarget(owner);
			}
			return targetIndex >= 0 ? Main.npc[targetIndex] : null;
		}

		private bool IsValidTarget(int index, Player owner) {
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC npc = Main.npc[index];
			return npc.CanBeChasedBy(Projectile) && Vector2.DistanceSquared(npc.Center, owner.Center) < OwnerTargetRange * OwnerTargetRange
				&& Vector2.DistanceSquared(npc.Center, Projectile.Center) < TargetRange * TargetRange * 1.44f
				&& Collision.CanHitLine(Projectile.position, Projectile.width, Projectile.height, npc.position, npc.width, npc.height);
		}

		/// <summary>The owner's whip/right-click target if it is in sight, else the nearest chaseable enemy in sight. The line
		/// check only runs for enemies nearer than the best so far (D1).</summary>
		private int SearchTarget(Player owner) {
			int forced = owner.MinionAttackTargetNPC;
			if (IsValidTarget(forced, owner)) {
				return forced;
			}
			int best = -1;
			float bestSq = TargetRange * TargetRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}
				float distanceSq = Vector2.DistanceSquared(npc.Center, Projectile.Center);
				if (distanceSq >= bestSq || Vector2.DistanceSquared(npc.Center, owner.Center) > OwnerTargetRange * OwnerTargetRange) {
					continue;
				}
				if (Collision.CanHitLine(Projectile.position, Projectile.width, Projectile.height, npc.position, npc.width, npc.height)) {
					best = npc.whoAmI;
					bestSq = distanceSq;
				}
			}
			return best;
		}

		/// <summary>Owner: a glob at the target, led by its velocity over the flight time (capped), synced by vanilla.</summary>
		private void Spit(NPC target) {
			Vector2 mouth = Projectile.Center + new Vector2(Projectile.spriteDirection * 10f, -2f);
			float time = MathHelper.Clamp(Vector2.Distance(mouth, target.Center) / ShotSpeed, 0f, 40f);
			Vector2 aim = target.Center + target.velocity * time * 0.8f;
			Vector2 velocity = (aim - mouth).SafeNormalize(Vector2.UnitX * Projectile.spriteDirection) * ShotSpeed;
			ShotCooldown = ShotInterval;
			Projectile.netUpdate = true;
			SafeSpawn.TryNewProjectile(Projectile.GetSource_FromThis(), mouth, velocity, ModContent.ProjectileType<TarSlimeShot>(),
				Projectile.damage, Projectile.knockBack, out _, Projectile.owner);
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Projectile.velocity.X != oldVelocity.X) {
				hitWall = true;
				Projectile.velocity.X = 0f;
			}
			if (Projectile.velocity.Y != oldVelocity.Y && oldVelocity.Y > 0f) {
				onGround = true;
				if (oldVelocity.Y > 4f && !Main.dedServ && CogpunkClientConfig.RollEffect()) {
					SoundEngine.PlaySound(SoundID.NPCHit1 with { Volume = 0.25f, Pitch = -0.4f, MaxInstances = 2 }, Projectile.Bottom);   // a wet landing
					SafeSpawn.TryNewDust(Projectile.BottomLeft - new Vector2(0f, 4f), Projectile.width, 4, ModContent.DustType<TarSplash>(), out _);
				}
			}
			return false;
		}

		// --- Frames and drawing -----------------------------------------------------------------------------------

		// Vanilla's slime frames (NPC.VanillaFindFrame, case 1): a counter of 1 a tick, 2 while it moves, a frame every 8;
		// a squash while it spits. Visual only (frameCounter is local); the steam wisp is the Living Tar's (clients only).
		private void UpdateFrame(bool grounded) {
			if (!Main.dedServ && Main.rand.NextBool(SteamOneIn)
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, 6, DustID.Smoke, out Dust wisp, 0f, -0.8f, 120, new Color(195, 200, 205), 0.8f)) {
				wisp.noGravity = true;
			}
			if (ShotCooldown > ShotInterval - SpitFrameTicks) {
				Projectile.frame = FrameSquashed;
				Projectile.frameCounter = 0;
				return;
			}
			bool moving = !grounded || Projectile.velocity.X != 0f || State == Mode.Fly;
			Projectile.frameCounter += moving ? 2 : 1;
			if (Projectile.frameCounter >= SlimeFrameCounter) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % FrameCount;
			}
		}

		// Anchored to the hitbox bottom, flipped by direction (the Living Tar's sheet faces left), snapped to whole pixels,
		// never rotated (D4); in flight the wings go behind it.
		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frame = Math.Clamp(Projectile.frame, 0, FrameCount - 1);
			Rectangle source = new(0, frame * FrameStride, FrameWidth, FrameHeight);
			Vector2 origin = new(FrameWidth * 0.5f, FrameHeight - FootPadding);
			Vector2 position = (Projectile.Bottom + new Vector2(0f, Projectile.gfxOffY) - Main.screenPosition).Floor();
			SpriteEffects effects = Projectile.spriteDirection == 1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Color color = Projectile.GetAlpha(lightColor);
			if (State == Mode.Fly && wings?.IsLoaded == true) {
				int flap = (int)(Main.GameUpdateCount / FlyFrameTicks % WingFrames);
				Rectangle wingSource = new(0, flap * WingStride, WingWidth, WingHeight);
				Vector2 wingOrigin = origin + new Vector2(WingCellX, WingCellY);
				Main.EntitySpriteDraw(wings.Value, position, wingSource, color, 0f, wingOrigin, 1f, effects);
			}
			Main.EntitySpriteDraw(texture, position, source, color, 0f, origin, 1f, effects);
			return false;
		}
	}
}
