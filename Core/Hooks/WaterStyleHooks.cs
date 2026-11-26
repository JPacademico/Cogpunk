using System;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Hooks
{
	/// <summary>
	/// Lets a biome's water style win over vanilla's background water. Vanilla picks the water style in
	/// <c>Main.CalculateWaterStyle</c> (decompiled 1.4.4): an active water fountain first, then the Blood Moon, then by the
	/// surface background (<c>Main.bgStyle</c>: the ocean 13, the desert 6, the jungle 3, the corruption 2, ...), and only
	/// with any other background does it ask tModLoader's water styles (<c>WaterStylesLoader.ChooseStyle</c>). So a
	/// <c>ModBiome.WaterStyle</c> on a vanilla background, the Junkyard's tar on the ocean's, was never drawn (user,
	/// 2026-11-26: "the water at the junkyard biome is not changing color and just looks like hot water instead off muddy
	/// tar"). This detours that method: when <see cref="Override"/> names a style for the local player (content sets it, so
	/// Core stays content-free) and no water fountain is running, that style is the answer.
	/// <para>Why this lives in Core/Hooks: tModLoader has no hook that outranks a vanilla background's water (mods give their
	/// biome its own surface background to get there). If the detour can't be applied (a tModLoader update renamed the
	/// method), one error is logged and water keeps vanilla's look (D0 rule 14). Clients only (water styles are client-side);
	/// tModLoader removes <c>On_</c> detours when the mod unloads. D1: one delegate call a frame.</para>
	/// </summary>
	public sealed class WaterStyleHooks : ModSystem
	{
		/// <summary>The water style slot to draw for the local player now, or -1 for vanilla's choice (set by content in Load,
		/// cleared in Unload).</summary>
		public static Func<int> Override;

		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			try {
				On_Main.CalculateWaterStyle += Calculate;
			}
			catch (Exception e) {
				SafeLog.Error("Hooks.WaterStyle", e);
			}
		}

		public override void Unload() {
			Override = null;
		}

		private static int Calculate(On_Main.orig_CalculateWaterStyle orig, bool ignoreFountains) {
			int vanilla = orig(ignoreFountains);
			if (!ignoreFountains && Main.SceneMetrics.ActiveFountainColor >= 0) {
				return vanilla;                                 // a player's own fountain still colours the water
			}
			int style = Override?.Invoke() ?? -1;
			return style >= 0 ? style : vanilla;
		}
	}
}
