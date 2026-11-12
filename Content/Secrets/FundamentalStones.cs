using Cogpunk.Content.Bosses.CursedConductor;
using Cogpunk.Content.Bosses.TarTyrant;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// The secret puzzle's five Fundamental Stones (user-set 2026-11-10: "add 5 Fundamental stones on the map ... a fixed
	/// background interactable object that always generates on 5 fixed spots on the map. For now keep one on the bottom of
	/// the tar pit and one on the westworld. These stones can be read with the right mouse click, saying random
	/// glyphs/runes"). Every stone is a style of <see cref="FundamentalStoneTile"/> with its own sigil and its own line of
	/// runes (<see cref="Inscriptions"/>).
	/// <list type="table">
	/// <item><term>0, <see cref="TarPit"/></term><description>on the floor of the Junkyard's tar pit, in its middle
	/// (<see cref="Junkyard.Generation.JunkyardPass"/>).</description></item>
	/// <item><term>1, <see cref="Westworld"/></term><description>at the west end of Westworld's street, in a niche cut into
	/// the cavern's rock (<see cref="OldBrassTown.Generation.OldBrassTownPass"/>).</description></item>
	/// <item><term>2, <see cref="Ruins"/></term><description>on the dais in the Fundamental Ruins' arena, sealed in a forcefield
	/// (2026-11-10b, <see cref="Generation.FundamentalRuinsPass"/>).</description></item>
	/// <item><term>3-4</term><description>not placed yet: the user will name their spots (their art and runes exist).</description></item>
	/// </list>
	/// <para>The runes are placeholders for the puzzle (my call: each stone's line is fixed, so readers can compare them; the
	/// user asked for "random glyphs/runes"): its own sigil, then nine runes from <c>FundamentalRunes.png</c>.</para>
	/// <para><b>Sealed</b> (user-set 2026-11-11: "add the force field to every fundamental stone; the shield disables
	/// permanently (making the stone interactable) once the boss of the area has been killed on the world"): each stone
	/// has a guardian (<see cref="GuardianDefeated"/>): the tar pit's is the Tar Tyrant (the boss fished out of that tar),
	/// Westworld's the Cursed Conductor; the ruins' and the two stones still to be placed have none yet, so they stay
	/// sealed. Until its guardian falls a stone wears a shield (drawn, not a wall: <see cref="FundamentalStoneTile"/>) and
	/// can't be read. D2: the guardians' kills are world flags (saved by name, sent with the world data when the boss
	/// dies), so every client opens the same stones at once and for good.</para>
	/// <para>D0: world generation only; every tile bounds-checked; a spot that isn't clear is refused, never forced (a solid
	/// block, a chest, any frame-important piece or the world's edge in the footprint), and only loose plants are
	/// cleared.</para>
	/// </summary>
	public static class FundamentalStones
	{
		public const int Count = 5;
		public const int TarPit = 0, Westworld = 1, Ruins = 2;

		/// <summary>True once stone <paramref name="style"/>'s guardian (its area's boss) has been killed in this world: the
		/// Tar Tyrant for the tar pit's, the Cursed Conductor for Westworld's; the others have no guardian yet.</summary>
		public static bool GuardianDefeated(int style) => style switch {
			TarPit => TarTyrantSystem.Downed,
			Westworld => CursedConductorSystem.Downed,
			_ => false,                                         // the ruins' boss and stones 4-5: to come
		};

		/// <summary>The stone wears its shield and can't be read yet.</summary>
		public static bool Sealed(int style) => !GuardianDefeated(style);
		public const int RuneCount = 16;                          // glyphs in FundamentalRunes.png: the five sigils, then runes

		/// <summary>Each stone's line, glyph indices into <c>FundamentalRunes.png</c> (its sigil first).</summary>
		public static readonly byte[][] Inscriptions = {
			new byte[] { 0, 7, 12, 5, 9, 14, 6, 11, 8, 13 },
			new byte[] { 1, 10, 5, 15, 7, 12, 9, 6, 14, 8 },
			new byte[] { 2, 13, 8, 11, 6, 15, 10, 5, 12, 9 },
			new byte[] { 3, 6, 14, 9, 12, 5, 11, 15, 7, 10 },
			new byte[] { 4, 15, 9, 7, 13, 10, 8, 12, 5, 11 },
		};

		/// <summary>World generation: stone <paramref name="style"/> with its left column at <paramref name="left"/>, standing on
		/// row <paramref name="floorY"/> (it fills the <see cref="FundamentalStoneTile.Height"/> rows above). Liquid and walls
		/// stay; loose cuttable plants in its way are cleared; anything else in its way refuses it (false).</summary>
		public static bool TryPlace(int style, int left, int floorY) {
			if (style < 0 || style >= Count) {
				return false;
			}
			int type = ModContent.TileType<FundamentalStoneTile>();
			int top = floorY - FundamentalStoneTile.Height;
			for (int x = left; x < left + FundamentalStoneTile.Width; x++) {
				for (int y = top; y < floorY; y++) {
					if (!TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin)) {
						return false;
					}
					if (tile.HasTile && !(Main.tileCut[tile.TileType] && !Main.tileFrameImportant[tile.TileType])) {
						return false;                              // a block or an object is there: not this spot
					}
				}
			}
			for (int dx = 0; dx < FundamentalStoneTile.Width; dx++) {
				for (int dy = 0; dy < FundamentalStoneTile.Height; dy++) {
					Tile tile = Main.tile[left + dx, top + dy];
					tile.ClearTile();
					tile.HasTile = true;
					tile.TileType = (ushort)type;
					tile.TileFrameX = (short)(style * FundamentalStoneTile.StyleWidth + dx * 18);
					tile.TileFrameY = (short)(dy * 18);
				}
			}
			return true;
		}
	}
}
