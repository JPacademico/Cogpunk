using System;
using System.Collections.Generic;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.UI;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// Reading a <see cref="FundamentalStoneTile"/> (user, 2026-11-10: "these stones can be read with the right mouse click";
	/// 2026-11-24: the runes are the Ghedalari script, <see cref="GhedalariScript"/>): a dark panel opens over the stone and
	/// its words (<see cref="GhedalariScript.Inscriptions"/>) light up one after another (<see cref="RevealTicks"/> apart); it
	/// stays <see cref="HoldTicks"/> ticks, or until the reader walks more than <see cref="CloseRange"/> from the stone, reads
	/// another, or right-clicks it again, then fades.
	/// <para><b>Translated</b> (user, 2026-11-24: "after unlocking the node and interacting with the stone again the symbols
	/// show are translated not to actual words but to more comprehensible symbols"): to a reader who has researched the
	/// stone's sigil in the Mystery of the Past (<see cref="GhedalariScript.Translated"/>) the words show as pictograms, else
	/// as runes, pale blue like the cuts in the slate. The tar pit's says only "..." (user).</para>
	/// <para>The game's fonts can't draw runes, so the glyphs are pixel art (<c>GhedalariGlyphs.png</c>: runes on its first
	/// row, pictograms on its second). Drawn in world space (<see cref="InterfaceScaleType.Game"/>) just before vanilla's mouse
	/// text.</para>
	/// <para>D2: local to the reader (nothing is sent). D1: one cached layer, at most a line of glyph draws a frame, no
	/// allocation; the layer list is searched with a static lambda; whether the reader can translate is looked up when the
	/// stone is read, not every frame. D0: the texture is never touched on a dedicated server; a missing texture draws
	/// nothing; the style and every word are clamped.</para>
	/// </summary>
	public sealed class FundamentalStoneReading : ModSystem
	{
		public const int RevealTicks = 5, HoldTicks = 600, FadeInTicks = 12, FadeOutTicks = 30;
		public const float CloseRange = 16f * 16f;
		private const int GlyphGap = 4, Padding = 12, Lift = 10;

		private static Asset<Texture2D> glyphs;
		private static LegacyGameInterfaceLayer layer;
		private static int style = -1, age, closing;
		private static bool translated;
		private static Vector2 anchor;

		public override void Load() {
			glyphs = DepthLayers.RequestOptional(GhedalariScript.Sheet);
			layer = new LegacyGameInterfaceLayer("Cogpunk: Fundamental Stone", Draw, InterfaceScaleType.Game);
		}

		public override void Unload() {
			glyphs = null;
			layer = null;
			style = -1;
		}

		public override void ClearWorld() {
			style = -1;
			FundamentalStoneTile.ResetShields();
		}

		/// <summary>The reader's client: show <paramref name="stone"/>'s runes over <paramref name="topCentre"/> (world px);
		/// the same stone read again closes them.</summary>
		public static void Open(int stone, Vector2 topCentre) {
			if (Main.dedServ) {
				return;
			}
			if (style == stone && closing == 0 && Vector2.DistanceSquared(anchor, topCentre) < 4f) {
				closing = 1;                                       // read again: fade out
				return;
			}
			style = Math.Clamp(stone, 0, FundamentalStones.Count - 1);
			translated = GhedalariScript.Translated(Main.LocalPlayer, style);
			// research (user, 2026-11-18): "reading a fundamental stone for the first time should give a knowledge point (individual,
			// and one per stone)"
			Main.LocalPlayer.GetModPlayer<Content.Research.ResearchPlayer>().Grant(Content.Research.KnowledgeTasks.Stone(style));
			anchor = topCentre;
			age = 0;
			closing = 0;
			SoundEngine.PlaySound(SoundID.Item4 with { Pitch = -0.45f, Volume = 0.55f }, topCentre);
			if (CogpunkClientConfig.RollEffect()) {
				for (int k = 0; k < 10; k++) {
					if (SafeSpawn.TryNewDust(topCentre + new Vector2(-28f, 8f), 56, 72, DustID.GemSapphire, out Dust d)) {
						d.noGravity = true;
						d.velocity = new Vector2(0f, -Main.rand.NextFloat(0.6f, 1.6f));
						d.scale = 0.9f;
					}
				}
			}
		}

		public override void PostUpdateEverything() {
			if (style < 0 || Main.dedServ) {
				return;
			}
			age++;
			Player reader = Main.LocalPlayer;
			if (closing == 0 && (age >= HoldTicks || !reader.active || reader.dead || Vector2.DistanceSquared(reader.Center, anchor) > CloseRange * CloseRange)) {
				closing = 1;
			}
			if (closing > 0 && ++closing > FadeOutTicks) {
				style = -1;
			}
		}

		public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers) {
			if (layer == null) {
				return;
			}
			int index = layers.FindIndex(static l => l.Name == "Vanilla: Mouse Text");
			layers.Insert(index < 0 ? layers.Count : index, layer);
		}

		private static bool Draw() {
			if (style < 0 || glyphs?.IsLoaded != true || style >= GhedalariScript.Inscriptions.Length) {
				return true;
			}
			GhedalariScript.Word[] line = GhedalariScript.Inscriptions[style];
			float alpha = Math.Min(1f, age / (float)FadeInTicks) * (closing > 0 ? 1f - closing / (float)FadeOutTicks : 1f);
			if (alpha <= 0f) {
				return true;
			}
			int width = line.Length * GhedalariScript.CellW + (line.Length - 1) * GlyphGap + Padding * 2;
			int height = GhedalariScript.CellH + Padding * 2;
			Vector2 centre = anchor - Main.screenPosition;
			Rectangle panel = new((int)(centre.X - width / 2f), (int)(centre.Y - Lift - height), width, height);
			SpriteBatch sb = Main.spriteBatch;
			Utils.DrawInvBG(sb, panel, new Color(14, 20, 46) * (0.9f * alpha));
			Texture2D sheet = glyphs.Value;
			int row = translated ? GhedalariScript.StrideY : 0;    // the pictograms' row, or the runes'
			for (int k = 0; k < line.Length; k++) {
				float shown = (age - FadeInTicks / 2 - k * RevealTicks) / (float)RevealTicks;
				if (shown <= 0f) {
					break;                                         // the next words aren't lit yet
				}
				int word = Math.Clamp((int)line[k], 0, GhedalariScript.WordCount - 1);
				Rectangle source = new(word * GhedalariScript.StrideX, row, GhedalariScript.CellW, GhedalariScript.CellH);
				if (source.Right > sheet.Width || source.Bottom > sheet.Height) {
					continue;
				}
				Vector2 at = new(panel.X + Padding + k * (GhedalariScript.CellW + GlyphGap), panel.Y + Padding);
				float breath = translated ? 1f : FundamentalStoneTile.Breath(style);   // runes breathe with the stone
				sb.Draw(sheet, at, source, Color.White * (alpha * Math.Min(1f, shown) * breath));
			}
			return true;
		}
	}
}
