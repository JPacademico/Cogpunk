using System;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Visuals
{
	/// <summary>
	/// Camera locks for cinematic moments ("the screen locks"): boss intros and boss deaths (art direction 2026-10-26: every
	/// boss gets a themed death that locks the camera like its spawn).
	/// <para>Client-side code calls <see cref="Request"/> every update with a world focus point and a strength in 0..1
	/// (its own ease in/out); the strongest request of the current update wins and pulls <c>Main.screenPosition</c>
	/// towards it with a smoothstep, rounded to whole pixels. A request lives for one update, so a boss that dies,
	/// despawns or stops asking releases the camera on its own. While the game is paused the last request holds.</para>
	/// <para>D1: two floats and a vector, no allocation. D2: purely local (never touches gameplay or other clients).</para>
	/// </summary>
	public sealed class CinematicCamera : ModSystem
	{
		private static Vector2 focus;
		private static float strength;
		private static uint requestTick = uint.MaxValue;

		/// <summary>Ask for the camera this update. <paramref name="amount"/> 0..1 (0 = no lock).</summary>
		public static void Request(Vector2 worldFocus, float amount) {
			if (Main.dedServ || amount <= 0f || !MathSafety.IsFinite(worldFocus)) {
				return;
			}
			amount = Math.Min(1f, amount);
			uint now = Main.GameUpdateCount;
			if (requestTick != now || amount > strength) {
				requestTick = now;
				focus = worldFocus;
				strength = amount;
			}
		}

		/// <summary>0..1 ease for a lock that lasts <paramref name="length"/> ticks: rises over the first
		/// <paramref name="easeIn"/> ticks, holds, and falls over the last <paramref name="easeOut"/>.</summary>
		public static float Envelope(float tick, float length, float easeIn, float easeOut) {
			if (tick < 0f || tick > length) {
				return 0f;
			}
			float a = easeIn > 0f ? tick / easeIn : 1f;
			float b = easeOut > 0f ? (length - tick) / easeOut : 1f;
			return MathHelper.Clamp(Math.Min(a, b), 0f, 1f);
		}

		public override void Unload() {
			requestTick = uint.MaxValue;
		}

		public override void OnWorldUnload() {
			requestTick = uint.MaxValue;
		}

		public override void ModifyScreenPosition() {
			if (Main.dedServ || Main.gameMenu || requestTick == uint.MaxValue) {
				return;
			}
			if (!Main.gamePaused && Main.GameUpdateCount - requestTick > 1) {
				requestTick = uint.MaxValue;               // nobody asked last update: release
				return;
			}
			float eased = strength * strength * (3f - 2f * strength);   // smoothstep
			Vector2 target = focus - new Vector2(Main.screenWidth, Main.screenHeight) * 0.5f;
			Main.screenPosition = Vector2.Lerp(Main.screenPosition, target, eased);
			Main.screenPosition = new Vector2(MathF.Round(Main.screenPosition.X), MathF.Round(Main.screenPosition.Y));
		}
	}
}
