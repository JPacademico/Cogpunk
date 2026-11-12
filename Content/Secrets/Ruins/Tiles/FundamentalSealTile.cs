using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Secrets.Ruins.Tiles
{
	/// <summary>
	/// The Sealed Gate (user-set 2026-11-11b: "the door to the arena is sealed shut until the player activates 3 rune glyphs
	/// on the area"): a 9x3 slab of Ancient Brick set in the arena's crown, the floor of the gate hall over it, carved with a
	/// ring of runes and three sockets, one for each Rune Glyph. A socket lights when its glyph is lit (the glow sheet, drawn
	/// added onto the slab); while all three aren't lit the slab is solid and nothing breaks it (the arena's rules); the third
	/// glyph removes it for good (<see cref="FundamentalRuinsSystem.LightGlyph"/>) and the hall's floor opens onto the arena.
	/// The cursor names it with how many glyphs are lit.
	/// <para>Placed whole by world generation (<see cref="Place"/>), never by a player: no item; no anchors, never reframed,
	/// can't be mined, blown up, hammered, sloped or replaced. Solid, like vanilla's closed doors (a solid frame-important
	/// tile).</para>
	/// <para>D2: the sockets read the glyphs' world flags; the server removes the slab's tiles and sends them (a tile square).
	/// D0: every index from the frame is clamped; no item, no drops. D1: O(1) hooks; the glow cached on clients.</para>
	/// </summary>
	public class FundamentalSealTile : CogpunkTile
	{
		public const int Width = 9, Height = 3;
		/// <summary>The sockets' columns in the slab (glyph 1, 2, 3), in its middle row.</summary>
		public static readonly int[] SocketColumns = { 2, 4, 6 };
		public const int SocketRow = 1;

		private static Asset<Texture2D> glow;

		public override void SetStaticDefaults() {
			Main.tileSolid[Type] = true;
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileBlockLight[Type] = true;
			Main.tileLavaDeath[Type] = false;
			Main.tileWaterDeath[Type] = false;
			Main.tileLighted[Type] = true;
			TileID.Sets.CanBeClearedDuringGeneration[Type] = false;
			TileID.Sets.GeneralPlacementTiles[Type] = false;
			TileID.Sets.DisableSmartCursor[Type] = true;

			DustType = DustID.Stone;
			HitSound = SoundID.Tink;

			TileObjectData.newTile.Width = Width;
			TileObjectData.newTile.Height = Height;
			TileObjectData.newTile.Origin = new Point16(0, 0);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 16, 16 };
			TileObjectData.newTile.CoordinateWidth = 16;
			TileObjectData.newTile.CoordinatePadding = 2;
			TileObjectData.newTile.AnchorBottom = AnchorData.Empty;
			TileObjectData.newTile.LavaDeath = false;
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(124, 107, 224), CreateMapEntryName());
			if (!Main.dedServ) {
				glow = DepthLayers.RequestOptional(Texture + "_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		/// <summary>World generation: the slab with its top-left tile at (<paramref name="left"/>, <paramref name="top"/>),
		/// written over whatever is there (the arena's crown). Cells outside the world are skipped.</summary>
		public static void Place(int left, int top) {
			int type = ModContent.TileType<FundamentalSealTile>();
			for (int dx = 0; dx < Width; dx++) {
				for (int dy = 0; dy < Height; dy++) {
					if (!TileSafety.TryGetTile(left + dx, top + dy, out Tile tile, TileSafety.EditMargin)) {
						continue;
					}
					tile.ClearTile();
					tile.HasTile = true;
					tile.TileType = (ushort)type;
					tile.TileFrameX = (short)(dx * 18);
					tile.TileFrameY = (short)(dy * 18);
				}
			}
		}

		// --- nothing takes it away (until the glyphs do) --------------------------------------------------------------------

		public override bool CanKillTile(int i, int j, ref bool blockDamaged) {
			blockDamaged = false;
			return false;
		}

		public override bool CanExplode(int i, int j) => false;

		public override bool CanReplace(int i, int j, int tileTypeBeingPlaced) => false;

		public override bool Slope(int i, int j) => false;

		public override bool TileFrame(int i, int j, ref bool resetFrame, ref bool noBreak) => false;

		// --- looks -----------------------------------------------------------------------------------------------------------

		public override void MouseOver(int i, int j) {
			Player player = Main.LocalPlayer;
			player.noThrow = 2;
			player.cursorItemIconEnabled = true;
			player.cursorItemIconID = -1;
			player.cursorItemIconText = Language.GetTextValue("Mods.Cogpunk.Tiles.FundamentalSealTile.Hover", FundamentalRuinsSystem.GlyphsLit,
				FundamentalRuinsSystem.GlyphCount);
		}

		/// <summary>The glyph whose socket this tile holds (-1: none).</summary>
		private static int SocketAt(Tile tile) {
			int col = Math.Clamp(tile.TileFrameX / 18, 0, Width - 1), row = Math.Clamp(tile.TileFrameY / 18, 0, Height - 1);
			if (row != SocketRow) {
				return -1;
			}
			for (int k = 0; k < SocketColumns.Length; k++) {
				if (SocketColumns[k] == col) {
					return k;
				}
			}
			return -1;
		}

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			int socket = SocketAt(Main.tile[i, j]);
			if (socket >= 0 && FundamentalRuinsSystem.GlyphLit(socket)) {
				r = 0.14f;
				g = 0.12f;
				b = 0.42f;
			}
		}

		/// <summary>The top-left tile, every frame: this client has seen the gate shut (its opening then plays here,
		/// <see cref="FundamentalRuinsSystem"/>).</summary>
		public override void DrawEffects(int i, int j, SpriteBatch spriteBatch, ref TileDrawInfo drawData) {
			Tile tile = Main.tile[i, j];
			if (tile.TileFrameX == 0 && tile.TileFrameY == 0) {
				FundamentalRuinsSystem.SawGateShut();
			}
		}

		/// <summary>A lit glyph's socket glows (added onto the slab, breathing); a dark one shows a faint ember of it.</summary>
		public override void PostDraw(int i, int j, SpriteBatch spriteBatch) {
			if (glow?.IsLoaded != true) {
				return;
			}
			Tile tile = Main.tile[i, j];
			int socket = SocketAt(tile);
			if (socket < 0) {
				return;
			}
			Rectangle source = new(tile.TileFrameX, tile.TileFrameY, 16, 16);
			if (source.Right > glow.Value.Width || source.Bottom > glow.Value.Height) {
				return;
			}
			float k = FundamentalRuinsSystem.GlyphLit(socket) ? 0.85f + 0.15f * MathF.Sin(Main.GlobalTimeWrappedHourly * 1.6f + socket) : 0.18f;
			Vector2 zero = Main.drawToScreen ? Vector2.Zero : new Vector2(Main.offScreenRange);
			Vector2 at = new Vector2(i * 16 - (int)Main.screenPosition.X, j * 16 - (int)Main.screenPosition.Y) + zero;
			spriteBatch.Draw(glow.Value, at, source, new Color(255, 255, 255, 0) * k, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
		}
	}
}
