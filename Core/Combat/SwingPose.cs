using System;
using Microsoft.Xna.Framework;
using Terraria;

namespace Cogpunk.Core.Combat
{
	/// <summary>
	/// Poses a swung melee item (vanilla's swing style) at any blade angle, for custom swing curves (the Metal Wrench's slam,
	/// 2026-11-05b) and, later, directional melee (docs/design/melee-mechanics-study.md).
	/// <para>Angles are in the <b>facing frame</b>: radians, 0 = straight ahead, positive = downwards (screen y), negative =
	/// up; -pi/2 points straight up, -pi straight back. The world angle is the same facing right and mirrored facing left.</para>
	/// <para>How vanilla draws and poses it (decompiled 1.4.4): the held item of a swing is drawn at <c>itemLocation</c> turned
	/// by <c>itemRotation</c> about its bottom-left corner (bottom-right facing left, the sprite flipped), and the sprite
	/// points to its top right, so its blade lies along <c>itemRotation - pi/4</c> facing right
	/// (<c>PlayerDrawLayers.DrawPlayer_27_HeldItem</c>: origin <c>(W/2 - W/2 * direction, H)</c>); a composite arm at rotation
	/// <c>r</c> points along <c>r + pi/2</c> and <c>Player.GetFrontHandPosition</c> gives its hand; the composite arms are reset
	/// every tick in <c>ItemCheck_Inner</c> just before the use style is applied (<c>ItemLoader.UseStyle</c> runs after
	/// vanilla's), so setting them in <c>UseStyle</c> holds for that tick's drawing (vanilla's own useStyle 9 does the same);
	/// under reversed gravity vanilla poses as if upright and mirrors <c>itemLocation</c> and <c>itemRotation</c> at the
	/// end, and <c>SetCompositeArmFront</c> mirrors the arm itself.</para>
	/// <para>D1: pure math on value types, no allocation. D0: no tile or array access; non-finite input is ignored.</para>
	/// </summary>
	public static class SwingPose
	{
		/// <summary>World angle (upright gravity) of a facing-frame angle.</summary>
		public static float WorldAngle(int direction, float facing) => direction == -1 ? MathHelper.Pi - facing : facing;

		/// <summary>The front arm's composite rotation that points it along <paramref name="facing"/>.</summary>
		public static float ArmRotation(int direction, float facing) => WorldAngle(direction, facing) - MathHelper.PiOver2;

		/// <summary>The hand and the item's rotation for a swung item laid along <paramref name="facing"/>, as vanilla will
		/// draw it, without changing the player (for trails and afterimages).</summary>
		public static void Compute(Player player, float facing, out Vector2 hand, out float itemRotation) {
			int direction = player.direction == -1 ? -1 : 1;
			float arm = ArmRotation(direction, facing);
			hand = player.GetFrontHandPosition(Player.CompositeArmStretchAmount.Full, arm);
			itemRotation = direction == 1 ? facing + MathHelper.PiOver4 : -(facing + MathHelper.PiOver4);
			if (player.gravDir == -1f) {
				itemRotation = -itemRotation;
				hand.Y = player.position.Y + player.height + (player.position.Y - hand.Y);
			}
		}

		/// <summary>Poses <paramref name="player"/>'s swung item along <paramref name="facing"/>: the front arm along it (and
		/// the back arm hanging, so vanilla's swing frames don't show), <c>itemLocation</c> at the hand, <c>itemRotation</c>.
		/// Call it from <c>UseStyle</c>.</summary>
		public static void Apply(Player player, float facing, float backArm = 0f) {
			if (!float.IsFinite(facing)) {
				return;
			}
			int direction = player.direction == -1 ? -1 : 1;
			float arm = ArmRotation(direction, facing);
			player.SetCompositeArmFront(true, Player.CompositeArmStretchAmount.Full, arm);
			player.SetCompositeArmBack(true, Player.CompositeArmStretchAmount.Full, backArm * direction);
			Compute(player, facing, out Vector2 hand, out float rotation);
			player.itemLocation = hand;
			player.itemRotation = rotation;
		}

		/// <summary>The blade's unit direction in the world (gravity included).</summary>
		public static Vector2 BladeDirection(Player player, float facing) {
			float world = WorldAngle(player.direction == -1 ? -1 : 1, facing);
			Vector2 d = new(MathF.Cos(world), MathF.Sin(world));
			if (player.gravDir == -1f) {
				d.Y = -d.Y;
			}
			return d;
		}

		/// <summary>The point <paramref name="along"/> px out along the blade and <paramref name="below"/> px to its lower
		/// side (the clockwise side facing right: the side vanilla's swing sprites hang their edge on).</summary>
		public static Vector2 BladePoint(Player player, Vector2 hand, float facing, float along, float below) {
			Vector2 d = BladeDirection(player, facing);
			Vector2 n = new(-d.Y, d.X);                     // clockwise from the blade, facing right
			if (player.direction == -1) {
				n = -n;                                    // the mirrored sprite keeps its edge below the blade
			}
			if (player.gravDir == -1f) {
				n = -n;
			}
			return hand + d * along + n * below;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Curves
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>0..1 of <paramref name="t"/> between <paramref name="from"/> and <paramref name="to"/>, clamped.</summary>
		public static float Phase(float t, float from, float to) => to <= from ? (t >= to ? 1f : 0f) : MathHelper.Clamp((t - from) / (to - from), 0f, 1f);

		public static float EaseInCubic(float t) => t * t * t;

		public static float EaseOutCubic(float t) {
			float u = 1f - t;
			return 1f - u * u * u;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Collision
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>True if the capsule from <paramref name="a"/> to <paramref name="b"/> with <paramref name="radius"/>
		/// touches <paramref name="rect"/>. Exact: in 2D a segment that misses a box is nearest to it at an end of one of
		/// them. (Vanilla's <c>Collision.CheckAABBvLineCollision</c> with a width allocates an array per call, and
		/// <c>Utils.LineRectangleDistance</c> misses a blade crossing the middle of a big box.)</summary>
		public static bool CapsuleHitsRect(Vector2 a, Vector2 b, float radius, Rectangle rect) {
			if (!float.IsFinite(a.X) || !float.IsFinite(a.Y) || !float.IsFinite(b.X) || !float.IsFinite(b.Y)) {
				return false;
			}
			float left = rect.X, top = rect.Y, right = rect.X + rect.Width, bottom = rect.Y + rect.Height;
			// broad phase: the capsule's bounds
			if (MathF.Max(a.X, b.X) + radius < left || MathF.Min(a.X, b.X) - radius > right || MathF.Max(a.Y, b.Y) + radius < top
				|| MathF.Min(a.Y, b.Y) - radius > bottom) {
				return false;
			}
			if (Inside(a, left, top, right, bottom) || Inside(b, left, top, right, bottom)) {
				return true;
			}
			Vector2 tl = new(left, top), tr = new(right, top), bl = new(left, bottom), br = new(right, bottom);
			if (SegmentsCross(a, b, tl, tr) || SegmentsCross(a, b, tr, br) || SegmentsCross(a, b, br, bl) || SegmentsCross(a, b, bl, tl)) {
				return true;
			}
			float r2 = radius * radius;
			return PointRectDistanceSquared(a, left, top, right, bottom) <= r2 || PointRectDistanceSquared(b, left, top, right, bottom) <= r2
				|| PointSegmentDistanceSquared(tl, a, b) <= r2 || PointSegmentDistanceSquared(tr, a, b) <= r2
				|| PointSegmentDistanceSquared(bl, a, b) <= r2 || PointSegmentDistanceSquared(br, a, b) <= r2;
		}

		private static bool Inside(Vector2 p, float left, float top, float right, float bottom) => p.X >= left && p.X <= right && p.Y >= top && p.Y <= bottom;

		private static float PointRectDistanceSquared(Vector2 p, float left, float top, float right, float bottom) {
			float dx = p.X < left ? left - p.X : p.X > right ? p.X - right : 0f;
			float dy = p.Y < top ? top - p.Y : p.Y > bottom ? p.Y - bottom : 0f;
			return dx * dx + dy * dy;
		}

		private static float PointSegmentDistanceSquared(Vector2 p, Vector2 a, Vector2 b) {
			Vector2 ab = b - a;
			float len2 = ab.LengthSquared();
			float t = len2 > 1e-6f ? MathHelper.Clamp(Vector2.Dot(p - a, ab) / len2, 0f, 1f) : 0f;
			return Vector2.DistanceSquared(p, a + ab * t);
		}

		private static float Cross(Vector2 o, Vector2 a, Vector2 b) => (a.X - o.X) * (b.Y - o.Y) - (a.Y - o.Y) * (b.X - o.X);

		private static bool SegmentsCross(Vector2 a, Vector2 b, Vector2 c, Vector2 d) {
			float d1 = Cross(c, d, a), d2 = Cross(c, d, b), d3 = Cross(a, b, c), d4 = Cross(a, b, d);
			return ((d1 > 0f && d2 < 0f) || (d1 < 0f && d2 > 0f)) && ((d3 > 0f && d4 < 0f) || (d3 < 0f && d4 > 0f));
		}
	}
}
