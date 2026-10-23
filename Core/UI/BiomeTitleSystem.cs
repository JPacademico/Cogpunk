using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using ReLogic.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.UI;
using Terraria.UI.Chat;

namespace Cogpunk.Core.UI
{
	/// <summary>
	/// Biome introduction banner: a large title at the top centre of the screen that fades in quickly, holds for three
	/// seconds and fades out, framed by the brass cog ornament (<c>Assets/UI/BiomeTitleOrnament.png</c>).
	/// <para>Client-local by design: call <see cref="Show"/> only for <c>Main.myPlayer</c> (a biome's <c>OnEnter</c> also runs
	/// for other players on some sides). Nothing is synced and nothing runs on a dedicated server. A title that was shown
	/// less than <see cref="RepeatCooldown"/> ticks ago is not shown again, so walking back and forth across a biome edge
	/// doesn't spam it.</para>
	/// </summary>
	public sealed class BiomeTitleSystem : ModSystem
	{
		public const int FadeInTicks = 12;
		public const int HoldTicks = 180;          // three seconds fully visible
		public const int FadeOutTicks = 30;
		public const int RepeatCooldown = 60 * 60;
		private const int TotalTicks = FadeInTicks + HoldTicks + FadeOutTicks;
		private const float TitleScale = 1.1f;
		private const float TopFraction = 0.16f;   // banner centre, as a fraction of the screen height

		private static readonly Color TextColor = new(223, 185, 78);     // Brass 4
		private static readonly Color ShadowColor = new(43, 26, 14);     // Brass 0

		private static LocalizedText title;
		private static int timer = -1;
		private static string lastKey;
		private static uint lastShownAt;
		private static Asset<Texture2D> ornament;
		private static GameInterfaceLayer layer;

		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			ornament = ModContent.Request<Texture2D>("Cogpunk/Assets/UI/BiomeTitleOrnament");
			layer = new LegacyGameInterfaceLayer("Cogpunk: Biome Title", DrawTitle, InterfaceScaleType.UI);
		}

		public override void Unload() {
			ornament = null;
			layer = null;
			title = null;
			lastKey = null;
		}

		public override void OnWorldUnload() {
			timer = -1;
			lastKey = null;
		}

		/// <summary>Shows <paramref name="text"/> unless the same title was shown in the last minute. Local client only.</summary>
		public static void Show(LocalizedText text) {
			if (Main.dedServ || text == null) {
				return;
			}
			if (text.Key == lastKey && Main.GameUpdateCount - lastShownAt < RepeatCooldown) {
				return;
			}
			title = text;
			lastKey = text.Key;
			lastShownAt = Main.GameUpdateCount;
			timer = 0;
		}

		public override void PostUpdateEverything() {
			if (timer >= 0 && ++timer >= TotalTicks) {
				timer = -1;
			}
		}

		public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers) {
			if (timer < 0 || layer == null) {
				return;
			}
			int index = layers.FindIndex(static l => l.Name == "Vanilla: Inventory");
			layers.Insert(index < 0 ? layers.Count : index, layer);
		}

		private static float Opacity() {
			if (timer < FadeInTicks) {
				return timer / (float)FadeInTicks;
			}
			if (timer < FadeInTicks + HoldTicks) {
				return 1f;
			}
			return 1f - (timer - FadeInTicks - HoldTicks) / (float)FadeOutTicks;
		}

		private static bool DrawTitle() {
			if (timer < 0 || title == null || Main.gameMenu) {
				return true;
			}
			float opacity = MathHelper.Clamp(Opacity(), 0f, 1f);
			SpriteBatch spriteBatch = Main.spriteBatch;
			DynamicSpriteFont font = FontAssets.DeathText.Value;
			string text = title.Value;
			Vector2 size = font.MeasureString(text) * TitleScale;
			Vector2 centre = new(Main.screenWidth / Main.UIScale * 0.5f, Main.screenHeight / Main.UIScale * TopFraction);

			if (ornament?.IsLoaded == true) {
				Texture2D tex = ornament.Value;
				int half = tex.Width / 2;
				Rectangle left = new(0, 0, half, tex.Height);
				Rectangle right = new(half, 0, tex.Width - half, tex.Height);
				Color tint = Color.White * opacity;
				Vector2 y = new(0f, centre.Y - tex.Height * 0.5f + 2f);
				spriteBatch.Draw(tex, new Vector2(centre.X - size.X * 0.5f - half - 8f, 0f) + y, left, tint);
				spriteBatch.Draw(tex, new Vector2(centre.X + size.X * 0.5f + 8f, 0f) + y, right, tint);
			}

			// Bronze outline (the text stamped at 8 offsets), then the brass text on top.
			Vector2 origin = size / TitleScale * 0.5f;
			Vector2 scale = new(TitleScale);
			ChatManager.DrawColorCodedStringShadow(spriteBatch, font, text, centre, ShadowColor * opacity, 0f, origin, scale, -1f, 2.5f);
			ChatManager.DrawColorCodedString(spriteBatch, font, text, centre, TextColor * opacity, 0f, origin, scale);
			return true;
		}
	}
}
