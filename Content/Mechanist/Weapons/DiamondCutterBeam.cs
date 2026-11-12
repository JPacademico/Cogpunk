using System;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// The Diamond Cutter's beam (user-set 2026-11-11b: "a precise instantaneous thin laser that can pierce up to 3 enemies
	/// ... should ignore 20% of enemy defense"). A hitscan line: the owner measures it as it fires (<see cref="Measure"/>:
	/// to the first solid block, platforms let it through, at most <see cref="Range"/>, and cut short inside the
	/// <see cref="MaxTargets"/>th enemy it reaches, so the ones it strikes are the nearest along it) and it strikes in the tick
	/// it is fired only (<see cref="CanDamage"/>), each enemy once, at most <see cref="MaxTargets"/> of them, ignoring
	/// <see cref="ArmorIgnore"/> of their defense (vanilla's <c>ScalingArmorPenetration</c>, decompiled
	/// <c>NPC.HitModifiers.GetDamage</c>: defense x the fraction comes off before the defense counts). Critters are passed
	/// through, never cut. It stays a few ticks for the eye: a white core between pale blue edges, thinning, then broken into
	/// sparkles, with a star at the muzzle and where it stops (added onto the scene, the fade in code: D4 rule 9).
	/// <para>D2: the owner's projectile; the hits are the owner's (vanilla works out a player projectile's hits on its owner's
	/// client), the length is <c>ai[0]</c> (sent with the spawn), so every client draws the same line; the direction is the
	/// velocity, which never moves it (<see cref="ShouldUpdatePosition"/>). D0/D1: the wall march is capped by the range,
	/// the enemy pass is one walk over the active NPCs keeping three floats, no allocation; dust and light on clients only,
	/// capped.</para>
	/// </summary>
	public class DiamondCutterBeam : CogpunkProjectile
	{
		public const int MaxTargets = 3;                           // user-set: "pierce up to 3 enemies"
		public const float ArmorIgnore = 0.2f;                     // user-set: "ignore 20% of enemy defense"
		public const float Range = 60f * 16f;                      // my call: well past the screen's half width
		public const float HitRadius = 3f;                         // half the beam's drawn width
		public const int Lifetime = 12;                            // the fade, ticks
		public const int FadeFrameTicks = 4;                       // per beam frame: full, thinning, sparkles
		public const int SegmentLength = 16, BeamHeight = 6, BeamFrames = 3, BeamStride = BeamHeight + 2;
		public const int SparkSize = 14, SparkFrames = 4, SparkStride = SparkSize + 2, SparkFrameTicks = 3;
		public const int MaxBeamDust = 8;

		private static Asset<Texture2D> spark;

		private float Length => MathHelper.Clamp(Projectile.ai[0], 0f, Range);
		private ref float Age => ref Projectile.localAI[0];
		private ref float Hits => ref Projectile.localAI[1];

		public override void SetStaticDefaults() {
			if (!Main.dedServ) {
				spark = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Weapons/DiamondCutterSpark");
			}
			ProjectileID.Sets.DrawScreenCheckFluff[Type] = (int)Range + 64;   // drawn while any of the line is on screen
		}

		public override void Unload() {
			spark = null;
		}

		public override void SetDefaults() {
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = ModContent.GetInstance<MechanistDamage>();
			Projectile.penetrate = -1;                                 // the hits are counted in CanHitNPC
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Lifetime;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;                       // each enemy once
			Projectile.aiStyle = -1;
		}

		public override bool ShouldUpdatePosition() => false;

		public override void AI() {
			Age++;
			MathSafety.Sanitize(ref Projectile.velocity);
			if (Projectile.velocity == Vector2.Zero) {
				Projectile.velocity = Vector2.UnitX;
			}
			Projectile.rotation = Projectile.velocity.ToRotation();
			if (Main.dedServ || Age > 2f) {
				return;
			}
			Vector2 dir = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			Vector2 end = Projectile.Center + dir * Length;
			Lighting.AddLight(Projectile.Center, 0.5f, 0.6f, 0.8f);
			Lighting.AddLight(end, 0.5f, 0.6f, 0.8f);
			if (Age == 1f) {
				Sparkle(end, 5);
				int count = Math.Min(MaxBeamDust, (int)(Length / 96f));
				for (int k = 1; k <= count && CogpunkClientConfig.RollEffect(); k++) {
					if (SafeSpawn.TryNewDust(Projectile.Center + dir * (Length * k / (count + 1)) - new Vector2(2f), 4, 4, DustID.GemDiamond, out Dust d)) {
						d.noGravity = true;
						d.velocity = dir * 0.5f;
						d.scale = 0.7f;
					}
				}
			}
		}

		private static void Sparkle(Vector2 at, int count) {
			for (int k = 0; k < count && CogpunkClientConfig.RollEffect(); k++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(4f), 8, 8, DustID.GemDiamond, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(2f, 2f);
					d.scale = 0.9f;
				}
			}
		}

		/// <summary>Only in the tick it is fired: the hit is instant.</summary>
		public override bool? CanDamage() => Age <= 1f ? null : false;

		public override bool? CanHitNPC(NPC target) {
			if (Hits >= MaxTargets || NPCID.Sets.CountsAsCritter[target.type]) {
				return false;
			}
			return null;
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 dir = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			return SwingPose.CapsuleHitsRect(Projectile.Center, Projectile.Center + dir * Length, HitRadius, targetHitbox);
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			modifiers.ScalingArmorPenetration += ArmorIgnore;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			Hits++;
			if (!Main.dedServ) {
				Sparkle(target.Center, 3);
			}
		}

		// --- the line ---------------------------------------------------------------------------------------------------------

		/// <summary>The owner, as it fires: the beam's length from <paramref name="start"/> along the unit
		/// <paramref name="dir"/>: to the first solid block (<see cref="WallDistance"/>), cut short in the middle of the
		/// <see cref="MaxTargets"/>th enemy it crosses, so the nearest are the ones struck.</summary>
		public static float Measure(Vector2 start, Vector2 dir) {
			if (!MathSafety.IsFinite(start) || !MathSafety.IsFinite(dir) || dir == Vector2.Zero) {
				return 0f;
			}
			float wall = WallDistance(start, dir, Range);
			float in1 = float.MaxValue, in2 = float.MaxValue, in3 = float.MaxValue, out3 = float.MaxValue;
			float out1 = 0f, out2 = 0f;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.friendly || npc.dontTakeDamage || NPCID.Sets.CountsAsCritter[npc.type]
					|| !Crosses(start, dir, npc.Hitbox, HitRadius, out float tIn, out float tOut) || tIn > wall) {
					continue;
				}
				tIn = Math.Max(tIn, 0f);
				if (tIn < in1) {
					(in3, out3) = (in2, out2);
					(in2, out2) = (in1, out1);
					(in1, out1) = (tIn, tOut);
				}
				else if (tIn < in2) {
					(in3, out3) = (in2, out2);
					(in2, out2) = (tIn, tOut);
				}
				else if (tIn < in3) {
					(in3, out3) = (tIn, tOut);
				}
			}
			if (in3 == float.MaxValue) {
				return wall;
			}
			return MathHelper.Clamp((in3 + Math.Min(out3, wall)) * 0.5f, 0f, wall);
		}

		/// <summary>The distance along the ray to the first solid block it enters (an Amanatides-Woo walk over the tiles, at
		/// most twice the range in tiles plus four steps); 0 when it starts inside one; out of the world counts as solid.</summary>
		public static float WallDistance(Vector2 start, Vector2 dir, float range) {
			int x = (int)Math.Floor(start.X / 16f), y = (int)Math.Floor(start.Y / 16f);
			int stepX = dir.X > 0f ? 1 : -1, stepY = dir.Y > 0f ? 1 : -1;
			float ax = Math.Abs(dir.X), ay = Math.Abs(dir.Y);
			float deltaX = ax > 1e-5f ? 16f / ax : float.MaxValue, deltaY = ay > 1e-5f ? 16f / ay : float.MaxValue;
			float maxX = ax > 1e-5f ? (dir.X > 0f ? (x + 1) * 16f - start.X : start.X - x * 16f) / ax : float.MaxValue;
			float maxY = ay > 1e-5f ? (dir.Y > 0f ? (y + 1) * 16f - start.Y : start.Y - y * 16f) / ay : float.MaxValue;
			float t = 0f;
			int steps = (int)(range / 16f) * 2 + 4;
			for (int k = 0; k < steps && t < range; k++) {
				if (Blocks(x, y)) {
					return t;
				}
				if (maxX < maxY) {
					t = maxX;
					maxX += deltaX;
					x += stepX;
				}
				else {
					t = maxY;
					maxY += deltaY;
					y += stepY;
				}
			}
			return range;
		}

		/// <summary>A solid, unactuated block (platforms and other solid-top tiles let the beam through); outside the world
		/// blocks it.</summary>
		private static bool Blocks(int x, int y) {
			if (!TileSafety.TryGetTile(x, y, out Tile tile)) {
				return true;
			}
			return tile.HasTile && !tile.IsActuated && Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType];
		}

		/// <summary>The ray from <paramref name="s"/> along <paramref name="d"/> against <paramref name="box"/> grown by
		/// <paramref name="pad"/> (the slab test): where it enters and leaves.</summary>
		private static bool Crosses(Vector2 s, Vector2 d, Rectangle box, float pad, out float tIn, out float tOut) {
			tIn = float.MinValue;
			tOut = float.MaxValue;
			if (!Slab(s.X, d.X, box.Left - pad, box.Right + pad, ref tIn, ref tOut)
				|| !Slab(s.Y, d.Y, box.Top - pad, box.Bottom + pad, ref tIn, ref tOut)) {
				return false;
			}
			return tOut >= Math.Max(tIn, 0f);
		}

		private static bool Slab(float s, float d, float lo, float hi, ref float tIn, ref float tOut) {
			if (Math.Abs(d) < 1e-5f) {
				return s >= lo && s <= hi;
			}
			float a = (lo - s) / d, b = (hi - s) / d;
			if (a > b) {
				(a, b) = (b, a);
			}
			tIn = Math.Max(tIn, a);
			tOut = Math.Min(tOut, b);
			return tIn <= tOut;
		}

		// --- looks ------------------------------------------------------------------------------------------------------------

		/// <summary>The line in <see cref="SegmentLength"/> px pieces of the frame for its age, the last one cut to fit, and the
		/// stars at both ends; all added onto the scene (alpha 0 in vanilla's premultiplied batch), fading out in the last
		/// frame.</summary>
		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			float length = Length;
			int frame = Math.Min(BeamFrames - 1, (int)((Math.Max(Age, 1f) - 1f) / FadeFrameTicks));
			float fade = frame < BeamFrames - 1 ? 1f : MathHelper.Clamp((Lifetime - Age + 1f) / FadeFrameTicks, 0f, 1f);
			Color colour = new Color(255, 255, 255, 0) * fade;
			Vector2 dir = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			Vector2 start = Projectile.Center - Main.screenPosition;
			Vector2 origin = new(0f, BeamHeight / 2f);
			if (tex.Height >= BeamFrames * BeamStride - 2) {
				for (float t = 0f; t < length; t += SegmentLength) {
					int w = (int)Math.Min(SegmentLength, length - t);
					if (w <= 0) {
						break;
					}
					Rectangle source = new(0, frame * BeamStride, w, BeamHeight);
					Main.EntitySpriteDraw(tex, start + dir * t, source, colour, Projectile.rotation, origin, 1f, SpriteEffects.None);
				}
			}
			if (spark?.IsLoaded == true) {
				int sf = Math.Min(SparkFrames - 1, (int)((Math.Max(Age, 1f) - 1f) / SparkFrameTicks));
				Rectangle source = new(0, sf * SparkStride, SparkSize, SparkSize);
				if (source.Bottom <= spark.Value.Height) {
					Vector2 o = new(SparkSize / 2f);
					Main.EntitySpriteDraw(spark.Value, start, source, colour, 0f, o, 1f, SpriteEffects.None);
					Main.EntitySpriteDraw(spark.Value, start + dir * length, source, colour, 0f, o, 1f, SpriteEffects.None);
				}
			}
			return false;
		}
	}
}
