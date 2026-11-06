namespace Cogpunk.Content.OldBrassTown.Generation
{
	/// <summary>One building of Old Brass Town: ASCII rows, top to bottom, all the same width; the last row is laid on the
	/// street row. Legend in <see cref="OldBrassTownBlueprints"/>.</summary>
	internal sealed class Blueprint
	{
		public readonly string Name;
		public readonly string[] Rows;

		public Blueprint(string name, string[] rows) {
			Name = name;
			Rows = rows;
		}

		public int Width => Rows.Length > 0 ? Rows[0].Length : 0;
		public int Height => Rows.Length;

		/// <summary>Non-empty and rectangular. <see cref="OldBrassTownPass"/> skips a building that fails this (D0: no row is
		/// ever indexed past its end).</summary>
		public bool IsValid() {
			if (Rows == null || Rows.Length == 0 || Rows[0] == null || Rows[0].Length == 0) {
				return false;
			}
			foreach (string row in Rows) {
				if (row == null || row.Length != Rows[0].Length) {
					return false;
				}
			}
			return true;
		}

		public char At(int x, int y) => x >= 0 && y >= 0 && y < Rows.Length && x < Rows[y].Length ? Rows[y][x] : ' ';
	}

	/// <summary>
	/// The buildings of Old Brass Town (2026-11-03), drawn as text so they are easy to read and change. Built from
	/// the town's own blocks and vanilla furniture in <see cref="OldBrassTownPass"/>; checked by
	/// <c>tools/sim/old_brass_town_sim.py</c> (equal widths, every piece of furniture inside the grid, on free cells and
	/// standing on something solid), which also renders the town for the D5 proof.
	/// <para>Legend. Blocks and air:
	/// <c>' '</c> leave the cavern as it is ·
	/// <c>.</c> interior air, Weathered Plank Wall behind ·
	/// <c>P</c> Weathered Planks · <c>B</c> Tarnished Brass Plating · <c>S</c> Brass Sandstone (blocks, plank wall behind) ·
	/// <c>W</c> window (air, Glass Wall) · <c>F</c> bars (air, Iron Fence wall) · <c>D</c> doorway (air, plank wall) ·
	/// <c>p</c> wood platform (plank wall) · <c>a</c> awning platform (cavern wall kept) · <c>I</c> Wooden Beam (cavern wall
	/// kept) · <c>w</c> water (plank wall).</para>
	/// <para>Furniture, placed after the blocks at the cell marked (vanilla <c>WorldGen.PlaceObject</c>, anchored at the
	/// tile's <c>TileObjectData</c> origin; decompiled): <c>T</c> wooden table (bottom middle of 3x2) · <c>n</c> piano
	/// (bottom middle of 3x2) · <c>o</c> bookcase (bottom middle of 3x4) · <c>k</c> keg (bottom left of 2x2) · <c>c</c> /
	/// <c>C</c> wooden chair facing left / right (bottom of 1x2) · <c>X</c> barrel (bottom left of 2x2,
	/// <c>WorldGen.PlaceChest</c>, filled with the town's loot) · <c>G</c> the bank vault's locked Brass Strongbox (bottom
	/// left of 2x2: vanilla's Gold Chest loot, the Sheriff's Revolver and a Broken Whistle; <see cref="OldBrassTownChests"/>;
	/// the column right of it needs air over a solid floor) · <c>m</c> mug (on a table or platform) · <c>L</c>
	/// chain lantern (top of 1x2, hangs from the solid block above) · <c>t</c> desert torch. The other cells of a piece
	/// of furniture are <c>.</c> (or <c>F</c>/<c>W</c>, whose wall they keep).</para>
	/// </summary>
	internal static class OldBrassTownBlueprints
	{
		public static readonly Blueprint Saloon = new(
			"Saloon",
			new[] {
				"        BBBBBBBBBB        ",
				"     BBBBBBBBBBBBBBBB     ",
				"     BBBBBBBBBBBBBBBB     ",
				" PPPPPPPPPPPPPPPPPPPPPPPP ",
				" P..L...............L...P ",
				" P.....WW..m.....WW...t.P ",
				" P.....WW........WW.....P ",
				" PX......C.T.c.o........P ",
				" PPPPPPPPPPPPPPPPPPPpppPP ",
				" P....L......L..........P ",
				"aPt....................tPa",
				" D.......m....m.m..m..ppD ",
				" D......................D ",
				" D..n..C.T.c...T..T..k..D ",
				"PPPPPPPPPPPPPPPPPPPPPPPPPP",
			});

		public static readonly Blueprint Sheriff = new(
			"Sheriff",
			new[] {
				"    PPPPPPPP    ",
				"  PPPPPPPPPPPP  ",
				" PPPPPPPPPPPPPP ",
				" P..L....PFFFFP ",
				"aP......tPFFFFP ",
				" D..m.....FFFFP ",
				" D........FFFFP ",
				" D..T.c...FXFFP ",
				"PPPPPPPPPPPPPPPP",
			});

		public static readonly Blueprint Store = new(
			"Store",
			new[] {
				"   PPPPPPPPPPPP   ",
				" BBBBBBBBBBBBBBBB ",
				" P.......L......P ",
				" Pm.m.m.....m.m.P ",
				"aPppppp....pppppPa",
				" D..WW...m..WW..D ",
				" D..WW......WW..D ",
				" D.......T...X..D ",
				"PPPPPPPPPPPPPPPPPP",
			});

		public static readonly Blueprint Bank = new(
			"Bank",
			new[] {
				"     BBBBBBBB     ",
				"   BBBBBBBBBBBB   ",
				" BBBBBBBBBBBBBBBB ",
				" B....L....BFFFFB ",
				" B.WW......BFFFFB ",
				"aB.WW......BFFtFB ",
				" D....m.....FFFFB ",
				" D..........FFFFB ",
				" D.C..T.c...FGFFB ",
				"BBBBBBBBBBBBBBBBBB",
			});

		public static readonly Blueprint WaterTower = new(
			"WaterTower",
			new[] {
				"   PPPP   ",
				" PPPPPPPP ",
				" PwwwwwwP ",
				" PwwwwwwP ",
				" PwwwwwwP ",
				" PwwwwwwP ",
				" PwwwwwwP ",
				" PPPPPPPP ",
				"  I    I  ",
				"  I    I  ",
				"  I    I  ",
				"  IaaaaI  ",
				"  I    I  ",
				"  I    I  ",
				"  I    I  ",
				"          ",
			});

		/// <summary>Every building, in the order the street is laid out before <see cref="OldBrassTownPass"/> shuffles each
		/// side. Declared last: static fields initialize in textual order.</summary>
		public static readonly Blueprint[] All = { Store, Sheriff, Saloon, Bank, WaterTower };
	}
}
