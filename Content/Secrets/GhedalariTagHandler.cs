using Cogpunk.Core.Hooks;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using ReLogic.Graphics;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.UI.Chat;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// The Ghedalari script in text (2026-11-24: the Last Ghedalari "should talk in Ghedalari symbols"): the chat tag
	/// <c>[ghd:N]</c> draws word N's rune, <c>[ghd/p:N]</c> its pictogram, <c>[ghd/s:K]</c> stone K's sigil
	/// (<see cref="GhedalariScript"/>). Vanilla parses tags in NPC dialogue (decompiled 1.4.4 <c>Main.TextDisplayCache</c>:
	/// <c>Utils.WordwrapStringSmart</c> -> <c>ChatManager.ParseMessage</c>) and in mouse text, so his lines are written as tags.
	/// Hovering a rune whose meaning the player has learned (a stone translated: <see cref="GhedalariScript.Knows"/>) shows its
	/// pictogram; an unknown one shows only that it is Ghedalari. D0: a bad number draws nothing; a missing sheet draws nothing;
	/// registered on clients only, removed on unload (<see cref="ChatTagRegistry"/>).
	/// </summary>
	public sealed class GhedalariTagHandler : ITagHandler
	{
		public const string Tag = "ghd";

		public TextSnippet Parse(string text, Color baseColor = default, string options = null) {
			int.TryParse(text, out int index);
			GhedalariSnippet.Kind kind = options == "p" ? GhedalariSnippet.Kind.Pictogram
				: options == "s" ? GhedalariSnippet.Kind.Sigil : GhedalariSnippet.Kind.Rune;
			return new GhedalariSnippet(kind, index) { Text = "#", Color = baseColor, CheckForHover = kind == GhedalariSnippet.Kind.Rune };
		}
	}

	/// <summary>One glyph in a line of text: it reports its own width (so lines wrap round it) and draws itself.</summary>
	public sealed class GhedalariSnippet : TextSnippet
	{
		public enum Kind : byte { Rune, Pictogram, Sigil }

		private static Asset<Texture2D> glyphs, sigils;
		private readonly Kind kind;
		private readonly int index;

		public GhedalariSnippet(Kind kind, int index) {
			this.kind = kind;
			this.index = index;
		}

		public static void LoadAssets() {
			glyphs = DepthLayers.RequestOptional(GhedalariScript.Sheet);
			sigils = DepthLayers.RequestOptional("Cogpunk/Content/Secrets/FundamentalRunes");
		}

		public static void UnloadAssets() {
			glyphs = sigils = null;
		}

		private bool Valid => kind == Kind.Sigil ? index >= 0 && index < FundamentalStones.Count : index >= 0 && index < GhedalariScript.WordCount;

		private int Width => kind == Kind.Sigil ? GhedalariScript.SigilW : GhedalariScript.CellW;

		private int Height => kind == Kind.Sigil ? GhedalariScript.SigilH : GhedalariScript.CellH;

		/// <summary>Vanilla's wrap measures snippets with this (and splits their text: an empty piece draws nothing).</summary>
		public override float GetStringLength(DynamicSpriteFont font) => string.IsNullOrEmpty(Text) || !Valid ? 0f : (Width + 2) * Scale;

		/// <summary>Vanilla's wrap copies snippets with this: the copy keeps the glyph.</summary>
		public override TextSnippet CopyMorph(string newText) {
			return new GhedalariSnippet(kind, index) { Text = newText, Color = Color, Scale = Scale, CheckForHover = CheckForHover };
		}

		public override bool UniqueDraw(bool justCheckingString, out Vector2 size, SpriteBatch spriteBatch, Vector2 position = default,
			Color color = default, float scale = 1f) {
			if (string.IsNullOrEmpty(Text) || !Valid) {
				size = Vector2.Zero;
				return true;
			}
			size = new Vector2((Width + 2) * scale, Height * scale);
			if (justCheckingString || spriteBatch == null) {
				return true;
			}
			Asset<Texture2D> sheet = kind == Kind.Sigil ? sigils : glyphs;
			if (sheet?.IsLoaded != true) {
				return true;
			}
			Rectangle source = kind == Kind.Sigil
				? new Rectangle(index * GhedalariScript.SigilStride, 0, GhedalariScript.SigilW, GhedalariScript.SigilH)
				: new Rectangle(index * GhedalariScript.StrideX, kind == Kind.Pictogram ? GhedalariScript.StrideY : 0, GhedalariScript.CellW, GhedalariScript.CellH);
			if (source.Right > sheet.Value.Width || source.Bottom > sheet.Value.Height) {
				return true;
			}
			// the glyph sits on the text's line (text is drawn from its top; the glyph's foot on the baseline)
			Vector2 at = new(position.X, position.Y + (24f - Height) * 0.5f * scale);
			spriteBatch.Draw(sheet.Value, at, source, color, 0f, Vector2.Zero, scale, SpriteEffects.None, 0f);
			return true;
		}

		/// <summary>A learned word shows its picture; any other only says it is Ghedalari.</summary>
		public override void OnHover() {
			if (kind != Kind.Rune || !Valid || Main.dedServ) {
				return;
			}
			bool known = GhedalariScript.Knows(Main.LocalPlayer, (GhedalariScript.Word)index);
			Main.instance.MouseText(known
				? Language.GetTextValue("Mods.Cogpunk.Secrets.GhedalariKnown", "[" + GhedalariTagHandler.Tag + "/p:" + index + "]")
				: Language.GetTextValue("Mods.Cogpunk.Secrets.GhedalariUnknown"));
		}
	}

	/// <summary>Registers the tag on clients and takes it away again on unload; loads the glyph sheets.</summary>
	public sealed class GhedalariTagSystem : ModSystem
	{
		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			GhedalariSnippet.LoadAssets();
			ChatTagRegistry.Register<GhedalariTagHandler>(GhedalariTagHandler.Tag);
		}

		public override void Unload() {
			GhedalariSnippet.UnloadAssets();
			if (!Main.dedServ) {
				ChatTagRegistry.Unregister(GhedalariTagHandler.Tag);
			}
		}
	}
}
