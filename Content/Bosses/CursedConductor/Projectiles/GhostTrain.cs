using System;
using Cogpunk.Content.Bosses.CursedConductor.Buffs;
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
using R = Cogpunk.Content.Bosses.CursedConductor.CursedConductorRigData;

namespace Cogpunk.Content.Bosses.CursedConductor.Projectiles
{
	/// <summary>
	/// The Cursed Conductor's ghost train (user-set 2026-11-04: "a spirit of a big flying ghost train"; 2026-11-05: "way
	/// longer, add 4 more wagons", "massive damage if it hits the player head on, the first wagon, but only half with the
	/// other wagons"): one projectile is the whole train, an engine and <see cref="Cars"/> passenger cars. The engine flies
	/// the route; every car follows the engine's own trail (a ring buffer of its last positions, walked by arc length) one
	/// spacing behind the one before, so the cars bend round the loop and the wave as a real train would. It flies through
	/// anything (a ghost); each segment is a thick line along its own heading (vanilla <c>Collision.CheckAABBvLineCollision</c>):
	/// the engine hits for the full damage, a car for <see cref="CarDamageScale"/>, and a cursed player takes
	/// <see cref="ConductorCurse.DamageTaken"/>x more. Drawn translucent with its windows and headlamp solid (the glow sheets).
	/// <para>Routes (<c>ai[0]</c>, <see cref="Route"/>): <b>Express</b>, <b>Dive</b> and <b>Diagonal</b> (2026-11-09: at 45
	/// degrees, the heading's own pre-drawn frame) run straight across a player's screen:
	/// each segment materializes as it crosses the entry line (the engine's start) and vanishes over <see cref="FadeOut"/> px
	/// before the exit line <c>ai[1]</c> px on (harmless while faded: user, 2026-11-05: "come from the screen limit ... and
	/// quickly fade out on the other screen limit"); <b>Wave</b> does the same along a sine of <see cref="WaveAmplitude"/> and
	/// <see cref="WaveLength"/> (its phase in <c>ai[2]</c>; the whistle's express); <b>Loop</b> runs in along a tangent of the
	/// circle round (<c>ai[1]</c>, <c>ai[2]</c>), round it for <see cref="LoopLaps"/> laps and out along the tangent;
	/// <b>Farewell</b> (the death: harmless) flies <c>ai[1]</c> px to the Conductor and then climbs away into the sky, fading.</para>
	/// <para>D2: a server (or singleplayer) projectile whose whole path follows from what vanilla syncs when it is made (its
	/// position, velocity and <c>ai[]</c>): every side flies the same route from its own first tick, so nothing is sent
	/// afterwards; a client's player is hit (or not) by the train it sees, and which segment hit it is that client's
	/// (<see cref="Colliding"/> then <see cref="ModifyHitPlayer"/>, decompiled <c>Projectile.Damage</c>). D0/D1: a fixed trail
	/// buffer made once per train, a finite <see cref="Projectile.timeLeft"/> from the route, at most a few trains alive. D4:
	/// 9 pre-drawn headings per segment, mirrored for the left half (never rotated), drawn at whole pixels; fades are opacity.</para>
	/// </summary>
	public class GhostTrain : CogpunkProjectile
	{
		public enum Route { Express = 0, Dive = 1, Loop = 2, Farewell = 3, Wave = 4, Diagonal = 5 }

		public const int Cars = 7;                          // 3 + 4 more wagons (user-set 2026-11-05)
		public const float EngineLength = 88f, CarLength = 74f, Gap = 6f;
		public const float EngineThickness = 40f, CarThickness = 34f;
		/// <summary>Trail distance between the middles of the engine and the first car, and of two cars.</summary>
		public const float FirstSpacing = EngineLength * 0.5f + Gap + CarLength * 0.5f, Spacing = CarLength + Gap;
		public const float Length = EngineLength + Cars * (CarLength + Gap);
		public const float LoopLaps = 3f;                   // user-set 2026-11-05: "lasting 3 circles"
		public const float CarDamageScale = 0.5f;           // user-set 2026-11-05: half from the wagons
		public const int TrailLength = 160;                 // ticks of the engine's path kept (the whole train at 5+ px/tick)
		public const float Opacity = 0.82f;
		public const float FadeIn = 40f, FadeOut = 64f;     // px over which a segment appears past the entry / vanishes before the exit
		public const float Solid = 0.4f;                    // a segment fainter than this can't hurt
		public const float WaveAmplitude = 6f * 16f, WaveLength = 36f * 16f;
		public const float FarewellTurn = 0.05f;            // radians a tick it turns up, once past the Conductor
		public const int FarewellTicks = 150, FadeTicks = 40;
		public const int MaxLifetime = 900;

		private static Asset<Texture2D> engineGlow, car, carGlow;

		private Vector2[] trail;                             // made per train in SetDefaults (D1: never per tick)
		private int head;                                    // index of the newest point
		private int filled;
		private bool started;
		private int age;
		private Vector2 start, direction, centre;
		private float speed, span, radius, angle, angularSpeed, approach, phase, baseY;
		private bool circling, leaving;
		private int hitSegment;

		private Route Path => (Route)(int)Projectile.ai[0];

		private bool Spans => Path == Route.Express || Path == Route.Dive || Path == Route.Wave || Path == Route.Diagonal;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.Headings;
			ProjectileID.Sets.DrawScreenCheckFluff[Type] = (int)Length * 2;   // drawn while any car is on screen
			if (!Main.dedServ) {
				const string path = "Cogpunk/Content/Bosses/CursedConductor/Projectiles/GhostTrain";
				engineGlow = DepthLayers.RequestOptional(path + "_Glow");
				car = DepthLayers.RequestOptional(path + "_Car");
				carGlow = DepthLayers.RequestOptional(path + "_CarGlow");
			}
		}

		public override void Unload() {
			engineGlow = car = carGlow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 40;
			Projectile.height = 40;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = MaxLifetime;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;           // the boss's immunity (and the Tar Tyrant's attacks)
			trail = new Vector2[TrailLength];
		}

		public override bool CanHitPlayer(Player target) => Path != Route.Farewell && started && age > 2;

		public override void AI() {
			if (!started) {
				Begin();
			}
			age++;
			switch (Path) {
				case Route.Loop:
					FlyLoop();
					break;
				case Route.Wave:
					FlyWave();
					break;
				case Route.Farewell:
					FlyFarewell();
					break;
			}
			MathSafety.Sanitize(ref Projectile.velocity);
			Record(Projectile.Center + Projectile.velocity);     // where vanilla moves it this tick
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Every side, on its first tick: the route's numbers from the synced spawn state, the trail laid out behind
		/// the engine in a straight line (the train arrives from beyond its entry line), and the lifetime.</summary>
		private void Begin() {
			started = true;
			start = Projectile.Center;
			speed = Math.Max(1f, Projectile.velocity.Length());
			direction = Projectile.velocity / speed;
			trail ??= new Vector2[TrailLength];
			for (int i = 0; i < TrailLength; i++) {
				trail[(TrailLength - i) % TrailLength] = start - direction * speed * i;
			}
			head = 0;
			filled = TrailLength;
			span = Math.Max(0f, Projectile.ai[1]);
			int life;
			switch (Path) {
				case Route.Loop: {
					centre = new Vector2(Projectile.ai[1], Projectile.ai[2]);
					approach = Math.Max(0f, Vector2.Dot(centre - start, direction));    // to the tangent point
					Vector2 tangentPoint = start + direction * approach;
					Vector2 r = tangentPoint - centre;
					radius = Math.Max(48f, r.Length());
					angle = MathF.Atan2(r.Y, r.X);
					float cross = r.X * Projectile.velocity.Y - r.Y * Projectile.velocity.X;
					angularSpeed = speed / radius * (cross >= 0f ? 1f : -1f);
					life = (int)((approach + LoopLaps * MathHelper.TwoPi * radius + Length + 60f * 16f) / speed);
					break;
				}
				case Route.Farewell:
					life = FarewellTicks;
					break;
				case Route.Wave:
					phase = Projectile.ai[2];
					baseY = start.Y - WaveAmplitude * MathF.Sin(phase);
					life = (int)((span + Length + FadeIn) * 1.5f / speed) + 4;   // a sine is longer than its run
					break;
				default:
					life = (int)((span + Length + FadeIn) / speed) + 4;
					break;
			}
			Projectile.timeLeft = Math.Clamp(life, 30, MaxLifetime);
			if (!Main.dedServ && Path != Route.Farewell) {
				// the train comes in from off screen: heard as it sets off (unplaced: a boss fight's sound), not where it starts
				SoundEngine.PlaySound(SoundID.DD2_BetsyFlyingCircleAttack with { Pitch = -0.5f, Volume = 0.8f, MaxInstances = 3 });
			}
		}

		/// <summary>In along the tangent, round the circle for <see cref="LoopLaps"/> laps, then out along the tangent. This
		/// tick's move (vanilla adds the velocity after the AI) takes the engine to where the route has it <see cref="age"/>
		/// ticks after it set off: on the line before the tangent point, on the circle after it.</summary>
		private void FlyLoop() {
			if (leaving) {
				return;
			}
			float travelled = age * speed;
			if (!circling) {
				if (travelled < approach) {
					return;
				}
				circling = true;
			}
			float a = angle + angularSpeed * (age - approach / speed);
			if ((travelled - approach) / radius >= LoopLaps * MathHelper.TwoPi) {
				leaving = true;                                 // off along the tangent at the same speed
				Projectile.velocity = new Vector2(-MathF.Sin(a), MathF.Cos(a)) * (Math.Sign(angularSpeed) * speed);
				return;
			}
			Projectile.velocity = centre + new Vector2(MathF.Cos(a), MathF.Sin(a)) * radius - Projectile.Center;
		}

		/// <summary>The whistle's express: along x at its speed, up and down a sine (its phase synced in <c>ai[2]</c>).</summary>
		private void FlyWave() {
			float run = age * speed;
			float x = start.X + direction.X * run;
			float y = baseY + WaveAmplitude * MathF.Sin(phase + MathHelper.TwoPi * run / WaveLength);
			Projectile.velocity = new Vector2(x, y) - Projectile.Center;
		}

		/// <summary>The death: on to the Conductor, then turning up into the sky.</summary>
		private void FlyFarewell() {
			if (age * speed < Projectile.ai[1]) {
				return;
			}
			float a = Projectile.velocity.ToRotation();
			float up = -MathHelper.PiOver2;
			float diff = MathHelper.WrapAngle(up - a);
			a += MathHelper.Clamp(diff, -FarewellTurn, FarewellTurn);
			Projectile.velocity = new Vector2(MathF.Cos(a), MathF.Sin(a)) * speed;
		}

		private void Record(Vector2 point) {
			head = (head + 1) % TrailLength;
			trail[head] = point;
			filled = Math.Min(TrailLength, filled + 1);
		}

		/// <summary>The point <paramref name="distance"/> px back along the engine's trail, by arc length (a wave's or a loop's
		/// path is longer per tick on its slopes; counting ticks would bunch the cars).</summary>
		private Vector2 Back(float distance) {
			int idx = head;
			if (distance <= 0f) {
				return trail[idx];
			}
			float acc = 0f;
			for (int k = 0; k < filled - 1; k++) {
				int prev = idx == 0 ? TrailLength - 1 : idx - 1;
				Vector2 a = trail[idx], b = trail[prev];
				float seg = Vector2.Distance(a, b);
				if (acc + seg >= distance) {
					return seg > 0.001f ? Vector2.Lerp(a, b, (distance - acc) / seg) : a;
				}
				acc += seg;
				idx = prev;
			}
			return trail[idx];
		}

		/// <summary>Segment <paramref name="index"/> (0 the engine): its middle and its heading (unit, the way it travels).</summary>
		private void Segment(int index, out Vector2 middle, out Vector2 heading) {
			float back = index == 0 ? 0f : FirstSpacing + (index - 1) * Spacing;
			middle = Back(back);
			Vector2 ahead = Back(Math.Max(0f, back - 12f));
			Vector2 behind = Back(back + 12f);
			heading = (ahead - behind).SafeNormalize(direction == Vector2.Zero ? Vector2.UnitX : direction);
		}

		/// <summary>0..1: how much of a segment at <paramref name="at"/> is there (an Express, a Dive or a Wave appears past
		/// its entry line and vanishes before its exit line); 1 for the other routes.</summary>
		private float Visibility(Vector2 at) {
			if (!Spans) {
				return 1f;
			}
			float s = Path == Route.Wave ? (at.X - start.X) * Math.Sign(direction.X == 0f ? 1f : direction.X) : Vector2.Dot(at - start, direction);
			return MathHelper.Clamp(s / FadeIn, 0f, 1f) * MathHelper.Clamp((span - s) / FadeOut, 0f, 1f);
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (!started) {
				return false;
			}
			float point = 0f;
			for (int k = 0; k <= Cars; k++) {
				Segment(k, out Vector2 middle, out Vector2 heading);
				if (Visibility(middle) < Solid) {
					continue;
				}
				float half = (k == 0 ? EngineLength : CarLength) * 0.5f - 8f;
				float thick = k == 0 ? EngineThickness : CarThickness;
				if (Collision.CheckAABBvLineCollision(targetHitbox.TopLeft(), targetHitbox.Size(), middle - heading * half, middle + heading * half, thick, ref point)) {
					hitSegment = k;
					return true;
				}
			}
			return false;
		}

		/// <summary>Head on (the engine) the full damage, a car half (user-set); +25% on a cursed player.</summary>
		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			if (hitSegment > 0) {
				modifiers.SourceDamage *= CarDamageScale;
			}
			ConductorCurse.Amplify(target, ref modifiers);
		}

		/// <summary>Ghost steam from the stack, a glow along the train; the farewell fades out at its end.</summary>
		private void Effects() {
			float fade = Fade;
			Segment(0, out Vector2 middle, out Vector2 heading);
			float vis = Visibility(middle) * fade;
			Lighting.AddLight(middle, 0.2f * vis, 0.55f * vis, 0.45f * vis);
			if (vis < Solid || !CogpunkClientConfig.RollEffect() || !Main.rand.NextBool(2)) {
				return;
			}
			Vector2 stack = middle + heading * 22f + new Vector2(heading.Y, -heading.X) * Math.Sign(heading.X == 0f ? 1f : heading.X) * 28f;
			if (SafeSpawn.TryNewDust(stack - new Vector2(6f), 12, 12, DustID.CursedTorch, out Dust d)) {
				d.noGravity = true;
				d.velocity = -Projectile.velocity * 0.1f + new Vector2(0f, -1f);
				d.scale = 1.4f;
			}
		}

		private float Fade => Path == Route.Farewell ? MathHelper.Clamp(Projectile.timeLeft / (float)FadeTicks, 0f, 1f) : 1f;

		public override bool PreDraw(ref Color lightColor) {
			if (!started) {
				return false;
			}
			Texture2D engine = TextureAssets.Projectile[Type].Value;
			float fade = Fade;
			for (int k = Cars; k >= 0; k--) {
				Segment(k, out Vector2 middle, out Vector2 heading);
				float vis = Visibility(middle) * fade;
				if (vis <= 0.02f) {
					continue;
				}
				int cell = k == 0 ? R.EngineCell : R.CarCell;
				Texture2D sheet = k == 0 ? engine : car?.IsLoaded == true ? car.Value : null;
				Texture2D lit = k == 0 ? (engineGlow?.IsLoaded == true ? engineGlow.Value : null) : (carGlow?.IsLoaded == true ? carGlow.Value : null);
				int frame = HeadingFrame(heading, out bool flip);
				Rectangle source = new(0, frame * (cell + 2), cell, cell);
				Vector2 at = middle - Main.screenPosition;
				at = new Vector2(MathF.Round(at.X), MathF.Round(at.Y));
				Vector2 origin = new(cell * 0.5f);
				SpriteEffects effects = flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
				if (sheet != null && source.Bottom <= sheet.Height) {
					Main.EntitySpriteDraw(sheet, at, source, Color.White * (Opacity * vis), 0f, origin, 1f, effects);
				}
				if (lit != null && source.Bottom <= lit.Height) {
					Main.EntitySpriteDraw(lit, at, source, Color.White * vis, 0f, origin, 1f, effects);
				}
			}
			return false;
		}

		/// <summary>The pre-drawn heading for a direction (frames run from straight up to straight down, facing right, 22.5
		/// degrees apart); a leftward direction uses its mirror image, flipped (so the train never rides upside down).</summary>
		public static int HeadingFrame(Vector2 heading, out bool flip) {
			float a = MathHelper.ToDegrees(MathF.Atan2(heading.Y, heading.X));
			flip = a > 90.5f || a < -90.5f;
			if (flip) {
				a = a > 0f ? 180f - a : -180f - a;
			}
			return Math.Clamp((int)MathF.Round((a + 90f) / 22.5f), 0, R.Headings - 1);
		}
	}
}
