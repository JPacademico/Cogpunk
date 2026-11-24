using System;
using Cogpunk.Content.Gems;
using Cogpunk.Content.Mechanist;
using Cogpunk.Content.Mechanist.Weapons;
using Cogpunk.Core.Combat;
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

namespace Cogpunk.Content.Research.Weapons
{
	/// <summary>
	/// The <see cref="JadeRefractor"/>'s beam (user, 2026-11-24: "a continuous thin jade colored laser that aply jade curse and deal
	/// 50% more damage to jade petrified enemies"): one held projectile that lives while its owner keeps firing, with the refractor
	/// in the owner's hand pointing it at the cursor.
	/// <list type="bullet">
	/// <item>The line: from the lens to the first solid block, at most <see cref="DiamondCutterBeam.Range"/>, cut inside the
	/// <see cref="DiamondCutterBeam.MaxTargets"/>th enemy it crosses (<see cref="DiamondCutterBeam.Measure"/>, the cutter's own
	/// measure, made every tick on every side for the drawing; the hits are the owner's, from the same line).</item>
	/// <item>The hits: each enemy on the line every <see cref="HitInterval"/> ticks (vanilla's local hit cooldown), ignoring
	/// <see cref="DiamondCutterBeam.ArmorIgnore"/> of its defense, x<see cref="JadeRefractor.PetrifiedBonus"/> on an enemy turned
	/// to jade, a jade curse stack on its first hit and every <see cref="CurseEvery"/>rd after (<see cref="JadeCurseNPC.Hit"/>:
	/// two stacks a second, an enemy turned to jade after about a second and a half of beam; my call).</item>
	/// <item>Its life: refreshed every tick; the owner ends it when the button is let go, the refractor is put away, items are
	/// locked (an overheat) or no use has run for <see cref="GraceTicks"/> ticks (the steam ran out: a use pays as it starts).</item>
	/// <item>The looks: the refractor drawn at the hand at the beam's angle (vanilla's held-gun way: flipped vertically when
	/// aiming left), the arm held out along it; the beam a thin jade line of <see cref="SegmentLength"/> px pieces, its frames
	/// shimmering, a star at the lens and where it stops, all added onto the scene (alpha 0); light along it; a hum.</item>
	/// </list>
	/// <para>D2: the owner's projectile; its direction is the velocity (never moved: <see cref="ShouldUpdatePosition"/>), sent
	/// when it turns, at most every <see cref="SyncTicks"/> ticks; other clients follow the owner and keep it until the owner's
	/// kill reaches them. D0/D1: the wall walk and the enemy pass are the cutter's (capped, no allocation); the per-enemy curse
	/// counter is one array a beam, made on its first hit; dust and light on clients only, capped.</para>
	/// </summary>
	public class JadeRefractorBeam : CogpunkProjectile
	{
		public const int HitInterval = 10;                        // six hits a second (D3: 13 x 6 x 1.12 = 87.4 eff DPS)
		public const int CurseEvery = 3;                          // a stack on the first hit and every 3rd (every 2nd before the 2026-11-24 nerf)
		public const int GraceTicks = 4;                          // between two uses of the held refractor
		public const int SyncTicks = 3;
		public const float SyncAngle = 0.02f;
		public const float AimFollow = 0.45f;                     // of the way to the cursor a tick: steady, not twitchy
		public const int SegmentLength = 16, BeamHeight = 6, BeamFrames = 4, BeamStride = BeamHeight + 2, BeamFrameTicks = 3;
		public const int SparkSize = 14, SparkFrames = 4, SparkStride = SparkSize + 2, SparkFrameTicks = 3;
		public const int HumTicks = 18;
		public const int MaxBeamLights = 8;

		private static Asset<Texture2D> spark, gun;
		private byte[] curseHits;

		private ref float Idle => ref Projectile.localAI[0];
		private ref float Age => ref Projectile.localAI[1];
		private ref float SentAngle => ref Projectile.localAI[2];
		private float length;

		public override void SetStaticDefaults() {
			if (!Main.dedServ) {
				spark = DepthLayers.RequestOptional("Cogpunk/Content/Research/Weapons/JadeRefractorSpark");
				gun = DepthLayers.RequestOptional("Cogpunk/Content/Research/Weapons/JadeRefractor");
			}
			ProjectileID.Sets.DrawScreenCheckFluff[Type] = (int)DiamondCutterBeam.Range + 64;
		}

		public override void Unload() {
			spark = gun = null;
		}

		public override void SetDefaults() {
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = ModContent.GetInstance<MechanistDamage>();
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = 2;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = HitInterval;
			Projectile.aiStyle = -1;
		}

		public override bool ShouldUpdatePosition() => false;

		public override void AI() {
			Player owner = Main.player[Projectile.owner];
			if (!owner.active || owner.dead) {
				Projectile.Kill();
				return;
			}
			Age++;
			MathSafety.Sanitize(ref Projectile.velocity);
			Vector2 dir = Projectile.velocity.SafeNormalize(new Vector2(owner.direction, 0f));
			if (Projectile.owner == Main.myPlayer) {
				Idle = owner.itemAnimation > 0 ? 0f : Idle + 1f;
				bool firing = owner.channel && owner.HeldItem?.ModItem is JadeRefractor && !owner.noItems && !owner.CCed
					&& !owner.GetModPlayer<SteamPlayer>().Overheated && Idle <= GraceTicks;
				if (!firing) {
					Projectile.Kill();
					return;
				}
				Vector2 aim = (Main.MouseWorld - owner.MountedCenter).SafeNormalize(dir);
				dir = Vector2.Lerp(dir, aim, AimFollow).SafeNormalize(aim);
				float angle = dir.ToRotation();
				if (Math.Abs(MathHelper.WrapAngle(angle - SentAngle)) > SyncAngle && (int)Age % SyncTicks == 0) {
					SentAngle = angle;
					Projectile.netUpdate = true;
				}
				Projectile.velocity = dir;
			}
			Projectile.timeLeft = 2;
			Projectile.rotation = dir.ToRotation();
			Vector2 hand = owner.RotatedRelativePoint(owner.MountedCenter, true);
			Vector2 muzzle = JadeRefractor.Muzzle(hand, dir);
			Projectile.Center = Collision.CanHit(hand, 0, 0, muzzle, 0, 0) ? muzzle : hand;
			length = DiamondCutterBeam.Measure(Projectile.Center, dir);
			// the refractor in the hand, the arm along it
			owner.ChangeDir(dir.X >= 0f ? 1 : -1);
			owner.heldProj = Projectile.whoAmI;
			owner.itemRotation = (dir * owner.direction).ToRotation();
			owner.SetCompositeArmFront(true, Player.CompositeArmStretchAmount.Full, Projectile.rotation - MathHelper.PiOver2);
			if (!Main.dedServ) {
				Effects(dir);
			}
		}

		/// <summary>Clients: light along the line, a mote at its end now and then, the hum.</summary>
		private void Effects(Vector2 dir) {
			int lights = Math.Min(MaxBeamLights, 1 + (int)(length / 96f));
			for (int k = 0; k <= lights; k++) {
				Lighting.AddLight(Projectile.Center + dir * (length * k / lights), 0.18f, 0.5f, 0.32f);
			}
			if ((int)Age % HumTicks == 1) {
				SoundEngine.PlaySound(SoundID.Item15 with { Pitch = 0.35f, Volume = 0.45f, MaxInstances = 2 }, Projectile.Center);
			}
			if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()) {
				if (SafeSpawn.TryNewDust(Projectile.Center + dir * length - new Vector2(4f), 8, 8, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(1.5f, 1.5f);
					d.scale = 0.8f;
				}
			}
		}

		public override bool? CanHitNPC(NPC target) => NPCID.Sets.CountsAsCritter[target.type] ? false : null;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 dir = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			return SwingPose.CapsuleHitsRect(Projectile.Center, Projectile.Center + dir * length, DiamondCutterBeam.HitRadius, targetHitbox);
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			modifiers.ScalingArmorPenetration += DiamondCutterBeam.ArmorIgnore;
			if (JadeCurseNPC.Petrified(target)) {
				modifiers.SourceDamage *= JadeRefractor.PetrifiedBonus;
			}
		}

		/// <summary>The owner (vanilla works out a player projectile's hits there): the curse on the first hit and every
		/// <see cref="CurseEvery"/>nd after, counted per enemy for this beam.</summary>
		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (target.whoAmI < 0 || target.whoAmI >= Main.maxNPCs) {
				return;
			}
			curseHits ??= new byte[Main.maxNPCs];
			int n = curseHits[target.whoAmI];
			curseHits[target.whoAmI] = (byte)((n + 1) % CurseEvery);
			if (n == 0) {
				JadeCurseNPC.Hit(target);
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				for (int k = 0; k < 2; k++) {
					if (SafeSpawn.TryNewDust(target.position, target.width, target.height, DustID.GemEmerald, out Dust d)) {
						d.noGravity = true;
						d.velocity *= 0.5f;
					}
				}
			}
		}

		// --- looks -----------------------------------------------------------------------------------------------------------

		public override bool PreDraw(ref Color lightColor) {
			Player owner = Main.player[Projectile.owner];
			Vector2 dir = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			DrawBeam(dir);
			DrawGun(owner, dir, lightColor);
			return false;
		}

		/// <summary>The line in <see cref="SegmentLength"/> px pieces of the frame for its age (a shimmer running along it), the
		/// last piece cut to fit, the stars at both ends; added onto the scene.</summary>
		private void DrawBeam(Vector2 dir) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			Color colour = new(255, 255, 255, 0);
			Vector2 start = Projectile.Center - Main.screenPosition;
			Vector2 origin = new(0f, BeamHeight / 2f);
			int frame0 = (int)(Age / BeamFrameTicks);
			if (tex.Height >= BeamFrames * BeamStride - 2) {
				int piece = 0;
				for (float t = 0f; t < length; t += SegmentLength, piece++) {
					int w = (int)Math.Min(SegmentLength, length - t);
					if (w <= 0) {
						break;
					}
					int f = ((frame0 - piece) % BeamFrames + BeamFrames) % BeamFrames;
					Rectangle source = new(0, f * BeamStride, w, BeamHeight);
					Main.EntitySpriteDraw(tex, start + dir * t, source, colour, Projectile.rotation, origin, 1f, SpriteEffects.None);
				}
			}
			if (spark?.IsLoaded == true) {
				int sf = (int)(Age / SparkFrameTicks) % SparkFrames;
				Rectangle source = new(0, sf * SparkStride, SparkSize, SparkSize);
				if (source.Bottom <= spark.Value.Height) {
					Vector2 o = new(SparkSize / 2f);
					Main.EntitySpriteDraw(spark.Value, start, source, colour, 0f, o, 1f, SpriteEffects.None);
					Main.EntitySpriteDraw(spark.Value, start + dir * length, source, colour, 0f, o, 1f, SpriteEffects.None);
				}
			}
		}

		/// <summary>The refractor in the hand: its grip (<see cref="JadeRefractor.GripOrigin"/>) on the hand, turned to the beam,
		/// flipped vertically when aiming left (vanilla's held guns), lit by the world.</summary>
		private static void DrawGun(Player owner, Vector2 dir, Color light) {
			if (gun?.IsLoaded != true) {
				return;
			}
			Texture2D tex = gun.Value;
			bool left = dir.X < 0f;
			Vector2 origin = left ? new Vector2(JadeRefractor.GripOrigin.X, tex.Height - JadeRefractor.GripOrigin.Y) : JadeRefractor.GripOrigin;
			Vector2 hand = owner.RotatedRelativePoint(owner.MountedCenter, true) - Main.screenPosition;
			Main.EntitySpriteDraw(tex, new Vector2(MathF.Round(hand.X), MathF.Round(hand.Y)), null, light, dir.ToRotation(), origin, 1f,
				left ? SpriteEffects.FlipVertically : SpriteEffects.None);
		}
	}
}
