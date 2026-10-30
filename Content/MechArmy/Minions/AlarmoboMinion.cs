using System;
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
using R = Cogpunk.Content.MechArmy.MechArmyRigData;

namespace Cogpunk.Content.MechArmy.Minions
{
	/// <summary>
	/// The Alarm Head's minion (user-set 2026-10-28): a reprogrammed Annoy-o-tron, the same alarm box on treads with a
	/// verdigris beacon instead of the red one (D3 colour code). One minion slot. It never attacks: it rolls along the
	/// ground after its owner (each one keeps its own spot behind them, so a pack spreads out), hops ledges, and zips back
	/// through walls when it falls far behind or gets stuck. Every player within <see cref="NPCs.AnnoyOTron.AlarmRange"/>
	/// gets its bonus (<see cref="AlarmPlayer"/>).
	/// <para>Movement follows <c>ScrappybotPet</c> (ground follower, owner-decided modes in <c>ai[0]</c>, synced; every
	/// client runs the same physics, D2). Drawn like the enemy: three grid planes and the spinning beacon on top
	/// (<see cref="DepthLayers.DrawWalker"/>, cells from <see cref="MechArmyRigData"/>'s Annoy* values; art:
	/// art/mecharmy/make_mecharmy_art.py). D1: no allocation; textures cached once; light and sound client-side.</para>
	/// </summary>
	public class AlarmoboMinion : CogpunkProjectile
	{
		private enum Mode { Follow, Zip }

		public const float MinionSlots = 1f;
		public const float Gravity = 0.4f;
		public const float MaxFallSpeed = 10f;
		public const float Acceleration = 0.25f;
		public const float WalkSpeed = 4.5f;
		public const float RunSpeed = 8f;
		public const float JumpSpeed = 7.5f;
		public const float FollowOffset = 44f;
		public const float FollowSpacing = 30f;          // each further Alarmobô keeps this much further back
		public const float ZipStartDistance = 480f;
		public const float ZipStopDistance = 120f;
		public const float ZipMaxSpeed = 14f;
		public const float TeleportDistance = 2000f;
		public const int StuckTicksBeforeZip = 45;
		public const float RunAnimDistance = 4f;
		public const int BeaconTicks = 4;
		public const float MaxParallax = 2f;

		private static Asset<Texture2D> far, near, glow, beacon, beaconGlow;

		private Mode State {
			get => (Mode)(int)Projectile.ai[0];
			set => Projectile.ai[0] = (float)value;
		}

		private ref float StuckTicks => ref Projectile.localAI[0];
		private ref float RunDistance => ref Projectile.localAI[1];
		private ref float Played => ref Projectile.localAI[2];

		private bool onGround;
		private bool hitWall;
		private int frame;

		public override void Unload() {
			far = near = glow = beacon = beaconGlow = null;
		}

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.AnnoyFrames;
			Main.projPet[Type] = true;
			ProjectileID.Sets.MinionSacrificable[Type] = true;
			far = DepthLayers.RequestOptional(Texture + "_Far");          // null on a dedicated server (D0)
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
			beacon = DepthLayers.RequestOptional(Texture + "_Beacon");
			beaconGlow = DepthLayers.RequestOptional(Texture + "_BeaconGlow");
		}

		public override void SetDefaults() {
			Projectile.width = 24;
			Projectile.height = 30;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.minion = true;
			Projectile.minionSlots = MinionSlots;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.netImportant = true;
			Projectile.timeLeft = 2;
		}

		public override bool? CanCutTiles() {
			return false;
		}

		public override bool MinionContactDamage() {
			return false;
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			int buff = ModContent.BuffType<AlarmoboBuff>();
			if (!owner.active || owner.dead) {
				owner.ClearBuff(buff);
				return;
			}
			if (owner.HasBuff(buff)) {
				Projectile.timeLeft = 2;
			}
			bool isOwner = Projectile.owner == Main.myPlayer;
			bool grounded = onGround;
			bool blocked = hitWall;
			onGround = false;
			hitWall = false;

			float distanceSq = Vector2.DistanceSquared(owner.Center, Projectile.Center);
			if (isOwner && distanceSq > TeleportDistance * TeleportDistance) {
				Projectile.Center = owner.Center;
				Projectile.velocity = Vector2.Zero;
				ChangeState(Mode.Follow, isOwner);
			}
			if (State == Mode.Zip) {
				UpdateZip(owner, isOwner);
			}
			else {
				UpdateFollow(owner, isOwner, grounded, blocked, distanceSq);
			}

			// D0: never let NaN movement through (it makes the minion vanish and breaks drawing).
			MathSafety.Sanitize(ref Projectile.velocity);
			if (!MathSafety.IsFinite(Projectile.position)) {
				Projectile.Center = owner.Center;
			}
			SoundTheAlarm();
			UpdateFrame(grounded);
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Every client: the local player hears it if within range (its own client applies the bonus).</summary>
		private void SoundTheAlarm() {
			if (Main.dedServ) {
				return;
			}
			Player local = Main.LocalPlayer;
			if (local.active && !local.dead && Vector2.DistanceSquared(local.Center, Projectile.Center) <= NPCs.AnnoyOTron.AlarmRange * NPCs.AnnoyOTron.AlarmRange) {
				local.GetModPlayer<AlarmPlayer>().Hear();
			}
		}

		private void UpdateFollow(Player owner, bool isOwner, bool grounded, bool blocked, float distanceSq) {
			Projectile.tileCollide = true;
			float spot = FollowOffset + FollowSpacing * Projectile.minionPos;
			float dx = owner.Center.X - owner.direction * spot - Projectile.Center.X;
			float absDx = Math.Abs(dx);
			bool wantsToMove = absDx > 20f;
			if (wantsToMove) {
				float maxSpeed = absDx > 160f ? RunSpeed : WalkSpeed;
				Projectile.velocity.X = MathHelper.Clamp(Projectile.velocity.X + Math.Sign(dx) * Acceleration, -maxSpeed, maxSpeed);
				Projectile.spriteDirection = Math.Sign(dx);
			}
			else {
				Projectile.velocity.X *= 0.85f;
				if (Math.Abs(Projectile.velocity.X) < 0.05f) {
					Projectile.velocity.X = 0f;
				}
				Projectile.spriteDirection = owner.Center.X >= Projectile.Center.X ? 1 : -1;
			}
			Collision.StepUp(ref Projectile.position, ref Projectile.velocity, Projectile.width, Projectile.height, ref Projectile.stepSpeed, ref Projectile.gfxOffY);
			bool ownerAbove = owner.velocity.Y == 0f && owner.Bottom.Y < Projectile.Bottom.Y - 48f && absDx < 160f;
			if (grounded && ((wantsToMove && blocked) || ownerAbove)) {
				Projectile.velocity.Y = -JumpSpeed;
			}
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);
			StuckTicks = wantsToMove && blocked && absDx > 120f ? StuckTicks + 1f : 0f;
			if (isOwner && (distanceSq > ZipStartDistance * ZipStartDistance || StuckTicks > StuckTicksBeforeZip)) {
				ChangeState(Mode.Zip, isOwner);
			}
		}

		/// <summary>Through walls, straight back to the owner (its treads spin in the air, a puff of steam behind).</summary>
		private void UpdateZip(Player owner, bool isOwner) {
			Projectile.tileCollide = false;
			Vector2 target = owner.Center + new Vector2(-owner.direction * FollowOffset, -24f);
			Vector2 toTarget = target - Projectile.Center;
			float speed = Math.Min(toTarget.Length() / 12f + 2f, ZipMaxSpeed);
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, toTarget.SafeNormalize(Vector2.Zero) * speed, 0.1f);
			if (Math.Abs(Projectile.velocity.X) > 0.2f) {
				Projectile.spriteDirection = Math.Sign(Projectile.velocity.X);
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect() && Main.rand.NextBool(3)
				&& SafeSpawn.TryNewDust(Projectile.Bottom + new Vector2(-8f, -6f), 16, 6, DustID.Smoke, out Dust puff, 0f, 1f, 100, new Color(238, 241, 243))) {
				puff.noGravity = true;
				puff.scale = 0.9f;
			}
			if (isOwner && Vector2.DistanceSquared(owner.Center, Projectile.Center) < ZipStopDistance * ZipStopDistance
				&& owner.velocity.Y == 0f && !Collision.SolidCollision(Projectile.position, Projectile.width, Projectile.height)) {
				ChangeState(Mode.Follow, isOwner);
			}
		}

		/// <summary>Only the owner decides; the change reaches the server and other clients through ai[] (D2).</summary>
		private void ChangeState(Mode next, bool isOwner) {
			if (!isOwner) {
				return;
			}
			State = next;
			StuckTicks = 0f;
			Projectile.netUpdate = true;
		}

		private void UpdateFrame(bool grounded) {
			if (State == Mode.Zip || (!grounded && Math.Abs(Projectile.velocity.Y) > 0.5f)) {
				frame = R.AnnoyHop;
				return;
			}
			float speed = Math.Abs(Projectile.velocity.X);
			if (speed > 0.3f) {
				RunDistance += speed;
				if (RunDistance >= RunAnimDistance * R.AnnoyDriveFrames) {
					RunDistance -= RunAnimDistance * R.AnnoyDriveFrames;
				}
				frame = R.AnnoyDrive + (int)(RunDistance / RunAnimDistance) % R.AnnoyDriveFrames;
				return;
			}
			frame = R.AnnoyIdle + (int)(Main.GameUpdateCount / 8 % 2);
		}

		private int BeaconFrame => (int)((Main.GameUpdateCount / BeaconTicks + (uint)Projectile.whoAmI) % R.BeaconFrames);

		private Vector2 BeaconPoint => Projectile.Bottom + new Vector2(0f, -22f * 2f + R.AnnoyBeaconY[Math.Clamp(frame, 0, R.AnnoyFrames - 1)]);

		/// <summary>Clients: a short chirp of the siren when it is set down, and its sweeping verdigris light.</summary>
		private void Effects() {
			if (Played == 0f) {
				Played = 1f;
				SoundEngine.PlaySound(MechArmySounds.Alarm with { Volume = 0.25f, Pitch = 0.3f }, Projectile.Center);
			}
			float facing = MathF.Cos(MathHelper.TwoPi * BeaconFrame / R.BeaconFrames);
			float strength = 0.4f + 0.35f * Math.Max(0f, facing);
			Lighting.AddLight(BeaconPoint, 0.25f * strength, 0.8f * strength, 0.65f * strength);
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

		// Drawn by hand like the Annoy-o-tron (MechWalker): the planes from their grid sheets anchored on the ground under
		// the hitbox, mirrored by direction, never rotated or scaled (D4), then the glow and the spinning beacon.
		public override bool PreDraw(ref Color lightColor) {
			Vector2 anchor = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = Projectile.spriteDirection == 1;             // the art faces left
			Color light = Projectile.GetAlpha(lightColor);
			int f = Math.Clamp(frame, 0, R.AnnoyFrames - 1);
			DepthLayers.DrawWalker(Main.spriteBatch, far?.Value, TextureAssets.Projectile[Type].Value, near?.Value, f, R.AnnoyCellWidth,
				R.AnnoyCellHeight, R.CellPadding, R.AnnoyOriginX, R.AnnoyOriginY, anchor, light, flip, MaxParallax);
			if (glow?.IsLoaded == true) {
				DepthLayers.DrawCell(Main.spriteBatch, glow.Value, f, 1, R.AnnoyCellWidth, R.AnnoyCellHeight, R.CellPadding, R.AnnoyOriginX,
					R.AnnoyOriginY, anchor, 0, Color.White, flip);
			}
			Vector2 at = anchor + new Vector2(0f, R.AnnoyBeaconY[f]);
			int b = BeaconFrame;
			if (beacon?.IsLoaded == true) {
				DepthLayers.DrawCell(Main.spriteBatch, beacon.Value, b, 1, R.AnnoyCellWidth, R.AnnoyCellHeight, R.CellPadding, R.AnnoyOriginX,
					R.AnnoyOriginY, at, 0, light, flip);
			}
			if (beaconGlow?.IsLoaded == true) {
				DepthLayers.DrawCell(Main.spriteBatch, beaconGlow.Value, b, 1, R.AnnoyCellWidth, R.AnnoyCellHeight, R.CellPadding, R.AnnoyOriginX,
					R.AnnoyOriginY, at, 0, Color.White, flip);
			}
			return false;
		}
	}
}
