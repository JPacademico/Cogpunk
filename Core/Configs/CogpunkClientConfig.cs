using System.ComponentModel;
using Terraria;
using Terraria.ModLoader.Config;

namespace Cogpunk.Core.Configs
{
	/// <summary>Per-player visual and accessibility settings. Never affects gameplay (that would desync, D2).</summary>
	public sealed class CogpunkClientConfig : ModConfig
	{
		/// <summary>Cached instance (D1: no lookups in hot paths). Null until loaded and after unload.</summary>
		public static CogpunkClientConfig Instance { get; internal set; }

		public override ConfigScope Mode => ConfigScope.ClientSide;

		[Header("Visuals")]
		[DefaultValue(true)]
		public bool ScreenShake;

		[DefaultValue(1f)]
		[Range(0f, 1f)]
		[Increment(0.1f)]
		[Slider]
		public float EffectDensity;

		[DefaultValue(false)]
		public bool ReduceFlashing;

		public override void OnLoaded() {
			Instance = this;
		}

		/// <summary>
		/// Roll before spawning an optional particle: returns false more often as Effect Density goes down.
		/// Always false on a dedicated server.
		/// </summary>
		public static bool RollEffect() {
			if (Main.dedServ) {
				return false;
			}
			float density = Instance?.EffectDensity ?? 1f;
			return density >= 1f || Main.rand.NextFloat() < density;
		}
	}
}
