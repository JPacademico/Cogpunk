using System;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// A short slow motion for every entity (first used by the Metal Wrench's riposte on a boss, user-set 2026-10-30: "time
	/// slows 80% for 0.5 seconds for every entity, for cool effect purposes"). For <see cref="Start"/>'s length (in real
	/// ticks) players, NPCs, projectiles, items, gore and dust only update on a fraction <c>rate</c> of the ticks (0.2: one
	/// tick in five), so everything moves, animates and counts down at that speed; time of day, spawning, UI, sound and the
	/// camera run on. The tick-skipping lives in <see cref="Hooks.SlowMotionHooks"/>; projectiles in
	/// <see cref="CogpunkSets.IgnoresSlowMotion"/> keep full speed (the effect that started it).
	/// <para>D0: it can't stick: the length is capped at <see cref="MaxTicks"/>, counted down every world tick before anything
	/// updates (<c>PreUpdatePlayers</c>, the first hook of <c>Main.DoUpdateInWorld</c>, decompiled), cleared with the world,
	/// and a new one is refused while one runs or for <see cref="Refractory"/> ticks after it (no chain of slow motions from
	/// several players, nor from a spammed packet). If the hooks failed to load, nothing slows and nothing breaks.</para>
	/// <para>D2: every side runs its own copy, started by the same synced event (the projectile that announces it reaches the
	/// server and every client); the server holds back NPCs and projectiles the same way, so positions stay in step, a few
	/// ticks apart at most.</para>
	/// </summary>
	public sealed class SlowMotion : ModSystem
	{
		public const int MaxTicks = 60;
		public const int Refractory = 60;

		private static int ticksLeft;
		private static int cooldown;
		private static float rate = 1f;
		private static float accumulator;

		/// <summary>False on a tick where entities hold still (read by the hooks).</summary>
		public static bool UpdateThisTick { get; private set; } = true;

		public static bool Active => ticksLeft > 0;

		/// <summary>Starts a slow motion of <paramref name="ticks"/> real ticks at <paramref name="speed"/> (0.2 = 80% slower);
		/// false while one runs or just ran.</summary>
		public static bool Start(int ticks, float speed) {
			if (ticksLeft > 0 || cooldown > 0 || ticks <= 0 || !(speed > 0f) || speed >= 1f) {
				return false;
			}
			ticksLeft = Math.Min(ticks, MaxTicks);
			rate = speed;
			accumulator = 0f;
			return true;
		}

		public override void PreUpdatePlayers() {
			if (ticksLeft <= 0) {
				UpdateThisTick = true;
				if (cooldown > 0) {
					cooldown--;
				}
				return;
			}
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

		private static void Clear() {
			ticksLeft = 0;
			cooldown = 0;
			rate = 1f;
			accumulator = 0f;
			UpdateThisTick = true;
		}

		public override void ClearWorld() => Clear();

		public override void OnWorldUnload() => Clear();

		public override void Unload() => Clear();
	}
}
