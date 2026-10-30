using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.UI;

namespace Cogpunk.Core.Events
{
	/// <summary>
	/// The progress bar of a <see cref="CogpunkInvasion"/>, drawn like vanilla's (decompiled <c>Main.DrawInvasionProgress</c>,
	/// the no-wave layout): bottom right, the "Cleared N%" bar in the blue box, the invasion's icon and name in a box in its
	/// colour above it, fading in and out at 0.05 a frame. Shown for <see cref="DisplayTicks"/> after a kill report, and all
	/// the time while near the invasion when the player picked "show near invasions" (vanilla's
	/// <c>invasionProgressMode == 2</c> and <c>CheckInvasionProgressDisplay</c>: a roster NPC within 5000 px of the screen,
	/// player above the surface). If vanilla's own bar is up (a Pumpkin or Frost Moon), ours sits above it.
	/// <para>Client only (D2); the layer is created once (D1: no allocation per frame, the percentage text is rebuilt only
	/// when it changes); the near check runs every <see cref="NearCheckInterval"/> ticks.</para>
	/// </summary>
	public sealed class InvasionProgressBar : ModSystem
	{
		public const int DisplayTicks = 160;               // vanilla ReportInvasionProgress
		public const int NearCheckInterval = 15;
		private const int NearRange = 5000;                // vanilla CheckInvasionProgressDisplay

		private static GameInterfaceLayer layer;
		private static string percentText = "";
		private static int percentShown = -1;

		public override void Load() {
			if (!Main.dedServ) {
				layer = new LegacyGameInterfaceLayer("Cogpunk: Invasion Progress", DrawLayer, InterfaceScaleType.UI);
			}
		}

		public override void Unload() {
			layer = null;
			percentText = "";
			percentShown = -1;
		}

		public override void UpdateUI(GameTime gameTime) {
			if (Main.dedServ || Main.gameMenu) {
				return;
			}
			var all = CogpunkInvasion.All;
			bool check = Main.GameUpdateCount % NearCheckInterval == 0;
			for (int i = 0; i < all.Count; i++) {
				CogpunkInvasion invasion = all[i];
				if (check) {
					invasion.Near = Main.invasionProgressMode == 2 && invasion.Active && NearRoster(invasion);
				}
				if (Main.invasionProgressMode == 2 && invasion.Near && invasion.DisplayLeft < DisplayTicks) {
					invasion.DisplayLeft = DisplayTicks;
				}
				if (!Main.gamePaused && invasion.DisplayLeft > 0) {
					invasion.DisplayLeft--;
				}
				invasion.Alpha = MathHelper.Clamp(invasion.Alpha + (invasion.DisplayLeft > 0 ? 0.05f : -0.05f), 0f, 1f);
				if (Main.invasionProgressMode == 0) {
					invasion.DisplayLeft = 0;
					invasion.Alpha = 0f;
				}
			}
		}

		private static bool NearRoster(CogpunkInvasion invasion) {
			Player player = Main.LocalPlayer;                  // UI: the local player is the one to ask about
			if (player.position.Y > Main.worldSurface * 16.0) {
				return false;
			}
			Rectangle screen = new((int)Main.screenPosition.X - NearRange, (int)Main.screenPosition.Y - NearRange,
				Main.screenWidth + NearRange * 2, Main.screenHeight + NearRange * 2);
			foreach (NPC npc in Main.ActiveNPCs) {
				if (invasion.KillValue(npc.type) > 0 && screen.Contains((int)npc.Center.X, (int)npc.Center.Y)) {
					return true;
				}
			}
			return false;
		}

		public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers) {
			if (layer == null) {
				return;
			}
			int index = layers.FindIndex(static l => l.Name == "Vanilla: Invasion Progress Bars");
			layers.Insert(index >= 0 ? index + 1 : layers.Count, layer);
		}

		private static bool DrawLayer() {
			var all = CogpunkInvasion.All;
			for (int i = 0; i < all.Count; i++) {
				if (all[i].Alpha > 0f) {
					Draw(Main.spriteBatch, all[i]);
					break;                                    // one invasion at a time
				}
			}
			return true;
		}

		private static void Draw(SpriteBatch spriteBatch, CogpunkInvasion invasion) {
			float alpha = invasion.Alpha;
			float scale = 0.5f + alpha * 0.5f;
			float lift = Main.invasionProgressAlpha > 0f ? 100f * scale : 0f;
			int width = (int)(200f * scale);
			int height = (int)(45f * scale);
			Vector2 barCentre = new(Main.screenWidth - 120, Main.screenHeight - 40 - lift);
			Utils.DrawInvBG(spriteBatch, new Rectangle((int)barCentre.X - width / 2, (int)barCentre.Y - height / 2, width, height), new Color(63, 65, 151, 255) * 0.785f);
			int percent = invasion.SizeStart > 0 ? (int)(invasion.Progress * 100f) : 0;
			if (percent != percentShown) {
				percentShown = percent;
				percentText = Language.GetTextValue("Game.WaveCleared", percent + "%");
			}
			Texture2D bar = TextureAssets.ColorBar.Value;
			spriteBatch.Draw(bar, barCentre, null, Color.White * alpha, 0f, new Vector2(bar.Width / 2, 0f), scale, SpriteEffects.None, 0f);
			float fill = invasion.Progress;
			Vector2 size = FontAssets.MouseText.Value.MeasureString(percentText);
			float textScale = size.Y > 22f ? scale * 22f / size.Y : scale;
			float barWidth = 169f * scale;
			float barHeight = 8f * scale;
			Vector2 at = barCentre + Vector2.UnitY * barHeight + Vector2.UnitX;
			Utils.DrawBorderString(spriteBatch, percentText, at + new Vector2(0f, -4f), Color.White * alpha, textScale, 0.5f, 1f);
			at += Vector2.UnitX * (fill - 0.5f) * barWidth;
			Texture2D pixel = TextureAssets.MagicPixel.Value;
			Rectangle one = new(0, 0, 1, 1);
			spriteBatch.Draw(pixel, at, one, new Color(255, 241, 51) * alpha, 0f, new Vector2(1f, 0.5f), new Vector2(barWidth * fill, barHeight), SpriteEffects.None, 0f);
			spriteBatch.Draw(pixel, at, one, new Color(255, 165, 0, 127) * alpha, 0f, new Vector2(1f, 0.5f), new Vector2(2f, barHeight), SpriteEffects.None, 0f);
			spriteBatch.Draw(pixel, at, one, Color.Black * alpha, 0f, new Vector2(0f, 0.5f), new Vector2(barWidth * (1f - fill), barHeight), SpriteEffects.None, 0f);

			// The name box: icon and name, in the invasion's colour.
			string name = invasion.DisplayName?.Value ?? "";
			Vector2 nameSize = FontAssets.MouseText.Value.MeasureString(name);
			Texture2D icon = invasion.Icon?.IsLoaded == true ? invasion.Icon.Value : null;
			int iconWidth = icon?.Width ?? 0;
			float right = 120f + (nameSize.X > 200f ? nameSize.X - 200f : 0f);
			Rectangle box = Utils.CenteredRectangle(new Vector2(Main.screenWidth - right, Main.screenHeight - 80 - lift), (nameSize + new Vector2(iconWidth + 12, 6f)) * scale);
			Utils.DrawInvBG(spriteBatch, box, invasion.BarColor);
			if (icon != null) {
				spriteBatch.Draw(icon, box.Left() + Vector2.UnitX * scale * 8f, null, Color.White * alpha, 0f, new Vector2(0f, icon.Height / 2), scale * 0.8f, SpriteEffects.None, 0f);
			}
			Utils.DrawBorderString(spriteBatch, name, box.Right() + Vector2.UnitX * scale * -22f, Color.White * alpha, scale * 0.9f, 1f, 0.4f);
		}
	}
}
