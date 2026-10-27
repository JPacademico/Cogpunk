using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
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
	/// Boss title card: the boss's name stamped large across the lower middle of the screen, with a smaller line above it
	/// between two ember rules: the epithet when it arrives (<see cref="Show"/>), "Defeated" when it dies
	/// (<see cref="ShowDefeated"/>). The name lands with a short slam (it shrinks from <see cref="SlamScale"/> to
	/// full size during the fade-in), holds, then fades out.
	/// <para>Hostile colours (D3: Ember and Steam for hostile effects): ember name with an Ember 0 outline, steam-grey
	/// epithet. Client-local like <see cref="BiomeTitleSystem"/>: the boss decides when each client calls
	/// <see cref="Show"/> from its synced state, and nothing here is synced or runs on a dedicated server.</para>
	/// </summary>
	public sealed class BossTitleSystem : ModSystem
	{
		public const int FadeInTicks = 14;
		public const int FadeOutTicks = 36;
		public const float SlamScale = 1.6f;
		private const float NameScale = 1.25f;
		private const float EpithetScale = 0.9f;
		private const float CentreFraction = 0.7f;     // card centre, as a fraction of the screen height
		private const float RuleLength = 120f;
		private const float RuleGap = 14f;

		private static readonly Color NameColor = new(255, 199, 90);       // Ember 3
		private static readonly Color NameShadow = new(77, 20, 10);        // Ember 0
		private static readonly Color EpithetColor = new(195, 200, 205);   // Steam 1
		private static readonly Color EpithetShadow = new(21, 22, 28);     // Iron 0
		private static readonly Color RuleColor = new(163, 48, 26);        // Ember 1

		private static LocalizedText name;
		private static LocalizedText epithet;
		private static int timer = -1;
		private static int holdTicks;
		private static GameInterfaceLayer layer;

		public static bool IsShowing => timer >= 0;

		public override void Load() {
			if (!Main.dedServ) {
				layer = new LegacyGameInterfaceLayer("Cogpunk: Boss Title", DrawTitle, InterfaceScaleType.UI);
			}
		}

		public override void Unload() {
			layer = null;
			name = null;
			epithet = null;
		}

		public override void OnWorldUnload() {
			timer = -1;
		}

		/// <summary>Shows the card for <paramref name="hold"/> ticks after its fade-in. Local client only.</summary>
		public static void Show(LocalizedText bossName, LocalizedText bossEpithet, int hold) {
			if (Main.dedServ || bossName == null) {
				return;
			}
			name = bossName;
			epithet = bossEpithet;
			holdTicks = hold < 0 ? 0 : hold;
			timer = 0;
		}

		/// <summary>Key of the second line of every boss's defeat card.</summary>
		public const string DefeatedKey = "Mods.Cogpunk.UI.BossDefeated";

		/// <summary>The defeat card (user rule, 2026-10-26: every boss): the boss's name and "Defeated", nothing else.
		/// Local client only; <c>BossNPC</c> calls it during the death cinematic.</summary>
		public static void ShowDefeated(LocalizedText bossName, int hold) {
			Show(bossName, Language.GetText(DefeatedKey), hold);
		}

		public override void PostUpdateEverything() {
			if (timer >= 0 && ++timer >= FadeInTicks + holdTicks + FadeOutTicks) {
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
			if (timer < FadeInTicks + holdTicks) {
				return 1f;
			}
			return 1f - (timer - FadeInTicks - holdTicks) / (float)FadeOutTicks;
		}

		private static bool DrawTitle() {
			if (timer < 0 || name == null || Main.gameMenu) {
				return true;
			}
			float opacity = MathHelper.Clamp(Opacity(), 0f, 1f);
			float slam = timer < FadeInTicks ? MathHelper.Lerp(SlamScale, 1f, timer / (float)FadeInTicks) : 1f;
			SpriteBatch spriteBatch = Main.spriteBatch;
			Vector2 centre = new(Main.screenWidth / Main.UIScale * 0.5f, Main.screenHeight / Main.UIScale * CentreFraction);

			DynamicSpriteFont big = FontAssets.DeathText.Value;
			string nameText = name.Value;
			Vector2 nameSize = big.MeasureString(nameText);
			Vector2 nameScale = new(NameScale * slam);
			ChatManager.DrawColorCodedStringShadow(spriteBatch, big, nameText, centre, NameShadow * opacity, 0f, nameSize * 0.5f, nameScale, -1f, 3f);
			ChatManager.DrawColorCodedString(spriteBatch, big, nameText, centre, NameColor * opacity, 0f, nameSize * 0.5f, nameScale);

			if (epithet == null) {
				return true;
			}
			DynamicSpriteFont small = FontAssets.MouseText.Value;
			string epithetText = epithet.Value;
			Vector2 epithetSize = small.MeasureString(epithetText);
			Vector2 epithetAt = centre - new Vector2(0f, nameSize.Y * NameScale * 0.5f + epithetSize.Y * 0.3f);
			Vector2 epithetScale = new(EpithetScale);
			ChatManager.DrawColorCodedStringShadow(spriteBatch, small, epithetText, epithetAt, EpithetShadow * opacity, 0f, epithetSize * 0.5f, epithetScale, -1f, 1.5f);
			ChatManager.DrawColorCodedString(spriteBatch, small, epithetText, epithetAt, EpithetColor * opacity, 0f, epithetSize * 0.5f, epithetScale);

			// Two ember rules either side of the epithet (MagicPixel is vanilla's 1x1 white texture).
			float halfText = epithetSize.X * epithetScale.X * 0.5f;
			Texture2D pixel = TextureAssets.MagicPixel.Value;
			Color rule = RuleColor * opacity;
			int ruleY = (int)epithetAt.Y - 1;
			spriteBatch.Draw(pixel, new Rectangle((int)(epithetAt.X - halfText - RuleGap - RuleLength), ruleY, (int)RuleLength, 2), rule);
			spriteBatch.Draw(pixel, new Rectangle((int)(epithetAt.X + halfText + RuleGap), ruleY, (int)RuleLength, 2), rule);
			return true;
		}
	}
}
