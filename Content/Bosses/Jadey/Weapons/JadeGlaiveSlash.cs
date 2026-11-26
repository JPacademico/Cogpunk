using System;
using System.Collections.Generic;
using Cogpunk.Content.Gems;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.Jadey.Weapons.JadeGlaiveRigData;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// One slash of the <see cref="JadeCursedGlaives"/> (2026-11-17): a glaive swept along a diagonal arc in perspective. Kind 0
	/// (<c>ai[0]</c>) is the front hand's "\" (down and across), kind 1 the back hand's "/" (up and across); two in a row cross
	/// in an X in front of the wielder.
	/// <para>The look is pre-rendered (art/bosses/jadey/make_jadey_loot_art.py; D4 rule 14: never turned at runtime): the swing is a
	/// circle in a plane tilted towards the viewer, so it projects to a thin ellipse along its diagonal; the glaive is rendered
	/// in 3D at each of <see cref="R.FramesPerSlash"/> frames (foreshortened as it turns, a step bigger and brighter as it
	/// comes near, a step smaller and darker behind the wielder) with ONE slash along the arc (<c>_Trail</c>, drawn added: light,
	/// never a dark smear; 2026-11-18, user: "one bigger slash effect", it was the blade's trail plus a separate wave). The glaive
	/// is the user's own art since 2026-11-18. Frames that pass behind the body are drawn behind the player, the rest over them
	/// (<see cref="DrawBehind"/>, from the generated <see cref="R.Near"/>). The glaive's hub sits in the hand: the hand is
	/// vanilla's (<c>GetFrontHandPosition</c> / <c>GetBackHandPosition</c> on the composite arm aimed at the rendered hub), and the
	/// frame is drawn so its hub lands there.</para>
	/// <para>Hits: the blade from hub to tip at the swing's current point, swept from the last tick's (<see cref="R.SamplesPerSlash"/>
	/// generated samples, interpolated by the swing's progress), a capsule <see cref="BladeRadius"/> px thick
	/// (<see cref="SwingPose.CapsuleHitsRect"/>); each enemy once a slash (local immunity); not through walls
	/// (<c>ownerHitCheck</c>); every hit adds a jade curse stack (<see cref="JadeCurseNPC.Hit"/>).</para>
	/// <para><b>Aimed</b> (user, 2026-11-26: "jade cursed glaives only attacks to the right and isnt follow the cursor on the basic
	/// attacks ... make the basic atack acrtualy directional so it follows the player cursor (dont change design)"): the
	/// slash is the same pre-rendered sweep, turned as a whole towards the cursor: <c>ai[2]</c> carries the side and the tilt
	/// (<see cref="PackAim"/>), and the arm, the blade's hits and the drawn frame all turn by the tilt about the hand. Turning the
	/// frame is the one runtime rotation of a pre-rendered sprite here, asked for by the user (vanilla turns every swung
	/// weapon the same way).</para>
	/// <para><b>Tracks the cursor through the swing</b> (user, 2026-11-26, 0.2.2: "the jade cursed glaive attacks are still not
	/// full dinamic tracking the player cursor (for example its never properly attacking for the left)"): the aim was taken once,
	/// as the slash was spawned, and the wielder kept facing wherever it last walked, so a slash to its back swung out of the
	/// wrong shoulder with the X drawn behind the body. Now the owner turns the slash towards the cursor every tick
	/// (<see cref="AimFollow"/> of the way to its tilt, the side at once) and every side turns the wielder to the slash's side
	/// (<c>ChangeDir</c>, from the synced aim), as vanilla's held projectiles do.</para>
	/// <para>D2: the owner's projectile; its kind, length (<c>ai[1]</c>: the use's <c>itemAnimationMax</c>) and aim (<c>ai[2]</c>,
	/// sent at once when it changes side, else at most every <see cref="AimSyncTicks"/> ticks when it turned more than
	/// <see cref="AimSyncTilt"/>) are synced, its age counts on every side, and it follows its owner's synced position. D0: it
	/// dies with its owner, its use, or its length; every table read is clamped; a non-finite cursor is ignored. D1: no
	/// allocation; textures cached on clients.</para>
	/// </summary>
	public class JadeGlaiveSlash : CogpunkProjectile
	{
		public const float BladeRadius = 10f;
		public const float AimFollow = 0.5f;               // of the way to the cursor's tilt a tick (2026-11-26, 0.2.2)
		public const int AimSyncTicks = 3;
		public const float AimSyncTilt = 0.04f;            // radians
		private static Asset<Texture2D> trail;

		private int Kind => Projectile.ai[0] >= 0.5f ? 1 : 0;
		private float Length => Math.Max(1f, Projectile.ai[1]);
		private ref float Age => ref Projectile.localAI[0];
		private ref float SinceSync => ref Projectile.localAI[1];
		private float sentAim;                             // the owner: the aim last sent to the others

		public override void SetStaticDefaults() {
			if (!Main.dedServ && ModContent.HasAsset(Texture + "_Trail")) {
				trail = ModContent.Request<Texture2D>(Texture + "_Trail");
			}
		}

		public override void Unload() {
			trail = null;
		}

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Melee;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.ownerHitCheck = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
			Projectile.timeLeft = 120;
			Projectile.hide = true;
		}

		/// <summary>The aim in one float for <c>ai[2]</c>: its sign is the side the cursor is on, its size 2 + the tilt
		/// (-pi/2 straight up .. pi/2 straight down; 2 keeps it clear of 0); 0 means "not aimed" (the wielder's facing, level),
		/// so a slash from an older version still swings.</summary>
		public static float PackAim(Vector2 toCursor) {
			if (!MathSafety.IsFinite(toCursor) || toCursor == Vector2.Zero) {
				return 0f;
			}
			int side = toCursor.X < 0f ? -1 : 1;
			float tilt = MathF.Atan2(toCursor.Y, MathF.Abs(toCursor.X));
			return side * (2f + tilt);
		}

		/// <summary>The side (1 right, -1 left) and the tilt (radians, down positive) this slash was aimed with.</summary>
		private void Aim(Player owner, out int dir, out float tilt) {
			float a = Projectile.ai[2];
			if (a == 0f || !float.IsFinite(a)) {
				dir = owner.direction == -1 ? -1 : 1;
				tilt = 0f;
				return;
			}
			dir = a < 0f ? -1 : 1;
			tilt = MathHelper.Clamp(MathF.Abs(a) - 2f, -MathHelper.PiOver2, MathHelper.PiOver2);
		}

		/// <summary>A facing-right rig offset turned by the tilt, then mirrored to the side.</summary>
		private static Vector2 Turn(Vector2 v, float tilt, int dir) {
			float c = MathF.Cos(tilt), s = MathF.Sin(tilt);
			return new Vector2((v.X * c - v.Y * s) * dir, v.X * s + v.Y * c);
		}

		/// <summary>The swing's progress, 0 to 1.</summary>
		private float Progress => MathHelper.Clamp(Age / Length, 0f, 1f);

		/// <summary>Hub and tip (facing right, from the wielder's centre, px) at progress <paramref name="p"/>, between samples.</summary>
		private void Sample(float p, out Vector2 hub, out Vector2 tip) {
			float s = MathHelper.Clamp(p, 0f, 1f) * (R.SamplesPerSlash - 1);
			int i = Math.Clamp((int)s, 0, R.SamplesPerSlash - 2);
			float f = s - i;
			int a = Kind * R.SamplesPerSlash + i, b = a + 1;
			hub = new Vector2(MathHelper.Lerp(R.HubX[a], R.HubX[b], f), MathHelper.Lerp(R.HubY[a], R.HubY[b], f));
			tip = new Vector2(MathHelper.Lerp(R.TipX[a], R.TipX[b], f), MathHelper.Lerp(R.TipY[a], R.TipY[b], f));
		}

		private int Frame => Kind * R.FramesPerSlash + Math.Clamp((int)(Progress * R.FramesPerSlash), 0, R.FramesPerSlash - 1);

		public override void OnSpawn(IEntitySource source) {
			sentAim = Projectile.ai[2];                    // the spawn carried it to everyone
		}

		/// <summary>The owner: the slash turned towards the cursor (its side at once, its tilt <see cref="AimFollow"/> of the way),
		/// sent to the others when it changes side or has turned enough.</summary>
		private void TrackCursor(Player owner) {
			Vector2 to = Main.MouseWorld - owner.MountedCenter;
			if (!MathSafety.IsFinite(to) || to.LengthSquared() < 1f) {
				return;
			}
			int side = to.X < 0f ? -1 : 1;
			float want = MathF.Atan2(to.Y, MathF.Abs(to.X));
			float a = Projectile.ai[2];
			float tilt = a == 0f || !float.IsFinite(a) ? want : MathHelper.Clamp(MathF.Abs(a) - 2f, -MathHelper.PiOver2, MathHelper.PiOver2);
			tilt = MathHelper.Clamp(MathHelper.Lerp(tilt, want, AimFollow), -MathHelper.PiOver2, MathHelper.PiOver2);
			float packed = side * (2f + tilt);
			Projectile.ai[2] = packed;
			SinceSync++;
			bool flipped = (packed < 0f) != (sentAim < 0f);
			if (flipped || (SinceSync >= AimSyncTicks && MathF.Abs(MathF.Abs(packed) - MathF.Abs(sentAim)) > AimSyncTilt)) {
				sentAim = packed;
				SinceSync = 0f;
				Projectile.netUpdate = true;
			}
		}

		public override void AI() {
			Player owner = Main.player[Projectile.owner];
			if (!owner.active || owner.dead || owner.CCed || (Age > 1f && owner.itemAnimation <= 0) || Age > Length + 1f) {
				Projectile.Kill();
				return;
			}
			Age++;
			if (Projectile.owner == Main.myPlayer) {
				TrackCursor(owner);
			}
			Aim(owner, out int dir, out float tilt);
			Projectile.direction = Projectile.spriteDirection = dir;
			owner.ChangeDir(dir);                          // every side: the wielder faces the slash (front arm, X before the body)
			owner.heldProj = Projectile.whoAmI;
			Sample(Progress, out Vector2 hub, out Vector2 _);
			Vector2 toHub = Turn(new Vector2(hub.X - R.ShoulderX, hub.Y - R.ShoulderY), tilt, dir);   // the arm turns on the shoulder
			float arm = toHub.ToRotation() - MathHelper.PiOver2;
			if (!float.IsFinite(arm)) {
				arm = 0f;
			}
			Vector2 hand;
			if (Kind == 0) {
				owner.SetCompositeArmFront(true, Player.CompositeArmStretchAmount.Full, arm);
				hand = owner.GetFrontHandPosition(Player.CompositeArmStretchAmount.Full, arm);
			}
			else {
				owner.SetCompositeArmBack(true, Player.CompositeArmStretchAmount.Full, arm);
				hand = owner.GetBackHandPosition(Player.CompositeArmStretchAmount.Full, arm);
			}
			Projectile.Center = hand;                          // the hub, in the hand
			Projectile.velocity = Vector2.Zero;
		}

		/// <summary>The blade at this tick's point and the last tick's, from the hub in the hand.</summary>
		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (Progress < 1f / R.FramesPerSlash) {
				return false;                                   // the wind-up, behind the wielder: no hits yet
			}
			Aim(Main.player[Projectile.owner], out int dir, out float tilt);
			float p = Progress, step = 1f / Length;
			for (int k = 0; k < 3; k++) {
				Sample(p - step * k * 0.5f, out Vector2 hub, out Vector2 tip);
				Vector2 blade = Turn(tip - hub, tilt, dir);
				if (SwingPose.CapsuleHitsRect(Projectile.Center, Projectile.Center + blade, BladeRadius, targetHitbox)) {
					return true;
				}
			}
			return false;
		}

		/// <summary>x<see cref="JadeCursedGlaives.PetrifiedBonus"/> on an enemy turned to jade (user, 2026-11-17: "the 50% should work for
		/// the basic glaive slashes as well").</summary>
		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			modifiers.HitDirectionOverride = Projectile.direction == -1 ? -1 : 1;
			if (JadeCurseNPC.Petrified(target)) {
				modifiers.SourceDamage *= JadeCursedGlaives.PetrifiedBonus;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			JadeCurseNPC.Hit(target);
			if (Main.dedServ || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < 5; i++) {
				if (SafeSpawn.TryNewDust(target.position, target.width, target.height, DustID.GemEmerald, out Dust shard)) {
					shard.velocity = Main.rand.NextVector2Circular(2.5f, 2.5f);
					shard.noGravity = true;
				}
			}
		}

		public override void DrawBehind(int index, List<int> behindNPCsAndTiles, List<int> behindNPCs, List<int> behindProjectiles, List<int> overPlayers,
			List<int> overWiresUI) {
			int f = Math.Clamp(Frame, 0, R.Near.Length - 1);
			if (R.Near[f] != 0) {
				overPlayers.Add(index);
			}
			else {
				behindProjectiles.Add(index);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D sheet = TextureAssets.Projectile[Type].Value;
			int f = Frame;
			int s = Math.Clamp(Kind * R.SamplesPerSlash + f % R.FramesPerSlash * 2, 0, R.HubX.Length - 1);
			bool left = Projectile.direction == -1;
			Aim(Main.player[Projectile.owner], out _, out float tilt);
			float rotation = left ? -tilt : tilt;                    // the mirrored sweep turns the other way to tilt down
			// the cell's origin is the wielder's centre; the hub (in the hand) is HubX/HubY from it
			Vector2 origin = new(left ? R.CellWidth - (R.OriginX + R.HubX[s]) : R.OriginX + R.HubX[s], R.OriginY + R.HubY[s]);
			Vector2 at = Projectile.Center - Main.screenPosition;
			at = new Vector2(MathF.Round(at.X), MathF.Round(at.Y));
			Rectangle frame = new(Kind * (R.CellWidth + R.Gap), f % R.FramesPerSlash * (R.CellHeight + R.Gap), R.CellWidth, R.CellHeight);   // a column a kind
			SpriteEffects flip = left ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			if (trail?.IsLoaded == true && frame.Bottom <= trail.Value.Height) {
				Main.EntitySpriteDraw(trail.Value, at, frame, new Color(255, 255, 255, 0) * 0.85f, rotation, origin, 1f, flip);
			}
			if (frame.Bottom <= sheet.Height) {
				Color light = Lighting.GetColor(Projectile.Center.ToTileCoordinates());
				Color lit = Color.Lerp(light, Color.White, 0.35f);       // jade catches the light
				Main.EntitySpriteDraw(sheet, at, frame, lit, rotation, origin, 1f, flip);
			}
			return false;
		}
	}
}
