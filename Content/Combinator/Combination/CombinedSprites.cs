using System;
using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>A combined sprite: the texture and where each weapon's own sprite sits inside it (px).</summary>
	public sealed class CombinedSprite
	{
		public Texture2D Texture;
		public int Width, Height;
		public Point AugmentOffset, BaseOffset;
		public Point AugmentSize, BaseSize;
	}

	/// <summary>
	/// The look of a combination, made at runtime (user, 2026-11-12: "the weapon formed by the combination should always look
	/// like the two sprites of the weapons combined (first half of the augment and second half of the base); make it dynamic
	/// so it does not require us to generate every single sprite"). No pair is drawn by hand: the first time a pair is drawn,
	/// both item textures are read back (<c>Texture2D.GetData</c>, their first animation frame when they have
	/// <c>Main.itemAnimations</c>) and glued into one new texture, cached per pair.
	/// <list type="bullet">
	/// <item>A sprite that points up and right (swords, spears, staffs: vanilla's swing, thrust and staff conventions) is split
	/// across its diagonal: the augment's lower-left half (the grip, the guard) and the base's upper-right half (the blade,
	/// the head), their diagonals' middles laid on one point.</item>
	/// <item>Anything else (guns, bows, books: they point right) is split down the middle: the augment's back half and the
	/// base's front half, their middle columns and centre rows laid on one line.</item>
	/// </list>
	/// Every cut and offset falls on the 2 px grid of the 2x art (D4 rule 1), so no art pixel is cut in two; the result keeps
	/// both sprites' own pixels and colours. Held items draw it through <see cref="CombinedHeldItemLayer"/>, the inventory and
	/// the world through <see cref="CombinedWeapon"/>'s draw hooks.
	/// <para>D0/D1: clients only (a dedicated server has no textures); built once per pair on the main thread (draw code),
	/// at most <see cref="MaxCached"/> pairs (the oldest disposed first); a texture that isn't loaded yet just shows the plain
	/// augment for a frame; a failure (an unreadable texture format) is remembered as "no sprite" and logged once; every
	/// texture is disposed on unload.</para>
	/// </summary>
	public static class CombinedSprites
	{
		public const int MaxCached = 96;

		private static readonly Dictionary<long, CombinedSprite> cache = new();
		private static readonly Queue<long> order = new();

		private static long Key(int augmentType, int baseType) => ((long)augmentType << 32) | (uint)baseType;

		/// <summary>The combined sprite of the pair, built on first use (clients only).</summary>
		public static bool TryGet(int augmentType, int baseType, out CombinedSprite sprite) {
			sprite = null;
			if (Main.dedServ || augmentType <= ItemID.None || baseType <= ItemID.None
				|| augmentType >= ItemLoader.ItemCount || baseType >= ItemLoader.ItemCount) {
				return false;
			}
			long key = Key(augmentType, baseType);
			if (cache.TryGetValue(key, out sprite)) {
				return sprite != null;
			}
			if (!Ready(augmentType) || !Ready(baseType)) {
				return false;                                  // not loaded yet: try again next frame
			}
			try {
				sprite = Build(augmentType, baseType);
			}
			catch (Exception e) {
				SafeLog.Warn("Combinator.SpriteFailed", "Combinator: the combined sprite of {0} could not be made ({1}).", augmentType + "+" + baseType, e.Message);
				sprite = null;
			}
			Remember(key, sprite);
			return sprite != null;
		}

		private static bool Ready(int type) {
			Main.instance.LoadItem(type);
			return TextureAssets.Item[type]?.IsLoaded == true;
		}

		private static void Remember(long key, CombinedSprite sprite) {
			while (order.Count >= MaxCached && order.Count > 0) {
				long old = order.Dequeue();
				if (cache.Remove(old, out CombinedSprite gone)) {
					gone?.Texture?.Dispose();
				}
			}
			cache[key] = sprite;
			order.Enqueue(key);
		}

		public static void Clear() {
			foreach (CombinedSprite s in cache.Values) {
				s?.Texture?.Dispose();
			}
			cache.Clear();
			order.Clear();
		}

		/// <summary>The item's drawn frame: its first animation frame, or the whole texture.</summary>
		private static Rectangle Frame(int type, Texture2D texture) {
			if (type < Main.itemAnimations.Length && Main.itemAnimations[type] != null) {
				return Main.itemAnimations[type].GetFrame(texture, 0);
			}
			return texture.Bounds;
		}

		/// <summary>Vanilla's conventions for which way a sprite points (D4 rule 8: swords and staffs top-right, guns right).</summary>
		public static bool PointsUpRight(int type) {
			Item sample = CombinationRules.Sample(type);
			if (sample == null) {
				return false;
			}
			return sample.useStyle == ItemUseStyleID.Swing || sample.useStyle == ItemUseStyleID.Thrust || sample.useStyle == ItemUseStyleID.Rapier
				|| Item.staff[type] || ItemID.Sets.Spears[type];
		}

		private static int Even(double v) => (int)Math.Round(v / 2.0) * 2;

		private static CombinedSprite Build(int augmentType, int baseType) {
			Texture2D ta = TextureAssets.Item[augmentType].Value, tb = TextureAssets.Item[baseType].Value;
			if (ta == null || tb == null || ta.Format != SurfaceFormat.Color || tb.Format != SurfaceFormat.Color) {
				return null;
			}
			Rectangle fa = Frame(augmentType, ta), fb = Frame(baseType, tb);
			if (fa.Width <= 0 || fa.Height <= 0 || fb.Width <= 0 || fb.Height <= 0 || fa.Width * fa.Height > 512 * 512 || fb.Width * fb.Height > 512 * 512) {
				return null;
			}
			Color[] ca = new Color[fa.Width * fa.Height], cb = new Color[fb.Width * fb.Height];
			ta.GetData(0, fa, ca, 0, ca.Length);
			tb.GetData(0, fb, cb, 0, cb.Length);
			int wa = fa.Width, ha = fa.Height, wb = fb.Width, hb = fb.Height;
			bool diagonal = PointsUpRight(augmentType);
			// where the base sits relative to the augment: their split points laid on one another
			int dx = Even(wa / 2.0 - wb / 2.0);
			int dy = Even(ha / 2.0 - hb / 2.0);
			int minX = Math.Min(0, dx), minY = Math.Min(0, dy);
			int maxX = Math.Max(wa, dx + wb), maxY = Math.Max(ha, dy + hb);
			int w = maxX - minX, h = maxY - minY;
			Point aOff = new(-minX, -minY), bOff = new(dx - minX, dy - minY);
			Color[] outPx = new Color[w * h];
			int splitA = Even(wa / 2.0), splitB = Even(wb / 2.0);
			for (int y = 0; y < h; y++) {
				for (int x = 0; x < w; x++) {
					int ax = x - aOff.X, ay = y - aOff.Y;
					if (ax >= 0 && ay >= 0 && ax < wa && ay < ha && FirstHalf(ax, ay, wa, ha, splitA, diagonal)) {
						Color c = ca[ay * wa + ax];
						if (c.A > 0) {
							outPx[y * w + x] = c;
							continue;
						}
					}
					int bx = x - bOff.X, by = y - bOff.Y;
					if (bx >= 0 && by >= 0 && bx < wb && by < hb && !FirstHalf(bx, by, wb, hb, splitB, diagonal)) {
						outPx[y * w + x] = cb[by * wb + bx];
					}
				}
			}
			Texture2D texture = new(Main.graphics.GraphicsDevice, w, h);
			texture.SetData(outPx);
			return new CombinedSprite {
				Texture = texture, Width = w, Height = h, AugmentOffset = aOff, BaseOffset = bOff,
				AugmentSize = new Point(wa, ha), BaseSize = new Point(wb, hb),
			};
		}

		/// <summary>Whether a pixel lies in its sprite's first half: left of the middle column, or (pointing up-right) below the
		/// anti-diagonal. Judged on the 2x2 block's corner, so whole art pixels go one way.</summary>
		private static bool FirstHalf(int x, int y, int w, int h, int split, bool diagonal) {
			x &= ~1;
			y &= ~1;
			if (!diagonal) {
				return x < split;
			}
			// t = x / w + (h - 1 - y) / h: 0 at the bottom-left corner (the grip), 2 at the top-right (the tip)
			float t = (x + 1f) / w + (h - 1f - (y + 1f)) / h;
			return t < 1f;
		}
	}

	/// <summary>Disposes the combined sprites when the mod unloads (on the main thread, where they were made).</summary>
	public sealed class CombinedSpritesSystem : ModSystem
	{
		public override void Unload() {
			if (Main.dedServ) {
				return;
			}
			Main.QueueMainThreadAction(CombinedSprites.Clear);
		}
	}
}
