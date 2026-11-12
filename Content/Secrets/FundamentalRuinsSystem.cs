using System.Collections.Generic;
using System.IO;
using Cogpunk.Content.Secrets.Generation;
using Cogpunk.Content.Secrets.Ruins.Tiles;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.Chat;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// Where the Fundamental Ruins are, and their gate. <see cref="FundamentalRuinsPass"/> runs after vanilla's "Final Cleanup"
	/// (the spider nests and everything round them exist, nothing vanilla runs after it to fill, smooth or plant the ruins).
	/// Saved by name with defaults (older worlds have no ruins and keep the Mysterious Map's placeholder) and sent with the
	/// world data (D2): <see cref="Area"/> (the ruins' box, the biome and the spawn rule's), <see cref="Arena"/> (its arena's
	/// box, kept for the boss to come) and <see cref="Gate"/> (the sealed gate's top-left tile). The stone's seal is its
	/// guardian's (<see cref="FundamentalStones.Sealed"/>).
	/// <para><b>The rune glyphs and the gate</b> (user-set 2026-11-11b: "the door to the arena is sealed shut until the player
	/// activates 3 rune glyphs on the area, placed on the dead ends"): <see cref="GlyphCount"/> glyphs, each a world flag
	/// (<c>RuinsGlyph1</c>-<c>3</c>, saved by name, sent with the world data). A click on a dark glyph asks the server
	/// (<see cref="RequestLight"/>: directly in singleplayer, else <see cref="RuinsGlyphPacket"/>, which the server checks: a
	/// glyph of that number at that spot, the sender's living player within reach); <see cref="LightGlyph"/> lights it and,
	/// with the third, opens the gate for good (<c>RuinsGateOpen</c>): the slab's tiles go (sent as a tile square), every
	/// player reads that the gate opened, and a client that saw it shut plays its opening (stone grinding, dust, a shake of
	/// the camera when near, <see cref="PostUpdateEverything"/>).</para>
	/// <para>D0: every index and spot checked; the slab's removal bounded by its size; missing save data means "no ruins".
	/// D1: the client's check is one bool a tick.</para>
	/// </summary>
	public sealed class FundamentalRuinsSystem : ModSystem
	{
		private const string AfterEverything = "Final Cleanup";
		public const int GlyphCount = 3;
		public const float ShakeRange = 90f * 16f;

		private static readonly int[] glyphFlags = new int[GlyphCount];
		private static int gateFlag = -1;
		private static bool sawGateShut;

		public static Rectangle Area { get; private set; }
		public static Rectangle Arena { get; private set; }
		/// <summary>The sealed gate's top-left tile (none in an older world: (0, 0)).</summary>
		public static Point Gate { get; private set; }
		public static bool Exists => Area.Width > 0 && Area.Height > 0;
		public static bool HasGate => Gate.X > 0 && Gate.Y > 0;

		public static void SetArea(Rectangle area, Rectangle arena) {
			Area = area;
			Arena = arena;
		}

		public static void SetGate(Point topLeft) {
			Gate = topLeft;
		}

		public static bool Contains(Vector2 worldPosition) => ContainsTile(worldPosition.ToTileCoordinates());

		/// <summary>The tile lies in the ruins' box (O(1)).</summary>
		public static bool ContainsTile(Point tile) => Exists && Area.Contains(tile);

		// --- the glyphs and the gate ------------------------------------------------------------------------------------------

		public override void Load() {
			for (int k = 0; k < GlyphCount; k++) {
				glyphFlags[k] = WorldFlagSystem.Register("RuinsGlyph" + (k + 1));
			}
			gateFlag = WorldFlagSystem.Register("RuinsGateOpen");
		}

		public static bool GlyphLit(int glyph) => glyph >= 0 && glyph < GlyphCount && WorldFlagSystem.Get(glyphFlags[glyph]);

		public static int GlyphsLit {
			get {
				int n = 0;
				for (int k = 0; k < GlyphCount; k++) {
					if (GlyphLit(k)) {
						n++;
					}
				}
				return n;
			}
		}

		public static bool GateOpen => WorldFlagSystem.Get(gateFlag);

		/// <summary>The clicker's client: glyph <paramref name="glyph"/> (its top-left tile at <paramref name="left"/>,
		/// <paramref name="top"/>) asks to be lit; the server decides.</summary>
		public static void RequestLight(int glyph, int left, int top) {
			if (Main.netMode == NetmodeID.SinglePlayer) {
				LightGlyph(glyph);
			}
			else if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<RuinsGlyphPacket>().Send(glyph, left, top);
			}
		}

		/// <summary>Server or singleplayer: lights glyph <paramref name="glyph"/> for good; the third opens the gate. The world
		/// data goes to every client.</summary>
		public static void LightGlyph(int glyph) {
			if (Main.netMode == NetmodeID.MultiplayerClient || glyph < 0 || glyph >= GlyphCount || GlyphLit(glyph)) {
				return;
			}
			WorldFlagSystem.Flag(glyphFlags[glyph]) = true;
			if (GlyphsLit >= GlyphCount && !GateOpen) {
				OpenGate();
			}
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.WorldData);
			}
		}

		/// <summary>Server or singleplayer: the slab goes (only its own tiles, within its size), the spot is reframed and sent,
		/// and every player is told.</summary>
		private static void OpenGate() {
			WorldFlagSystem.Flag(gateFlag) = true;
			if (HasGate) {
				int type = ModContent.TileType<FundamentalSealTile>();
				Point g = Gate;
				for (int dx = 0; dx < FundamentalSealTile.Width; dx++) {
					for (int dy = 0; dy < FundamentalSealTile.Height; dy++) {
						if (TileSafety.TryGetTile(g.X + dx, g.Y + dy, out Tile tile, TileSafety.EditMargin) && tile.HasTile && tile.TileType == type) {
							tile.ClearTile();
						}
					}
				}
				if (TileSafety.InWorld(g.X - 1, g.Y - 1, TileSafety.EditMargin) && TileSafety.InWorld(g.X + FundamentalSealTile.Width, g.Y + FundamentalSealTile.Height, TileSafety.EditMargin)) {
					WorldGen.RangeFrame(g.X - 1, g.Y - 1, g.X + FundamentalSealTile.Width, g.Y + FundamentalSealTile.Height);
					if (Main.netMode == NetmodeID.Server) {
						NetMessage.SendTileSquare(-1, g.X - 1, g.Y - 1, FundamentalSealTile.Width + 2, FundamentalSealTile.Height + 2);
					}
				}
			}
			Color colour = new(198, 189, 255);
			if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey("Mods.Cogpunk.Secrets.GateOpened"), colour);
			}
			else {
				Main.NewText(Language.GetTextValue("Mods.Cogpunk.Secrets.GateOpened"), colour);
			}
		}

		/// <summary>Clients: the gate's slab is on screen and shut (<see cref="FundamentalSealTile"/>).</summary>
		public static void SawGateShut() {
			if (!GateOpen) {
				sawGateShut = true;
			}
		}

		/// <summary>Clients (and singleplayer): the gate this client saw shut has opened: its opening plays here, once.</summary>
		public override void PostUpdateEverything() {
			if (Main.dedServ || !sawGateShut || !GateOpen) {
				return;
			}
			sawGateShut = false;
			if (!HasGate) {
				return;
			}
			Vector2 centre = new((Gate.X + FundamentalSealTile.Width / 2f) * 16f, (Gate.Y + FundamentalSealTile.Height / 2f) * 16f);
			SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f, Volume = 0.9f }, centre);
			SoundEngine.PlaySound(SoundID.Item29 with { Pitch = -0.7f, Volume = 0.7f }, centre);
			for (int k = 0; k < 60 && CogpunkClientConfig.RollEffect(); k++) {
				int dust = k % 3 == 0 ? DustID.PurificationPowder : DustID.Stone;
				if (SafeSpawn.TryNewDust(new Vector2(Gate.X * 16f, Gate.Y * 16f), FundamentalSealTile.Width * 16, FundamentalSealTile.Height * 16, dust, out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), Main.rand.NextFloat(0.5f, 4f));
					d.noGravity = dust == DustID.PurificationPowder;
					d.scale = 1.3f;
				}
			}
			Player me = Main.LocalPlayer;
			if ((CogpunkClientConfig.Instance?.ScreenShake ?? true) && me != null && Vector2.DistanceSquared(me.Center, centre) < ShakeRange * ShakeRange) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(centre, Vector2.UnitY, 6f, 8f, 40, 2400f, "Cogpunk:RuinsGate"));
			}
		}

		// --- the world ----------------------------------------------------------------------------------------------------------

		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			GenPassUtils.InsertAfter(tasks, AfterEverything, new FundamentalRuinsPass(), ref totalWeight);
		}

		/// <summary>A new world: no box, no gate; the per-client "seen" states of the stones' shields, the glyphs and the gate
		/// start over (so a world loaded with them already open plays nothing).</summary>
		public override void ClearWorld() {
			Area = default;
			Arena = default;
			Gate = default;
			sawGateShut = false;
			FundamentalStoneTile.ResetShields();
			FundamentalGlyphTile.ResetSeen();
		}

		public override void SaveWorldData(TagCompound tag) {
			if (Exists) {
				tag["ruinsArea"] = new[] { Area.X, Area.Y, Area.Width, Area.Height };
				tag["ruinsArena"] = new[] { Arena.X, Arena.Y, Arena.Width, Arena.Height };
			}
			if (HasGate) {
				tag["ruinsGate"] = new[] { Gate.X, Gate.Y };
			}
		}

		// Missing or malformed data (older worlds) means "no ruins"; never index past an array.
		public override void LoadWorldData(TagCompound tag) {
			int[] a = tag.GetIntArray("ruinsArea");
			int[] b = tag.GetIntArray("ruinsArena");
			int[] g = tag.GetIntArray("ruinsGate");
			Area = a != null && a.Length == 4 && a[2] > 0 && a[3] > 0 ? new Rectangle(a[0], a[1], a[2], a[3]) : default;
			Arena = b != null && b.Length == 4 && b[2] > 0 && b[3] > 0 ? new Rectangle(b[0], b[1], b[2], b[3]) : default;
			Gate = g != null && g.Length == 2 && TileSafety.InWorld(g[0], g[1]) ? new Point(g[0], g[1]) : default;
		}

		public override void NetSend(BinaryWriter writer) {
			writer.Write(Area.X);
			writer.Write(Area.Y);
			writer.Write(Area.Width);
			writer.Write(Area.Height);
			writer.Write(Arena.X);
			writer.Write(Arena.Y);
			writer.Write(Arena.Width);
			writer.Write(Arena.Height);
			writer.Write(Gate.X);
			writer.Write(Gate.Y);
		}

		public override void NetReceive(BinaryReader reader) {
			int x = reader.ReadInt32(), y = reader.ReadInt32(), w = reader.ReadInt32(), h = reader.ReadInt32();
			int ax = reader.ReadInt32(), ay = reader.ReadInt32(), aw = reader.ReadInt32(), ah = reader.ReadInt32();
			int gx = reader.ReadInt32(), gy = reader.ReadInt32();
			Area = w > 0 && h > 0 ? new Rectangle(x, y, w, h) : default;
			Arena = aw > 0 && ah > 0 ? new Rectangle(ax, ay, aw, ah) : default;
			Gate = TileSafety.InWorld(gx, gy) ? new Point(gx, gy) : default;
		}
	}

	/// <summary>A client asks the server to light a rune glyph: its number and its top-left tile (a byte and two shorts). The
	/// server lights it only if that tile is that glyph and the sender's living player stands within reach of it.</summary>
	public sealed class RuinsGlyphPacket : CogpunkPacket
	{
		public void Send(int glyph, int left, int top) {
			ModPacket packet = Begin();
			packet.Write((byte)glyph);
			packet.Write((short)left);
			packet.Write((short)top);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			int glyph = reader.ReadByte();
			int left = reader.ReadInt16(), top = reader.ReadInt16();
			if (Main.netMode != NetmodeID.Server || glyph >= FundamentalRuinsSystem.GlyphCount || sender < 0 || sender >= Main.maxPlayers) {
				return;
			}
			Player player = Main.player[sender];
			if (!player.active || player.dead || !TileSafety.TryGetTile(left, top, out Tile tile, TileSafety.EditMargin)
				|| !tile.HasTile || tile.TileType != ModContent.TileType<FundamentalGlyphTile>()
				|| FundamentalGlyphTile.StyleAt(left, top, out int x0, out int y0) != glyph || x0 != left || y0 != top) {
				return;
			}
			Vector2 centre = new(left * 16f + FundamentalGlyphTile.Width * 8f, top * 16f + FundamentalGlyphTile.Height * 8f);
			float reach = FundamentalGlyphTile.Reach + 64f;                     // a little slack for the lag
			if (Vector2.DistanceSquared(player.Center, centre) > reach * reach) {
				return;
			}
			FundamentalRuinsSystem.LightGlyph(glyph);
		}
	}
}
