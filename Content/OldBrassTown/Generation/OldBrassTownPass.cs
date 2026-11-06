using System;
using System.Collections.Generic;
using Cogpunk.Content.Junkyard;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Content.OldBrassTown.Tiles;
using Cogpunk.Content.OldBrassTown.Walls;
using Cogpunk.Content.OldBrassTown.Weapons;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.OldBrassTown.Generation
{
	/// <summary>
	/// Builds Old Brass Town (user-set 2026-11-03): a cavern in the middle of the underground desert holding an abandoned
	/// old-west street, like Calamity's Sunken Sea is placed there. Runs late (after vanilla's "Micro Biomes"), so the
	/// desert hive and everything vanilla puts in it already exist.
	/// <para>Steps:
	/// <list type="number">
	/// <item>Size and place: <see cref="WidthFraction"/> of the hive's width (vanilla <c>GenVars.UndergroundDesertHiveLocation</c>,
	/// decompiled <c>DesertBiome.ExportDescriptionToEngine</c>; 320 tiles wide on a small world, 640 on a large one),
	/// clamped to <see cref="MinWidth"/>-<see cref="MaxWidth"/>, centred <see cref="CentreDepth"/> down the hive. Up to
	/// <see cref="PlacementAttempts"/> nearby centres are tried until the footprint holds no dungeon, temple or Shimmer
	/// and stays clear of the Junkyard; otherwise the town is skipped (logged once).</item>
	/// <item>Carve: a cavern with a low superellipse roof (<see cref="CeilingExponent"/>; a ragged ceiling with
	/// stalactites) over an elliptical bowl cut flat at the street (<see cref="FloorLevel"/>), wrapped in at least
	/// <see cref="ShellThickness"/> tiles of Brass Sandstone whose outer edge is roughened into the desert, with veins of
	/// Tarnished Brass Ore, all backed by Brass Sandstone Wall. tools/sim/old_brass_town_sim.py --sweep checks that every
	/// building fits under the roof on every world size.</item>
	/// <item>Build: the buildings of <see cref="OldBrassTownBlueprints"/> along the street (the saloon in the middle, each
	/// side shuffled, the whole row mirrored half the time), lamp posts in the gaps, then the furniture and the loot: the
	/// bank vault's locked Brass Strongbox and the buried cache with its key (<see cref="OldBrassTownChests"/>, user-set
	/// 2026-11-04).</item>
	/// <item>Connect: a mine tunnel from each end of the cavern out into the hive's caves.</item>
	/// </list></para>
	/// <para>D0: every loop is bounded by the cavern's size (or a fixed attempt count); every tile goes through
	/// <see cref="TileSafety"/> and the footprint keeps <see cref="WorldMargin"/> from the world's edge; chests and signs
	/// the cavern overwrites are unregistered first; the footprint is framed afterwards, which also removes the remains
	/// of furniture the edge cut through (vanilla <c>Item.NewItem</c> returns early while <c>WorldGen.gen</c> is set, so
	/// nothing drops). A failure is caught by <see cref="SafeGenPass"/> and world creation continues.</para>
	/// </summary>
	internal sealed class OldBrassTownPass : SafeGenPass
	{
		// --- size and place (tiles) ---
		public const double WidthFraction = 0.55;      // of the desert hive's width
		public const int MinWidth = 110;
		public const int MaxWidth = 220;
		public const double HeightRatio = 0.24;        // of the cavern's width
		public const double CeilingExponent = 2.6;     // the roof is a superellipse: flatter than the bowl, headroom to the ends
		public const int MinHeight = 38;
		public const int MaxHeight = 62;
		public const double CentreDepth = 0.45;        // the cavern's centre, down the hive from its top
		public const double FloorLevel = 0.4;          // the street: this fraction of the half-height below the centre
		public const int ShellThickness = 6;           // Brass Sandstone around the cavern, at least
		public const int ShellNoise = 3;
		public const int CeilingNoise = 4;             // rock hanging from the ceiling, at most
		public const int NoiseStep = 5;                // columns between noise control points
		public const int RoughSpacing = 5;             // one rough patch of Brass Sandstone on the shell's edge per this many columns
		public const int StalactiteSpacing = 8;        // one stalactite per this many columns of cavern
		public const int StalactiteClearance = 20;     // rows kept between a stalactite's tip and the street (the buildings' height)
		public const int MinHiveWidth = 140;
		public const int MinHiveHeight = 100;
		public const int WorldMargin = 40;
		public const int SurfaceClearance = 30;        // rows kept between the shell and the surface layer
		public const int UnderworldClearance = 40;
		public const int PlacementAttempts = 8;
		public const int ShimmerRadius = 125;          // WorldGen.ShimmerMakeBiome works within +-genRand.Next(105, 125)

		// --- the street ---
		public const int StreetMargin = 6;             // free street kept at each end
		public const int MinStreetHeadroom = 4;        // a flat column counts as street with this much air above it
		public const int MinGap = 4;
		public const int MaxGap = 9;
		public const int HeadRoom = 3;                 // air kept between a building and the ceiling
		public const int LampGap = 3;                  // a gap at least this wide gets a lamp post

		// --- tunnels and ore ---
		public const int TunnelLength = 45;
		public const int TunnelHeight = 3;
		public const int TunnelDrift = 6;              // rows a tunnel may climb from where it starts
		public const int OreVeinSpacing = 6;           // one vein per this many columns of footprint

		// --- the buried cache ---
		public const int CacheDepth = 4;               // rows of rock from the street down to the cache's pocket
		public const int CacheHeight = 3;              // the pocket: 4 wide, this tall, the chest on its floor

		// --- vanilla styles (decompiled Item.SetDefaults) ---
		private const int DesertTorchStyle = 16;       // ItemID.DesertTorch: DefaultToTorch(16)
		private const int BarrelStyle = 5;             // ItemID.Barrel: createTile 21, placeStyle 5
		private const int MugStyle = 4;                // ItemID.Mug: createTile 13, placeStyle 4
		private const int FramePad = 6;                // framed beyond the footprint: furniture the edge cut through
		private const int ChestSize = 2;

		private static readonly int[] CowboyVanity = { ItemID.CowboyHat, ItemID.CowboyJacket, ItemID.CowboyPants };

		private readonly struct Piece
		{
			public readonly char Kind;
			public readonly int X, Y;

			public Piece(char kind, int x, int y) {
				Kind = kind;
				X = x;
				Y = y;
			}
		}

		private ushort sandstone, ore, plank, plating, cavernWall, plankWall;
		private int left, right, top, bottom, cx, cy, floorY;
		private double rx, ry;
		private int[] airTop, airBottom, rockTop, rockBottom;   // per column, indexed x - left; empty when top > bottom
		private readonly List<int> cacheSpots = new();          // the street's lamp posts: where the cache may be buried
		private int vaultChest = -1;                            // the bank vault's strongbox, or -1

		public OldBrassTownPass() : base("Cogpunk: Old Brass Town", 30.0) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.OldBrassTown");
			sandstone = (ushort)ModContent.TileType<BrassSandstoneTile>();
			ore = (ushort)ModContent.TileType<TarnishedBrassOreTile>();
			plank = (ushort)ModContent.TileType<WeatheredPlankTile>();
			plating = (ushort)ModContent.TileType<TarnishedBrassPlatingTile>();
			cavernWall = (ushort)ModContent.WallType<BrassSandstoneWallTile>();
			plankWall = (ushort)ModContent.WallType<WeatheredPlankWallTile>();

			Rectangle hive = GenVars.UndergroundDesertHiveLocation;
			if (hive.Width <= 0 || hive.Height <= 0) {
				hive = GenVars.UndergroundDesertLocation;
			}
			if (hive.Width < MinHiveWidth || hive.Height < MinHiveHeight) {
				SafeLog.Warn("OldBrassTown.NoDesert", "Old Brass Town skipped: the underground desert is too small ({0} x {1} tiles).", hive.Width, hive.Height);
				return;
			}
			int width = Math.Clamp((int)Math.Round(hive.Width * WidthFraction), MinWidth, MaxWidth);
			int height = Math.Clamp((int)Math.Round(width * HeightRatio), MinHeight, MaxHeight);
			rx = width / 2.0;
			ry = height / 2.0;
			if (!ChooseCentre(hive)) {
				SafeLog.Warn("OldBrassTown.NoSite", "Old Brass Town skipped: no clear site in the underground desert near x={0}.", hive.Center.X);
				return;
			}
			cacheSpots.Clear();                                 // a pass is reused for every world made this session
			vaultChest = -1;
			BuildProfile();
			progress.Set(0.15);

			RemoveChestsAndSigns();
			Carve();
			RoughenShell();
			HangStalactites();
			PlaceOre();
			progress.Set(0.4);

			List<Piece> furniture = new();
			int built = BuildStreet(furniture);
			progress.Set(0.6);
			PlaceFurniture(furniture);
			BuryCache();
			DigTunnel(-1);
			DigTunnel(1);
			progress.Set(0.85);

			WorldGen.RangeFrame(Math.Max(TileSafety.EditMargin, left - TunnelLength - FramePad), Math.Max(TileSafety.EditMargin, top - FramePad),
				Math.Min(Main.maxTilesX - TileSafety.EditMargin - 1, right + TunnelLength + FramePad), Math.Min(Main.maxTilesY - TileSafety.EditMargin - 1, bottom + FramePad));
			Rectangle area = new(left, top, right - left + 1, bottom - top + 1);
			OldBrassTownSystem.SetArea(area);
			GenVars.structures?.AddProtectedStructure(area);
			SafeLog.Info("WorldGen.OldBrassTown", $"Old Brass Town: {built} buildings in a {width}x{height} cavern at ({cx}, {cy}).");
			airTop = airBottom = rockTop = rockBottom = null;
			cacheSpots.Clear();
		}

		// --- site -------------------------------------------------------------------------------------------------------

		private bool ChooseCentre(Rectangle hive) {
			int margin = (int)Math.Ceiling(ry) + ShellThickness + ShellNoise;
			int minY = (int)Main.worldSurface + margin + SurfaceClearance;
			int maxY = Main.UnderworldLayer - margin - UnderworldClearance;
			if (minY > maxY) {
				return false;
			}
			int baseX = hive.Center.X;
			int baseY = hive.Y + (int)(hive.Height * CentreDepth);
			for (int attempt = 0; attempt < PlacementAttempts; attempt++) {
				int x = baseX, y = baseY;
				if (attempt > 0) {
					x += WorldGen.genRand.Next(-hive.Width / 6, hive.Width / 6 + 1);
					y += WorldGen.genRand.Next(-hive.Height / 8, hive.Height / 8 + 1);
				}
				y = Math.Clamp(y, minY, maxY);
				Rectangle outer = OuterBounds(x, y);
				if (outer.Left < WorldMargin || outer.Right > Main.maxTilesX - WorldMargin || outer.Top < WorldMargin || outer.Bottom > Main.maxTilesY - WorldMargin) {
					continue;
				}
				if (JunkyardSystem.Exists && (JunkyardSystem.SurfaceArea.Intersects(outer) || JunkyardSystem.PoolArea.Intersects(outer))) {
					continue;
				}
				if (NearShimmer(outer) || HasForbidden(outer)) {
					continue;
				}
				cx = x;
				cy = y;
				floorY = cy + (int)Math.Round(ry * FloorLevel);
				return true;
			}
			return false;
		}

		private Rectangle OuterBounds(int x, int y) {
			int hx = (int)Math.Ceiling(rx) + ShellThickness + ShellNoise + 1;
			int hy = (int)Math.Ceiling(ry) + ShellThickness + ShellNoise + 1;
			return new Rectangle(x - hx, y - hy, hx * 2 + 1, hy * 2 + 1);
		}

		private static bool NearShimmer(Rectangle outer) {
			if (GenVars.shimmerPosition.X == 0 && GenVars.shimmerPosition.Y == 0) {
				return false;
			}
			Rectangle zone = outer;
			zone.Inflate(ShimmerRadius, ShimmerRadius);
			return zone.Contains((int)GenVars.shimmerPosition.X, (int)GenVars.shimmerPosition.Y);
		}

		/// <summary>One scan of the footprint (TunnelLength wider on each side, where the tunnels may go) for what the
		/// town must never cut into.</summary>
		private static bool HasForbidden(Rectangle outer) {
			for (int x = outer.Left - TunnelLength; x < outer.Right + TunnelLength; x++) {
				for (int y = outer.Top; y < outer.Bottom; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin) && IsForbidden(tile)) {
						return true;
					}
				}
			}
			return false;
		}

		/// <summary>Dungeon or temple brick and walls, and Shimmer (the Junkyard pass's rule).</summary>
		private static bool IsForbidden(Tile tile) {
			if (tile.HasTile) {
				ushort type = tile.TileType;
				if (Main.tileDungeon[type] || type == TileID.LihzahrdBrick || type == TileID.LihzahrdAltar) {
					return true;
				}
			}
			ushort wall = tile.WallType;
			if (wall > WallID.None && wall < Main.wallDungeon.Length && (Main.wallDungeon[wall] || wall == WallID.LihzahrdBrickUnsafe)) {
				return true;
			}
			return tile.LiquidAmount > 0 && tile.LiquidType == LiquidID.Shimmer;
		}

		// --- shape --------------------------------------------------------------------------------------------------

		/// <summary>Per column: the cavern's air (a superellipse roof with a ragged ceiling over an elliptical bowl, cut flat
		/// at the street) and the rock around it (the same shape, larger and ragged).</summary>
		private void BuildProfile() {
			Rectangle outer = OuterBounds(cx, cy);
			left = outer.Left;
			right = outer.Right - 1;
			int count = right - left + 1;
			airTop = new int[count];
			airBottom = new int[count];
			rockTop = new int[count];
			rockBottom = new int[count];
			double[] shell = Noise(count, ShellNoise);
			double[] ceiling = Noise(count, CeilingNoise);
			top = int.MaxValue;
			bottom = int.MinValue;
			for (int i = 0; i < count; i++) {
				double dx = left + i - cx;
				double u = dx / rx;
				if (Math.Abs(u) < 1.0) {
					airTop[i] = (int)Math.Ceiling(cy - ry * Roof(u) + ceiling[i]);
					airBottom[i] = Math.Min(floorY - 1, (int)Math.Floor(cy + ry * Math.Sqrt(1.0 - u * u)));
				}
				else {
					airTop[i] = 1;
					airBottom[i] = 0;
				}
				double ox = rx + ShellThickness + shell[i];
				double oy = ry + ShellThickness + shell[i];
				double v = dx / ox;
				if (Math.Abs(v) < 1.0) {
					rockTop[i] = (int)Math.Floor(cy - oy * Roof(v));
					rockBottom[i] = (int)Math.Ceiling(cy + oy * Math.Sqrt(1.0 - v * v));
					top = Math.Min(top, rockTop[i]);
					bottom = Math.Max(bottom, rockBottom[i]);
				}
				else {
					rockTop[i] = 1;
					rockBottom[i] = 0;
				}
			}
		}

		/// <summary>The roof's height (0..1 of the half-height) at <paramref name="u"/> (-1..1 across): a superellipse of
		/// <see cref="CeilingExponent"/>, which stays high further out than an ellipse.</summary>
		private static double Roof(double u) => Math.Pow(1.0 - Math.Pow(Math.Abs(u), CeilingExponent), 1.0 / CeilingExponent);

		/// <summary>Smooth value noise in [0, amplitude]: random control points every <see cref="NoiseStep"/> columns,
		/// linearly interpolated.</summary>
		private static double[] Noise(int count, double amplitude) {
			int points = count / NoiseStep + 2;
			double[] control = new double[points];
			for (int k = 0; k < points; k++) {
				control[k] = WorldGen.genRand.NextDouble() * amplitude;
			}
			double[] result = new double[count];
			for (int i = 0; i < count; i++) {
				int k = i / NoiseStep;
				double f = (i % NoiseStep) / (double)NoiseStep;
				result[i] = control[k] + (control[k + 1] - control[k]) * f;
			}
			return result;
		}

		private bool InFootprint(int x, int y) {
			int i = x - left;
			return i >= 0 && i < rockTop.Length && y >= rockTop[i] && y <= rockBottom[i];
		}

		private bool IsAir(int x, int y) {
			int i = x - left;
			return i >= 0 && i < airTop.Length && y >= airTop[i] && y <= airBottom[i];
		}

		private bool IsStreet(int i) {
			return airBottom[i] == floorY - 1 && airBottom[i] - airTop[i] + 1 >= MinStreetHeadroom;
		}

		// --- carving --------------------------------------------------------------------------------------------------

		/// <summary>Unregisters every chest and sign the footprint touches and clears all four of its tiles (one may stick
		/// out of the footprint), so no chest entry is left without its tile and no half chest without its entry.</summary>
		private void RemoveChestsAndSigns() {
			for (int i = 0; i < Main.maxChests; i++) {
				Chest chest = Main.chest[i];
				if (chest != null && TouchesFootprint(chest.x, chest.y)) {
					ClearSquare(chest.x, chest.y);
					Main.chest[i] = null;
				}
			}
			for (int i = 0; i < Main.sign.Length; i++) {
				Sign sign = Main.sign[i];
				if (sign != null && TouchesFootprint(sign.x, sign.y)) {
					ClearSquare(sign.x, sign.y);
					Main.sign[i] = null;
				}
			}
		}

		private bool TouchesFootprint(int x, int y) {
			for (int dx = 0; dx < ChestSize; dx++) {
				for (int dy = 0; dy < ChestSize; dy++) {
					if (InFootprint(x + dx, y + dy)) {
						return true;
					}
				}
			}
			return false;
		}

		private static void ClearSquare(int x, int y) {
			for (int dx = 0; dx < ChestSize; dx++) {
				for (int dy = 0; dy < ChestSize; dy++) {
					if (TileSafety.TryGetTile(x + dx, y + dy, out Tile tile, TileSafety.EditMargin)) {
						tile.ClearTile();
					}
				}
			}
		}

		private void Carve() {
			for (int i = 0; i < rockTop.Length; i++) {
				int x = left + i;
				for (int y = rockTop[i]; y <= rockBottom[i]; y++) {
					if (!TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin)) {
						continue;
					}
					tile.ClearEverything();
					tile.WallType = cavernWall;
					if (y < airTop[i] || y > airBottom[i]) {
						Place(tile, sandstone);
					}
				}
			}
		}

		/// <summary>
		/// Patches of Brass Sandstone (radius 1.5-3.5) centred on the shell's outer edge, so it meets the desert in a ragged
		/// line instead of an ellipse. They only turn plain solid blocks into Brass Sandstone (never air, furniture,
		/// chests, pots or anything forbidden), so nothing outside the cleared footprint breaks.
		/// </summary>
		private void RoughenShell() {
			int patches = rockTop.Length / RoughSpacing;
			for (int p = 0; p < patches; p++) {
				int i = WorldGen.genRand.Next(rockTop.Length);
				if (rockTop[i] > rockBottom[i]) {
					continue;
				}
				int x = left + i;
				int y = WorldGen.genRand.NextBool() ? rockTop[i] : rockBottom[i];
				double radius = 1.5 + WorldGen.genRand.NextDouble() * 2.0;
				for (int dx = -4; dx <= 4; dx++) {
					for (int dy = -4; dy <= 4; dy++) {
						if (dx * dx + dy * dy > radius * radius || InFootprint(x + dx, y + dy)
							|| !TileSafety.TryGetTile(x + dx, y + dy, out Tile tile, TileSafety.EditMargin)) {
							continue;
						}
						if (tile.HasTile && Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType] && !Main.tileFrameImportant[tile.TileType]
							&& TileID.Sets.GeneralPlacementTiles[tile.TileType] && !IsForbidden(tile)) {
							tile.TileType = sandstone;
						}
					}
				}
			}
		}

		/// <summary>Tapered spikes of Brass Sandstone, 2-5 rows, hanging from the roof where it is high enough that the tip
		/// stays <see cref="StalactiteClearance"/> rows above the street (the tallest building is 16).</summary>
		private void HangStalactites() {
			int count = rockTop.Length / StalactiteSpacing;
			for (int n = 0; n < count; n++) {
				int i = WorldGen.genRand.Next(rockTop.Length);
				if (i + 1 >= airTop.Length || airTop[i] > airBottom[i] || airTop[i + 1] > airBottom[i + 1]) {
					continue;
				}
				int length = WorldGen.genRand.Next(2, 6);
				int rootY = Math.Max(airTop[i], airTop[i + 1]);
				int tipY = rootY + length - 1;
				if (tipY >= floorY - StalactiteClearance) {
					continue;
				}
				// each column grows down from its own ceiling, so neither half hangs below a gap
				FillRock(left + i, airTop[i], tipY);
				FillRock(left + i + 1, airTop[i + 1], rootY + length / 2 - 1);
			}
		}

		private void FillRock(int x, int fromY, int toY) {
			for (int y = fromY; y <= toY; y++) {
				if (TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin) && !tile.HasTile) {
					Place(tile, sandstone);
				}
			}
		}

		/// <summary>Small round veins of Tarnished Brass Ore in the cavern's own rock, never in the street's top two rows.</summary>
		private void PlaceOre() {
			int veins = Math.Max(4, rockTop.Length / OreVeinSpacing);
			for (int v = 0; v < veins; v++) {
				for (int attempt = 0; attempt < 10; attempt++) {
					int i = WorldGen.genRand.Next(rockTop.Length);
					if (rockTop[i] > rockBottom[i]) {
						continue;
					}
					int x = left + i;
					int y = WorldGen.genRand.Next(rockTop[i], rockBottom[i] + 1);
					if (IsAir(x, y)) {
						continue;
					}
					double radius = 1.2 + WorldGen.genRand.NextDouble() * 1.2;
					for (int dx = -3; dx <= 3; dx++) {
						for (int dy = -3; dy <= 3; dy++) {
							double reach = radius * (0.85 + WorldGen.genRand.NextDouble() * 0.3);
							int ox = x + dx, oy = y + dy;
							if (dx * dx + dy * dy > reach * reach || oy == floorY || oy == floorY + 1 || !InFootprint(ox, oy)
								|| !TileSafety.TryGetTile(ox, oy, out Tile tile, TileSafety.EditMargin)) {
								continue;
							}
							if (tile.HasTile && tile.TileType == sandstone) {
								tile.TileType = ore;
							}
						}
					}
					break;
				}
			}
		}

		// --- the street -------------------------------------------------------------------------------------------------

		/// <summary>Lays the buildings along the street, centred, with lamp posts in the gaps. Returns how many were built.</summary>
		private int BuildStreet(List<Piece> furniture) {
			int streetLeft = -1, streetRight = -1;
			for (int i = 0; i < airTop.Length; i++) {
				if (IsStreet(i)) {
					if (streetLeft < 0) {
						streetLeft = left + i;
					}
					streetRight = left + i;
				}
			}
			if (streetLeft < 0) {
				return 0;
			}
			int from = streetLeft + StreetMargin;
			int to = streetRight - StreetMargin;
			List<Blueprint> row = ChooseOrder();
			List<int> gaps = new();
			for (int k = 0; k < row.Count; k++) {
				gaps.Add(WorldGen.genRand.Next(MinGap, MaxGap + 1));
			}
			// Too long for this street (small worlds): drop buildings from the ends, never the saloon.
			for (int guard = 0; guard < OldBrassTownBlueprints.All.Length && row.Count > 1 && RowLength(row, gaps) > to - from + 1; guard++) {
				int drop = row[^1] != OldBrassTownBlueprints.Saloon && (guard % 2 == 0 || row[0] == OldBrassTownBlueprints.Saloon) ? row.Count - 1 : 0;
				row.RemoveAt(drop);
				gaps.RemoveAt(drop);
			}
			if (RowLength(row, gaps) > to - from + 1) {
				return 0;
			}

			int x = from + (to - from + 1 - RowLength(row, gaps)) / 2;
			AddLamp(furniture, x - 3);
			int built = 0;
			for (int k = 0; k < row.Count; k++) {
				Blueprint blueprint = row[k];
				if (!blueprint.IsValid()) {
					SafeLog.Warn("OldBrassTown.BadBlueprint:" + blueprint.Name, "Old Brass Town: blueprint '{0}' is not rectangular; skipped.", blueprint.Name);
				}
				else if (FitsUnderCeiling(blueprint, x)) {
					Build(blueprint, x, floorY - (blueprint.Height - 1), furniture);
					built++;
				}
				int gap = k < row.Count - 1 ? gaps[k] : 0;
				if (gap >= LampGap) {
					AddLamp(furniture, x + blueprint.Width + gap / 2);
				}
				x += blueprint.Width + gap;
			}
			AddLamp(furniture, x + 2);
			return built;
		}

		/// <summary>The saloon in the middle, the store and the sheriff on one side and the bank and the water tower on
		/// the other, each side in random order, the whole row mirrored half the time.</summary>
		private static List<Blueprint> ChooseOrder() {
			Blueprint a = OldBrassTownBlueprints.Store, b = OldBrassTownBlueprints.Sheriff;
			Blueprint c = OldBrassTownBlueprints.Bank, d = OldBrassTownBlueprints.WaterTower;
			if (WorldGen.genRand.NextBool()) {
				(a, b) = (b, a);
			}
			if (WorldGen.genRand.NextBool()) {
				(c, d) = (d, c);
			}
			List<Blueprint> row = new() { a, b, OldBrassTownBlueprints.Saloon, c, d };
			if (WorldGen.genRand.NextBool()) {
				row.Reverse();
			}
			return row;
		}

		private static int RowLength(List<Blueprint> row, List<int> gaps) {
			int length = 0;
			for (int k = 0; k < row.Count; k++) {
				length += row[k].Width + (k < row.Count - 1 ? gaps[k] : 0);
			}
			return length;
		}

		private void AddLamp(List<Piece> furniture, int x) {
			cacheSpots.Add(x);
			if (IsAir(x, floorY - 1)) {
				furniture.Add(new Piece('l', x, floorY - 1));
			}
		}

		/// <summary>Each column's highest block stays <see cref="HeadRoom"/> below the cavern's ceiling.</summary>
		private bool FitsUnderCeiling(Blueprint blueprint, int x0) {
			int y0 = floorY - (blueprint.Height - 1);
			for (int bx = 0; bx < blueprint.Width; bx++) {
				int i = x0 + bx - left;
				if (i < 0 || i >= airTop.Length || airTop[i] > airBottom[i]) {
					return false;
				}
				for (int by = 0; by < blueprint.Height; by++) {
					if (blueprint.At(bx, by) != ' ') {
						if (y0 + by < airTop[i] + HeadRoom) {
							return false;
						}
						break;
					}
				}
			}
			return true;
		}

		/// <summary>Writes a blueprint's blocks, walls and water (legend in <see cref="OldBrassTownBlueprints"/>) and
		/// queues its furniture.</summary>
		private void Build(Blueprint blueprint, int x0, int y0, List<Piece> furniture) {
			for (int by = 0; by < blueprint.Height; by++) {
				for (int bx = 0; bx < blueprint.Width; bx++) {
					char ch = blueprint.At(bx, by);
					int x = x0 + bx, y = y0 + by;
					if (ch == ' ' || !TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin)) {
						continue;
					}
					ushort keptWall = tile.WallType;
					tile.ClearEverything();
					switch (ch) {
						case '.':
						case 'D':
							tile.WallType = plankWall;
							break;
						case 'P':
							tile.WallType = plankWall;
							Place(tile, plank);
							break;
						case 'B':
							tile.WallType = plankWall;
							Place(tile, plating);
							break;
						case 'S':
							tile.WallType = plankWall;
							Place(tile, sandstone);
							break;
						case 'W':
							tile.WallType = WallID.Glass;
							break;
						case 'F':
							tile.WallType = WallID.IronFence;
							break;
						case 'p':
							tile.WallType = plankWall;
							PlaceFramed(tile, TileID.Platforms);
							break;
						case 'a':
							tile.WallType = keptWall;
							PlaceFramed(tile, TileID.Platforms);
							break;
						case 'I':
							tile.WallType = keptWall;
							PlaceFramed(tile, TileID.WoodenBeam);
							break;
						case 'w':
							tile.WallType = plankWall;
							tile.LiquidType = LiquidID.Water;
							tile.LiquidAmount = byte.MaxValue;
							break;
						default:
							// Furniture: air with the room's wall (iron bars when it stands among them), placed later.
							tile.WallType = blueprint.At(bx - 1, by) == 'F' || blueprint.At(bx + 1, by) == 'F' ? WallID.IronFence : plankWall;
							furniture.Add(new Piece(ch, x, y));
							break;
					}
				}
			}
		}

		private static void Place(Tile tile, ushort type) {
			tile.HasTile = true;
			tile.TileType = type;
			tile.Slope = SlopeType.Solid;
			tile.IsHalfBlock = false;
			tile.LiquidAmount = 0;
		}

		/// <summary>Platforms and beams keep their style in the frame, so it is set to style 0 (wood) here; framing fixes
		/// the rest.</summary>
		private static void PlaceFramed(Tile tile, ushort type) {
			Place(tile, type);
			tile.TileFrameX = 0;
			tile.TileFrameY = 0;
		}

		// --- furniture and loot -----------------------------------------------------------------------------------------

		/// <summary>Standing furniture first (mugs need their tables), then mugs, lanterns and torches. Vanilla checks each
		/// spot (<c>TileObject.CanPlace</c>); a piece that doesn't fit is simply left out.</summary>
		private void PlaceFurniture(List<Piece> furniture) {
			for (int stage = 0; stage < 4; stage++) {
				foreach (Piece piece in furniture) {
					if (Stage(piece.Kind) == stage && TileSafety.InWorld(piece.X, piece.Y, TileSafety.EditMargin)) {
						PlacePiece(piece);
					}
				}
			}
		}

		private static int Stage(char kind) => kind switch {
			'm' => 1,
			'L' => 2,
			't' => 3,
			_ => 0,
		};

		private void PlacePiece(Piece piece) {
			int x = piece.X, y = piece.Y;
			switch (piece.Kind) {
				case 'T':
					WorldGen.PlaceObject(x, y, TileID.Tables, mute: true);
					break;
				case 'n':
					WorldGen.PlaceObject(x, y, TileID.Pianos, mute: true);
					break;
				case 'o':
					WorldGen.PlaceObject(x, y, TileID.Bookcases, mute: true);
					break;
				case 'k':
					WorldGen.PlaceObject(x, y, TileID.Kegs, mute: true);
					break;
				case 'c':
				case 'C':
					WorldGen.PlaceObject(x, y, TileID.Chairs, mute: true, direction: piece.Kind == 'C' ? 1 : -1);
					break;
				case 'l':
					WorldGen.PlaceObject(x, y, TileID.Lampposts, mute: true);
					break;
				case 'm':
					WorldGen.PlaceObject(x, y, TileID.Bottles, mute: true, style: MugStyle);
					break;
				case 'L':
					WorldGen.PlaceObject(x, y, TileID.HangingLanterns, mute: true);
					break;
				case 't':
					WorldGen.PlaceTile(x, y, TileID.Torches, mute: true, forced: false, plr: -1, style: DesertTorchStyle);
					break;
				case 'X':
					int barrel = WorldGen.PlaceChest(x, y, TileID.Containers, false, BarrelStyle);
					if (barrel >= 0 && barrel < Main.maxChests && Main.chest[barrel] != null) {
						Fill(Main.chest[barrel]);
					}
					break;
				case 'G':
					PlaceVault(x, y);
					break;
			}
		}

		/// <summary>A barrel: Tarnished Brass Bars, Rusted Cogs, silver and healing potions, and a third of the time a piece
		/// of vanilla's cowboy vanity.</summary>
		private static void Fill(Chest chest) {
			int slot = 0;
			Add(chest, ref slot, ModContent.ItemType<TarnishedBrassBar>(), WorldGen.genRand.Next(6, 13));
			Add(chest, ref slot, ModContent.ItemType<RustedCog>(), WorldGen.genRand.Next(10, 21));
			Add(chest, ref slot, ItemID.SilverCoin, WorldGen.genRand.Next(30, 61));
			Add(chest, ref slot, ItemID.LesserHealingPotion, WorldGen.genRand.Next(3, 6));
			if (WorldGen.genRand.NextBool(3)) {
				Add(chest, ref slot, CowboyVanity[WorldGen.genRand.Next(CowboyVanity.Length)], 1);
			}
		}

		/// <summary>The bank vault (user-set 2026-11-04: "this house chest should contain normal gold underground chest loot +
		/// the Sheriff's Revolver and a Broken Whistle"): a Gold Chest with vanilla's loot and those two, turned into the
		/// locked Brass Strongbox that only the buried cache's Sheriff's Key opens.</summary>
		private void PlaceVault(int x, int y) {
			int index = OldBrassTownChests.PlaceGoldChest(x, y);
			if (index < 0) {
				SafeLog.Warn("OldBrassTown.NoVault", "Old Brass Town: the bank vault's strongbox didn't fit at ({0}, {1}); the buried cache holds its loot.", x, y);
				return;
			}
			StockVault(Main.chest[index]);
			OldBrassTownChests.SetStrongbox(index, locked: true);
			vaultChest = index;
		}

		private static void StockVault(Chest chest) {
			OldBrassTownChests.Add(chest, ModContent.ItemType<SheriffsRevolver>(), 1)?.Prefix(-1);   // a random prefix, as vanilla's chest items get
			OldBrassTownChests.Add(chest, ModContent.ItemType<BrokenWhistle>(), 1);
		}

		// --- the buried cache -------------------------------------------------------------------------------------------

		/// <summary>
		/// The buried cache (user-set 2026-11-04: "a single buried secret chest ... with normal golden underground chest
		/// loot + the Sheriff's Key"): a Gold Chest with vanilla's loot and the key, sealed in a pocket of rock
		/// <see cref="CacheDepth"/> rows under the street beneath one of the lamp posts (a random one with rock all round);
		/// two Weathered Planks in the street over it are the only hint (my call).
		/// <para>So the revolver and the whistle always stay reachable: if the bank's strongbox wasn't built, the cache holds
		/// them instead of the key; if no spot fits the cache, the strongbox is left unlocked. Both logged once.</para>
		/// </summary>
		private void BuryCache() {
			int count = cacheSpots.Count;
			int start = count > 0 ? WorldGen.genRand.Next(count) : 0;
			for (int k = 0; k < count; k++) {
				int gx = cacheSpots[(start + k) % count] - 1;   // the chest's left column: the lamp post stands over its right one
				if (!CanBury(gx)) {
					continue;
				}
				int pocketTop = floorY + CacheDepth;
				int pocketFloor = pocketTop + CacheHeight;
				SetPocket(gx, pocketTop, pocketFloor, dig: true);
				int index = OldBrassTownChests.PlaceGoldChest(gx, pocketFloor - 1);
				if (index < 0) {
					SetPocket(gx, pocketTop, pocketFloor, dig: false);
					continue;
				}
				Chest chest = Main.chest[index];
				if (vaultChest >= 0) {
					OldBrassTownChests.Add(chest, ModContent.ItemType<SheriffsKey>(), 1);
				}
				else {
					StockVault(chest);
				}
				return;
			}
			if (vaultChest >= 0) {
				OldBrassTownChests.SetStrongbox(vaultChest, locked: false);
				SafeLog.Warn("OldBrassTown.NoCache", "Old Brass Town: no rock to bury the cache in under the street; the strongbox was left unlocked.");
			}
			else {
				SafeLog.Warn("OldBrassTown.NoLoot", "Old Brass Town: neither the strongbox nor the buried cache could be placed.");
			}
		}

		/// <summary>The pocket (columns <paramref name="gx"/>-1 to +2, rows <c>floorY + CacheDepth</c> to the floor) and a
		/// ring of one tile round it all lie in the town's own rock, never in air or outside the footprint.</summary>
		private bool CanBury(int gx) {
			for (int x = gx - 2; x <= gx + 3; x++) {
				for (int y = floorY; y <= floorY + CacheDepth + CacheHeight + 1; y++) {
					if (!TileSafety.InWorld(x, y, TileSafety.EditMargin) || !InFootprint(x, y) || IsAir(x, y)) {
						return false;
					}
				}
			}
			return true;
		}

		/// <summary>Digs the pocket out (its floor and the two hint planks laid), or fills it back in. Bounds checked by
		/// <see cref="CanBury"/>; the cavern's wall stays behind it.</summary>
		private void SetPocket(int gx, int pocketTop, int pocketFloor, bool dig) {
			for (int x = gx - 1; x <= gx + 2; x++) {
				for (int y = pocketTop; y < pocketFloor; y++) {
					if (dig) {
						Main.tile[x, y].ClearTile();
					}
					else {
						Place(Main.tile[x, y], sandstone);
					}
				}
			}
			for (int x = gx; x <= gx + 1; x++) {
				Place(Main.tile[x, pocketFloor], sandstone);
				Place(Main.tile[x, floorY], dig ? plank : sandstone);
			}
		}

		private static void Add(Chest chest, ref int slot, int type, int stack) {
			if (slot >= chest.item.Length) {
				return;
			}
			chest.item[slot] ??= new Item();
			chest.item[slot].SetDefaults(type);
			chest.item[slot].stack = Math.Min(stack, chest.item[slot].maxStack);
			slot++;
		}

		// --- tunnels ----------------------------------------------------------------------------------------------------

		/// <summary>
		/// A 3-tall mine tunnel from the cavern's end on one side (<paramref name="dir"/> -1 left, 1 right), drifting
		/// slowly upwards, until it opens into a cave of the hive or reaches <see cref="TunnelLength"/>. Outside the town it
		/// stops before liquid (no flooding) and before any object of the hive (chests, pots, statues: frame-important or
		/// protected tiles), so no chest is ever left without its tile; it never enters anything forbidden; and it turns
		/// falling sand above it into Brass Sandstone so the roof holds.
		/// </summary>
		private void DigTunnel(int dir) {
			int start = -1;
			for (int k = 0; k < airTop.Length; k++) {
				int i = dir < 0 ? k : airTop.Length - 1 - k;
				if (airTop[i] <= airBottom[i]) {
					start = i;
					break;
				}
			}
			if (start < 0) {
				return;
			}
			int x = left + start;
			int floor = airBottom[start];
			int startFloor = floor;
			int open = 0;
			for (int step = 1; step <= TunnelLength; step++) {
				x += dir;
				if (step % 4 == 0) {
					floor = Math.Clamp(floor + WorldGen.genRand.Next(-1, 1), startFloor - TunnelDrift, startFloor);
				}
				bool blocked = false, allOpen = true;
				for (int y = floor - TunnelHeight + 1; y <= floor && !blocked; y++) {
					if (!TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin) || IsForbidden(tile)
						|| (!InFootprint(x, y) && (tile.LiquidAmount > 0 || (tile.HasTile && (Main.tileFrameImportant[tile.TileType]
							|| !TileID.Sets.GeneralPlacementTiles[tile.TileType]))))) {
						blocked = true;                       // liquid, or a chest, pot or other object of the hive: never cut through it
					}
					else if (tile.HasTile) {
						allOpen = false;
					}
				}
				if (blocked) {
					return;
				}
				if (allOpen && !InFootprint(x, floor)) {
					if (++open >= 2) {
						return;                               // reached a cave of the hive
					}
					continue;
				}
				open = 0;
				for (int y = floor - TunnelHeight + 1; y <= floor; y++) {
					Main.tile[x, y].ClearTile();             // bounds checked above
				}
				if (TileSafety.TryGetTile(x, floor - TunnelHeight, out Tile roof, TileSafety.EditMargin) && roof.HasTile && TileID.Sets.Falling[roof.TileType]) {
					roof.TileType = sandstone;
				}
				if (TileSafety.TryGetTile(x, floor + 1, out Tile ground, TileSafety.EditMargin) && !ground.HasTile) {
					Place(ground, sandstone);
				}
			}
		}
	}
}
