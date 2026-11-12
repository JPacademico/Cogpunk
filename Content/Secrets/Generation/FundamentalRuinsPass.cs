using System;
using System.Collections.Generic;
using Cogpunk.Content.Secrets.Ruins.Tiles;
using Cogpunk.Content.Secrets.Ruins.Walls;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;
using L = Cogpunk.Content.Secrets.Generation.FundamentalRuinsLayout;

namespace Cogpunk.Content.Secrets.Generation
{
	/// <summary>
	/// Builds the Fundamental Ruins (user-set 2026-11-10b: "a new area called Fundamental Ruins; it should always generate
	/// replacing a random spider nest area on the world ... and a Fundamental Stone in a special room arena in the middle ...
	/// like ancient ruins"; 2026-11-11: an unbreakable arena only in the middle, darker blocks; 2026-11-11b: "increase the
	/// size of the ruins and rework its level design, it should be based on hollow knight metroidvania areas and the door to
	/// the arena is sealed shut until the player activates 3 rune glyphs on the area, placed on the dead ends"). Runs after
	/// vanilla's "Final Cleanup", when the spider nests and everything round them exist.
	/// <para>Steps:
	/// <list type="number">
	/// <item>The nests: vanilla's spider caves are cavern pockets walled with Spider Wall (decompiled <c>Spread.Spider</c>:
	/// wall 62 over 500-3500 open tiles). Their walls are found (every <see cref="ScanStep"/>th tile), each nest flood-filled
	/// once (at most <see cref="MaxNestCells"/> cells) and measured.</item>
	/// <item>The site: the footprint is the map's size (<see cref="FundamentalRuinsLayout"/>: 224 x 120 tiles), centred on a
	/// random nest, inside the caverns, clear of every protected structure and of their blocks; no nest fits: random spots in
	/// the caverns, then a sweep over them (the ruins always generate when there is room anywhere).</item>
	/// <item>The nest goes (its Spider Wall and cobwebs), and in the footprint every pot, pile, chest and liquid; then its
	/// open spaces are filled with stone (ores and the rock stay), so the map's passages are the only ways through.</item>
	/// <item>The map is carved (mirrored left to right half of the time): air with the ruins' brick wall (fluted columns in
	/// the gallery and the sanctum), stone platforms, brick ledges, water, spikes, rubble. Rock that borders a passage
	/// becomes the ruins' brick, coral on its outer layer where the noise says the sea reached it, a glowing rune brick in a
	/// vault now and then; kelp hangs from the ceilings.</item>
	/// <item><b>The arena</b>, in the middle under the gate hall: a domed hall of Ancient Brick that nothing breaks
	/// (<see cref="FundamentalArenaBrickTile"/>, its inner face set with unbreakable rune bricks), fluted pillars, two puddles,
	/// kelp, stone platforms to fight from and to climb back out, and on a rune-brick dais the third Fundamental Stone
	/// (<see cref="FundamentalStones.Ruins"/>, sealed by its shield until the area's boss falls). Its only way in is
	/// <b>the sealed gate</b> in its crown, the gate hall's floor (<see cref="FundamentalSealTile"/>): solid and unbreakable
	/// until the three rune glyphs are lit (<see cref="FundamentalRuinsSystem.LightGlyph"/>), then gone for good.</item>
	/// <item>The three rune glyphs (<see cref="FundamentalGlyphTile"/>) on the map's three dead ends, the chest (a Water Chest:
	/// vanilla's underground loot for its depth, and Rune Bricks) in the treasury; tunnels out from both entrances to the
	/// nearest caves (<see cref="TunnelMax"/> at most).</item>
	/// <item>Framed; registered (<see cref="FundamentalRuinsSystem.SetArea"/>, the gate's spot, a protected structure); the
	/// Mysterious Map points at the arena (<see cref="MapTargetSystem.SetTarget"/>).</item>
	/// </list></para>
	/// <para>D0: <see cref="SafeGenPass"/> catches any failure (world creation goes on without the ruins); every tile through
	/// <see cref="TileSafety"/> with the world's edit margin; every loop bounded by the footprint (the scan by the world, a
	/// flood fill by <see cref="MaxNestCells"/>, the sites by <see cref="Attempts"/> and the sweep's steps, a tunnel by
	/// <see cref="TunnelMax"/>); multi-tiles written whole and cleared whole-cell (no <c>KillTile</c>: no drops, no chained
	/// framing during generation); chests removed from <c>Main.chest</c> with their tiles; the chest placed by vanilla's own
	/// <c>AddBuriedChest</c> (a refused spot is logged, once). D2: the boxes and the gate's spot go to the world data.</para>
	/// </summary>
	internal sealed class FundamentalRuinsPass : SafeGenPass
	{
		// --- the nests ---
		public const int ScanStep = 3;
		public const int MinNestCells = 150;
		public const int MaxNestCells = 40000;
		public const int MaxNests = 96;
		// --- the footprint: the map's size ---
		public const int AreaWidth = L.Width * L.Cell, AreaHeight = L.Height * L.Cell;   // 224 x 120
		public const int EdgeMargin = 70, SurfaceGap = 30, HellGap = 30;
		public const int Attempts = 200, SweepStepX = 40, SweepStepY = 30;
		public const int ClearMargin = 4;
		// --- the arena (under the gate hall; the map's A block) ---
		public const int ArenaFloorRow = 89;                 // the arena floor's top row, from the footprint's top
		public const int ArenaHalf = 30;                     // interior half-width
		public const int ArenaTop = 26;                      // interior rows over the floor at the crown
		public const int ArenaSide = 12;                     // the dome's walls rise straight this high
		public const int Shell = 3, FloorDepth = 4;
		public const int DaisHalf = 4, DaisSteps = 3;        // the dais: 8 wide on top, 2 wider each step down
		public const int PuddleX = 17, PuddleWidth = 4;
		public const int RuneEvery = 5;
		public const int LowPlatformY = 7, HighPlatformY = 14;       // rows over the floor
		public const int LowPlatformFrom = 12, LowPlatformTo = 19;   // columns out from the middle, each side
		public const int HighPlatformFrom = 0, HighPlatformTo = 9;   // across the middle: the drop from the gate lands here
		public const int LadderY1 = 20, LadderHalf1 = 3;             // two more under the gate, to climb back out
		public const int LadderY2 = 25, LadderHalf2 = 2;
		public const int StonePlatformStyle = 43;            // vanilla's Stone Platform (decompiled Item 4416: tile 19, style 43)
		public static readonly int[] ColumnX = { 11, 22 };
		// --- the passages ---
		public const int ShellDepth = 2;                     // rock within this many tiles of a passage turns to brick
		public const int WaterChestStyle = 17;               // vanilla's Water Chest (decompiled Item 1298: tile 21, style 17)
		public const int RuneBricksMin = 10, RuneBricksMax = 20;
		public const int TunnelMax = 40, TunnelHeight = 4;
		public const int KelpMin = 2, KelpMax = 6, KelpChance = 7;   // a strand on 1 in KelpChance ceiling columns
		public const int VaultRuneEvery = 9;                 // a glowing rune brick in a vault every few tiles
		public const double CoralShare = 0.35;

		private static readonly ushort[] Forbidden = { TileID.BlueDungeonBrick, TileID.GreenDungeonBrick, TileID.PinkDungeonBrick,
			TileID.CrackedBlueDungeonBrick, TileID.CrackedGreenDungeonBrick, TileID.CrackedPinkDungeonBrick, TileID.LihzahrdBrick,
			TileID.LihzahrdAltar, TileID.Hive, TileID.ShimmerBlock };

		private readonly struct Nest
		{
			public readonly Point Start;
			public readonly Rectangle Box;
			public readonly int Cells;

			public Nest(Point start, Rectangle box, int cells) {
				Start = start;
				Box = box;
				Cells = cells;
			}
		}

		private ushort brick, coral, rune, arenaBrick, arenaRune, rubble, kelp, brickWall, columnWall;
		private bool[] anyTile;
		private bool[,] carved;
		private readonly List<Nest> nests = new();
		private readonly HashSet<int> seen = new();
		private readonly Queue<Point> queue = new();
		private Rectangle area, arena;
		private int cx, fy, half;
		private bool flip;

		public FundamentalRuinsPass() : base("Cogpunk: Fundamental Ruins", 30.0) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.FundamentalRuins");
			brick = (ushort)ModContent.TileType<FundamentalBrickTile>();
			coral = (ushort)ModContent.TileType<FundamentalCoralTile>();
			rune = (ushort)ModContent.TileType<FundamentalRuneTile>();
			arenaBrick = (ushort)ModContent.TileType<FundamentalArenaBrickTile>();
			arenaRune = (ushort)ModContent.TileType<FundamentalArenaRuneTile>();
			rubble = (ushort)ModContent.TileType<FundamentalRubbleTile>();
			kelp = (ushort)ModContent.TileType<FundamentalKelpTile>();
			brickWall = (ushort)ModContent.WallType<FundamentalBrickWallTile>();
			columnWall = (ushort)ModContent.WallType<FundamentalColumnWallTile>();
			anyTile = new bool[TileLoader.TileCount];
			Array.Fill(anyTile, true);                           // CanPlace then checks the protected structures only
			carved = new bool[AreaWidth, AreaHeight];
			nests.Clear();
			seen.Clear();
			queue.Clear();

			FindNests();
			progress.Set(0.3);
			if (!ChooseSite(out Nest? chosen)) {
				SafeLog.Warn("Ruins.NoSite", "Fundamental Ruins skipped: no room for them in the caverns ({0} nests).", nests.Count);
				return;
			}
			if (chosen.HasValue) {
				ClearNest(chosen.Value.Start);
			}
			ClearFootprint();
			FillFootprint();
			progress.Set(0.5);
			flip = WorldGen.genRand.NextBool();
			cx = area.X + AreaWidth / 2;
			fy = area.Y + ArenaFloorRow;
			half = ArenaHalf;
			CarveLayout();
			BuildShells();
			BuildArena();
			Furnish();
			progress.Set(0.8);
			WorldGen.RangeFrame(Math.Max(TileSafety.EditMargin, area.Left - TunnelMax - 2), Math.Max(TileSafety.EditMargin, area.Top - 2),
				Math.Min(Main.maxTilesX - TileSafety.EditMargin - 1, area.Right + TunnelMax + 2),
				Math.Min(Main.maxTilesY - TileSafety.EditMargin - 1, area.Bottom + 2));
			FundamentalRuinsSystem.SetArea(area, arena);
			MapTargetSystem.SetTarget(new Point(cx, fy - 8));
			GenVars.structures?.AddProtectedStructure(area);
			SafeLog.Info("WorldGen.Ruins", $"Fundamental Ruins: {area.Width}x{area.Height} at ({area.X}, {area.Y}){(flip ? ", mirrored" : "")}, the arena's floor at row {fy}, the gate at ({FundamentalRuinsSystem.Gate.X}, {FundamentalRuinsSystem.Gate.Y}), over {(chosen.HasValue ? "a spider nest of " + chosen.Value.Cells + " cells" : "no nest (fallback)")}.");
			nests.Clear();
			seen.Clear();
			carved = null;
		}

		// --- the nests ---------------------------------------------------------------------------------------------------

		private static int Key(int x, int y) => x * Main.maxTilesY + y;

		/// <summary>Every spider nest in the caverns: sampled every <see cref="ScanStep"/>th tile, each flood-filled once.</summary>
		private void FindNests() {
			int top = (int)Main.worldSurface, bottom = Main.maxTilesY - 200;
			for (int x = EdgeMargin; x < Main.maxTilesX - EdgeMargin && nests.Count < MaxNests; x += ScanStep) {
				for (int y = top; y < bottom && nests.Count < MaxNests; y += ScanStep) {
					if (!TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin) || tile.WallType != WallID.SpiderUnsafe || seen.Contains(Key(x, y))) {
						continue;
					}
					int cells = Flood(new Point(x, y), false, out Rectangle box);
					if (cells >= MinNestCells) {
						nests.Add(new Nest(new Point(x, y), box, cells));
					}
				}
			}
		}

		/// <summary>Flood fill over Spider Wall from <paramref name="start"/> (4-neighbours, at most <see cref="MaxNestCells"/>),
		/// marking it seen; with <paramref name="clear"/> its walls and cobwebs go. Returns the cells and their box.</summary>
		private int Flood(Point start, bool clear, out Rectangle box) {
			queue.Clear();
			queue.Enqueue(start);
			seen.Add(Key(start.X, start.Y));
			int cells = 0, x0 = start.X, x1 = start.X, y0 = start.Y, y1 = start.Y;
			while (queue.Count > 0 && cells < MaxNestCells) {
				Point p = queue.Dequeue();
				if (!TileSafety.TryGetTile(p.X, p.Y, out Tile tile, TileSafety.EditMargin) || tile.WallType != WallID.SpiderUnsafe) {
					continue;
				}
				cells++;
				x0 = Math.Min(x0, p.X);
				x1 = Math.Max(x1, p.X);
				y0 = Math.Min(y0, p.Y);
				y1 = Math.Max(y1, p.Y);
				if (clear) {
					tile.WallType = WallID.None;
					if (tile.HasTile && tile.TileType == TileID.Cobweb) {
						tile.HasTile = false;
					}
				}
				for (int k = 0; k < 4; k++) {
					int nx = p.X + (k == 0 ? 1 : k == 1 ? -1 : 0), ny = p.Y + (k == 2 ? 1 : k == 3 ? -1 : 0);
					int key = Key(nx, ny);
					if (TileSafety.InWorld(nx, ny, TileSafety.EditMargin) && (clear || !seen.Contains(key))) {
						if (!clear) {
							seen.Add(key);
						}
						if (Main.tile[nx, ny].WallType == WallID.SpiderUnsafe) {
							queue.Enqueue(new Point(nx, ny));
						}
					}
				}
			}
			box = new Rectangle(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
			return cells;
		}

		private void ClearNest(Point start) {
			Flood(start, true, out _);
			queue.Clear();
		}

		// --- the site -------------------------------------------------------------------------------------------------------

		/// <summary>A random nest first (Fisher-Yates with the world's seed); then random spots in the caverns; then a sweep
		/// over them in <see cref="SweepStepX"/> x <see cref="SweepStepY"/> steps (bounded by the world).</summary>
		private bool ChooseSite(out Nest? chosen) {
			chosen = null;
			for (int n = nests.Count - 1; n > 0; n--) {
				int k = WorldGen.genRand.Next(n + 1);
				(nests[n], nests[k]) = (nests[k], nests[n]);
			}
			foreach (Nest nest in nests) {
				if (TryFootprint(nest.Box.Center.X, nest.Box.Center.Y)) {
					chosen = nest;
					return true;
				}
			}
			int minX = EdgeMargin + AreaWidth / 2, maxX = Main.maxTilesX - EdgeMargin - AreaWidth / 2;
			int minY = (int)Main.rockLayer, maxY = Main.UnderworldLayer - HellGap - AreaHeight / 2;
			if (maxX <= minX || maxY <= minY) {
				return false;
			}
			for (int attempt = 0; attempt < Attempts; attempt++) {
				if (TryFootprint(WorldGen.genRand.Next(minX, maxX), WorldGen.genRand.Next(minY, maxY))) {
					return true;
				}
			}
			for (int x = minX; x < maxX; x += SweepStepX) {
				for (int y = minY; y < maxY; y += SweepStepY) {
					if (TryFootprint(x, y)) {
						return true;
					}
				}
			}
			return false;
		}

		/// <summary>The footprint centred on (<paramref name="x"/>, <paramref name="y"/>), clamped into the caverns; true (and
		/// kept) when it is clear of protected structures and their blocks.</summary>
		private bool TryFootprint(int x, int y) {
			int w = AreaWidth, h = AreaHeight;
			int minX = EdgeMargin, maxX = Main.maxTilesX - EdgeMargin - w;
			int minY = (int)Main.worldSurface + SurfaceGap, maxY = Main.UnderworldLayer - HellGap - h;
			if (maxX < minX || maxY < minY) {
				return false;
			}
			Rectangle box = new(Math.Clamp(x - w / 2, minX, maxX), Math.Clamp(y - h / 2, minY, maxY), w, h);
			if (GenVars.structures != null && !GenVars.structures.CanPlace(box, anyTile, ClearMargin)) {
				return false;
			}
			for (int i = box.Left; i < box.Right; i++) {
				for (int j = box.Top; j < box.Bottom; j++) {
					if (!TileSafety.TryGetTile(i, j, out Tile tile, TileSafety.EditMargin)) {
						return false;
					}
					if (tile.LiquidAmount > 0 && tile.LiquidType == LiquidID.Shimmer) {
						return false;
					}
					if (tile.HasTile && Array.IndexOf(Forbidden, tile.TileType) >= 0) {
						return false;
					}
				}
			}
			area = box;
			return true;
		}

		/// <summary>Every chest, pot, pile and liquid in the footprint (and a little round it, for the objects) goes.</summary>
		private void ClearFootprint() {
			Rectangle outer = area;
			outer.Inflate(ClearMargin, ClearMargin);
			for (int c = 0; c < Main.maxChests; c++) {
				Chest chest = Main.chest[c];
				if (chest == null || !outer.Contains(chest.x, chest.y)) {
					continue;
				}
				for (int dx = 0; dx < 2; dx++) {
					for (int dy = 0; dy < 2; dy++) {
						if (TileSafety.TryGetTile(chest.x + dx, chest.y + dy, out Tile t, TileSafety.EditMargin)) {
							t.HasTile = false;
						}
					}
				}
				Main.chest[c] = null;
			}
			for (int i = outer.Left; i < outer.Right; i++) {
				for (int j = outer.Top; j < outer.Bottom; j++) {
					if (!TileSafety.TryGetTile(i, j, out Tile t, TileSafety.EditMargin)) {
						continue;
					}
					if (t.HasTile && (Main.tileFrameImportant[t.TileType] || t.TileType == TileID.Cobweb)) {
						t.HasTile = false;                            // whole cell: no KillTile, no drops (D0)
					}
					if (area.Contains(i, j)) {
						t.LiquidAmount = 0;
						if (t.WallType == WallID.SpiderUnsafe) {
							t.WallType = WallID.None;
						}
					}
				}
			}
		}

		/// <summary>The footprint's open spaces filled with stone (its ores and rock stay): the map's passages are carved into
		/// solid ground, so no cave of the old nest opens a way round a collapse or into the arena.</summary>
		private void FillFootprint() {
			for (int i = area.Left; i < area.Right; i++) {
				for (int j = area.Top; j < area.Bottom; j++) {
					if (TileSafety.TryGetTile(i, j, out Tile t, TileSafety.EditMargin) && !t.HasTile) {
						Solid(i, j, TileID.Stone);
					}
				}
			}
		}

		// --- cells ----------------------------------------------------------------------------------------------------------

		private static void Solid(int x, int y, ushort type) {
			if (!TileSafety.TryGetTile(x, y, out Tile t, TileSafety.EditMargin)) {
				return;
			}
			t.HasTile = true;
			t.TileType = type;
			t.Slope = SlopeType.Solid;
			t.IsHalfBlock = false;
			t.IsActuated = false;
			t.LiquidAmount = 0;
		}

		private static void Air(int x, int y, ushort wall) {
			if (!TileSafety.TryGetTile(x, y, out Tile t, TileSafety.EditMargin)) {
				return;
			}
			t.HasTile = false;
			t.LiquidAmount = 0;
			t.WallType = wall;
		}

		private static void Water(int x, int y, ushort wall) {
			if (!TileSafety.TryGetTile(x, y, out Tile t, TileSafety.EditMargin)) {
				return;
			}
			t.HasTile = false;
			t.WallType = wall;
			t.LiquidType = LiquidID.Water;
			t.LiquidAmount = byte.MaxValue;
		}

		private static void Wall(int x, int y, ushort wall) {
			if (TileSafety.TryGetTile(x, y, out Tile t, TileSafety.EditMargin)) {
				t.WallType = wall;
			}
		}

		private static bool IsAir(int x, int y) => TileSafety.TryGetTile(x, y, out Tile t, TileSafety.EditMargin) && !t.HasTile;

		private bool IsArena(int x, int y) => TileSafety.TryGetTile(x, y, out Tile t, TileSafety.EditMargin) && t.HasTile
			&& (t.TileType == arenaBrick || t.TileType == arenaRune);

		private void Platform(int x, int y) {
			if (!TileSafety.TryGetTile(x, y, out Tile t, TileSafety.EditMargin)) {
				return;
			}
			Solid(x, y, TileID.Platforms);
			t.TileFrameX = 0;
			t.TileFrameY = (short)(StonePlatformStyle * 18);
		}

		/// <summary>Smooth noise in 0..1 from the world's seed (coral patches): a hash on a 4-tile lattice, blended.</summary>
		private static double Noise(int x, int y) {
			static double Hash(int a, int b) => (((a * 73856093) ^ (b * 19349663) ^ (WorldGen._genRandSeed * 83492791)) & 0x7FFFFFFF) % 1000 / 1000.0;
			int gx = (int)Math.Floor(x / 4.0), gy = (int)Math.Floor(y / 4.0);
			double fx = x / 4.0 - gx, fy = y / 4.0 - gy;
			double a = Hash(gx, gy), b = Hash(gx + 1, gy), c = Hash(gx, gy + 1), d = Hash(gx + 1, gy + 1);
			return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy;
		}

		/// <summary>The map's character for the cell drawn at (<paramref name="col"/>, <paramref name="row"/>) (mirrored when
		/// <see cref="flip"/>); rock outside the map.</summary>
		private char At(int col, int row) {
			if (row < 0 || row >= L.Height || col < 0 || col >= L.Width) {
				return '#';
			}
			string line = L.Rows[row];
			int c = flip ? L.Width - 1 - col : col;
			return c < line.Length ? line[c] : '#';
		}

		// --- the map ----------------------------------------------------------------------------------------------------------

		/// <summary>Every cell of the map into tiles (rock and the arena's block are left as they are).</summary>
		private void CarveLayout() {
			for (int row = 0; row < L.Height; row++) {
				for (int col = 0; col < L.Width; col++) {
					char ch = At(col, row);
					if (ch == '#' || ch == 'A') {
						continue;
					}
					int x0 = area.X + col * L.Cell, y0 = area.Y + row * L.Cell;
					for (int dy = 0; dy < L.Cell; dy++) {
						for (int dx = 0; dx < L.Cell; dx++) {
							int x = x0 + dx, y = y0 + dy;
							carved[x - area.X, y - area.Y] = true;
							bool topRow = dy == 0, bottomRow = dy == L.Cell - 1;
							switch (ch) {
								case ',':
									Air(x, y, columnWall);
									break;
								case '=':
									Air(x, y, brickWall);
									if (topRow) {
										Platform(x, y);
									}
									break;
								case '-':
									Air(x, y, brickWall);
									if (topRow) {
										Solid(x, y, brick);
									}
									break;
								case '~':
									Water(x, y, brickWall);
									break;
								case '^':
									Air(x, y, brickWall);
									if (bottomRow) {
										Solid(x, y, TileID.Spikes);
									}
									break;
								case 'r':
									Solid(x, y, rubble);
									Wall(x, y, brickWall);
									break;
								default:                                  // . E H 1 2 3 c: air
									Air(x, y, brickWall);
									break;
							}
						}
					}
				}
			}
		}

		/// <summary>Rock within <see cref="ShellDepth"/> tiles of a passage (the fill's stone, or ore and rock that was there)
		/// becomes the ruins' brick (coral on its outer layer where the noise says so, a glowing rune brick over a passage now
		/// and then, in its vault). Runs before the arena is built, so the arena's own blocks are written over it.</summary>
		private void BuildShells() {
			for (int x = area.Left; x < area.Right; x++) {
				for (int y = area.Top; y < area.Bottom; y++) {
					int lx = x - area.X, ly = y - area.Y;
					if (carved[lx, ly] || !TileSafety.TryGetTile(x, y, out Tile t, TileSafety.EditMargin) || !t.HasTile
						|| !Main.tileSolid[t.TileType] || Main.tileFrameImportant[t.TileType]) {
						continue;                                     // a passage, or nothing solid to face it with
					}
					int near = Nearest(lx, ly);
					if (near > ShellDepth) {
						continue;
					}
					bool vault = ly + 1 < AreaHeight && carved[lx, ly + 1] && (lx + ly) % VaultRuneEvery == 0;
					Solid(x, y, vault ? rune : (near == ShellDepth && Noise(x, y) < CoralShare ? coral : brick));
					Wall(x, y, brickWall);
				}
			}
		}

		/// <summary>The distance (Chebyshev, tiles) from a footprint tile to the nearest carved one, or ShellDepth + 1.</summary>
		private int Nearest(int lx, int ly) {
			int best = ShellDepth + 1;
			for (int oy = -ShellDepth; oy <= ShellDepth; oy++) {
				for (int ox = -ShellDepth; ox <= ShellDepth; ox++) {
					int x = lx + ox, y = ly + oy;
					if (x < 0 || y < 0 || x >= AreaWidth || y >= AreaHeight || !carved[x, y]) {
						continue;
					}
					best = Math.Min(best, Math.Max(Math.Abs(ox), Math.Abs(oy)));
				}
			}
			return best;
		}

		/// <summary>The glyphs, the chest, kelp from the ceilings and the tunnels out of both entrances.</summary>
		private void Furnish() {
			int leftFloor = -1, rightFloor = -1;
			for (int row = 0; row < L.Height; row++) {
				for (int col = 0; col < L.Width; col++) {
					char ch = At(col, row);
					int x0 = area.X + col * L.Cell, y0 = area.Y + row * L.Cell;
					if (ch >= '1' && ch <= '3') {
						int style = ch - '1';
						if (!FundamentalGlyphTile.TryPlace(style, x0, y0 + L.Cell)) {
							SafeLog.Warn("Ruins.NoGlyph", "Fundamental Ruins: glyph {0} didn't fit at ({1}).", style + 1, x0 + ", " + y0);
						}
					}
					else if (ch == 'c') {
						PlaceChest(x0, y0 + L.Cell - 1);
					}
					else if (ch == 'E') {
						if (col == 0) {
							leftFloor = Math.Max(leftFloor, y0 + L.Cell);
						}
						else if (col == L.Width - 1) {
							rightFloor = Math.Max(rightFloor, y0 + L.Cell);
						}
					}
				}
			}
			for (int x = area.Left + 1; x < area.Right - 1; x++) {    // kelp from the ceilings
				for (int y = area.Top + 1; y < area.Bottom - 4; y++) {
					if (!carved[x - area.X, y - area.Y] || IsArena(x, y - 1) || !IsAir(x, y) || IsAir(x, y - 1)
						|| WorldGen.genRand.Next(KelpChance) != 0) {
						continue;
					}
					Kelp(x, y, WorldGen.genRand.Next(KelpMin, KelpMax + 1));
				}
			}
			if (leftFloor >= 0) {
				Tunnel(area.Left - 1, -1, leftFloor);
			}
			if (rightFloor >= 0) {
				Tunnel(area.Right, 1, rightFloor);
			}
		}

		// --- the arena ------------------------------------------------------------------------------------------------------

		/// <summary>The arena's interior height over its floor in column offset <paramref name="dx"/> (0 outside it).</summary>
		private int Inside(int dx) {
			double u = (dx + 0.5) / (half + 0.5);
			if (Math.Abs(u) > 1.0) {
				return 0;
			}
			return Math.Max(ArenaSide, (int)Math.Round(ArenaTop * Math.Sqrt(1.0 - u * u)));
		}

		private bool Interior(int dx, int dy) => dy >= 1 && dy <= Inside(dx);

		private void BuildArena() {
			int reach = half + Shell;
			for (int dx = -reach; dx < reach; dx++) {
				for (int dy = 1 - FloorDepth; dy <= ArenaTop + Shell; dy++) {
					int x = cx + dx, y = fy - dy;
					if (Interior(dx, dy)) {
						Air(x, y, brickWall);
						continue;
					}
					bool near = dy <= 0 && Math.Abs(dx + 0.5) <= reach;
					for (int ox = -Shell; ox <= Shell && !near; ox++) {
						for (int oy = -Shell; oy <= Shell && !near; oy++) {
							near = Interior(dx + ox, dy + oy);
						}
					}
					if (!near) {
						continue;
					}
					bool face = Interior(dx + 1, dy) || Interior(dx - 1, dy) || Interior(dx, dy + 1) || Interior(dx, dy - 1);
					Solid(x, y, face && dy >= 2 && (dx + dy) % RuneEvery == 0 ? arenaRune : arenaBrick);
				}
			}
			arena = new Rectangle(cx - reach, fy - ArenaTop - Shell, 2 * reach, ArenaTop + Shell + FloorDepth);
			foreach (int c in ColumnX) {                          // fluted pillars behind
				if (c >= half - 1) {
					continue;
				}
				for (int dy = 1; dy <= Inside(c); dy++) {
					foreach (int dx in new[] { c - 1, c, -c, -c - 1 }) {
						if (Interior(dx, dy)) {
							Wall(cx + dx, fy - dy, columnWall);
						}
					}
				}
			}
			foreach (int side in new[] { 1, -1 }) {               // two puddles sunk in the floor
				int start = side > 0 ? PuddleX - PuddleWidth / 2 : -PuddleX - PuddleWidth / 2;
				for (int k = 0; k < PuddleWidth && Math.Abs(start + k) < half - 1; k++) {
					Water(cx + start + k, fy, brickWall);
				}
			}
			for (int step = 1; step <= DaisSteps; step++) {       // the dais: unbreakable rune brick steps
				int w = DaisHalf + (DaisSteps - step) * 2;
				for (int dx = -w; dx < w; dx++) {
					Solid(cx + dx, fy - step, arenaRune);
				}
			}
			if (!FundamentalStones.TryPlace(FundamentalStones.Ruins, cx - 2, fy - DaisSteps)) {
				SafeLog.Warn("Ruins.NoStone", "Fundamental Ruins: the stone didn't fit on the dais at ({0}, {1}).", cx - 2, fy - DaisSteps);
			}
			// the gate: the crown's three shell rows over its middle, the gate hall's floor
			int gateLeft = cx - FundamentalSealTile.Width / 2, gateTop = fy - ArenaTop - Shell;
			FundamentalSealTile.Place(gateLeft, gateTop);
			FundamentalRuinsSystem.SetGate(new Point(gateLeft, gateTop));
			Platforms(LowPlatformY, LowPlatformFrom, Math.Min(LowPlatformTo, half - 3));     // to fight from: low out wide, high in close
			Platforms(HighPlatformY, HighPlatformFrom, HighPlatformTo);
			Platforms(LadderY1, 0, LadderHalf1);                  // and up under the gate, to climb back out of it
			Platforms(LadderY2, 0, LadderHalf2);
			for (int dx = -half + 2; dx < half - 2; dx += WorldGen.genRand.Next(3, 7)) {   // kelp from the vault, clear of the dais and the gate
				if (Math.Abs(dx + 0.5) >= 10) {
					Kelp(cx + dx, fy - Inside(dx), WorldGen.genRand.Next(KelpMin, KelpMax + 1));
				}
			}
		}

		/// <summary>A pair of vanilla stone platforms <paramref name="dy"/> rows over the floor, from <paramref name="from"/> to
		/// <paramref name="to"/> columns out each side (a platform frames itself; its style is its frame row).</summary>
		private void Platforms(int dy, int from, int to) {
			for (int k = from; k <= to; k++) {
				foreach (int dx in new[] { k - 1, -k }) {
					if (!Interior(dx, dy) || !TileSafety.TryGetTile(cx + dx, fy - dy, out Tile t, TileSafety.EditMargin)) {
						continue;
					}
					Platform(cx + dx, fy - dy);
				}
			}
		}

		/// <summary>A strand of kelp down from the ceiling over (<paramref name="x"/>, <paramref name="y"/>) (the highest air cell
		/// under a solid one), <paramref name="length"/> long at most, never down to the floor.</summary>
		private void Kelp(int x, int y, int length) {
			if (!TileSafety.TryGetTile(x, y - 1, out Tile above, TileSafety.EditMargin) || !above.HasTile || !Main.tileSolid[above.TileType]
				|| Main.tileSolidTop[above.TileType]) {
				return;
			}
			for (int k = 0; k < length; k++) {
				if (!IsAir(x, y + k) || !IsAir(x, y + k + 3)) {
					return;                                         // keep three rows clear over whatever is below
				}
				if (TileSafety.TryGetTile(x, y + k, out Tile t, TileSafety.EditMargin) && t.LiquidAmount == 0) {
					t.HasTile = true;
					t.TileType = kelp;
					t.TileFrameX = (short)(x % 3 * 18);
					t.TileFrameY = 0;
				}
			}
		}

		// --- the chest and the tunnels ---------------------------------------------------------------------------------------

		/// <summary>The treasury's Water Chest, its bottom-left tile at (<paramref name="x"/>, <paramref name="y"/>) on the floor
		/// under it: vanilla's own underground loot for its depth (<c>WorldGen.AddBuriedChest</c>) and a stack of Rune
		/// Bricks.</summary>
		private void PlaceChest(int x, int y) {
			// AddBuriedChest(i, j) searches down from j at column i for the floor and places the chest at (i - 1, floor - 1)
			if (!WorldGen.AddBuriedChest(x + 1, y - 1, 0, false, WaterChestStyle)) {
				SafeLog.Warn("Ruins.NoChest", "Fundamental Ruins: the chest didn't fit at ({0}, {1}).", x, y);
				return;
			}
			int index = Chest.FindChest(x, y - 1);
			if (index < 0 || index >= Main.maxChests || Main.chest[index] == null) {
				return;
			}
			Chest chest = Main.chest[index];
			for (int k = 0; k < chest.item.Length; k++) {
				chest.item[k] ??= new Item();
				if (chest.item[k].IsAir) {
					chest.item[k].SetDefaults(ModContent.ItemType<Ruins.Items.FundamentalRune>());
					chest.item[k].stack = WorldGen.genRand.Next(RuneBricksMin, RuneBricksMax + 1);
					return;
				}
			}
		}

		/// <summary>From an entrance out past the footprint (<paramref name="dir"/>), <see cref="TunnelHeight"/> tall at
		/// <paramref name="floor"/>, until it opens into a cave or <see cref="TunnelMax"/>.</summary>
		private void Tunnel(int x, int dir, int floor) {
			for (int step = 0; step < TunnelMax; step++) {
				int col = x + dir * step;
				if (!TileSafety.InWorld(col, floor, TileSafety.EditMargin + 2) || step > 2 && Opens(col, floor)) {
					return;
				}
				for (int y = floor - TunnelHeight; y < floor; y++) {
					if (TileSafety.TryGetTile(col, y, out Tile t, TileSafety.EditMargin) && t.HasTile
						&& (Main.tileFrameImportant[t.TileType] || Array.IndexOf(Forbidden, t.TileType) >= 0)) {
						return;                                     // never into a structure or an object
					}
				}
				for (int y = floor - TunnelHeight; y < floor; y++) {
					if (TileSafety.TryGetTile(col, y, out Tile t, TileSafety.EditMargin)) {
						t.HasTile = false;
					}
				}
			}
		}

		/// <summary>The column is open (a cave): three empty cells over the floor.</summary>
		private static bool Opens(int x, int floor) => IsAir(x, floor - 1) && IsAir(x, floor - 2) && IsAir(x, floor - 3);
	}
}
