using Microsoft.Xna.Framework;

namespace Cogpunk.Core.Safety
{
	/// <summary>
	/// NaN/Infinity guards. A NaN position or velocity makes entities vanish, breaks collision and can
	/// crash drawing; it usually comes from normalizing a zero vector or dividing by a zero distance.
	/// Prefer <c>vector.SafeNormalize(Vector2.Zero)</c> over <c>Vector2.Normalize</c>.
	/// </summary>
	public static class MathSafety
	{
		public static bool IsFinite(Vector2 value) {
			return float.IsFinite(value.X) && float.IsFinite(value.Y);
		}

		/// <summary>Replaces a non-finite vector with <paramref name="fallback"/>. Returns true if it had to.</summary>
		public static bool Sanitize(ref Vector2 value, Vector2 fallback = default) {
			if (IsFinite(value)) {
				return false;
			}
			value = fallback;
			return true;
		}

		/// <summary>Division that returns <paramref name="fallback"/> instead of NaN/Infinity.</summary>
		public static float SafeDivide(float numerator, float denominator, float fallback = 0f) {
			float result = numerator / denominator;
			return float.IsFinite(result) ? result : fallback;
		}
	}
}
