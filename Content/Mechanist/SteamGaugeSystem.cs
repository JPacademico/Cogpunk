using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.UI;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// The steam gauge (user-set 2026-10-27): a brass-caged glass boiler tank just left of the life hearts. The steam level
	/// rises and falls inside it; hovering it shows the amount (like vanilla's life and mana hovers, decompiled
	/// <c>CommonResourceBarMethods.DrawLifeMouseOver</c>). While overheated the steam turns ember-hot and the tank rattles.
	/// <para>Placement: vanilla draws the hearts from <c>Main.screenWidth - 300</c> (decompiled
	/// <c>ClassicPlayerResourcesDisplaySet</c> 500 + screenWidth - 800, <c>FancyClassicPlayerResourcesDisplaySet</c>
	/// screenWidth - 296), so the tank's right edge sits <see cref="GapToHearts"/> px left of that, in the UI-scaled layer.</para>
	/// <para>Art (art/mechanist/make_mechanist_art.py, SteamGauge.png, 2x): <see cref="Frames"/> frames of
	/// <see cref="Width"/>x<see cref="Height"/> on a <see cref="Stride"/> px stride: the tank behind the glass, the steam,
	/// the overheated steam, the front (cage bars, glint, valve), the valve turned. Client only; it draws only while
	/// <see cref="SteamPlayer.ShowGauge"/>. D1: one cached layer object, cached hover text rebuilt only when the numbers
	/// change, no allocation per frame.</para>
	/// </summary>
	[Autoload(Side = ModSide.Client)]
	public sealed class SteamGaugeSystem : ModSystem
	{
		public const int Width = 32, Height = 64, Stride = 66, Frames = 5;
		public const int FillTop = 10, FillBottom = 54;  // the glass's inside, in sheet px (the steam fills between)
		public const int GapToHearts = 14;
		public const int Top = 18;

		private static Asset<Texture2D> texture;
		private static LegacyGameInterfaceLayer layer;
		private static LocalizedText hoverFormat;
		private static string hoverText = "";
		private static int shownSteam = -1, shownMax = -1;

		public override void Load() {
			const string path = "Cogpunk/Content/Mechanist/SteamGauge";
			texture = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;   // missing art never blocks loading (D0)
			layer = new LegacyGameInterfaceLayer("Cogpunk: Steam Gauge", DrawGauge, InterfaceScaleType.UI);
			hoverFormat = Mod.GetLocalization("Mechanist.SteamHover");
		}

		public override void Unload() {
			texture = null;
			layer = null;
			hoverFormat = null;
			hoverText = "";
			shownSteam = shownMax = -1;
		}

		public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers) {
			int index = layers.FindIndex(static l => l.Name == "Vanilla: Resource Bars");
			if (index >= 0 && layer != null) {
				layers.Insert(index, layer);
			}
		}

		private static bool DrawGauge() {
			Player player = Main.LocalPlayer;
			if (player == null || !player.active || Main.gameMenu || texture?.IsLoaded != true) {
				return true;
			}
			SteamPlayer steam = player.GetModPlayer<SteamPlayer>();
			if (!steam.ShowGauge && !player.dead) {
				return true;
			}
			Texture2D tex = texture.Value;
			int x = Main.screenWidth - 300 - GapToHearts - Width;
			int y = Top;
			if (steam.Overheated && !Main.gamePaused) {
				x += Main.rand.Next(-1, 2) * 2;               // the tank rattles (2 px steps: stays on the art grid)
			}
			SpriteBatch sb = Main.spriteBatch;
			sb.Draw(tex, new Vector2(x, y), new Rectangle(0, 0, Width, Height), Color.White);
			float fill = steam.SteamMax > 0 ? MathHelper.Clamp(steam.Steam / (float)steam.SteamMax, 0f, 1f) : 0f;
			int inside = FillBottom - FillTop;
			int level = (int)(inside * fill * 0.5f) * 2;     // whole art pixels
			if (level > 0) {
				int frame = steam.Overheated ? 2 : 1;
				int top = FillBottom - level;
				sb.Draw(tex, new Vector2(x, y + top), new Rectangle(0, frame * Stride + top, Width, level), Color.White);
			}
			int front = steam.Steam < steam.SteamMax && steam.RegenWait >= 1f && (Main.GameUpdateCount / 8) % 2 == 1 ? 4 : 3;
			sb.Draw(tex, new Vector2(x, y), new Rectangle(0, front * Stride, Width, Height), Color.White);
			if (Main.MouseScreen.X >= x && Main.MouseScreen.X < x + Width && Main.MouseScreen.Y >= y && Main.MouseScreen.Y < y + Height
				&& !Main.mouseText) {
				player.cursorItemIconEnabled = false;
				Main.instance.MouseTextHackZoom(HoverText(steam));
				Main.mouseText = true;
			}
			return true;
		}

		/// <summary>"Steam: 75/100", rebuilt only when a number changes.</summary>
		private static string HoverText(SteamPlayer steam) {
			if (steam.Steam != shownSteam || steam.SteamMax != shownMax) {
				shownSteam = steam.Steam;
				shownMax = steam.SteamMax;
				hoverText = hoverFormat?.Format(shownSteam, shownMax) ?? "";
			}
			return hoverText;
		}
	}
}
