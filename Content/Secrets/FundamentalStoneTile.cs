using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent.Drawing;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// A Fundamental Stone (Pedra Fundamental; user-set 2026-11-10, "the secret puzzle", from a reference image of a rune
	/// tablet on a pedestal): a 4x6 monolith of blue slate with runes cut into it that glow, one of <see cref="FundamentalStones.Count"/>,
	/// each with its own sigil (the tile's style, <see cref="FundamentalStones"/>). It is a fixed background piece: players
	/// walk through it (not solid), and nothing can take it away: it can't be mined, hammered, blown up, swapped, washed or
	/// burnt away, and the block it stands on can't be mined or swapped from under it either. Right-click (within reach) to
	/// read it: a line of runes appears over it (<see cref="FundamentalStoneReading"/>).
	/// <para><b>The shield</b> (user-set 2026-11-11: "rework the shield for the fundamental stones, it should not be a physical
	/// wall but only an effect/visual cue for a primordial stone that can't be interacted with yet; add the force field to
	/// every fundamental stone"): while its guardian lives (<see cref="FundamentalStones.Sealed"/>) a dome of aether light
	/// stands over the stone (<c>FundamentalShield.png</c>, 6 frames, its lattice drifting up, drawn after the tiles and
	/// added onto them, pulsing; a mote now and then), the cursor names it sealed and a right click only hums back. When
	/// the guardian dies the dome is gone for good, shattering for whoever is looking (a burst of light and the glass sound,
	/// once per client: <see cref="ResetShields"/>).</para>
	/// <para><b>Awake</b> (the puzzle, 2026-11-24: <see cref="FundamentalStoneAwakening"/>): a stone woken in its order glows
	/// gold (<c>_Awake</c>, the same cuts) and lights its slate gold; one touched out of turn flares gold and dies out for its
	/// toucher.</para>
	/// <para>Placed whole by world generation (<see cref="FundamentalStones.TryPlace"/>), never by a player: it has no item.
	/// Its <see cref="TileObjectData"/> has no anchors and it refuses vanilla's framing (<see cref="TileFrame"/>), so no
	/// neighbour change can break it. The glow (<c>_Glow</c>) is drawn at full brightness, breathing slowly (the fade is in
	/// code, D4 rule 9); the cuts light the slate round them.</para>
	/// <para>D0: no item, no drops, never killed; every index from the frame is clamped. D1: O(1) hooks; the glow texture
	/// cached on clients. D2: the tiles are world data (sent with the world); reading is local to the reader.</para>
	/// </summary>
	public class FundamentalStoneTile : CogpunkTile
	{
		public const int Width = 4, Height = 6;
		public const int StyleWidth = Width * 18;                // frame px per style

		public const int ShieldW = 104, ShieldH = 128, ShieldFrames = 6, ShieldGap = 2;   // FundamentalShield.png (game px)
		public const int ShieldStoneX = 20, ShieldStoneY = 32;   // the stone's top-left inside the shield's frame
		public const int ShieldFrameTicks = 6;
		public const float ShieldOpacity = 0.55f;

		private static Asset<Texture2D> glow, awakeGlow, shield;
		private static readonly sbyte[] seenSealed = new sbyte[FundamentalStones.Count];   // per stone: -1 unseen, 0 open, 1 sealed

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = false;
			Main.tileWaterDeath[Type] = false;
			Main.tileLighted[Type] = true;
			TileID.Sets.CanBeClearedDuringGeneration[Type] = false;   // later passes leave it alone
			TileID.Sets.PreventsTileRemovalIfOnTopOfIt[Type] = true;  // the block it stands on stays
			TileID.Sets.PreventsTileReplaceIfOnTopOfIt[Type] = true;
			TileID.Sets.PreventsTileHammeringIfOnTopOfIt[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;

			DustType = DustID.Cobalt;

			TileObjectData.newTile.Width = Width;
			TileObjectData.newTile.Height = Height;
			TileObjectData.newTile.Origin = new Point16(0, Height - 1);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 16, 16, 16, 16, 16 };
			TileObjectData.newTile.CoordinateWidth = 16;
			TileObjectData.newTile.CoordinatePadding = 2;
			TileObjectData.newTile.StyleHorizontal = true;
			TileObjectData.newTile.AnchorBottom = AnchorData.Empty;
			TileObjectData.newTile.LavaDeath = false;
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(46, 58, 100), CreateMapEntryName());
			if (!Main.dedServ) {
				glow = DepthLayers.RequestOptional(Texture + "_Glow");
				awakeGlow = DepthLayers.RequestOptional(Texture + "_Awake");
				shield = DepthLayers.RequestOptional("Cogpunk/Content/Secrets/FundamentalShield");
			}
			ResetShields();
		}

		public override void Unload() {
			glow = awakeGlow = shield = null;
		}

		/// <summary>A new world: no stone seen yet (so a world loaded with a guardian already dead shows no shatter).</summary>
		public static void ResetShields() {
			for (int k = 0; k < seenSealed.Length; k++) {
				seenSealed[k] = -1;
			}
		}

		// --- nothing takes it away ----------------------------------------------------------------------------------------

		public override bool CanKillTile(int i, int j, ref bool blockDamaged) {
			blockDamaged = false;
			return false;
		}

		public override bool CanExplode(int i, int j) => false;

		public override bool CanReplace(int i, int j, int tileTypeBeingPlaced) => false;

		/// <summary>Never reframed or checked against its neighbours (it is placed whole and has no anchors).</summary>
		public override bool TileFrame(int i, int j, ref bool resetFrame, ref bool noBreak) => false;

		// --- reading ------------------------------------------------------------------------------------------------------

		/// <summary>The stone's number (its style) and its top-left tile.</summary>
		public static int StyleAt(int i, int j, out int left, out int top) {
			Tile tile = Main.tile[i, j];
			int style = Math.Clamp(tile.TileFrameX / StyleWidth, 0, FundamentalStones.Count - 1);
			left = i - tile.TileFrameX % StyleWidth / 18;
			top = j - Math.Clamp(tile.TileFrameY / 18, 0, Height - 1);
			return style;
		}

		public override void MouseOver(int i, int j) {
			Player player = Main.LocalPlayer;
			player.noThrow = 2;
			player.cursorItemIconEnabled = true;
			player.cursorItemIconID = -1;
			player.cursorItemIconText = Language.GetTextValue(FundamentalStones.Sealed(StyleAt(i, j, out _, out _))
				? "Mods.Cogpunk.Tiles.FundamentalStoneTile.Sealed" : "Mods.Cogpunk.Tiles.FundamentalStoneTile.MapEntry");
		}

		/// <summary>The reader's client: its runes appear over it; a sealed stone (its guardian lives) only hums back.</summary>
		public override bool RightClick(int i, int j) {
			int style = StyleAt(i, j, out int left, out int top);
			// research (user, 2026-11-24): touching a stone, sealed or not, opens the Mystery of the Past's tab
			Main.LocalPlayer.GetModPlayer<Content.Research.ResearchPlayer>().TouchStone();
			if (FundamentalStones.Sealed(style)) {
				SoundEngine.PlaySound(SoundID.Item93 with { Pitch = -0.6f, Volume = 0.6f }, new Vector2(i * 16f + 8f, j * 16f + 8f));
				CombatText.NewText(new Rectangle(left * 16, top * 16, Width * 16, 16), new Color(198, 189, 255),
					Language.GetTextValue("Mods.Cogpunk.Tiles.FundamentalStoneTile.SealedSay"));
				return true;
			}
			FundamentalStoneReading.Open(style, new Vector2(left * 16f + Width * 8f, top * 16f));
			// the puzzle (user, 2026-11-24): "the stone of the tar pit should only say "..." and activate right upon interaction"
			FundamentalStoneAwakening.RequestTouch(style, left, top);
			return true;
		}

		// --- looks -----------------------------------------------------------------------------------------------------------

		/// <summary>The cuts' glow breathing: 0.7..1, a slow 4 s cycle, each stone a little out of step.</summary>
		public static float Breath(int style) => 0.85f + 0.15f * MathF.Sin(Main.GlobalTimeWrappedHourly * 1.57f + style * 1.3f);

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			int row = Main.tile[i, j].TileFrameY / 18;
			if (row >= Height - 1) {
				return;                                         // the pedestal
			}
			int style = Math.Clamp(Main.tile[i, j].TileFrameX / StyleWidth, 0, FundamentalStones.Count - 1);
			float k = Breath(style);
			if (FundamentalStoneAwakening.Awake(style)) {
				r = 0.42f * k;                                      // awake: its cuts glow gold
				g = 0.32f * k;
				b = 0.10f * k;
				return;
			}
			r = 0.05f * k;
			g = 0.13f * k;
			b = 0.32f * k;
		}

		/// <summary>The top-left tile, every frame: a sealed stone asks for its shield to be drawn after the tiles
		/// (<see cref="SpecialDraw"/>); a stone seen sealed that has just opened shatters, once.</summary>
		public override void DrawEffects(int i, int j, SpriteBatch spriteBatch, ref TileDrawInfo drawData) {
			Tile tile = Main.tile[i, j];
			if (tile.TileFrameX % StyleWidth != 0 || tile.TileFrameY != 0) {
				return;
			}
			int style = Math.Clamp(tile.TileFrameX / StyleWidth, 0, FundamentalStones.Count - 1);
			bool sealedNow = FundamentalStones.Sealed(style);
			if (seenSealed[style] == 1 && !sealedNow) {
				Shatter(i, j);
			}
			seenSealed[style] = (sbyte)(sealedNow ? 1 : 0);
			FundamentalStoneAwakening.Seen(style, i, j);
			if (sealedNow) {
				Main.instance.TilesRenderer.AddSpecialPoint(i, j, TileDrawing.TileCounterType.CustomNonSolid);
			}
		}

		/// <summary>The shield over the stone whose top-left tile is (<paramref name="i"/>, <paramref name="j"/>), added onto
		/// what is behind it (alpha 0), pulsing; drawn on the screen at 60 fps (a custom non-solid point: no off-screen
		/// range to add).</summary>
		public override void SpecialDraw(int i, int j, SpriteBatch spriteBatch) {
			if (shield?.IsLoaded != true) {
				return;
			}
			int frame = (int)(Main.GameUpdateCount / ShieldFrameTicks % ShieldFrames);
			Rectangle source = new(0, frame * (ShieldH + ShieldGap), ShieldW, ShieldH);
			if (source.Bottom > shield.Value.Height) {
				return;
			}
			float pulse = 0.8f + 0.2f * MathF.Sin(Main.GlobalTimeWrappedHourly * 2.4f + i * 0.31f);
			Vector2 at = new(i * 16 - (int)Main.screenPosition.X - ShieldStoneX, j * 16 - (int)Main.screenPosition.Y - ShieldStoneY);
			spriteBatch.Draw(shield.Value, at, source, new Color(255, 255, 255, 0) * (ShieldOpacity * pulse), 0f, Vector2.Zero, 1f,
				SpriteEffects.None, 0f);
		}

		/// <summary>A mote of the shield's light now and then (clients; vanilla calls this at its particle rate).</summary>
		public override void EmitParticles(int i, int j, Tile tile, short tileFrameX, short tileFrameY, Color tileLight, bool visible) {
			if (!visible || tileFrameX % StyleWidth != 0 || tileFrameY != 0 || !Main.rand.NextBool(12)) {
				return;
			}
			int style = Math.Clamp(tileFrameX / StyleWidth, 0, FundamentalStones.Count - 1);
			if (FundamentalStones.Sealed(style) && SafeSpawn.TryNewDust(new Vector2(i * 16 - 16, j * 16 - 24), Width * 16 + 32, Height * 16 + 8,
				DustID.PurificationPowder, out Dust mote)) {
				mote.noGravity = true;
				mote.velocity = new Vector2(0f, -0.6f);
				mote.scale = 0.9f;
			}
		}

		/// <summary>The shield breaks (this client saw it sealed, and its guardian has just died): a burst of its light, the
		/// glass sound.</summary>
		private static void Shatter(int i, int j) {
			Vector2 centre = new(i * 16 + Width * 8, j * 16 + Height * 8);
			SoundEngine.PlaySound(SoundID.Shatter with { Pitch = -0.3f }, centre);
			for (int k = 0; k < 40; k++) {
				if (SafeSpawn.TryNewDust(centre - new Vector2(40f, 56f), 80, 112, DustID.PurificationPowder, out Dust shard)) {
					shard.noGravity = true;
					shard.velocity = (shard.position - centre).SafeNormalize(Vector2.UnitY) * Main.rand.NextFloat(2f, 5f);
					shard.scale = 1.3f;
				}
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
			int style = Math.Clamp(tile.TileFrameX / StyleWidth, 0, FundamentalStones.Count - 1);
			Vector2 zero = Main.drawToScreen ? Vector2.Zero : new Vector2(Main.offScreenRange);
			Vector2 at = new Vector2(i * 16 - (int)Main.screenPosition.X, j * 16 - (int)Main.screenPosition.Y) + zero;
			// an awake stone's cuts glow gold (the puzzle, 2026-11-24); one touched out of turn flares gold and dies out (its
			// toucher's view, FundamentalStoneAwakening.Flare)
			bool awake = FundamentalStoneAwakening.Awake(style);
			float flare = awake ? 0f : FundamentalStoneAwakening.Flare(style);
			if ((awake || flare > 0f) && awakeGlow?.IsLoaded == true && source.Right <= awakeGlow.Value.Width && source.Bottom <= awakeGlow.Value.Height) {
				if (flare < 1f && !awake) {
					spriteBatch.Draw(glow.Value, at, source, Color.White * (Breath(style) * (1f - flare)), 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
				}
				spriteBatch.Draw(awakeGlow.Value, at, source, Color.White * (awake ? Breath(style) : flare), 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
				return;
			}
			spriteBatch.Draw(glow.Value, at, source, Color.White * Breath(style), 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
		}
	}
}
