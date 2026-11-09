using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Dusts
{
	/// <summary>
	/// The smoke a <see cref="Tiles.LiftTurbineTile"/> pours down under Coghaven: pixel-art puffs (four sizes, 10x10 art each,
	/// art/coghaven/make_coghaven_art.py) that billow as they sink, spread, slow down and fade. The puff grows by changing
	/// frame, never by scaling (no mixels, D4); the fade is done in code (<see cref="GetAlpha"/>), the sheet is opaque.
	/// <para>The age rides in <c>dust.fadeIn</c> (vanilla's dust field, unused while <see cref="Update"/> returns false), the
	/// lifetime is <see cref="Lifetime"/> ticks. D1: no allocation, a few float operations a tick; spawned on clients only by
	/// the turbine, through <c>SafeSpawn</c>.</para>
	/// </summary>
	public class TurbineSmoke : ModDust
	{
		public const int Lifetime = 96;
		public const int FrameSize = 20;
		private const int Frames = 4;

		public override void OnSpawn(Dust dust) {
			dust.noGravity = true;
			dust.noLight = true;
			dust.scale = 1f;
			dust.rotation = 0f;
			dust.alpha = 0;
			dust.fadeIn = 0f;
			dust.frame = new Rectangle(0, 0, FrameSize, FrameSize);
		}

		public override bool Update(Dust dust) {
			float age = ++dust.fadeIn;
			dust.position += dust.velocity;
			dust.velocity.Y = dust.velocity.Y * 0.985f + 0.004f;    // sinks, slowing
			dust.velocity.X *= 0.99f;
			if (age % 24f == 0f) {
				dust.velocity.X += Main.rand.NextFloat(-0.12f, 0.12f);  // a little drift (visual only)
			}
			int frame = age < 12f ? 0 : age < 30f ? 1 : age < 56f ? 2 : 3;
			dust.frame.Y = frame * FrameSize;
			dust.alpha = age < Lifetime * 0.45f ? 0 : (int)(255f * (age - Lifetime * 0.45f) / (Lifetime * 0.55f));
			if (age >= Lifetime || dust.alpha >= 255) {
				dust.active = false;
			}
			return false;
		}

		public override Color? GetAlpha(Dust dust, Color lightColor) {
			float keep = (255 - dust.alpha) / 255f;
			Color lit = Color.Lerp(lightColor, Color.White, 0.35f);     // steam catches a little light of its own
			return lit * keep;
		}
	}
}
