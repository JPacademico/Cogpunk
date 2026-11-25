using System;
using System.Collections.Generic;
using Cogpunk.Core.Configs;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;
using Terraria.UI;

namespace Cogpunk.Core.Visuals
{
	/// <summary>
	/// A white flash over the whole screen that fades out (first used by the Fungimancer's rainbow mushroom blast, user
	/// 2026-11-25: "with quick a white flash"): <see cref="Flash"/> on a client starts it; it is drawn under the interface (the
	/// first interface layer), strongest at once and fading by a curve; Reduce Flashing (the client config) halves it.
	/// <para>D1: one rectangle a frame while it runs, nothing otherwise. Clients only (nothing on a server); cleared with the
	/// world.</para>
	/// </summary>
	public sealed class ScreenFlash : ModSystem
	{
		private static int ticksLeft, length;

		/// <summary>A flash of <paramref name="ticks"/> (a stronger one wins; never on a server).</summary>
		public static void Flash(int ticks) {
			if (Main.dedServ || ticks <= 0) {
				return;
			}
			if (ticks >= ticksLeft) {
				ticksLeft = length = Math.Min(ticks, 180);
			}
		}

		public override void PostUpdateEverything() {
			if (ticksLeft > 0) {
				ticksLeft--;
			}
		}

		public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers) {
			layers.Insert(0, new LegacyGameInterfaceLayer("Cogpunk: Screen Flash", Draw, InterfaceScaleType.None));
		}

		private static bool Draw() {
			if (ticksLeft <= 0 || length <= 0) {
				return true;
			}
			float t = ticksLeft / (float)length;
			float strength = t * t * (CogpunkClientConfig.Instance?.ReduceFlashing == true ? 0.5f : 0.95f);
			Main.spriteBatch.Draw(TextureAssets.MagicPixel.Value, new Rectangle(0, 0, Main.screenWidth, Main.screenHeight), Color.White * strength);
			return true;
		}

		private static void Clear() {
			ticksLeft = length = 0;
		}

		public override void ClearWorld() => Clear();

		public override void Unload() => Clear();
	}
}
