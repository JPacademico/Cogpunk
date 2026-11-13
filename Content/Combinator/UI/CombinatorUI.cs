using System;
using Cogpunk.Content.Combinator.Combination;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using ReLogic.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.GameInput;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.UI;
using Terraria.UI.Chat;

namespace Cogpunk.Content.Combinator.UI
{
	/// <summary>
	/// The Combinator's window (user-set 2026-11-12): two slots, "base" and "augment", a "product" slot under them, a name box
	/// and a "?" in the corner that explains it all. Drawn and handled the way vanilla does its inventory and reforge slot (in
	/// the inventory layer, in UI scale; clicks read from <c>Main.mouseLeft</c>/<c>mouseLeftRelease</c>; hover tooltips through
	/// <c>ItemSlot.MouseHover</c>; item icons through <c>ItemSlot.DrawItemIcon</c>, which runs the combined look's draw hook).
	/// <list type="bullet">
	/// <item>A slot swaps with the mouse item when the mouse item is a weapon it takes (<see cref="CombinationRules.Check"/>;
	/// the product slot takes only combinations, to rename or take apart), or is empty (take it out). Shift-click sends a slot's
	/// item to the inventory. Nothing moves while the player is using an item (vanilla's own rule for slots).</item>
	/// <item><b>Combine</b> (both inputs, of one class, an empty product slot): the two weapons go in, the product comes out in
	/// the product slot. Until then the product slot shows a faint preview and the line under it the result's damage and use
	/// time, or what is wrong.</item>
	/// <item><b>Take apart</b> (a combination in the product slot, both inputs empty): the two weapons, as they went in, come back
	/// to their slots.</item>
	/// <item>The <b>name box</b> names the combination in the product slot (Enter or a click elsewhere keeps it, Escape drops
	/// it), vanilla's text input (<c>Main.GetInputText</c>, <c>PlayerInput.WritingText</c>, as its search bars do).</item>
	/// </list>
	/// Looks: the window, slots and buttons are pixel art in the Cogpunk palette (art/combinator/make_combinator_art.py); the
	/// pipes between the slots are palette-coloured rectangles on the 2 px grid. D1: the preview item is made only when the
	/// inputs change; text is measured, not allocated, except for the strings vanilla's font API needs.
	/// </summary>
	public static class CombinatorUI
	{
		public const int Width = 312, Height = 288;
		public const int SlotSize = 52, ProductSize = 60;

		private static Asset<Texture2D> panel, slot, productSlot, button, help;

		// colours from the Cogpunk palette (art/palettes/cogpunk.gpl)
		private static readonly Color Brass = new(223, 185, 78), BrassDark = new(138, 93, 34), BrassDeep = new(90, 58, 23);
		private static readonly Color Steam = new(238, 241, 243), SteamDim = new(195, 200, 205), Iron = new(46, 50, 59);
		private static readonly Color Error = new(236, 122, 88), Jade = new(140, 201, 176);

		private static Item preview;                        // the product the inputs would make
		private static int previewBase = -1, previewAugment = -1;
		private static CombinationRefusal refusal;

		private static bool naming;
		private static string nameText = "";
		private static Item namingItem;

		public static void Load() {
			const string dir = "Cogpunk/Content/Combinator/UI/";
			panel = Optional(dir + "CombinatorPanel");
			slot = Optional(dir + "CombinatorSlot");
			productSlot = Optional(dir + "CombinatorProductSlot");
			button = Optional(dir + "CombinatorButton");
			help = Optional(dir + "CombinatorHelp");
		}

		private static Asset<Texture2D> Optional(string path) {
			return ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
		}

		public static void Unload() {
			panel = slot = productSlot = button = help = null;
			preview = null;
			namingItem = null;
		}

		public static void OnOpen() {
			previewBase = previewAugment = -1;
			preview = null;
			naming = false;
		}

		public static void OnClose() {
			StopNaming(keep: true);
			preview = null;
		}

		public static Vector2 Origin => new(73f, Main.instance.invBottom + 10f);

		// --- drawing and input, once a frame in UI scale ----------------------------------------------------------------------

		public static void Draw(SpriteBatch sb) {
			Player player = Main.LocalPlayer;
			CombinatorPlayer slots = player.GetModPlayer<CombinatorPlayer>();
			Vector2 o = Origin;
			Rectangle area = new((int)o.X, (int)o.Y, Width, Height);
			bool overPanel = area.Contains(Main.mouseX, Main.mouseY);
			if (overPanel) {
				player.mouseInterface = true;
			}
			NineSlice(sb, panel, area, 16, Color.White, IronFill);
			DrawText(sb, Language.GetTextValue("Mods.Cogpunk.Combinator.Title"), new Vector2(o.X + Width / 2f, o.Y + 14f), Brass, 1f, centred: true);

			Rectangle baseRect = new((int)o.X + 44, (int)o.Y + 60, SlotSize, SlotSize);
			Rectangle augRect = new((int)o.X + Width - 44 - SlotSize, (int)o.Y + 60, SlotSize, SlotSize);
			Rectangle prodRect = new((int)o.X + Width / 2 - ProductSize / 2, (int)o.Y + 140, ProductSize, ProductSize);
			DrawText(sb, Language.GetTextValue("Mods.Cogpunk.Combinator.Base"), new Vector2(baseRect.Center.X, o.Y + 42f), SteamDim, 0.85f, centred: true);
			DrawText(sb, Language.GetTextValue("Mods.Cogpunk.Combinator.Augment"), new Vector2(augRect.Center.X, o.Y + 42f), SteamDim, 0.85f, centred: true);
			DrawText(sb, Language.GetTextValue("Mods.Cogpunk.Combinator.Product"), new Vector2(prodRect.X - 46f, prodRect.Center.Y - 8f), SteamDim, 0.85f, centred: true);
			Pipes(sb, baseRect, augRect, prodRect);

			UpdatePreview(slots);
			Slot(sb, ref slots.BaseSlot, baseRect, slot, SlotKind.Input, player);
			Slot(sb, ref slots.AugmentSlot, augRect, slot, SlotKind.Input, player);
			Slot(sb, ref slots.ProductSlot, prodRect, productSlot, SlotKind.Product, player);

			Status(sb, slots, new Vector2(o.X + Width / 2f, prodRect.Bottom + 10f));
			NameBox(sb, slots, new Rectangle((int)o.X + 20, (int)o.Y + 222, Width - 40, 24));
			bool canCombine = slots.ProductSlot.IsAir && refusal == CombinationRefusal.None && preview != null;
			bool canSeparate = CombinedWeapon.IsCombined(slots.ProductSlot) && slots.BaseSlot.IsAir && slots.AugmentSlot.IsAir;
			if (Button(sb, new Rectangle((int)o.X + 20, (int)o.Y + 254, 128, 24), Language.GetTextValue("Mods.Cogpunk.Combinator.Combine"), canCombine)) {
				Combine(slots);
			}
			if (Button(sb, new Rectangle((int)o.X + Width - 20 - 128, (int)o.Y + 254, 128, 24), Language.GetTextValue("Mods.Cogpunk.Combinator.Separate"), canSeparate)) {
				Separate(slots);
			}
			Help(sb, new Rectangle((int)o.X + Width - 34, (int)o.Y + 8, 22, 22));
			if (naming && Main.mouseLeft && Main.mouseLeftRelease && !nameBoxRect.Contains(Main.mouseX, Main.mouseY)) {
				StopNaming(keep: true);                         // a click anywhere else keeps the name
			}
		}

		private static void IronFill(SpriteBatch sb, Rectangle r) {
			sb.Draw(TextureAssets.MagicPixel.Value, r, Iron);
		}

		private enum SlotKind { Input, Product }

		private static void Slot(SpriteBatch sb, ref Item item, Rectangle rect, Asset<Texture2D> frame, SlotKind kind, Player player) {
			if (frame?.IsLoaded == true) {
				sb.Draw(frame.Value, rect, Color.White);
			}
			else {
				sb.Draw(TextureAssets.InventoryBack.Value, rect, Color.White);
			}
			bool hover = rect.Contains(Main.mouseX, Main.mouseY);
			Vector2 centre = rect.Center.ToVector2();
			if (!item.IsAir) {
				ItemSlot.DrawItemIcon(item, ItemSlot.Context.PrefixItem, sb, centre, 1f, 32f, Color.White);
			}
			else if (kind == SlotKind.Product && preview != null) {
				ItemSlot.DrawItemIcon(preview, ItemSlot.Context.PrefixItem, sb, centre, 1f, 32f, Color.White * 0.45f);
			}
			if (!hover) {
				return;
			}
			player.mouseInterface = true;
			if (Main.mouseLeft && Main.mouseLeftRelease && player.itemAnimation == 0 && player.itemTime == 0) {
				if (ItemSlot.ShiftInUse && !item.IsAir) {
					Item give = item;
					item = new Item();
					Core.Safety.SafeSpawn.TryGiveToLocalPlayer(player, give, "CombinatorSlot");
					previewBase = previewAugment = -1;
					SoundEngine.PlaySound(SoundID.Grab);
					Main.mouseLeftRelease = false;
				}
				else if (Accepts(kind, Main.mouseItem) && (!Main.mouseItem.IsAir || !item.IsAir)) {
					if (naming) {
						StopNaming(keep: true);
					}
					Utils.Swap(ref item, ref Main.mouseItem);
					SoundEngine.PlaySound(SoundID.Grab);
					Main.mouseLeftRelease = false;
					previewBase = previewAugment = -1;            // inputs changed: recompute
				}
			}
			if (!item.IsAir) {
				ItemSlot.MouseHover(ref item, ItemSlot.Context.PrefixItem);
			}
			else {
				string tip = Language.GetTextValue(kind == SlotKind.Product ? "Mods.Cogpunk.Combinator.ProductTip" : "Mods.Cogpunk.Combinator.InputTip");
				Main.instance.MouseText(tip);
			}
		}

		private static bool Accepts(SlotKind kind, Item mouse) {
			if (mouse == null || mouse.IsAir) {
				return true;                                  // taking out
			}
			if (mouse.favorited) {
				return false;
			}
			return kind == SlotKind.Product ? CombinedWeapon.IsCombined(mouse) : CombinationRules.Check(mouse) == CombinationRefusal.None;
		}

		private static void UpdatePreview(CombinatorPlayer slots) {
			int b = slots.BaseSlot.IsAir ? 0 : slots.BaseSlot.type, a = slots.AugmentSlot.IsAir ? 0 : slots.AugmentSlot.type;
			if (b == previewBase && a == previewAugment) {
				return;
			}
			previewBase = b;
			previewAugment = a;
			preview = null;
			refusal = CombinationRefusal.Empty;
			if (b == 0 || a == 0) {
				return;
			}
			refusal = CombinationRules.CanCombine(slots.BaseSlot, slots.AugmentSlot);
			if (refusal == CombinationRefusal.None) {
				preview = CombinationRules.Combine(slots.BaseSlot, slots.AugmentSlot);
			}
		}

		private static void Status(SpriteBatch sb, CombinatorPlayer slots, Vector2 at) {
			string text;
			Color colour = SteamDim;
			if (CombinedWeapon.TryGet(slots.ProductSlot, out CombinedWeapon made) && made.IsProduct) {
				text = Language.GetTextValue("Mods.Cogpunk.Combinator.StatusProduct");
				colour = Jade;
			}
			else if (!slots.ProductSlot.IsAir) {
				text = "";
			}
			else if (preview != null) {
				int useTime = preview.useAnimation;
				text = Language.GetTextValue("Mods.Cogpunk.Combinator.StatusReady", preview.damage, useTime);
				colour = Brass;
			}
			else if (refusal != CombinationRefusal.Empty && refusal != CombinationRefusal.None) {
				text = Language.GetTextValue("Mods.Cogpunk.Combinator.Refusal." + refusal);
				colour = Error;
			}
			else {
				text = Language.GetTextValue("Mods.Cogpunk.Combinator.StatusEmpty");
			}
			if (text.Length > 0) {
				DrawText(sb, text, at, colour, 0.8f, centred: true);
			}
		}

		private static Rectangle nameBoxRect;

		private static void NameBox(SpriteBatch sb, CombinatorPlayer slots, Rectangle rect) {
			nameBoxRect = rect;
			bool enabled = CombinedWeapon.TryGet(slots.ProductSlot, out CombinedWeapon data) && data.IsProduct;
			if (naming && (!enabled || !ReferenceEquals(namingItem, slots.ProductSlot))) {
				StopNaming(keep: false);
			}
			sb.Draw(TextureAssets.MagicPixel.Value, rect, BrassDeep);
			sb.Draw(TextureAssets.MagicPixel.Value, new Rectangle(rect.X + 2, rect.Y + 2, rect.Width - 4, rect.Height - 4), naming ? Iron : new Color(21, 22, 28));
			string label = Language.GetTextValue("Mods.Cogpunk.Combinator.Name");
			DrawText(sb, label, new Vector2(rect.X + 8f, rect.Y + 4f), enabled ? Brass : BrassDark, 0.8f, centred: false);
			float labelW = FontAssets.MouseText.Value.MeasureString(label).X * 0.8f + 14f;
			Vector2 textAt = new(rect.X + 8f + labelW, rect.Y + 4f);
			if (!enabled) {
				return;
			}
			bool hover = rect.Contains(Main.mouseX, Main.mouseY);
			if (hover) {
				Main.LocalPlayer.mouseInterface = true;
				if (!naming && Main.mouseLeft && Main.mouseLeftRelease) {
					naming = true;
					namingItem = slots.ProductSlot;
					nameText = data.CustomName;
					Main.mouseLeftRelease = false;
					SoundEngine.PlaySound(SoundID.MenuTick);
				}
			}
			if (naming) {
				PlayerInput.WritingText = true;
				Main.CurrentInputTextTakerOverride = namingItem;
				Main.instance.HandleIME();
				string typed = Main.GetInputText(nameText);
				if (typed.Length > CombinationRules.MaxNameLength) {
					typed = typed[..CombinationRules.MaxNameLength];
				}
				nameText = typed;
				if (Main.inputTextEnter) {
					StopNaming(keep: true);
				}
				else if (Main.inputTextEscape) {
					StopNaming(keep: false);
				}
				bool caret = Main.GameUpdateCount / 20 % 2 == 0;
				DrawText(sb, nameText + (caret ? "|" : ""), textAt, Steam, 0.8f, centred: false);
				return;
			}
			string shown = data.CustomName.Length > 0 ? data.CustomName : CombinationRules.DefaultName(slots.ProductSlot.type, data.Base.type);
			DrawText(sb, shown, textAt, data.CustomName.Length > 0 ? Steam : SteamDim, 0.8f, centred: false);
		}

		private static void StopNaming(bool keep) {
			if (!naming) {
				return;
			}
			naming = false;
			if (keep && namingItem != null && CombinedWeapon.TryGet(namingItem, out CombinedWeapon data) && data.IsProduct) {
				data.Rename(namingItem, nameText);
			}
			namingItem = null;
		}

		private static bool Button(SpriteBatch sb, Rectangle rect, string label, bool enabled) {
			bool hover = enabled && rect.Contains(Main.mouseX, Main.mouseY);
			if (rect.Contains(Main.mouseX, Main.mouseY)) {
				Main.LocalPlayer.mouseInterface = true;
			}
			if (button?.IsLoaded == true) {
				Texture2D t = button.Value;
				int fh = t.Height / 2;
				Rectangle src = new(0, hover ? fh : 0, t.Width, fh);
				NineSliceFrom(sb, t, src, rect, 8, enabled ? Color.White : new Color(120, 120, 120));
			}
			else {
				sb.Draw(TextureAssets.MagicPixel.Value, rect, hover ? Brass : BrassDark);
			}
			DrawText(sb, label, rect.Center.ToVector2() - new Vector2(0f, 9f), enabled ? (hover ? Steam : Brass) : BrassDark, 0.85f, centred: true);
			if (hover && Main.mouseLeft && Main.mouseLeftRelease) {
				Main.mouseLeftRelease = false;
				return true;
			}
			return false;
		}

		private static void Help(SpriteBatch sb, Rectangle rect) {
			bool hover = rect.Contains(Main.mouseX, Main.mouseY);
			if (help?.IsLoaded == true) {
				Texture2D t = help.Value;
				int fh = t.Height / 2;
				sb.Draw(t, rect, new Rectangle(0, hover ? fh : 0, t.Width, fh), Color.White);
			}
			else {
				DrawText(sb, "?", rect.Center.ToVector2() - new Vector2(0f, 10f), hover ? Steam : Brass, 1f, centred: true);
			}
			if (hover) {
				Main.LocalPlayer.mouseInterface = true;
				Main.instance.MouseText(Language.GetTextValue("Mods.Cogpunk.Combinator.Help"));
			}
		}

		private static void Combine(CombinatorPlayer slots) {
			Item product = CombinationRules.Combine(slots.BaseSlot, slots.AugmentSlot);
			if (product == null) {
				SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = -0.6f });
				return;
			}
			slots.BaseSlot = new Item();
			slots.AugmentSlot = new Item();
			slots.ProductSlot = product;
			previewBase = previewAugment = -1;
			SoundEngine.PlaySound(SoundID.Item37);                 // vanilla's reforge chime
			SoundEngine.PlaySound(SoundID.Item13 with { Pitch = -0.3f, Volume = 0.7f });   // a hiss of steam
		}

		private static void Separate(CombinatorPlayer slots) {
			if (!CombinationRules.Separate(slots.ProductSlot, out Item b, out Item a)) {
				SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = -0.6f });
				return;
			}
			StopNaming(keep: false);
			slots.BaseSlot = b;
			slots.AugmentSlot = a;
			slots.ProductSlot = new Item();
			previewBase = previewAugment = -1;
			SoundEngine.PlaySound(SoundID.Item53 with { Pitch = -0.2f });
		}

		// --- small drawing helpers --------------------------------------------------------------------------------------------

		/// <summary>The brass pipes from both inputs into the product (2 px steps, palette colours, a dark rim).</summary>
		private static void Pipes(SpriteBatch sb, Rectangle a, Rectangle b, Rectangle p) {
			int joinY = (a.Bottom + p.Top) / 2 & ~1;
			int midX = p.Center.X & ~1;
			Pipe(sb, new Rectangle((a.Center.X & ~1) - 4, a.Bottom, 8, joinY - a.Bottom + 4));
			Pipe(sb, new Rectangle((b.Center.X & ~1) - 4, b.Bottom, 8, joinY - b.Bottom + 4));
			Pipe(sb, new Rectangle((a.Center.X & ~1) - 4, joinY - 4, (b.Center.X & ~1) - (a.Center.X & ~1) + 8, 8));
			Pipe(sb, new Rectangle(midX - 4, joinY - 4, 8, p.Top - joinY + 6));
		}

		private static void Pipe(SpriteBatch sb, Rectangle r) {
			sb.Draw(TextureAssets.MagicPixel.Value, r, BrassDeep);
			sb.Draw(TextureAssets.MagicPixel.Value, new Rectangle(r.X + 2, r.Y + 2, r.Width - 4, r.Height - 4), BrassDark);
			if (r.Width > r.Height) {
				sb.Draw(TextureAssets.MagicPixel.Value, new Rectangle(r.X + 2, r.Y + 2, r.Width - 4, 2), Brass);
			}
			else {
				sb.Draw(TextureAssets.MagicPixel.Value, new Rectangle(r.X + 2, r.Y + 2, 2, r.Height - 4), Brass);
			}
		}

		private static void DrawText(SpriteBatch sb, string text, Vector2 at, Color colour, float scale, bool centred) {
			if (string.IsNullOrEmpty(text)) {
				return;
			}
			DynamicSpriteFont font = FontAssets.MouseText.Value;
			Vector2 size = font.MeasureString(text) * scale;
			Vector2 pos = centred ? at - new Vector2(size.X / 2f, 0f) : at;
			ChatManager.DrawColorCodedStringWithShadow(sb, font, text, new Vector2(MathF.Round(pos.X), MathF.Round(pos.Y)), colour, 0f, Vector2.Zero, new Vector2(scale));
		}

		private static void NineSlice(SpriteBatch sb, Asset<Texture2D> asset, Rectangle dest, int corner, Color colour, Action<SpriteBatch, Rectangle> fallback) {
			if (asset?.IsLoaded != true) {
				fallback(sb, dest);
				return;
			}
			NineSliceFrom(sb, asset.Value, asset.Value.Bounds, dest, corner, colour);
		}

		/// <summary>A nine-slice: the corners at their size, the edges and middle stretched (the art keeps them plain along
		/// their length, so stretching makes no smears).</summary>
		private static void NineSliceFrom(SpriteBatch sb, Texture2D t, Rectangle src, Rectangle dest, int c, Color colour) {
			int sw = src.Width, sh = src.Height;
			Span<int> sx = stackalloc int[] { src.X, src.X + c, src.X + sw - c, src.X + sw };   // no heap allocation (D1)
			Span<int> sy = stackalloc int[] { src.Y, src.Y + c, src.Y + sh - c, src.Y + sh };
			Span<int> dx = stackalloc int[] { dest.X, dest.X + c, dest.Right - c, dest.Right };
			Span<int> dy = stackalloc int[] { dest.Y, dest.Y + c, dest.Bottom - c, dest.Bottom };
			for (int j = 0; j < 3; j++) {
				for (int i = 0; i < 3; i++) {
					Rectangle s = new(sx[i], sy[j], sx[i + 1] - sx[i], sy[j + 1] - sy[j]);
					Rectangle d = new(dx[i], dy[j], dx[i + 1] - dx[i], dy[j + 1] - dy[j]);
					if (s.Width > 0 && s.Height > 0 && d.Width > 0 && d.Height > 0) {
						sb.Draw(t, d, s, colour);
					}
				}
			}
		}
	}
}
