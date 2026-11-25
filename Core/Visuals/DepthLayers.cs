using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Visuals
{
	/// <summary>
	/// Multiplane drawing for layered sprites (art direction 2026-10-26): bosses, minibosses and other important sprites are
	/// split into up to three layers, <see cref="Far"/>, <see cref="Middle"/> and <see cref="Near"/> (e.g. the far arm, the
	/// torso, the near arm), each animated on its own and shifted by a small parallax so the parts read as standing at
	/// different depths.
	/// <para><b>Parallax</b> follows vanilla's background scrolling (decompiled <c>Main.DrawSurfaceBG</c>: a background
	/// layer is placed at <c>-screenPosition.X * bgParallax</c>, so a factor below 1 moves slower than the world). For a
	/// layer at depth factor <c>p = 1 + k * depth</c> attached to an object, that is an offset of
	/// <c>(anchor - screen centre) * (p - 1)</c>: nothing at the centre of the view, growing towards the edges, opposite
	/// for the far and near layers, so the parts slide against each other as the camera pans. It is clamped to
	/// <c>maxShift</c> and snapped to the 2 px art grid (D4: whole art pixels only, no mixels).</para>
	/// <para><b>Optimized:</b> every layer is a pre-rendered frame from a generator (no runtime rotation or scaling) drawn
	/// with the current SpriteBatch state: no Begin/End, no allocation (D1), the same cost as vanilla's multi-part bosses
	/// (Skeletron's and Prime's limbs are extra textures drawn from <c>Main.DrawNPCDirect</c> in the same pass).</para>
	/// </summary>
	public static class DepthLayers
	{
		public const float Far = -1f;
		public const float Middle = 0f;
		public const float Near = 1f;

		/// <summary>Rows below a layer's origin that are still drawn: one art pixel (2 px), so planted hands bite into the
		/// ground instead of hovering on it.</summary>
		public const int GroundOverlap = 2;

		/// <summary>Screen-pixel offset for a layer at <paramref name="depth"/> (-1 far .. +1 near) of an object drawn at
		/// <paramref name="screenAnchor"/>; at most <paramref name="maxShift"/> px horizontally (half that vertically).</summary>
		public static Vector2 Shift(Vector2 screenAnchor, float depth, float maxShift) {
			if (depth == 0f || maxShift <= 0f || Main.screenWidth <= 0 || Main.screenHeight <= 0) {
				return Vector2.Zero;
			}
			float halfW = Main.screenWidth * 0.5f;
			float halfH = Main.screenHeight * 0.5f;
			float dx = MathHelper.Clamp((screenAnchor.X - halfW) / halfW, -1.5f, 1.5f);
			float dy = MathHelper.Clamp((screenAnchor.Y - halfH) / halfH, -1.5f, 1.5f);
			float limit = maxShift * 1.5f;
			return new Vector2(Snap(MathHelper.Clamp(dx * maxShift * depth, -limit, limit)),
				Snap(MathHelper.Clamp(dy * maxShift * 0.5f * depth, -limit, limit)));
		}

		/// <summary>Rounds to the 2 px grid of 2x art.</summary>
		public static float Snap(float value) => MathF.Round(value * 0.5f) * 2f;

		/// <summary>Light for a layer: the far layer is a little darker (aerial depth; its art is already baked one ramp
		/// step darker), the middle and near layers keep the light as it is.</summary>
		public static Color Tint(Color light, float depth) {
			if (depth >= 0f) {
				return light;
			}
			float k = 1f + 0.12f * depth;
			return new Color((byte)(light.R * k), (byte)(light.G * k), (byte)(light.B * k), light.A);
		}

		/// <summary>Values per frame in a packed frame table (<see cref="DrawFrame"/>): page, x, y, width, height, origin x, origin y.</summary>
		public const int FrameFields = 7;

		/// <summary>
		/// Draws frame <paramref name="frame"/> of a packed atlas: every frame cropped to its own pixels and packed onto one of
		/// several <paramref name="pages"/> by the art generator, described by <paramref name="table"/>
		/// (<see cref="FrameFields"/> values per frame: page, the rectangle on it, and the rig origin inside that rectangle).
		/// Placement and clipping are the same as <see cref="DrawCell"/>: the origin lands on <paramref name="anchor"/>, nothing
		/// is drawn more than <see cref="GroundOverlap"/> below it, <paramref name="buried"/> px more are cut off while the sprite
		/// sinks, and it mirrors around the origin when <paramref name="flip"/>. D0: an unknown frame, a missing or unloaded
		/// page, or a rectangle outside its texture draws nothing.
		/// </summary>
		public static void DrawFrame(SpriteBatch spriteBatch, Asset<Texture2D>[] pages, short[] table, int frame, Vector2 anchor,
			int buried, Color color, bool flip, float scale = 1f) {
			int i = frame * FrameFields;
			if (pages == null || table == null || frame < 0 || i + FrameFields > table.Length) {
				return;
			}
			int page = table[i], width = table[i + 3], height = table[i + 4], originX = table[i + 5], originY = table[i + 6];
			if (page < 0 || page >= pages.Length || width <= 0 || height <= 0 || pages[page]?.IsLoaded != true) {
				return;
			}
			int visible = Math.Min(height, originY + GroundOverlap - buried);
			if (visible <= 0) {
				return;
			}
			Texture2D texture = pages[page].Value;
			Rectangle source = new(table[i + 1], table[i + 2], width, visible);
			if (source.Right > texture.Width || source.Bottom > texture.Height) {
				return;
			}
			float left = flip ? anchor.X - (width - originX) * scale : anchor.X - originX * scale;
			Vector2 position = new(left, anchor.Y + (buried - originY) * scale);
			if (scale != 1f) {
				position = new Vector2(MathF.Round(position.X), MathF.Round(position.Y));   // a scaled sprite (Tar Tyrant shrinking) on whole pixels
			}
			spriteBatch.Draw(texture, position, source, color, 0f, Vector2.Zero, scale,
				flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None, 0f);
		}

		/// <summary>A layer's atlas pages (<c>Name</c>, <c>Name_Page1</c>, ...), requested once; a missing page stays null and
		/// its frames are simply not drawn (D0). Clients only: returns null on a dedicated server.</summary>
		public static Asset<Texture2D>[] RequestPages(string path, int count) {
			if (Main.dedServ || count <= 0) {
				return null;
			}
			var pages = new Asset<Texture2D>[count];
			for (int k = 0; k < count; k++) {
				string name = k == 0 ? path : path + "_Page" + k;
				pages[k] = ModContent.HasAsset(name) ? ModContent.Request<Texture2D>(name) : null;
			}
			return pages;
		}

		/// <summary>A texture if it exists, requested once; null on a dedicated server or when the file is missing (D0).</summary>
		public static Asset<Texture2D> RequestOptional(string path) {
			return !Main.dedServ && ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
		}

		/// <summary>
		/// A small layered walker: the same <paramref name="frame"/> of its far, middle and near grid sheets (vertical, equal
		/// cells, <paramref name="padding"/> px under each), far to near, with the far plane a little darker. The parallax is
		/// horizontal only (at most <paramref name="maxShift"/> px): a walker's feet stay on the ground line. A null sheet
		/// is skipped. <paramref name="maxShift"/> 0 (the bestiary) draws the planes stacked. A sheet too tall for one column
		/// (the 2048 px texture limit) wraps into <paramref name="columns"/>, left to right, then down (the Jade Golem, 2026-11-06).
		/// <paramref name="buried"/> px are cut off the bottom of every plane (sinking into the ground: the Crystal Lizard digging
		/// away, 2026-11-25).
		/// </summary>
		public static void DrawWalker(SpriteBatch spriteBatch, Texture2D far, Texture2D middle, Texture2D near, int frame, int cellWidth,
			int cellHeight, int padding, int originX, int originY, Vector2 anchor, Color light, bool flip, float maxShift, float scale = 1f,
			int columns = 1, int buried = 0) {
			Vector2 farShift = new(Shift(anchor, Far, maxShift).X, 0f);
			Vector2 nearShift = new(Shift(anchor, Near, maxShift).X, 0f);
			if (far != null) {
				DrawCell(spriteBatch, far, frame, columns, cellWidth, cellHeight, padding, originX, originY, anchor + farShift, buried, Tint(light, Far), flip, scale);
			}
			if (middle != null) {
				DrawCell(spriteBatch, middle, frame, columns, cellWidth, cellHeight, padding, originX, originY, anchor, buried, light, flip, scale);
			}
			if (near != null) {
				DrawCell(spriteBatch, near, frame, columns, cellWidth, cellHeight, padding, originX, originY, anchor + nearShift, buried, light, flip, scale);
			}
		}

		/// <summary>
		/// Draws one cell of a grid sheet (equal cells, <paramref name="padding"/> px between them) so that the cell's rig
		/// origin (<paramref name="originX"/>, <paramref name="originY"/>) lands on <paramref name="anchor"/>; rows below the
		/// origin are never drawn past <see cref="GroundOverlap"/> (the ground line: planted parts sink one art pixel into
		/// the ground and no further), and <paramref name="buried"/> px more are cut off the bottom while the sprite sinks
		/// below it (emerging / burrowing). Mirrors around the origin when <paramref name="flip"/>.
		/// </summary>
		public static void DrawCell(SpriteBatch spriteBatch, Texture2D texture, int frame, int columns, int cellWidth, int cellHeight,
			int padding, int originX, int originY, Vector2 anchor, int buried, Color color, bool flip, float scale = 1f) {
			if (texture == null || columns <= 0 || frame < 0) {
				return;
			}
			int visible = Math.Min(cellHeight, originY + GroundOverlap - buried);
			if (visible <= 0) {
				return;
			}
			int col = frame % columns;
			int row = frame / columns;
			Rectangle source = new(col * (cellWidth + padding), row * (cellHeight + padding), cellWidth, visible);
			if (source.Right > texture.Width || source.Bottom > texture.Height) {
				return;                                    // frame index past the sheet: draw nothing rather than garbage
			}
			float left = flip ? anchor.X - (cellWidth - originX) * scale : anchor.X - originX * scale;
			Vector2 position = new(left, anchor.Y + (buried - originY) * scale);
			spriteBatch.Draw(texture, position, source, color, 0f, Vector2.Zero, scale,
				flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None, 0f);
		}
	}
}
