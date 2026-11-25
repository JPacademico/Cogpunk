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
	/// "time slows 80% for 0.5 seconds for every entity, for cool effect purposes"): for its length (in real ticks) players,
	/// NPCs, projectiles, items, gore and dust only update on a fraction <c>rate</c> of the ticks (0.2: one tick in five), so
	/// everything moves, animates and counts down at that speed; time of day, spawning, UI, sound and the camera run on.</item>
	/// <item><b>Around a point</b> (<see cref="StartZone"/>; first used by crit kills, user 2026-11-25: "0.33 seconds of slow
	/// motion (our slow motion effect) for everything arround in a 1.5x screen size area (so it does not affect entities or
	/// players that are too far away)"): the same holding back at <see cref="ZoneSpeed"/>, but only for entities whose centre
	/// is inside one of at most <see cref="MaxZones"/> rectangles. All zones share one clock, so overlapping zones hold the same
	/// ticks (two zones can never freeze an entity between them). Dust has no position test (vanilla updates it all at once):
	/// it is held while the viewer's screen centre is inside a holding zone.</item>
	/// </list>
	/// The tick-skipping lives in <see cref="Hooks.SlowMotionHooks"/> (<see cref="ShouldUpdate"/>); projectiles in
	/// <see cref="CogpunkSets.IgnoresSlowMotion"/> keep full speed (the effect that started it).
	/// <para>D0: nothing can stick: every length is capped at <see cref="MaxTicks"/>, counted down every world tick before
	/// anything updates (<c>PreUpdatePlayers</c>, the first hook of <c>Main.DoUpdateInWorld</c>, decompiled), everything is
	/// cleared with the world, a new world-wide one is refused while one runs or for <see cref="Refractory"/> ticks after it,
	/// and zones are a fixed array (a full array refuses a new zone). If the hooks failed to load, nothing slows and nothing
	/// breaks.</para>
	/// <para>D2: every side runs its own copy, started by the same synced event (a projectile that reaches every side, or the
	/// server's own packet); the server holds back NPCs and projectiles the same way, so positions stay in step, a few ticks
	/// apart at most, and the totals of held ticks are the same on every side. D1: with nothing running the test is one bool;
	/// with zones, four rectangle tests per entity at most.</para>
	/// </summary>
	public sealed class SlowMotion : ModSystem
	{
		public const int MaxTicks = 60;
		public const int Refractory = 60;
		public const int MaxZones = 4;
		/// <summary>The zones' speed: 80% slower, the same as the Metal Wrench's (Cogpunk's slow motion).</summary>
		public const float ZoneSpeed = 0.2f;

		private static int ticksLeft;
		private static int cooldown;
		private static float rate = 1f;
		private static float accumulator;

		private static readonly Vector2[] zoneCenter = new Vector2[MaxZones];
		private static readonly Vector2[] zoneHalf = new Vector2[MaxZones];
		private static readonly int[] zoneTicks = new int[MaxZones];
		private static readonly bool[] zoneOn = new bool[MaxZones];         // the zone applies this tick
		private static bool zonesOn;                                        // any zone applies this tick
		private static float zoneAccumulator;

		/// <summary>False on a tick where every entity holds still (read by the hooks).</summary>
		public static bool UpdateThisTick { get; private set; } = true;

		/// <summary>False on a tick where entities inside a zone hold still.</summary>
		public static bool ZoneUpdateThisTick { get; private set; } = true;

		public static bool Active => ticksLeft > 0;

		/// <summary>A zone applies this tick.</summary>
		public static bool ZonesActive => zonesOn;

		/// <summary>Starts a world-wide slow motion of <paramref name="ticks"/> real ticks at <paramref name="speed"/> (0.2 = 80%
		/// slower); false while one runs or just ran.</summary>
		public static bool Start(int ticks, float speed) {
			if (ticksLeft > 0 || cooldown > 0 || ticks <= 0 || !(speed > 0f) || speed >= 1f) {
				return false;
			}
			ticksLeft = Math.Min(ticks, MaxTicks);
			rate = speed;
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
				if (zoneTicks[k] > 0 && Vector2.DistanceSquared(zoneCenter[k], center) < 16f * 16f) {
					zoneTicks[k] = Math.Max(zoneTicks[k], ticks);      // the same spot told twice: one zone
					return true;
				}
				if (free < 0 && zoneTicks[k] <= 0) {
					free = k;
				}
			}
			if (free < 0) {
				return false;
			}
			if (!zonesOn) {
				zoneAccumulator = 0f;                                 // a fresh clock when no zone was running
			}
			zoneCenter[free] = center;
			zoneHalf[free] = halfSize;
			zoneTicks[free] = ticks;
			return true;
		}

		/// <summary>Should an entity whose centre is at <paramref name="position"/> update this tick? (The hooks ask.)</summary>
		public static bool ShouldUpdate(Vector2 position) {
			if (!UpdateThisTick) {
				return false;
			}
			if (!zonesOn || ZoneUpdateThisTick) {
				return true;
			}
			for (int k = 0; k < MaxZones; k++) {
				if (zoneOn[k] && Math.Abs(position.X - zoneCenter[k].X) <= zoneHalf[k].X && Math.Abs(position.Y - zoneCenter[k].Y) <= zoneHalf[k].Y) {
					return false;
				}
			}
			return true;
		}

		/// <summary>Should the dust update this tick? Dust is updated all at once (vanilla <c>Dust.UpdateDust</c>), so a zone
		/// holds it while the viewer's screen centre is inside it (clients; the server has no dust).</summary>
		public static bool DustShouldUpdate() {
			if (!UpdateThisTick) {
				return false;
			}
			if (!zonesOn || ZoneUpdateThisTick || Main.dedServ) {
				return true;
			}
			Vector2 view = Main.screenPosition + new Vector2(Main.screenWidth * 0.5f, Main.screenHeight * 0.5f);
			return ShouldUpdate(view);
		}

		public override void PreUpdatePlayers() {
			if (ticksLeft <= 0) {
				UpdateThisTick = true;
				if (cooldown > 0) {
					cooldown--;
				}
			}
			else {
				ticksLeft--;
				accumulator += rate;
				UpdateThisTick = accumulator >= 1f;
				if (UpdateThisTick) {
					accumulator -= 1f;
				}
				if (ticksLeft == 0) {
					cooldown = Refractory;
				}
			}
			bool any = false;
			for (int k = 0; k < MaxZones; k++) {
				zoneOn[k] = zoneTicks[k] > 0;                        // a zone with one tick left still holds this one
				if (zoneOn[k]) {
					zoneTicks[k]--;
					any = true;
				}
			}
			zonesOn = any;
			if (any) {
				zoneAccumulator += ZoneSpeed;
				ZoneUpdateThisTick = zoneAccumulator >= 1f;
				if (ZoneUpdateThisTick) {
					zoneAccumulator -= 1f;
				}
			}
			else {
				ZoneUpdateThisTick = true;
				zoneAccumulator = 0f;
			}
		}

		private static void Clear() {
			ticksLeft = 0;
			cooldown = 0;
			rate = 1f;
			accumulator = 0f;
			UpdateThisTick = true;
			for (int k = 0; k < MaxZones; k++) {
				zoneTicks[k] = 0;
				zoneOn[k] = false;
			}
			zonesOn = false;
			zoneAccumulator = 0f;
			ZoneUpdateThisTick = true;
		}

		public override void ClearWorld() => Clear();

		public override void OnWorldUnload() => Clear();

		public override void Unload() => Clear();
	}
}
