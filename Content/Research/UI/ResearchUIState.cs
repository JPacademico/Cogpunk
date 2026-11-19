using System;
using System.Text;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.GameContent.UI.Elements;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.UI;
using Terraria.Utilities;

namespace Cogpunk.Content.Research.UI
{
	/// <summary>
	/// The research window (user, 2026-11-18, with a reference image: a dark starry field, square nodes with an item in each,
	/// curved arrows between some, a name shown on hover): a brass-framed panel over the screen, its title and the player's
	/// knowledge points along the top, a close button, and the tree under them (<see cref="ResearchTreeView"/>).
	/// </summary>
	public sealed class ResearchUIState : UIState
	{
		public const float WindowMaxWidth = 1080f, WindowMaxHeight = 700f, Header = 46f;

		private ResearchWindow window;
		private ResearchTreeView tree;

		public override void OnInitialize() {
			window = new ResearchWindow();
			window.Width.Set(0f, 0.84f);
			window.Height.Set(0f, 0.8f);
			window.MaxWidth.Set(WindowMaxWidth, 0f);
			window.MaxHeight.Set(WindowMaxHeight, 0f);
			window.MinWidth.Set(560f, 0f);
			window.MinHeight.Set(400f, 0f);
			window.HAlign = 0.5f;
			window.VAlign = 0.5f;
			Append(window);

			UIElement clip = new() { OverflowHidden = true };
			clip.Left.Set(10f, 0f);
			clip.Top.Set(Header, 0f);
			clip.Width.Set(-20f, 1f);
			clip.Height.Set(-Header - 10f, 1f);
			window.Append(clip);

			tree = new ResearchTreeView();
			tree.Width.Set(0f, 1f);
			tree.Height.Set(0f, 1f);
			clip.Append(tree);

			ResearchCloseButton close = new();
			close.Width.Set(28f, 0f);
			close.Height.Set(28f, 0f);
			close.Left.Set(-38f, 1f);
			close.Top.Set(10f, 0f);
			close.OnLeftClick += (_, _) => IngameFancyUI.Close();
			window.Append(close);
		}

		public override void OnActivate() {
			tree?.ResetView();
		}
	}

	/// <summary>The panel: a dark field in a brass frame (Cogpunk palette), the title and the knowledge count.</summary>
	public sealed class ResearchWindow : UIElement
	{
		private static readonly Color Rim = new(21, 22, 28), Brass = new(184, 138, 51), BrassLight = new(223, 185, 78), BrassDark = new(90, 58, 23);
		private static readonly Color Field = new(24, 20, 36), Steam = new(238, 241, 243), Jade = new(140, 201, 176);
		private int shownKnowledge = int.MinValue;
		private string knowledgeText = "";
		private static Asset<Texture2D> knowledgeIcon;                 // ResearchKnowledge.png: the knowledge point's sign

		public ResearchWindow() {
			if (!Main.dedServ && knowledgeIcon == null) {
				const string path = "Cogpunk/Content/Research/UI/ResearchKnowledge";
				knowledgeIcon = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
			}
		}

		protected override void DrawSelf(SpriteBatch sb) {
			if (IsMouseHovering) {
				Main.LocalPlayer.mouseInterface = true;
			}
			CalculatedStyle d = GetDimensions();
			Rectangle r = d.ToRectangle();
			Texture2D px = TextureAssets.MagicPixel.Value;
			sb.Draw(px, r, Rim);
			sb.Draw(px, new Rectangle(r.X + 2, r.Y + 2, r.Width - 4, r.Height - 4), BrassDark);
			sb.Draw(px, new Rectangle(r.X + 2, r.Y + 2, r.Width - 4, 2), BrassLight);
			sb.Draw(px, new Rectangle(r.X + 2, r.Y + 2, 2, r.Height - 4), BrassLight);
			sb.Draw(px, new Rectangle(r.X + 4, r.Y + 4, r.Width - 8, r.Height - 8), Brass);
			sb.Draw(px, new Rectangle(r.X + 8, r.Y + 8, r.Width - 16, r.Height - 16), Rim);
			sb.Draw(px, new Rectangle(r.X + 10, r.Y + 10, r.Width - 20, r.Height - 20), Field);

			string title = Language.GetTextValue("Mods.Cogpunk.Research.Title");
			Vector2 size = FontAssets.DeathText.Value.MeasureString(title) * 0.55f;
			Utils.DrawBorderStringBig(sb, title, new Vector2(MathF.Round(d.X + d.Width / 2f - size.X / 2f), d.Y + 12f), BrassLight, 0.55f);

			// the knowledge points: their sign and the number (user, 2026-11-18: "instead of "knowledge points:" add a stylized icon
			// so it lowers the text amount"); the words only if the art is missing; hovering the sign names it
			int k = Main.LocalPlayer.GetModPlayer<ResearchPlayer>().Knowledge;
			bool icon = knowledgeIcon?.IsLoaded == true;
			if (k != shownKnowledge) {
				shownKnowledge = k;
				knowledgeText = icon ? k.ToString() : Language.GetTextValue("Mods.Cogpunk.Research.Knowledge", k);   // only on change (D1)
			}
			if (icon) {
				Texture2D t = knowledgeIcon.Value;
				Rectangle at = new((int)d.X + 18, (int)d.Y + 12, t.Width, t.Height);
				sb.Draw(t, at, Color.White);
				Utils.DrawBorderStringBig(sb, knowledgeText, new Vector2(at.Right + 8f, d.Y + 12f), Jade, 0.5f);
				if (at.Contains(Main.MouseScreen.ToPoint())) {
					Main.instance.MouseText(Language.GetTextValue("Mods.Cogpunk.Research.KnowledgeName"));
				}
			}
			else {
				Utils.DrawBorderString(sb, knowledgeText, new Vector2(d.X + 20f, d.Y + 16f), Jade, 1f);
			}
		}
	}

	/// <summary>The close button: a brass square with an X (lit on hover).</summary>
	public sealed class ResearchCloseButton : UIElement
	{
		protected override void DrawSelf(SpriteBatch sb) {
			Rectangle r = GetDimensions().ToRectangle();
			Texture2D px = TextureAssets.MagicPixel.Value;
			bool hover = IsMouseHovering;
			sb.Draw(px, r, new Color(21, 22, 28));
			sb.Draw(px, new Rectangle(r.X + 2, r.Y + 2, r.Width - 4, r.Height - 4), hover ? new Color(184, 138, 51) : new Color(90, 58, 23));
			Utils.DrawBorderString(sb, "X", new Vector2(r.Center.X - 5f, r.Y + 4f), hover ? Color.White : new Color(223, 185, 78), 1f);
			if (hover) {
				Main.LocalPlayer.mouseInterface = true;
				Main.instance.MouseText(Language.GetTextValue("Mods.Cogpunk.Research.Close"));
			}
		}
	}

	/// <summary>
	/// The tree (user, 2026-11-18): every visible node (secret ones once revealed) as a square with its item's sprite, row 0 at
	/// the bottom ("from bottom-up order"); curved arrows only between the nodes a node <see cref="ResearchNode.Links"/> to;
	/// the starry field behind drifts a little as the view is dragged. Dragging (user, 2026-11-18: "add draggability on the menu
	/// so players can navigate it left right top and down when it expands in content"): hold the left button anywhere in the
	/// field, a node too, and move past <see cref="DragThreshold"/> px; the view follows the mouse, kept so some node stays in
	/// sight (<see cref="ClampPan"/>: the visible nodes' bounds), and the release doesn't count as a click. Hover: the node's name,
	/// what it does and what it needs (met in green, missing in red); left click: unlock it if it can be
	/// (<see cref="ResearchPlayer.TryUnlock"/>), with a chime and a flash, or a dull click if not.
	/// <para>Drawn by hand (no element per node): the node squares are laid out every frame into a preallocated array, the
	/// tooltip is rebuilt only when the hovered node or what the player has changes (D1).</para>
	/// </summary>
	public sealed class ResearchTreeView : UIElement
	{
		public const int NodeSize = 56;
		public const float SpacingX = 132f, SpacingY = 116f, BottomMargin = 64f;
		public const int Stars = 260;
		private const int StarField = 2048;
		public const float DragThreshold = 6f, PanMargin = 24f;

		private static Asset<Texture2D> frames;                  // ResearchNode.png: locked, available, researched (56 x 56, 2 apart)
		private static readonly Color LinkDim = new(127, 135, 148), LinkLit = new(223, 185, 78);

		private Vector2 pan;
		private bool pressing, moved;
		private Vector2 pressAt, pressPan;
		private Rectangle[] rects = Array.Empty<Rectangle>();
		private Item[] icons = Array.Empty<Item>();
		private int hovered = -1, tipFor = -2, tipStamp = -1;
		private string tip = "";
		private int flashNode = -1, flashTicks;
		private readonly StringBuilder builder = new(512);
		private static readonly int[] starX = new int[Stars], starY = new int[Stars];
		private static readonly byte[] starShade = new byte[Stars];

		static ResearchTreeView() {
			UnifiedRandom r = new(1118);
			for (int k = 0; k < Stars; k++) {
				starX[k] = r.Next(StarField);
				starY[k] = r.Next(StarField);
				starShade[k] = (byte)r.Next(4);
			}
		}

		public ResearchTreeView() {
			if (!Main.dedServ && frames == null) {
				const string path = "Cogpunk/Content/Research/UI/ResearchNode";
				frames = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
			}
		}

		public void ResetView() {
			pan = Vector2.Zero;
			pressing = false;
			moved = false;
			tipFor = -2;
		}

		private void Layout() {
			var nodes = ResearchNodes.All;
			if (rects.Length != nodes.Count) {
				rects = new Rectangle[nodes.Count];
				icons = new Item[nodes.Count];
				for (int k = 0; k < nodes.Count; k++) {
					icons[k] = new Item(nodes[k].IconItem);
				}
			}
			CalculatedStyle d = GetDimensions();
			float cx = d.X + d.Width / 2f + pan.X;
			float bottom = d.Y + d.Height - BottomMargin + pan.Y;
			for (int k = 0; k < nodes.Count; k++) {
				int x = (int)MathF.Round(cx + nodes[k].Column * SpacingX - NodeSize / 2f);
				int y = (int)MathF.Round(bottom - nodes[k].Row * SpacingY - NodeSize / 2f);
				rects[k] = new Rectangle(x, y, NodeSize, NodeSize);
			}
		}

		public override void Update(GameTime gameTime) {
			base.Update(gameTime);
			if (pressing) {
				if (!Main.mouseLeft) {
					pressing = false;                            // the release's click event ran before this (UserInterface.Update_Inner,
					moved = false;                               // then Update_End): LeftClick has already seen the drag
				}
				else {
					Vector2 delta = Main.MouseScreen - pressAt;
					if (!moved && delta.LengthSquared() > DragThreshold * DragThreshold) {
						moved = true;
					}
					if (moved) {
						pan = pressPan + delta;
						Main.LocalPlayer.mouseInterface = true;
					}
				}
			}
			ClampPan();
			if (flashTicks > 0) {
				flashTicks--;
			}
		}

		/// <summary>Keeps the visible nodes reachable: content narrower than the view stays inside it, wider content can be
		/// moved until its far edge reaches the view's (<see cref="PanMargin"/> px in).</summary>
		private void ClampPan() {
			var nodes = ResearchNodes.All;
			ResearchPlayer research = Main.LocalPlayer.GetModPlayer<ResearchPlayer>();
			int minC = 0, maxC = 0, minR = 0, maxR = 0;
			for (int k = 0; k < nodes.Count; k++) {
				if (!nodes[k].Teaser && !research.Visible(nodes[k])) {
					continue;
				}
				minC = Math.Min(minC, nodes[k].Column);
				maxC = Math.Max(maxC, nodes[k].Column);
				minR = Math.Min(minR, nodes[k].Row);
				maxR = Math.Max(maxR, nodes[k].Row);
			}
			CalculatedStyle d = GetDimensions();
			float half = NodeSize / 2f;
			float x0 = minC * SpacingX - half, x1 = maxC * SpacingX + half;              // from the view's centre line
			float yTop = d.Height - BottomMargin - maxR * SpacingY - half;                // from the view's top edge
			float yBottom = d.Height - BottomMargin - minR * SpacingY + half;
			float a = d.Width / 2f - PanMargin - x1, b = -d.Width / 2f + PanMargin - x0;
			float c = PanMargin - yTop, e = d.Height - PanMargin - yBottom;
			pan.X = MathHelper.Clamp(pan.X, Math.Min(a, b), Math.Max(a, b));
			pan.Y = MathHelper.Clamp(pan.Y, Math.Min(c, e), Math.Max(c, e));
		}

		public override void LeftMouseDown(UIMouseEvent evt) {
			base.LeftMouseDown(evt);
			pressing = true;
			moved = false;
			pressAt = Main.MouseScreen;
			pressPan = pan;
		}

		public override void LeftClick(UIMouseEvent evt) {
			base.LeftClick(evt);
			if (moved) {
				return;                                          // that was a drag, not a click
			}
			if (hovered < 0 || hovered >= ResearchNodes.All.Count) {
				return;
			}
			ResearchNode node = ResearchNodes.All[hovered];
			ResearchPlayer r = Main.LocalPlayer.GetModPlayer<ResearchPlayer>();
			if (r.TryUnlock(node)) {
				SoundEngine.PlaySound(SoundID.ResearchComplete);
				Main.NewText(Language.GetTextValue("Mods.Cogpunk.Research.Unlocked", node.DisplayName.Value), new Color(223, 185, 78));
				flashNode = hovered;
				flashTicks = 30;
				tipFor = -2;
			}
			else {
				SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = -0.6f });
			}
		}

		protected override void DrawSelf(SpriteBatch sb) {
			CalculatedStyle d = GetDimensions();
			Rectangle area = d.ToRectangle();
			Texture2D px = TextureAssets.MagicPixel.Value;
			if (IsMouseHovering) {
				Main.LocalPlayer.mouseInterface = true;
			}
			DrawStars(sb, px, area);
			Layout();
			Player player = Main.LocalPlayer;
			ResearchPlayer research = player.GetModPlayer<ResearchPlayer>();
			var nodes = ResearchNodes.All;

			// links first (under the nodes)
			for (int k = 0; k < nodes.Count; k++) {
				if (!research.Visible(nodes[k])) {
					continue;
				}
				foreach (string link in nodes[k].Links) {
					ResearchNode from = ResearchNodes.Get(link);
					if (from != null && from.Index < rects.Length && research.Visible(from)) {
						DrawLink(sb, px, rects[from.Index], rects[k], research.Has(from) ? LinkLit : LinkDim);
					}
				}
			}

			hovered = -1;
			Point mouse = Main.MouseScreen.ToPoint();
			for (int k = 0; k < nodes.Count; k++) {
				ResearchNode node = nodes[k];
				bool visible = research.Visible(node);
				if (!visible && !node.Teaser) {
					continue;
				}
				Rectangle r = rects[k];
				if (!area.Intersects(r)) {
					continue;
				}
				if (!visible) {                                  // a question mark until its boss falls (user, 2026-11-19)
					bool overTeaser = IsMouseHovering && r.Contains(mouse);
					if (overTeaser) {
						hovered = k;
					}
					DrawNode(sb, px, r, 0, overTeaser, 0);
					Utils.DrawBorderStringBig(sb, "?", r.Center.ToVector2() + new Vector2(0f, 4f), new Color(138, 144, 150), 0.8f, 0.5f, 0.5f);
					continue;
				}
				ResearchPlayer.Blocker why = research.Check(node);
				int state = why == ResearchPlayer.Blocker.Unlocked ? 2 : why == ResearchPlayer.Blocker.None ? 1 : 0;
				bool over = IsMouseHovering && r.Contains(mouse);
				if (over) {
					hovered = k;
				}
				DrawNode(sb, px, r, state, over, k == flashNode ? flashTicks : 0);
				Color tint = state == 0 ? new Color(120, 120, 130) : Color.White;
				ItemSlot.DrawItemIcon(icons[k], ItemSlot.Context.InventoryItem, sb, r.Center.ToVector2(), 1f, 32f, tint);
			}
			Utils.DrawBorderString(sb, Language.GetTextValue("Mods.Cogpunk.Research.DragHint"), new Vector2(area.X + 10f, area.Bottom - 26f),
				new Color(138, 144, 150), 0.8f);
			if (hovered >= 0 && !moved) {
				Main.instance.MouseText(Tooltip(nodes[hovered], research));
			}
		}

		private void DrawStars(SpriteBatch sb, Texture2D px, Rectangle area) {
			sb.Draw(px, area, new Color(18, 16, 30));
			float t = Main.GlobalTimeWrappedHourly;
			int ox = (int)(pan.X * 0.3f), oy = (int)(pan.Y * 0.3f);
			for (int k = 0; k < Stars; k++) {
				int x = area.X + Mod(starX[k] + ox, Math.Max(1, area.Width));
				int y = area.Y + Mod(starY[k] + oy, Math.Max(1, area.Height));
				int shade = starShade[k];
				bool twinkle = shade == 3 && MathF.Sin(t * 2.2f + k) > 0.6f;
				Color c = shade switch {
					0 => new Color(46, 50, 59),
					1 => new Color(70, 58, 147),
					2 => new Color(127, 135, 148),
					_ => twinkle ? new Color(238, 241, 243) : new Color(198, 189, 255),
				};
				int size = shade == 3 ? 4 : 2;
				if (x + size <= area.Right && y + size <= area.Bottom) {
					sb.Draw(px, new Rectangle(x, y, size, size), c);
				}
			}
		}

		private static int Mod(int a, int m) => ((a % m) + m) % m;

		/// <summary>A node's square: the generated frame for its state (or a drawn one if the art is missing), lit on hover,
		/// a flash as it is researched.</summary>
		private static void DrawNode(SpriteBatch sb, Texture2D px, Rectangle r, int state, bool over, int flash) {
			if (frames?.IsLoaded == true) {
				Rectangle src = new(0, state * (NodeSize + 2), NodeSize, NodeSize);
				if (src.Bottom <= frames.Value.Height) {
					sb.Draw(frames.Value, r, src, Color.White);
				}
			}
			else {
				Color rim = state == 2 ? new Color(223, 185, 78) : state == 1 ? new Color(140, 201, 176) : new Color(79, 85, 98);
				sb.Draw(px, r, new Color(21, 22, 28));
				sb.Draw(px, new Rectangle(r.X + 2, r.Y + 2, r.Width - 4, r.Height - 4), rim);
				sb.Draw(px, new Rectangle(r.X + 6, r.Y + 6, r.Width - 12, r.Height - 12), new Color(30, 28, 44));
			}
			if (over) {
				sb.Draw(px, new Rectangle(r.X, r.Y, r.Width, 2), Color.White);
				sb.Draw(px, new Rectangle(r.X, r.Bottom - 2, r.Width, 2), Color.White);
				sb.Draw(px, new Rectangle(r.X, r.Y, 2, r.Height), Color.White);
				sb.Draw(px, new Rectangle(r.Right - 2, r.Y, 2, r.Height), Color.White);
			}
			if (flash > 0) {
				sb.Draw(px, r, new Color(255, 250, 222) * (flash / 30f * 0.6f));
			}
		}

		/// <summary>A curved arrow from <paramref name="a"/> (below) to <paramref name="b"/>: a quadratic curve of 2 px dots and
		/// a head of dots at its end.</summary>
		private static void DrawLink(SpriteBatch sb, Texture2D px, Rectangle a, Rectangle b, Color c) {
			Vector2 p0 = new(a.Center.X, a.Top), p2 = new(b.Center.X, b.Bottom);
			Vector2 p1 = new((p0.X + p2.X) / 2f + (p2.Y - p0.Y) * 0.25f, (p0.Y + p2.Y) / 2f);
			const int steps = 40;
			Vector2 last = p0;
			for (int s = 0; s <= steps; s++) {
				float t = s / (float)steps;
				Vector2 q = (1 - t) * (1 - t) * p0 + 2 * (1 - t) * t * p1 + t * t * p2;
				sb.Draw(px, new Rectangle((int)q.X & ~1, (int)q.Y & ~1, 2, 2), c);
				if (s == steps - 2) {
					last = q;
				}
			}
			Vector2 dir = (p2 - last).SafeNormalize(Vector2.UnitY);
			Vector2 side = new(-dir.Y, dir.X);
			for (int k = 1; k <= 4; k++) {
				Vector2 q1 = p2 - dir * (k * 2f) + side * (k * 2f), q2 = p2 - dir * (k * 2f) - side * (k * 2f);
				sb.Draw(px, new Rectangle((int)q1.X & ~1, (int)q1.Y & ~1, 2, 2), c);
				sb.Draw(px, new Rectangle((int)q2.X & ~1, (int)q2.Y & ~1, 2, 2), c);
			}
		}

		/// <summary>The hover text (rebuilt when the node, the points or the inventory change, else every half second).</summary>
		private string Tooltip(ResearchNode node, ResearchPlayer r) {
			int stamp = (int)(Main.GameUpdateCount / 30);
			if (node.Index == tipFor && stamp == tipStamp) {
				return tip;
			}
			tipFor = node.Index;
			tipStamp = stamp;
			builder.Clear();
			if (node.Teaser && !r.Visible(node)) {
				builder.Append("[c/DFB94E:???]").Append('\n').Append("[c/8A909A:").Append(Language.GetTextValue("Mods.Cogpunk.Research.Teaser")).Append(']');
				return tip = builder.ToString();
			}
			builder.Append("[c/DFB94E:").Append(node.DisplayName.Value).Append(']').Append('\n');
			builder.Append(node.Description.Value).Append('\n');
			if (r.Has(node)) {
				builder.Append('\n').Append("[c/8CE458:").Append(Language.GetTextValue("Mods.Cogpunk.Research.Researched")).Append(']');
				return tip = builder.ToString();
			}
			builder.Append('\n');
			if (node.Cost > 0) {
				AddLine(Language.GetTextValue("Mods.Cogpunk.Research.Cost", node.Cost, r.Knowledge), r.Knowledge >= node.Cost);
			}
			foreach (string req in node.Requires) {
				ResearchNode need = ResearchNodes.Get(req);
				if (need != null) {
					AddLine(Language.GetTextValue("Mods.Cogpunk.Research.Requires", need.DisplayName.Value), r.Has(need));
				}
			}
			if (node.ConditionText != null) {
				bool met = node.Condition == null || node.Condition(Main.LocalPlayer);
				AddLine(node.ConditionText(Main.LocalPlayer), met);
			}
			foreach (ResearchItemCost cost in node.Items) {
				int have = r.CountItems(cost);
				AddLine(Language.GetTextValue("Mods.Cogpunk.Research.Takes", Language.GetTextValue("Mods.Cogpunk.Research.Costs." + cost.LabelKey, cost.Count), have),
					have >= cost.Count);
			}
			builder.Append('\n').Append(r.Check(node) == ResearchPlayer.Blocker.None
				? "[c/8CE458:" + Language.GetTextValue("Mods.Cogpunk.Research.ClickToResearch") + "]"
				: "[c/8A909A:" + Language.GetTextValue("Mods.Cogpunk.Research.NotYet") + "]");
			return tip = builder.ToString();
		}

		private void AddLine(string text, bool met) {
			builder.Append(met ? "[c/8CE458:" : "[c/EC7A58:").Append(text.Replace("]", "")).Append(']').Append('\n');
		}
	}
}
