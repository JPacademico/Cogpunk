using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Secrets.Ruins.Tiles
{
	/// <summary>
	/// A Rune Glyph (user-set 2026-11-11b: "the door to the arena is sealed shut until the player activates 3 rune glyphs on
	/// the area, placed on the dead ends"): a 2x3 slab of blue rune stone on a slate foot, its rune cut deep, one of
	/// <see cref="FundamentalRuinsSystem.GlyphCount"/> (the tile's style, each with its own rune), standing at the end of one
	/// of the ruins' three wings. Right-click it (within reach) to light it: the rune blazes and stays lit for good, and one of
	/// the sealed gate's three sockets lights with it; the third opens the gate (<see cref="FundamentalRuinsSystem.LightGlyph"/>).
	/// Unlit, its rune breathes faintly (a cue that it can be used); the cursor names it.
	/// <para>Placed whole by world generation (<see cref="TryPlace"/>), never by a player: it has no item; nothing takes it
	/// away (the Fundamental Stone's rules: no anchors, never reframed, can't be mined, blown up, replaced, washed or burnt,
	/// and the block under it stays). Not solid.</para>
	/// <para>D2: the lit glyphs are world flags (saved by name, sent with the world data): a client's click asks the server
	/// (<see cref="FundamentalRuinsSystem.RequestLight"/>, checked there), the server lights it and sends the world data, so
	/// every client lights the same glyphs; each client plays the lighting once, if it saw the glyph dark
	/// (<see cref="DrawEffects"/>). D0: no item, no drops, never killed; every index from the frame is clamped. D1: O(1)
	/// hooks; the glow cached on clients.</para>
	/// </summary>
	public class FundamentalGlyphTile : CogpunkTile
	{
		public const int Width = 2, Height = 3;
		public const int StyleWidth = Width * 18;
		public const float Reach = 10f * 16f;                    // the player's centre to the glyph's, to light it

		private static Asset<Texture2D> glow;
		private static readonly sbyte[] seenLit = new sbyte[FundamentalRuinsSystem.GlyphCount];   // -1 unseen, 0 dark, 1 lit

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = false;
			Main.tileWaterDeath[Type] = false;
			Main.tileLighted[Type] = true;
			TileID.Sets.CanBeClearedDuringGeneration[Type] = false;
			TileID.Sets.PreventsTileRemovalIfOnTopOfIt[Type] = true;
			TileID.Sets.PreventsTileReplaceIfOnTopOfIt[Type] = true;
			TileID.Sets.PreventsTileHammeringIfOnTopOfIt[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;

			DustType = DustID.Cobalt;

			TileObjectData.newTile.Width = Width;
			TileObjectData.newTile.Height = Height;
			TileObjectData.newTile.Origin = new Point16(0, Height - 1);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 16, 16 };
			TileObjectData.newTile.CoordinateWidth = 16;
			TileObjectData.newTile.CoordinatePadding = 2;
			TileObjectData.newTile.StyleHorizontal = true;
			TileObjectData.newTile.AnchorBottom = AnchorData.Empty;
			TileObjectData.newTile.LavaDeath = false;
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(66, 86, 136), CreateMapEntryName());
			if (!Main.dedServ) {
				glow = DepthLayers.RequestOptional(Texture + "_Glow");
			}
			ResetSeen();
		}

		public override void Unload() {
			glow = null;
		}

		/// <summary>A new world: no glyph seen yet (so a world loaded with them already lit plays nothing).</summary>
		public static void ResetSeen() {
			for (int k = 0; k < seenLit.Length; k++) {
				seenLit[k] = -1;
			}
		}

		// --- world generation -------------------------------------------------------------------------------------------------

		/// <summary>World generation: glyph <paramref name="style"/> with its left column at <paramref name="left"/>, standing on
		/// row <paramref name="floorY"/> (it fills the <see cref="Height"/> rows above). Loose cuttable plants in its way are
		/// cleared; anything else refuses it (false).</summary>
		public static bool TryPlace(int style, int left, int floorY) {
			if (style < 0 || style >= FundamentalRuinsSystem.GlyphCount) {
				return false;
			}
			int type = ModContent.TileType<FundamentalGlyphTile>();
			int top = floorY - Height;
			for (int x = left; x < left + Width; x++) {
				for (int y = top; y < floorY; y++) {
					if (!TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin)) {
						return false;
					}
					if (tile.HasTile && !(Main.tileCut[tile.TileType] && !Main.tileFrameImportant[tile.TileType])) {
						return false;
					}
				}
			}
			for (int dx = 0; dx < Width; dx++) {
				for (int dy = 0; dy < Height; dy++) {
					Tile tile = Main.tile[left + dx, top + dy];
					tile.ClearTile();
					tile.HasTile = true;
					tile.TileType = (ushort)type;
					tile.TileFrameX = (short)(style * StyleWidth + dx * 18);
					tile.TileFrameY = (short)(dy * 18);
				}
			}
			return true;
		}

		// --- nothing takes it away ----------------------------------------------------------------------------------------

		public override bool CanKillTile(int i, int j, ref bool blockDamaged) {
			blockDamaged = false;
			return false;
		}

		public override bool CanExplode(int i, int j) => false;

		public override bool CanReplace(int i, int j, int tileTypeBeingPlaced) => false;

		public override bool TileFrame(int i, int j, ref bool resetFrame, ref bool noBreak) => false;

		// --- lighting it ----------------------------------------------------------------------------------------------------

		/// <summary>The glyph's number (its style) and its top-left tile.</summary>
		public static int StyleAt(int i, int j, out int left, out int top) {
			Tile tile = Main.tile[i, j];
			int style = Math.Clamp(tile.TileFrameX / StyleWidth, 0, FundamentalRuinsSystem.GlyphCount - 1);
			left = i - tile.TileFrameX % StyleWidth / 18;
			top = j - Math.Clamp(tile.TileFrameY / 18, 0, Height - 1);
			return style;
		}

		public override void MouseOver(int i, int j) {
			Player player = Main.LocalPlayer;
			player.noThrow = 2;
			player.cursorItemIconEnabled = true;
			player.cursorItemIconID = -1;
			player.cursorItemIconText = Language.GetTextValue(FundamentalRuinsSystem.GlyphLit(StyleAt(i, j, out _, out _))
				? "Mods.Cogpunk.Tiles.FundamentalGlyphTile.Lit" : "Mods.Cogpunk.Tiles.FundamentalGlyphTile.MapEntry");
		}

		/// <summary>The clicker's client: a dark glyph asks to be lit (the server decides); a lit one only hums.</summary>
		public override bool RightClick(int i, int j) {
			int style = StyleAt(i, j, out int left, out int top);
			Vector2 centre = new(left * 16f + Width * 8f, top * 16f + Height * 8f);
			if (FundamentalRuinsSystem.GlyphLit(style)) {
				SoundEngine.PlaySound(SoundID.Item93 with { Pitch = -0.2f, Volume = 0.5f }, centre);
				return true;
			}
			if (Vector2.DistanceSquared(Main.LocalPlayer.Center, centre) > Reach * Reach) {
				return true;
			}
			FundamentalRuinsSystem.RequestLight(style, left, top);
			return true;
		}

		// --- looks -----------------------------------------------------------------------------------------------------------

		/// <summary>Lit: a steady glow breathing 0.85..1. Dark: a faint pulse 0.12..0.36 every 2 s, each glyph out of step.</summary>
		public static float GlowOf(int style) {
			float t = Main.GlobalTimeWrappedHourly;
			return FundamentalRuinsSystem.GlyphLit(style) ? 0.85f + 0.15f * MathF.Sin(t * 1.6f + style)
				: 0.24f + 0.12f * MathF.Sin(t * 3.1f + style * 2.1f);
		}

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			int style = Math.Clamp(Main.tile[i, j].TileFrameX / StyleWidth, 0, FundamentalRuinsSystem.GlyphCount - 1);
			float k = GlowOf(style);
			r = 0.12f * k;
			g = 0.16f * k;
			b = 0.42f * k;
		}

		/// <summary>The top-left tile, every frame: a glyph this client saw dark that is now lit plays its lighting, once.</summary>
		public override void DrawEffects(int i, int j, SpriteBatch spriteBatch, ref TileDrawInfo drawData) {
			Tile tile = Main.tile[i, j];
			if (tile.TileFrameX % StyleWidth != 0 || tile.TileFrameY != 0) {
				return;
			}
			int style = Math.Clamp(tile.TileFrameX / StyleWidth, 0, FundamentalRuinsSystem.GlyphCount - 1);
			bool lit = FundamentalRuinsSystem.GlyphLit(style);
			if (seenLit[style] == 0 && lit) {
				Awaken(i, j);
			}
			seenLit[style] = (sbyte)(lit ? 1 : 0);
		}

		/// <summary>The rune blazes: a burst of its light, a chime, and how many glyphs are lit.</summary>
		private static void Awaken(int i, int j) {
			Vector2 centre = new(i * 16 + Width * 8, j * 16 + Height * 8);
			SoundEngine.PlaySound(SoundID.Item29 with { Pitch = -0.3f, Volume = 0.8f }, centre);
			SoundEngine.PlaySound(SoundID.Item4 with { Pitch = -0.5f, Volume = 0.6f }, centre);
			for (int k = 0; k < 24 && CogpunkClientConfig.RollEffect(); k++) {
				if (SafeSpawn.TryNewDust(centre - new Vector2(12f, 20f), 24, 40, DustID.PurificationPowder, out Dust mote)) {
					mote.noGravity = true;
					mote.velocity = (mote.position - centre).SafeNormalize(Vector2.UnitY) * Main.rand.NextFloat(1.5f, 4f);
					mote.scale = 1.2f;
				}
			}
			CombatText.NewText(new Rectangle(i * 16, j * 16 - 16, Width * 16, 16), new Color(198, 189, 255),
				Language.GetTextValue("Mods.Cogpunk.Tiles.FundamentalGlyphTile.Awakened", FundamentalRuinsSystem.GlyphsLit,
				FundamentalRuinsSystem.GlyphCount));
		}

		/// <summary>A mote of a lit glyph's light now and then (clients; vanilla calls this at its particle rate).</summary>
		public override void EmitParticles(int i, int j, Tile tile, short tileFrameX, short tileFrameY, Color tileLight, bool visible) {
			if (!visible || tileFrameX % StyleWidth != 0 || tileFrameY != 0 || !Main.rand.NextBool(14)) {
				return;
			}
			int style = Math.Clamp(tileFrameX / StyleWidth, 0, FundamentalRuinsSystem.GlyphCount - 1);
			if (FundamentalRuinsSystem.GlyphLit(style) && SafeSpawn.TryNewDust(new Vector2(i * 16, j * 16), Width * 16, Height * 16,
				DustID.PurificationPowder, out Dust mote)) {
				mote.noGravity = true;
				mote.velocity = new Vector2(0f, -0.5f);
				mote.scale = 0.8f;
			}
		}

		public override void PostDraw(int i, int j, SpriteBatch spriteBatch) {
			if (glow?.IsLoaded != true) {
				return;
			}
			Tile tile = Main.tile[i, j];
			Rectangle source = new(tile.TileFrameX, tile.TileFrameY, 16, 16);
			if (source.Right > glow.Value.Width || source.Bottom > glow.Value.Height) {
				return;
			}
			int style = Math.Clamp(tile.TileFrameX / StyleWidth, 0, FundamentalRuinsSystem.GlyphCount - 1);
			Vector2 zero = Main.drawToScreen ? Vector2.Zero : new Vector2(Main.offScreenRange);
			Vector2 at = new Vector2(i * 16 - (int)Main.screenPosition.X, j * 16 - (int)Main.screenPosition.Y) + zero;
			spriteBatch.Draw(glow.Value, at, source, new Color(255, 255, 255, 0) * GlowOf(style), 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
		}
	}
}
