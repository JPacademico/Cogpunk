using System;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace Cogpunk.Core.Visuals
{
	/// <summary>
	/// Thin smoke trails behind fast shots (user, 2026-11-05: "a thin smoke trail effect to the bullets ... this smoke trail
	/// should quickly vanish after some time (0.5 seconds); this is to add more impact to the shots"). A shot adds the
	/// segment it flew this update (<see cref="Add"/>); every segment lives <see cref="LifeTicks"/> ticks on its own, so the
	/// trail stays and fades where the shot flew even after the shot is gone. Drawn as a line of 2x2 px squares on the 2 px
	/// art grid (D4: one art pixel wide, never a rotated or scaled sprite), drifting up a little and breaking up as it fades
	/// (a part of its squares drop out, then the rest fade out).
	/// <para>D1/D0: a fixed ring of <see cref="Capacity"/> segments made once on clients (the oldest is reused, never a
	/// new allocation; at most ~3000 small draws in one SpriteBatch pass); nothing on a dedicated server; NaN and jumps
	/// (a teleport, a bounce reset) are refused. D2: purely visual and local: each client draws the shots it simulates.
	/// Drawn after the tiles and NPCs and before the projectiles (decompiled <c>Main.DoDraw</c>: <c>SystemLoader.PostDrawTiles</c>
	/// runs between them with the SpriteBatch ended, so it is begun and ended here with vanilla's own settings).</para>
	/// </summary>
	public sealed class SmokeTrails : ModSystem
	{
		public const int Capacity = 1024;
		public const int LifeTicks = 30;                    // 0.5 s (user-set)
		public const float MaxSegment = 160f;               // longer than any shot flies in one update: a jump, not a flight
		public const float Rise = 0.12f;                    // px a tick the smoke drifts up as it ages
		private const int Square = 2;                       // one art pixel

		private struct Segment
		{
			public Vector2 A, B;
			public uint Born;
			public Color Tint;
			public byte Seed;
		}

		private static Segment[] segments;
		private static int next;
		private static int live;                            // segments added in the last LifeTicks (an early out)
		private static uint lastAdd;

		public override void Load() {
			if (!Main.dedServ) {
				segments = new Segment[Capacity];
			}
		}

		public override void Unload() {
			segments = null;
		}

		public override void OnWorldUnload() {
			if (segments != null) {
				Array.Clear(segments);
			}
			next = 0;
			live = 0;
		}

		/// <summary>Clients: the smoke a shot leaves between two points this update (world px). Light steam grey by default.</summary>
		public static void Add(Vector2 from, Vector2 to, Color? tint = null) {
			if (segments == null || Main.dedServ || !MathSafety.IsFinite(from) || !MathSafety.IsFinite(to)) {
				return;
			}
			if (Vector2.DistanceSquared(from, to) > MaxSegment * MaxSegment || from == to) {
				return;
			}
			ref Segment s = ref segments[next];
			s.A = from;
			s.B = to;
			s.Born = Main.GameUpdateCount;
			s.Tint = tint ?? new Color(195, 200, 205);       // Steam 1
			s.Seed = (byte)(next * 37);
			next = (next + 1) % Capacity;
			live = Math.Min(Capacity, live + 1);
			lastAdd = Main.GameUpdateCount;
		}

		public override void PostDrawTiles() {
			if (segments == null || live == 0) {
				return;
			}
			uint now = Main.GameUpdateCount;
			if (now - lastAdd > LifeTicks) {
				live = 0;                                    // everything has faded
				return;
			}
			Texture2D pixel = TextureAssets.MagicPixel.Value;
			Vector2 screen = Main.screenPosition;
			float left = screen.X - 32f, top = screen.Y - 32f;
			float right = screen.X + Main.screenWidth + 32f, bottom = screen.Y + Main.screenHeight + 32f;
			SpriteBatch sb = Main.spriteBatch;
			sb.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend, Main.DefaultSamplerState, DepthStencilState.None, Main.Rasterizer, null,
				Main.GameViewMatrix.TransformationMatrix);
			for (int i = 0; i < Capacity; i++) {
				ref Segment s = ref segments[i];
				uint age = now - s.Born;
				if (age >= LifeTicks || s.Born == 0) {
					continue;
				}
				if (Math.Max(s.A.X, s.B.X) < left || Math.Min(s.A.X, s.B.X) > right || Math.Max(s.A.Y, s.B.Y) < top || Math.Min(s.A.Y, s.B.Y) > bottom) {
					continue;
				}
				float life = 1f - age / (float)LifeTicks;
				float keep = 0.35f + life;                   // the share of squares still there: it breaks up as it fades
				Vector2 mid = (s.A + s.B) * 0.5f;
				Color light = Lighting.GetColor((int)(mid.X / 16f), (int)(mid.Y / 16f));
				Color color = Color.Lerp(light, Color.White, 0.3f).MultiplyRGB(s.Tint) * (0.75f * life * life + 0.1f * life);
				Vector2 d = s.B - s.A;
				int steps = Math.Clamp((int)(Math.Max(Math.Abs(d.X), Math.Abs(d.Y)) / Square), 1, (int)(MaxSegment / Square));
				float rise = age * Rise;
				for (int k = 0; k < steps; k++) {
					if (((k * 73 + s.Seed * 19 + (int)age * 3) & 15) / 16f > keep) {
						continue;
					}
					Vector2 p = s.A + d * (k / (float)steps);
					int x = (int)MathF.Floor(p.X / Square) * Square;
					int y = (int)MathF.Floor((p.Y - rise) / Square) * Square;
					sb.Draw(pixel, new Rectangle(x - (int)screen.X, y - (int)screen.Y, Square, Square), color);
				}
			}
			sb.End();
		}
	}
}
