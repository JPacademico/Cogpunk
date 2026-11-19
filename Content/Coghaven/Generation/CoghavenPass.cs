using System;
using System.Collections.Generic;
using Cogpunk.Content.Coghaven.Tiles;
using Cogpunk.Content.Coghaven.Walls;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;
using B = Cogpunk.Content.Coghaven.Generation.CoghavenBlueprints;

namespace Cogpunk.Content.Coghaven.Generation
{
	/// <summary>
	/// Builds Coghaven (user-set 2026-11-06): "a floaty island like the default game's cloud islands, always on the right
	/// side of the map before the beach ocean biome; cog steampunk themed but also a Chinese jade palace, red, bronze and
	/// jade; double the size of a normal cloud island; a base of cloud and cogs with steam turbines emitting smoke, to look
	/// like they keep it flying (no actual gravity); the palace like a well designed, detailed dungeon". Runs last, after
	/// vanilla's "Final Cleanup", in the columns <see cref="CoghavenSitePass"/> claimed (so no vanilla island is there), when
	/// the terrain, the Dungeon and the trees under it exist; nothing vanilla runs afterwards to smooth, fill or plant it.
	/// <para>Steps:
	/// <list type="number">
	/// <item>Height: the highest thing under the island's columns (any tile, wall or liquid) is found; the tallest pagoda
	/// of <see cref="CoghavenBlueprints.Pagodas"/> and the deepest base (<see cref="BaseDepth"/> down to
	/// <see cref="MinBaseDepth"/>) that fit between <see cref="TopLimit"/> and <see cref="MinClearance"/> rows over it are
	/// chosen, the island hung <see cref="PreferredClearance"/> rows up when there is room. No fit: skipped, logged once.</item>
	/// <item>The base (twice a vanilla cloud island: <see cref="CoghavenBlueprints.IslandWidth"/> wide against vanilla's
	/// 100-150, <see cref="BaseDepth"/> deep against vanilla's 15-20): a lens of vanilla Cloud (cloud wall behind its
	/// inside, as vanilla's islands), billowing underneath with cloud and rain cloud puffs, its ends rounded down; a bronze
	/// core (a superellipse of Bronze Gearwork), its keel and the turbines' mounts showing through the cloud; a skin of
	/// Palace Flagstone (the palace's terrace: since the user's second request of 2026-11-06 every floor is stone and the
	/// jade is the roofs' alone) or dirt and grass (the gardens, with a koi pond and sakura) on top.</item>
	/// <item>Cogs: big Bronze Cogs turning in sockets on the island's lower flanks; five Lift Turbines bolted under it,
	/// pouring smoke (<see cref="LiftTurbineTile"/>).</item>
	/// <item>The palace from <see cref="CoghavenBlueprints"/> (legend in art/coghaven/make_coghaven_blueprints.py): the
	/// Jade Vault inside the core (since 2026-11-16: one long machine hall with an unbreakable shell, Jadey's arena, the
	/// <see cref="Tiles.CoghavenChestTile"/> vault in its middle; it replaced the engine deck's rooms), then the gate, the
	/// Main Hall, the pagoda and the tea pavilion on the surface; then their furniture (vanilla Dynasty and Steampunk pieces,
	/// placed through <c>WorldGen.PlaceObject</c> at their <c>TileObjectData</c> origins, standing pieces first, then
	/// candles, then what hangs) and the chests (<see cref="CoghavenChests"/>: the pagoda's is a Locked Pagoda Chest since
	/// 2026-11-16, the vault's the Jade Vault); lamps and sakura trees in the gardens.</item>
	/// </list></para>
	/// <para>D0: <see cref="SafeGenPass"/> catches any failure (world creation continues without Coghaven); every loop is
	/// bounded by the island's size; every tile through <see cref="TileSafety"/> with the world's edit margin; a blueprint
	/// that is not rectangular is skipped; our own multi-tiles are written whole with their anchors made sure of (the cogs
	/// stand on two solid tiles, the turbines hang from four); the area is framed afterwards. D2: the island's box goes to
	/// <see cref="CoghavenSystem.Area"/> (saved, sent with the world data).</para>
	/// </summary>
	internal sealed class CoghavenPass : SafeGenPass
	{
		// --- the base (tiles) ---
		public const int BaseDepth = 34;               // at the middle; a vanilla cloud island is 15-20 deep
		public const int MinBaseDepth = 24;            // the Jade Vault (19 rows) still fits under the middle, with cloud under it
		public const int DepthStep = 2;
		public const double FlatTop = 0.93;            // of the half-width: beyond it the surface rounds down (x 8-212 flat)
		public const int EdgeDrop = 6;
		public const double BottomExponent = 0.55;
		public const int BottomNoise = 2;
		public const int NoiseStep = 6;
		public const int MinThickness = 4;
		public const int SoilRows = 3;                 // flagstone (terrace) or dirt (gardens) on top
		public const int PondDepth = 6;                // rows of water in the koi pond (the lining under them)
		public const int CloudPuffs = 30;
		public const int RainCloudOneIn = 3;
		public const int TipTufts = 6;
		// --- the bronze core ---
		public const double CoreRx = 62.0, CoreRy = 11.0, CoreDepth = 16.0, CoreExponent = 3.0;   // the engine deck's middle
		public const int CoreSkin = 3;                 // rows of cloud kept under the core
		public const int KeelHalfWidth = 8;
		public const int MountRows = 3;
		// --- placement ---
		public const int TopLimit = 43;                // the highest row anything is built in (the camera stops at 41)
		public const int PreferredClearance = 40;
		public const int MinClearance = 12;
		public const int LastClearance = 4;            // the last resort before giving up: just over the Dungeon's roof
		public const int PuffReach = 4;                // rows the cloud puffs hang under the base, at most
		public const int ScanBelowSurface = 60;
		public const int FramePad = 6;
		// --- vanilla styles (decompiled Item.SetDefaults) ---
		private const int DynastyPlatformStyle = 32, DynastyChairStyle = 27, DynastyTableStyle = 25, DynastyBookcaseStyle = 22;
		private const int DynastySofaStyle = 34, DynastyPianoStyle = 31, DynastyClockStyle = 1, DynastyLanternStyle = 26;
		private const int DynastyChandelierStyle = 22, DynastyCandleStyle = 17, DynastyLampStyle = 17, DynastyCandelabraStyle = 17;
		private const int SteampunkLanternStyle = 14;

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

		private ushort stone, lacquer, gearwork, roofTile, cogTile, turbineTile, vault, chestTile;
		private ushort stoneWall, panelWall, latticeWall, gearWall, vaultWall;
		// 2026-11-19 (user: "rework cogpalace design ... a quality terraria japanese building"): white plaster between red beams
		private const ushort PlasterWall = WallID.WhiteDynasty;
		private int left, s, depth;
		private int[] top, bottom;
		private bool[] turbineKept;                         // a turbine that would come too close to what is under it is left out
		private int clearance;
		private string[] pagoda;
		private readonly List<Piece> furniture = new();

		public CoghavenPass() : base("Cogpunk: Coghaven", 40.0) {
		}

		private int W => B.IslandWidth;

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.Coghaven");
			stone = (ushort)ModContent.TileType<PalaceFlagstoneTile>();
			lacquer = (ushort)ModContent.TileType<CinnabarLacquerTile>();
			gearwork = (ushort)ModContent.TileType<BronzeGearworkTile>();
			roofTile = (ushort)ModContent.TileType<JadeRoofTile>();
			cogTile = (ushort)ModContent.TileType<BronzeCogTile>();
			turbineTile = (ushort)ModContent.TileType<LiftTurbineTile>();
			stoneWall = (ushort)ModContent.WallType<PalaceFlagstoneWallTile>();
			panelWall = (ushort)ModContent.WallType<CinnabarPanelWallTile>();
			latticeWall = (ushort)ModContent.WallType<BronzeLatticeWallTile>();
			gearWall = (ushort)ModContent.WallType<BronzeGearworkWallTile>();
			vault = (ushort)ModContent.TileType<VaultGearworkTile>();
			vaultWall = (ushort)ModContent.WallType<VaultGearworkWallTile>();
			chestTile = (ushort)ModContent.TileType<CoghavenChestTile>();
			furniture.Clear();                                  // a pass is reused for every world made this session
			turbineKept = null;                                 // every turbine counts until the heights are chosen
			pagoda = null;
			CoghavenChests.Reset();                             // the two chests' sky items: two different ones

			Rectangle band = CoghavenSystem.Band;
			int home;
			if (band.Width > 0) {
				home = band.Left + CoghavenSitePass.BandMargin;
			}
			else if (!CoghavenSitePass.ChooseColumns(out home, out _)) {
				SafeLog.Warn("Coghaven.NoColumns", "Coghaven skipped: no room for it before the right beach.");
				return;
			}
			if (!ChooseSite(home, band.Width > 0)) {
				SafeLog.Warn("Coghaven.NoHeight", "Coghaven skipped: no room in the sky over columns {0}.", home);
				return;
			}
			BuildProfile();
			progress.Set(0.1);

			Base();
			Puffs();
			Pond();
			progress.Set(0.35);
			Sockets();
			Turbines();
			Plan(B.Vault, left + B.MainHallX, s);
			Plan(B.Gate, left + B.GateX, s - (B.Gate.Length - 1));
			Plan(B.MainHall, left + B.MainHallX, s - (B.MainHall.Length - 1));
			Plan(pagoda, left + B.PagodaX, s - (pagoda.Length - 1));
			Plan(B.Pavilion, left + B.PavilionX, s - (B.Pavilion.Length - 1));
			progress.Set(0.6);
			PlaceFurniture();
			GardenLamps();
			Trees();
			progress.Set(0.85);

			int highest = s - (Above() + 1);
			int lowest = s;
			for (int i = 0; i < W; i++) {
				lowest = Math.Max(lowest, bottom[i]);
			}
			lowest += LiftTurbineTile.Height + 1;              // the turbines under it (the puffs reach less far)
			WorldGen.RangeFrame(Math.Max(TileSafety.EditMargin, left - FramePad), Math.Max(TileSafety.EditMargin, highest - FramePad),
				Math.Min(Main.maxTilesX - TileSafety.EditMargin - 1, left + W + FramePad), Math.Min(Main.maxTilesY - TileSafety.EditMargin - 1, lowest + FramePad));
			Rectangle area = new(left, highest, W, lowest - highest + 1);
			CoghavenSystem.SetArea(area);
			GenVars.structures?.AddProtectedStructure(area);
			SafeLog.Info("WorldGen.Coghaven", $"Coghaven: a {W}x{depth} island at ({left}, {s}), a {pagoda.Length}-row pagoda, {clearance} rows over the ground, {furniture.Count} pieces of furniture.");
			top = bottom = null;
			turbineKept = null;
			furniture.Clear();
		}

		// --- height --------------------------------------------------------------------------------------------------

		/// <summary>The island's columns and heights: its home columns first (just before the beach), then slid along its
		/// band (<see cref="Shifts"/>, never further than the band's spare <see cref="CoghavenSitePass.BandMargin"/>, so no
		/// vanilla island is there) to dodge what stands under it, at the normal clearance and then at the last resort.</summary>
		private bool ChooseSite(int home, bool inBand) {
			foreach (int room in Clearances) {
				foreach (int shift in Shifts) {
					if (!inBand && shift != 0) {
						continue;
					}
					left = home + shift;
					if (left < CoghavenSitePass.WorldMargin || left + W > Main.maxTilesX - CoghavenSitePass.WorldMargin) {
						continue;
					}
					if (ChooseHeights(ObstacleRows(), room)) {
						return true;
					}
				}
			}
			return false;
		}

		private static readonly int[] Clearances = { MinClearance, LastClearance };
		private static readonly int[] Shifts = { 0, -12, 12, -24, 24 };

		/// <summary>Per island column (with the next column each side folded in), the highest row holding anything (a
		/// tile, a wall or liquid), scanning down from <see cref="TopLimit"/>; at most the surface layer plus
		/// <see cref="ScanBelowSurface"/>.</summary>
		private int[] ObstacleRows() {
			int floor = Math.Min(Main.maxTilesY - 50, (int)Main.worldSurface + ScanBelowSurface);
			int[] column = new int[W + 2];
			for (int k = 0; k < column.Length; k++) {
				int x = left - 1 + k;
				column[k] = floor;
				for (int y = TopLimit; y < floor; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin) && (tile.HasTile || tile.WallType != WallID.None || tile.LiquidAmount > 0)) {
						column[k] = y;
						break;
					}
				}
			}
			int[] rows = new int[W];
			for (int i = 0; i < W; i++) {
				rows[i] = Math.Min(column[i + 1], Math.Min(column[i], column[i + 2]));
			}
			return rows;
		}

		private static int Min(int[] values) {
			int m = int.MaxValue;
			foreach (int v in values) {
				m = Math.Min(m, v);
			}
			return m;
		}

		/// <summary>Rows the island hangs under its surface row in column <paramref name="i"/> with a base
		/// <paramref name="d"/> deep: the base with its noise, and the cloud puffs under it, or the turbine when
		/// <paramref name="withTurbine"/> and one hangs there.</summary>
		private int Below(int i, int d, bool withTurbine) {
			double u = (i + 0.5 - W / 2.0) / (W / 2.0);
			int body = Math.Max((int)Math.Round(d * Math.Pow(Math.Max(0.0, 1.0 - u * u), BottomExponent)) + BottomNoise, MinThickness);
			int turbine = withTurbine && InTurbineColumns(i, 0) ? LiftTurbineTile.Height + 1 + BottomNoise : 0;
			return body + Math.Max(turbine, PuffReach);
		}

		/// <summary>Rows the buildings stand over the surface row (the tallest of them).</summary>
		private int Above() {
			return Math.Max(Math.Max(B.Gate.Length, B.MainHall.Length), Math.Max(pagoda?.Length ?? 0, B.Pavilion.Length)) - 1;
		}

		/// <summary>The tallest pagoda and the deepest base that fit at clearance <paramref name="room"/>: the surface row as
		/// low as <see cref="PreferredClearance"/> allows, never so low that any column comes within <paramref name="room"/>
		/// rows of what is under it (column by column: a tall Dungeon entrance under the island's thin end needs less room
		/// than under its keel), never so high that a roof passes <see cref="TopLimit"/>. A turbine that would then come too
		/// close to what is under it is left out (they are only a look).</summary>
		private bool ChooseHeights(int[] obstacle, int room) {
			foreach (string[] candidate in B.Pagodas) {
				pagoda = candidate;
				for (int d = BaseDepth; d >= MinBaseDepth; d -= DepthStep) {
					int sMin = TopLimit + Above();
					int sMax = int.MaxValue, preferred = int.MaxValue;
					for (int i = 0; i < W; i++) {
						sMax = Math.Min(sMax, obstacle[i] - room - Below(i, d, false));
						preferred = Math.Min(preferred, obstacle[i] - PreferredClearance - Below(i, d, true));
					}
					if (sMin > sMax) {
						continue;
					}
					depth = d;
					clearance = room;
					s = Math.Clamp(preferred, sMin, sMax);
					turbineKept = new bool[B.TurbineX.Length];
					for (int k = 0; k < turbineKept.Length; k++) {
						bool fits = true;
						for (int c = B.TurbineX[k]; c < B.TurbineX[k] + LiftTurbineTile.Width && c < W && fits; c++) {
							fits = s + Below(c, d, true) <= obstacle[c] - room;
						}
						turbineKept[k] = fits;
					}
					return true;
				}
			}
			pagoda = null;
			return false;
		}

		// --- the base -------------------------------------------------------------------------------------------------

		private void BuildProfile() {
			top = new int[W];
			bottom = new int[W];
			double[] noise = Noise(W, BottomNoise);
			for (int i = 0; i < W; i++) {
				double u = (i + 0.5 - W / 2.0) / (W / 2.0);
				double a = Math.Abs(u);
				int drop = a > FlatTop ? (int)Math.Round(Math.Pow((a - FlatTop) / (1.0 - FlatTop), 2.0) * EdgeDrop) : 0;
				top[i] = s + drop;
				int d = (int)Math.Round(depth * Math.Pow(Math.Max(0.0, 1.0 - u * u), BottomExponent) + noise[i]);
				bottom[i] = Math.Max(top[i] + MinThickness, s + d);
				if (i >= B.PondLeft - 1 && i <= B.PondRight + 1) {
					bottom[i] = Math.Max(bottom[i], s + PondDepth + 2);   // cloud under the pond's lining, never open sky
				}
			}
			for (int k = 0; k < B.TurbineX.Length; k++) {      // each turbine's mount: four columns, one flat bottom
				if (!turbineKept[k]) {
					continue;
				}
				int tx = B.TurbineX[k];
				int m = 0;
				for (int c = tx; c < tx + LiftTurbineTile.Width && c < W; c++) {
					m = Math.Max(m, bottom[c]);
				}
				for (int c = tx; c < tx + LiftTurbineTile.Width && c < W; c++) {
					bottom[c] = m;
				}
			}
		}

		/// <summary>Smooth value noise in [-amplitude, amplitude]: random control points every <see cref="NoiseStep"/>
		/// columns, linearly interpolated.</summary>
		private static double[] Noise(int count, double amplitude) {
			int points = count / NoiseStep + 2;
			double[] control = new double[points];
			for (int k = 0; k < points; k++) {
				control[k] = (WorldGen.genRand.NextDouble() * 2.0 - 1.0) * amplitude;
			}
			double[] result = new double[count];
			for (int i = 0; i < count; i++) {
				int k = i / NoiseStep;
				double f = (i % NoiseStep) / (double)NoiseStep;
				result[i] = control[k] + (control[k + 1] - control[k]) * f;
			}
			return result;
		}

		private bool InCore(int i, int y) {
			double dx = Math.Abs(i + 0.5 - W / 2.0) / CoreRx;
			double dy = Math.Abs(y - (s + CoreDepth)) / CoreRy;
			return Math.Pow(dx, CoreExponent) + Math.Pow(dy, CoreExponent) <= 1.0;
		}

		/// <summary>Column <paramref name="i"/> is under a turbine (one that is kept, once the heights are chosen), give or
		/// take <paramref name="margin"/>.</summary>
		private bool InTurbineColumns(int i, int margin) {
			for (int k = 0; k < B.TurbineX.Length; k++) {
				int tx = B.TurbineX[k];
				if ((turbineKept == null || turbineKept[k]) && i >= tx - margin && i < tx + LiftTurbineTile.Width + margin) {
					return true;
				}
			}
			return false;
		}

		private bool IsMount(int i) => InTurbineColumns(i, 0);

		private bool InIsland(int i, int y) => i >= 0 && i < W && y >= top[i] && y <= bottom[i];

		/// <summary>Cloud below a skin of flagstone (the terrace) or dirt and grass (the gardens); the bronze core, its keel
		/// and the turbines' mounts inside; cloud walls behind the cloud's inside, as vanilla's islands have.</summary>
		private void Base() {
			for (int i = 0; i < W; i++) {
				int x = left + i;
				bool terrace = i >= B.TerraceLeft && i <= B.TerraceRight;
				bool keel = Math.Abs(i + 0.5 - W / 2.0) <= KeelHalfWidth;
				for (int y = top[i]; y <= bottom[i]; y++) {
					if (!TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin)) {
						continue;
					}
					tile.ClearEverything();
					if (y < top[i] + SoilRows) {
						if (terrace) {
							Place(tile, stone);
							tile.WallType = y > top[i] ? stoneWall : WallID.None;
						}
						else {
							Place(tile, y == top[i] ? TileID.Grass : TileID.Dirt);
						}
					}
					else if ((InCore(i, y) && y <= bottom[i] - CoreSkin) || (keel && y >= s + SoilRows + 1)
						|| (IsMount(i) && y > bottom[i] - MountRows)) {
						Place(tile, gearwork);
						tile.WallType = gearWall;
					}
					else {
						Place(tile, TileID.Cloud);
					}
				}
			}
			for (int i = 1; i < W - 1; i++) {
				for (int y = top[i] + 1; y < bottom[i]; y++) {
					if (!TileSafety.TryGetTile(left + i, y, out Tile tile, TileSafety.EditMargin) || !tile.HasTile || tile.TileType != TileID.Cloud) {
						continue;
					}
					bool inside = true;
					for (int dx = -1; dx <= 1 && inside; dx++) {
						for (int dy = -1; dy <= 1 && inside; dy++) {
							inside = InIsland(i + dx, y + dy);
						}
					}
					if (inside) {
						tile.WallType = WallID.Cloud;
					}
				}
			}
		}

		/// <summary>Billows under the island (some of rain cloud, which drips) and little tufts on its tips; never under a
		/// turbine, never over anything but sky.</summary>
		private void Puffs() {
			for (int p = 0; p < CloudPuffs; p++) {
				int i = WorldGen.genRand.Next(W);
				double r = 2.0 + WorldGen.genRand.NextDouble() * 2.5;
				ushort type = WorldGen.genRand.NextBool(RainCloudOneIn) ? TileID.RainCloud : TileID.Cloud;
				Blob(i, bottom[i] - 1 + (int)(r * 0.3), r, type, under: true);
			}
			for (int p = 0; p < TipTufts; p++) {
				int i = p % 2 == 0 ? WorldGen.genRand.Next(0, 6) : WorldGen.genRand.Next(W - 6, W);
				Blob(i, top[i], 1.5 + WorldGen.genRand.NextDouble() * 1.5, TileID.Cloud, under: false);
			}
		}

		private void Blob(int ci, int cy, double r, ushort type, bool under) {
			int reach = (int)Math.Ceiling(r) + 1;
			for (int dx = -reach; dx <= reach; dx++) {
				int i = ci + dx;
				if (i < 0 || i >= W || InTurbineColumns(i, 2)) {
					continue;
				}
				for (int dy = -reach; dy <= reach; dy++) {
					int y = cy + dy;
					if (dx * dx + dy * dy * 1.6 > r * r || (under && y <= bottom[i]) || (!under && y >= top[i])) {
						continue;
					}
					if (TileSafety.TryGetTile(left + i, y, out Tile tile, TileSafety.EditMargin) && !tile.HasTile && tile.WallType == WallID.None) {
						Place(tile, type);
					}
				}
			}
		}

		/// <summary>The koi pond in the west garden: <see cref="PondDepth"/> rows of water from the surface down, lined with
		/// flagstone. Since 2026-11-12 it is 14 x 6 = 84 water tiles (it was 10 x 3): vanilla won't fish in a pool of fewer than
		/// 75 (decompiled <c>Projectile.FishingCheck</c>: "Not Enough Water"), and up here 75 is also the full fishing power
		/// (the sky's thin air: 300 x 0.25), so the Koi can be caught (<see cref="KoiFishing"/>).</summary>
		private void Pond() {
			for (int i = B.PondLeft - 1; i <= B.PondRight + 1; i++) {
				for (int y = s; y <= s + PondDepth; y++) {
					if (!TileSafety.TryGetTile(left + i, y, out Tile tile, TileSafety.EditMargin) || y < top[i]) {
						continue;
					}
					bool lining = i == B.PondLeft - 1 || i == B.PondRight + 1 || y == s + PondDepth;
					tile.ClearEverything();
					if (lining) {
						Place(tile, stone);
					}
					else {
						tile.LiquidType = LiquidID.Water;
						tile.LiquidAmount = byte.MaxValue;
					}
				}
			}
		}

		// --- cogs and turbines ------------------------------------------------------------------------------------------

		/// <summary>Big cogs turning in sockets in the island's cloud: a 6x6 hollow with the gearwork wall behind, its
		/// <see cref="CoghavenBlueprints.CogSocketLift"/> rows above the island's bottom, the cog standing on the base under it.</summary>
		private void Sockets() {
			int count = Math.Min(B.CogSocketX.Length, Math.Min(B.CogSocketStyle.Length, B.CogSocketLift.Length));
			for (int k = 0; k < count; k++) {
				int i0 = B.CogSocketX[k];
				if (i0 < 0 || i0 + BronzeCogTile.Size > W) {
					continue;
				}
				int sb = int.MaxValue;
				for (int c = i0; c < i0 + BronzeCogTile.Size; c++) {
					sb = Math.Min(sb, bottom[c]);
				}
				sb -= B.CogSocketLift[k];
				int sy = sb - (BronzeCogTile.Size - 1);
				bool inside = true;
				if (TouchesVault(i0, sy, BronzeCogTile.Size, sb - sy + 1)) {
					continue;                                       // a shallow island: the vault's shell would cut the cog in two
				}
				for (int c = i0; c < i0 + BronzeCogTile.Size && inside; c++) {
					inside = sy > top[c] + SoilRows && sb + 1 <= bottom[c];
					if (c >= B.PondLeft - 1 && c <= B.PondRight + 1) {
						inside &= sy > s + PondDepth + 1;   // never into the pond (a shallow island leaves this cog out)
					}
				}
				if (!inside) {
					continue;
				}
				for (int c = i0; c < i0 + BronzeCogTile.Size; c++) {
					for (int y = sy; y <= sb; y++) {
						if (TileSafety.TryGetTile(left + c, y, out Tile tile, TileSafety.EditMargin)) {
							tile.ClearEverything();
							tile.WallType = gearWall;
						}
					}
				}
				for (int c = i0 + 2; c <= i0 + 3; c++) {
					if (TileSafety.TryGetTile(left + c, sb + 1, out Tile under, TileSafety.EditMargin) && !under.HasTile) {
						Place(under, gearwork);
					}
				}
				PlaceMultiTile(cogTile, left + i0, sy, BronzeCogTile.Size, BronzeCogTile.Size, B.CogSocketStyle[k]);
			}
		}

		/// <summary>Whether island columns <paramref name="i0"/>.. (<paramref name="width"/>) and rows <paramref name="y0"/>..
		/// (<paramref name="height"/>) come within a tile of the Jade Vault's shell (built later over them: nothing of ours may
		/// be cut in two by it).</summary>
		private bool TouchesVault(int i0, int y0, int width, int height) {
			int vx0 = B.MainHallX + B.VaultLeft - 1, vx1 = B.MainHallX + B.VaultRight + 1;
			int vy0 = s + B.VaultTop - 1, vy1 = s + B.VaultFloor + 1;
			return i0 <= vx1 && i0 + width - 1 >= vx0 && y0 <= vy1 && y0 + height - 1 >= vy0;
		}

		/// <summary>The five Lift Turbines under their gearwork mounts (four solid tiles over each: its anchor).</summary>
		private void Turbines() {
			for (int k = 0; k < B.TurbineX.Length; k++) {
				int tx = B.TurbineX[k];
				if (!turbineKept[k] || tx < 0 || tx + LiftTurbineTile.Width > W) {
					continue;
				}
				int m = bottom[tx];
				bool clear = true;
				for (int c = tx; c < tx + LiftTurbineTile.Width && clear; c++) {
					clear = TileSafety.TryGetTile(left + c, m, out Tile mount, TileSafety.EditMargin) && mount.HasTile && Main.tileSolid[mount.TileType];
					for (int y = m + 1; y <= m + LiftTurbineTile.Height && clear; y++) {
						clear = TileSafety.TryGetTile(left + c, y, out Tile cell, TileSafety.EditMargin) && !cell.HasTile;
					}
				}
				if (clear) {
					PlaceMultiTile(turbineTile, left + tx, m + 1, LiftTurbineTile.Width, LiftTurbineTile.Height, 0);
				}
			}
		}

		/// <summary>Writes a whole multi-tile object of ours (frames on the 18 px stride, <paramref name="style"/> laid out
		/// horizontally); its anchors are made sure of by the caller.</summary>
		private static void PlaceMultiTile(ushort type, int x0, int y0, int width, int height, int style) {
			for (int dx = 0; dx < width; dx++) {
				for (int dy = 0; dy < height; dy++) {
					if (!TileSafety.TryGetTile(x0 + dx, y0 + dy, out Tile tile, TileSafety.EditMargin)) {
						continue;
					}
					tile.HasTile = true;
					tile.TileType = type;
					tile.Slope = SlopeType.Solid;
					tile.IsHalfBlock = false;
					tile.LiquidAmount = 0;
					tile.TileFrameX = (short)((style * width + dx) * 18);
					tile.TileFrameY = (short)(dy * 18);
				}
			}
		}

		// --- the palace -------------------------------------------------------------------------------------------------

		private static bool IsRectangular(string[] rows) {
			if (rows == null || rows.Length == 0 || string.IsNullOrEmpty(rows[0])) {
				return false;
			}
			foreach (string row in rows) {
				if (row == null || row.Length != rows[0].Length) {
					return false;
				}
			}
			return true;
		}

		/// <summary>Writes a blueprint's blocks, walls, platforms and water (the legend in
		/// art/coghaven/make_coghaven_blueprints.py) with its top-left cell at (<paramref name="x0"/>, <paramref name="y0"/>)
		/// and queues its furniture.</summary>
		private void Plan(string[] rows, int x0, int y0) {
			if (!IsRectangular(rows)) {
				SafeLog.Warn("Coghaven.BadBlueprint", "Coghaven: a blueprint is not rectangular; skipped.");
				return;
			}
			for (int by = 0; by < rows.Length; by++) {
				string row = rows[by];
				for (int bx = 0; bx < row.Length; bx++) {
					char ch = row[bx];
					int x = x0 + bx, y = y0 + by;
					if (ch == ' ' || !TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin)) {
						continue;
					}
					ushort kept = tile.WallType;
					tile.ClearEverything();
					tile.WallType = kept;
					switch (ch) {
						case 'F': Place(tile, stone); tile.WallType = stoneWall; break;
						case 'f': Place(tile, stone); break;
						case 'R': Place(tile, lacquer); tile.WallType = panelWall; break;
						case 'r': Place(tile, lacquer); break;
						case 'G': Place(tile, gearwork); tile.WallType = gearWall; break;
						case 'g': Place(tile, gearwork); break;
						case 'T': Place(tile, roofTile); break;
						case 'Y': Place(tile, TileID.GoldBrick); break;
						case '/': Place(tile, roofTile); tile.Slope = SlopeType.SlopeDownRight; break;
						case '\\': Place(tile, roofTile); tile.Slope = SlopeType.SlopeDownLeft; break;
						case '(': Place(tile, stone); tile.Slope = SlopeType.SlopeDownRight; break;
						case ')': Place(tile, stone); tile.Slope = SlopeType.SlopeDownLeft; break;
						case '-': Place(tile, roofTile); tile.IsHalfBlock = true; break;
						case '.': tile.WallType = panelWall; break;
						case ',': tile.WallType = stoneWall; break;
						case 'm': tile.WallType = PlasterWall; break;
						case ':': tile.WallType = gearWall; break;
						case '#': tile.WallType = latticeWall; break;
						case '=': PlacePlatform(tile); tile.WallType = panelWall; break;
						case '+': PlacePlatform(tile); break;
						case '%': PlacePlatform(tile); tile.WallType = gearWall; break;
						case 'w': Water(tile); break;
						case '~': Water(tile); tile.WallType = stoneWall; break;
						case 'X': Place(tile, vault); tile.WallType = vaultWall; break;
						case 'x': Place(tile, vault); break;
						case ';': tile.WallType = vaultWall; break;
						case '$': PlacePlatform(tile); tile.WallType = vaultWall; break;
						default:
							tile.WallType = RoomWall(rows, bx, by, kept);   // furniture: air with the room's wall, placed later
							furniture.Add(new Piece(ch, x, y));
							break;
					}
				}
			}
		}

		/// <summary>The wall of the room a piece of furniture stands in: its neighbours' in the blueprint, or the wall the
		/// cell already had when it stands in the open (the cog on the pagoda's mast: no wall square in the sky).</summary>
		private ushort RoomWall(string[] rows, int bx, int by, ushort kept) {
			for (int k = 0; k < 4; k++) {
				int nx = bx + (k == 0 ? -1 : k == 1 ? 1 : 0), ny = by + (k == 2 ? -1 : k == 3 ? 1 : 0);
				if (ny < 0 || ny >= rows.Length || nx < 0 || nx >= rows[ny].Length) {
					continue;
				}
				switch (rows[ny][nx]) {
					case '.': return panelWall;
					case ',': return stoneWall;
					case 'm': return PlasterWall;
					case ':': return gearWall;
					case '#': return latticeWall;
					case ';': return vaultWall;
				}
			}
			return kept;
		}

		private static void Place(Tile tile, ushort type) {
			tile.HasTile = true;
			tile.TileType = type;
			tile.Slope = SlopeType.Solid;
			tile.IsHalfBlock = false;
			tile.LiquidAmount = 0;
		}

		/// <summary>A Dynasty platform: platforms keep their style in the frame (row = style x 18); framing does the rest.</summary>
		private static void PlacePlatform(Tile tile) {
			Place(tile, TileID.Platforms);
			tile.TileFrameX = 0;
			tile.TileFrameY = (short)(DynastyPlatformStyle * 18);
		}

		private static void Water(Tile tile) {
			tile.HasTile = false;
			tile.LiquidType = LiquidID.Water;
			tile.LiquidAmount = byte.MaxValue;
		}

		// --- furniture and loot -----------------------------------------------------------------------------------------

		/// <summary>Standing pieces first (chests, tables, cogs...), then candles on the tables, then what hangs from the
		/// ceilings. Vanilla checks each spot (<c>TileObject.CanPlace</c>); a piece that doesn't fit is left out.</summary>
		private void PlaceFurniture() {
			int chests = 0;
			for (int stage = 0; stage < 3; stage++) {
				foreach (Piece piece in furniture) {
					if (Stage(piece.Kind) != stage || !TileSafety.InWorld(piece.X, piece.Y, TileSafety.EditMargin + 6)) {
						continue;
					}
					if (piece.Kind == 'C' || piece.Kind == 'Q' || piece.Kind == '&') {
						if (CoghavenChests.Place(piece.X, piece.Y, piece.Kind != 'C', chests, piece.Kind == '&', piece.Kind == 'C') >= 0) {
							chests++;
							// filled as a Dynasty chest (vanilla's sky loot), now ours: the gallery's plain (2026-11-17), the
							// pagoda's locked, the vault's Jadey's
							CoghavenChests.Convert(piece.X, piece.Y - 1, chestTile, piece.Kind == 'C' ? CoghavenChestTile.PagodaStyle
								: piece.Kind == 'Q' ? CoghavenChestTile.LockedPagodaStyle : CoghavenChestTile.VaultStyle);
						}
						else {
							SafeLog.Warn("Coghaven.NoChest", "Coghaven: a chest didn't fit at ({0}, {1}).", piece.X, piece.Y);
						}
						continue;
					}
					PlacePiece(piece);
				}
			}
		}

		private static int Stage(char kind) => kind switch {
			'i' => 1,
			'L' or 'O' or 'H' or '^' => 2,
			_ => 0,
		};

		private void PlacePiece(Piece piece) {
			int x = piece.X, y = piece.Y;
			switch (piece.Kind) {
				case '<':
				case '>':
					WorldGen.PlaceObject(x, y, TileID.Chairs, mute: true, style: DynastyChairStyle, direction: piece.Kind == '>' ? 1 : -1);
					break;
				case 'A':
					WorldGen.PlaceObject(x, y, TileID.Tables, mute: true, style: DynastyTableStyle);
					break;
				case 'B':
					WorldGen.PlaceObject(x, y, TileID.Bookcases, mute: true, style: DynastyBookcaseStyle);
					break;
				case 'S':
					WorldGen.PlaceObject(x, y, TileID.Benches, mute: true, style: DynastySofaStyle);   // sofas are tile 89, "Benches"
					break;
				case 'P':
					WorldGen.PlaceObject(x, y, TileID.Pianos, mute: true, style: DynastyPianoStyle);
					break;
				case 'K':
					WorldGen.PlaceObject(x, y, TileID.GrandfatherClocks, mute: true, style: DynastyClockStyle);
					break;
				case 'N':
					WorldGen.PlaceObject(x, y, TileID.Thrones, mute: true);
					break;
				case 'U':
					WorldGen.PlaceObject(x, y, TileID.SteampunkBoiler, mute: true);
					break;
				case 'I':
					WorldGen.PlaceObject(x, y, TileID.Lamps, mute: true, style: DynastyLampStyle);
					break;
				case 'V':
					WorldGen.PlaceObject(x, y, TileID.Candelabras, mute: true, style: DynastyCandelabraStyle);
					break;
				case 'i':
					WorldGen.PlaceObject(x, y, TileID.Candles, mute: true, style: DynastyCandleStyle);
					break;
				case 'L':
					WorldGen.PlaceObject(x, y, TileID.HangingLanterns, mute: true, style: DynastyLanternStyle);
					break;
				case '^':
					WorldGen.PlaceObject(x, y, TileID.HangingLanterns, mute: true, style: SteampunkLanternStyle);
					break;
				case 'O':
					WorldGen.PlaceObject(x + 1, y, TileID.ChineseLanterns, mute: true);   // its origin is the top right cell
					break;
				case 'H':
					WorldGen.PlaceObject(x, y, TileID.Chandeliers, mute: true, style: DynastyChandelierStyle);
					break;
				case 'Z':
				case 'z':
					PlaceCog(x, y, piece.Kind == 'z' ? 1 : 0);
					break;
			}
		}

		/// <summary>A cog standing on the two tiles under its middle (its anchor): placed only if its 6x6 is clear of tiles
		/// and those two are solid.</summary>
		private void PlaceCog(int x0, int y0, int style) {
			int size = BronzeCogTile.Size;
			for (int dx = 0; dx < size; dx++) {
				for (int dy = 0; dy < size; dy++) {
					if (!TileSafety.TryGetTile(x0 + dx, y0 + dy, out Tile cell, TileSafety.EditMargin) || cell.HasTile) {
						return;
					}
				}
			}
			for (int dx = 2; dx <= 3; dx++) {
				if (!TileSafety.TryGetTile(x0 + dx, y0 + size, out Tile under, TileSafety.EditMargin) || !under.HasTile || !Main.tileSolid[under.TileType]) {
					return;
				}
			}
			PlaceMultiTile(cogTile, x0, y0, size, size, style);
		}

		/// <summary>Dynasty lamps along the terrace and the gardens, where the surface is open.</summary>
		private void GardenLamps() {
			foreach (int lx in B.LampX) {
				if (lx < 0 || lx >= W) {
					continue;
				}
				int x = left + lx, y = top[lx] - 1;
				if (TileSafety.TryGetTile(x, y, out Tile cell, TileSafety.EditMargin) && !cell.HasTile) {
					WorldGen.PlaceObject(x, y, TileID.Lamps, mute: true, style: DynastyLampStyle);
				}
			}
		}

		/// <summary>Sakura trees in the gardens (user, 2026-11-06: "the cherry trees should be able to be cut with an axe, like a
		/// default Terraria tree"): real vanilla sakura (tile 596, which vanilla's axes cut: decompiled <c>Main.tileAxe[596]</c>)
		/// grown by vanilla's own grower, on the island's flat top where it has what it needs (decompiled
		/// <c>WorldGen.GrowTreeWithSettings</c>: grass under it and beside it on the same row, nothing within two columns over
		/// it). Should one still not take, a vanilla forest tree grows there instead.</summary>
		private void Trees() {
			foreach (int tx in B.TreeX) {
				if (tx < 2 || tx >= W - 2) {
					continue;
				}
				int x = left + tx, y = top[tx];
				if (!TileSafety.TryGetTile(x, y, out Tile ground, TileSafety.EditMargin) || !ground.HasTile || ground.TileType != TileID.Grass) {
					continue;
				}
				if (!WorldGen.TryGrowingTreeByType(TileID.VanityTreeSakura, x, y)) {
					WorldGen.GrowTree(x, y);
				}
			}
		}
	}
}
