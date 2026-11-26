using System;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// Short slow motions, for the whole world or for a region of it.
	/// <list type="bullet">
	/// <item><b>Everywhere</b> (<see cref="Start"/>; first used by the Metal Wrench's riposte on a boss, user-set 2026-10-30:
	/// "time slows 80% ... for every entity, for cool effect purposes"): for its length (in real ticks) players, NPCs,
	/// projectiles, items, gore and dust only update on a fraction of the ticks, so everything moves, animates and counts down
	/// slower; time of day, spawning, UI, sound and the camera run on.</item>
	/// <item><b>Around a point</b> (<see cref="StartZone"/>; first used by crit kills, user 2026-11-25: "slow motion (our slow
	/// motion effect) for everything arround in a 1.5x screen size area (so it does not affect entities or players that are
	/// too far away)"): the same holding back, but only for entities whose centre is inside one of at most
	/// <see cref="MaxZones"/> rectangles; an entity inside two follows the first. Dust has no position test (vanilla updates it
	/// all at once): it follows the zone round the viewer's screen centre.</item>
	/// </list>
	/// <para>The speed curve (user, 2026-11-26: "they should last 0.7 seconds now and be more smooth so they dont feel like a
	/// shutter. it should quickly gradualy return to normal speed now instead of abruptly trasitioning from slow to normal"):
	/// each slow motion eases from full speed down to its slowest over <see cref="EaseInTicks"/>, holds, then eases back up to
	/// full speed over its last <see cref="EaseOutTicks"/> (<see cref="Speed"/>, a smoothstep both ways). Each has its own
	/// clock (an accumulator: an entity updates on the ticks where it passes 1), so the held ticks fall evenly. The other half
	/// of the smoothness is drawn: between two of its updates a held entity is drawn where its last step would have taken it by
	/// now (<see cref="Visuals.SlowMotionSmoothing"/>, clients only), so it glides instead of jumping every few frames.</para>
	/// The tick-skipping lives in <see cref="Hooks.SlowMotionHooks"/> (<see cref="ShouldUpdate"/>); projectiles in
	/// <see cref="CogpunkSets.IgnoresSlowMotion"/> keep full speed (the effect that started it).
	/// <para>D0: nothing can stick: every length is capped at <see cref="MaxTicks"/>, counted down every world tick before
	/// anything updates (<c>PreUpdatePlayers</c>, the first hook of <c>Main.DoUpdateInWorld</c>, decompiled), everything is
	/// cleared with the world, a new world-wide one is refused while one runs or for <see cref="Refractory"/> ticks after it,
	/// and zones are a fixed array (a full array refuses a new zone). If the hooks failed to load, nothing slows and nothing
	/// breaks.</para>
	/// <para>D2: every side runs its own copy, started by the same synced event (a projectile that reaches every side, or the
	/// server's own packet), and the curve depends only on each slow motion's age, so every side holds back the same entities
	/// on the same number of ticks, a few ticks apart at most (the packet's trip). The drawn glide moves nothing for real: it
	/// is put back before anything updates. D1: with nothing running the test is one bool; with zones, four rectangle tests
	/// per entity at most.</para>
	/// </summary>
	public sealed class SlowMotion : ModSystem
	{
		public const int MaxTicks = 60;
		public const int Refractory = 60;
		public const int MaxZones = 4;
		/// <summary>The zones' slowest speed: 80% slower, the same as the Metal Wrench's (Cogpunk's slow motion).</summary>
		public const float ZoneSpeed = 0.2f;
		/// <summary>Real ticks from full speed down to the slowest (a quick drop).</summary>
		public const int EaseInTicks = 5;
		/// <summary>Real ticks from the slowest back up to full speed at the end (0.25 s: "quickly gradualy return to normal").</summary>
		public const int EaseOutTicks = 15;

		// the world-wide one
		private static int length, age;
		private static int cooldown;
		private static float slowest = 1f;
		private static float accumulator;

		// the zones
		private static readonly Vector2[] zoneCenter = new Vector2[MaxZones];
		private static readonly Vector2[] zoneHalf = new Vector2[MaxZones];
		private static readonly int[] zoneLength = new int[MaxZones];
		private static readonly int[] zoneAge = new int[MaxZones];
		private static readonly float[] zoneAccumulator = new float[MaxZones];
		private static readonly bool[] zoneOn = new bool[MaxZones];          // the zone applies this tick
		private static readonly bool[] zoneUpdate = new bool[MaxZones];      // its entities update this tick
		private static bool zonesOn;                                         // any zone applies this tick
		private static bool worldOn;                                         // the world-wide one applies this tick

		/// <summary>False on a tick where every entity holds still (read by the hooks).</summary>
		public static bool UpdateThisTick { get; private set; } = true;

		/// <summary>A world-wide slow motion is running.</summary>
		public static bool Active => age < length;

		/// <summary>A zone applies this tick.</summary>
		public static bool ZonesActive => zonesOn;

		/// <summary>Anything slows this tick (the hooks record the entities' steps for the drawn glide only then).</summary>
		public static bool AnyActive => worldOn || zonesOn;

		/// <summary>Counts the slow motions that began while none was running (the drawn glide only uses steps noted in the
		/// current one, never a stale step from an earlier one).</summary>
		public static int Episode { get; private set; }

		/// <summary>A world-wide slow motion or a zone has ticks left (started, maybe not yet applied).</summary>
		private static bool Running() {
			if (age < length) {
				return true;
			}
			for (int k = 0; k < MaxZones; k++) {
				if (zoneAge[k] < zoneLength[k]) {
					return true;
				}
			}
			return false;
		}

		/// <summary>How fast time runs (1 full speed) <paramref name="tick"/> real ticks into a slow motion of
		/// <paramref name="total"/> ticks whose slowest is <paramref name="min"/>: a smoothstep down over
		/// <see cref="EaseInTicks"/>, the slowest, a smoothstep back up over the last <see cref="EaseOutTicks"/> (a short one
		/// shares its length between the two).</summary>
		public static float Speed(int tick, int total, float min) {
			if (total <= 0 || tick >= total) {
				return 1f;
			}
			int easeIn = Math.Min(EaseInTicks, total / 3), easeOut = Math.Min(EaseOutTicks, total - easeIn);
			float t;
			if (tick < easeIn) {
				t = 1f - (tick + 1f) / (easeIn + 1f);                 // 1 -> 0: from full speed down
			}
			else if (tick >= total - easeOut) {
				t = (tick - (total - easeOut) + 1f) / (easeOut + 1f); // 0 -> 1: back up to full speed
			}
			else {
				return min;
			}
			t = t * t * (3f - 2f * t);
			return min + (1f - min) * t;
		}

		/// <summary>Starts a world-wide slow motion of <paramref name="ticks"/> real ticks whose slowest is <paramref name="speed"/>
		/// (0.2 = 80% slower); false while one runs or just ran.</summary>
		public static bool Start(int ticks, float speed) {
			if (age < length || cooldown > 0 || ticks <= 0 || !(speed > 0f) || speed >= 1f) {
				return false;
			}
			if (!Running()) {
				Episode++;
			}
			length = Math.Min(ticks, MaxTicks);
			age = 0;
			slowest = speed;
			accumulator = 0f;
			return true;
		}

		/// <summary>Starts a slow motion of <paramref name="ticks"/> real ticks (capped at <see cref="MaxTicks"/>) for entities
		/// within <paramref name="halfSize"/> of <paramref name="center"/> (world px); false when the numbers are bad or every
		/// zone is in use. A zone over a spot that already has one running merely runs to the longer end.</summary>
		public static bool StartZone(Vector2 center, Vector2 halfSize, int ticks) {
			if (ticks <= 0 || !float.IsFinite(center.X) || !float.IsFinite(center.Y) || !(halfSize.X > 0f) || !(halfSize.Y > 0f)) {
				return false;
			}
			ticks = Math.Min(ticks, MaxTicks);
			int free = -1;
			for (int k = 0; k < MaxZones; k++) {
				bool running = zoneAge[k] < zoneLength[k];
				if (running && Vector2.DistanceSquared(zoneCenter[k], center) < 16f * 16f) {
					zoneLength[k] = Math.Min(MaxTicks, Math.Max(zoneLength[k], zoneAge[k] + ticks));   // the same spot told twice
					return true;
				}
				if (free < 0 && !running) {
					free = k;
				}
			}
			if (free < 0) {
				return false;
			}
			if (!Running()) {
				Episode++;
			}
			zoneCenter[free] = center;
			zoneHalf[free] = halfSize;
			zoneLength[free] = ticks;
			zoneAge[free] = 0;
			zoneAccumulator[free] = 0f;
			return true;
		}

		/// <summary>The zone holding an entity whose centre is at <paramref name="position"/> this tick (the first that contains
		/// it), or -1.</summary>
		private static int ZoneAt(Vector2 position) {
			for (int k = 0; k < MaxZones; k++) {
				if (zoneOn[k] && Math.Abs(position.X - zoneCenter[k].X) <= zoneHalf[k].X && Math.Abs(position.Y - zoneCenter[k].Y) <= zoneHalf[k].Y) {
					return k;
				}
			}
			return -1;
		}

		/// <summary>Should an entity whose centre is at <paramref name="position"/> update this tick? (The hooks ask.)</summary>
		public static bool ShouldUpdate(Vector2 position) {
			if (!UpdateThisTick) {
				return false;
			}
			if (!zonesOn) {
				return true;
			}
			int k = ZoneAt(position);
			return k < 0 || zoneUpdate[k];
		}

		/// <summary>How far (0..1 of a step) an entity at <paramref name="position"/> is from its last update towards its next
		/// one while a slow motion holds it (0: it updates every tick). The drawn glide moves it this much of its last step.</summary>
		public static float HeldFraction(Vector2 position) {
			if (worldOn) {
				return accumulator;
			}
			if (!zonesOn) {
				return 0f;
			}
			int k = ZoneAt(position);
			return k < 0 ? 0f : zoneAccumulator[k];
		}

		/// <summary>The viewer's screen centre (the dust's test).</summary>
		public static Vector2 ViewCenter => Main.screenPosition + new Vector2(Main.screenWidth * 0.5f, Main.screenHeight * 0.5f);

		/// <summary>Should the dust update this tick? Dust is updated all at once (vanilla <c>Dust.UpdateDust</c>), so it follows
		/// the zone round the viewer's screen centre (clients; the server has no dust).</summary>
		public static bool DustShouldUpdate() {
			if (!UpdateThisTick) {
				return false;
			}
			if (!zonesOn || Main.dedServ) {
				return true;
			}
			return ShouldUpdate(ViewCenter);
		}

		public override void PreUpdatePlayers() {
			worldOn = age < length;
			if (!worldOn) {
				UpdateThisTick = true;
				if (cooldown > 0) {
					cooldown--;
				}
			}
			else {
				accumulator += Speed(age, length, slowest);
				age++;
				UpdateThisTick = accumulator >= 1f;
				if (UpdateThisTick) {
					accumulator -= 1f;
				}
				if (age >= length) {
					cooldown = Refractory;
				}
			}
			bool any = false;
			for (int k = 0; k < MaxZones; k++) {
				zoneOn[k] = zoneAge[k] < zoneLength[k];             // a zone in its last tick still holds this one
				if (!zoneOn[k]) {
					zoneUpdate[k] = true;
					continue;
				}
				any = true;
				zoneAccumulator[k] += Speed(zoneAge[k], zoneLength[k], ZoneSpeed);
				zoneAge[k]++;
				zoneUpdate[k] = zoneAccumulator[k] >= 1f;
				if (zoneUpdate[k]) {
					zoneAccumulator[k] -= 1f;
				}
			}
			zonesOn = any;
		}

		private static void Clear() {
			length = 0;
			age = 0;
			cooldown = 0;
			slowest = 1f;
			accumulator = 0f;
			worldOn = false;
			UpdateThisTick = true;
			for (int k = 0; k < MaxZones; k++) {
				zoneLength[k] = 0;
				zoneAge[k] = 0;
				zoneAccumulator[k] = 0f;
				zoneOn[k] = false;
				zoneUpdate[k] = true;
			}
			zonesOn = false;
		}

		public override void ClearWorld() => Clear();

		public override void OnWorldUnload() => Clear();

		public override void Unload() => Clear();
	}
}
