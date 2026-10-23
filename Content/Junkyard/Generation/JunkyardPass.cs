using System;
using Cogpunk.Content.Furniture;
using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Content.Scrap.Tiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Junkyard.Generation
{
	/// <summary>
	/// Replaces the vanilla left beach and ocean with the Junkyard. Runs late (after "Micro Biomes" and the Rusted Scrap
	/// heaps, like Calamity's Sulphurous Sea) and rebuilds the strip from the world edge to <c>GenVars.leftBeachEnd</c>
	/// (300-380 tiles on every world size, the vanilla left beach), so nothing vanilla puts on the beach later survives in it.
	/// <para>Sections, from the land towards the world edge:
	/// <list type="number">
	/// <item>Beach, 18-22 tiles: sand sloping gently down, palm trees, a few buried Rusted Scrap clumps and loose blocks.</item>
	/// <item>Junkyard, 100-123 tiles: Rusted Scrap heaps half-buried in sand with water puddles between them, and a larger
	/// central heap holding a buried Scrappy Trunk cache.</item>
	/// <item>Deep pool, the rest: a sheer drop into water walled with Polished Metal, reaching halfway from the surface to
	/// the underworld. Inside the Junkyard all water is drawn as steaming tar and burns (<see cref="Tar.TarWaterStyle"/>,
	/// <see cref="Tar.TarPlayer"/>), so the whole pool is a tar pit.</item>
	/// </list></para>
	/// <para>Vanilla's big structures are kept away beforehand: the Dungeon is moved to the right
	/// (<see cref="JunkyardLayoutPass"/>), the footprint is claimed in the structure map (<see cref="JunkyardReservePass"/>)
	/// and the Shimmer is placed past it (<see cref="ShimmerPlacementPass"/>).</para>
	/// <para>D0: every loop is bounded by the strip's size; tiles are written only inside <see cref="EdgeMargin"/>; vanilla
	/// chests and signs inside the strip are unregistered before their tiles are cleared; as a last safety net the pool
	/// floor is raised above anything it would still cut into (dungeon or temple brick and walls, the Shimmer), found in
	/// one bounded scan. A failure is caught by <see cref="SafeGenPass"/> and world creation continues.</para>
	/// </summary>
	internal sealed class JunkyardPass : SafeGenPass
	{
		public const int BeachMinWidth = 18;
		public const int BeachMaxWidth = 22;
		public const int YardMinWidth = 100;
		public const int YardMaxWidth = 123;
		public const int WallThickness = 4;           // Polished Metal between the junkyard and the pool
		public const int PoolDrop = 2;                // tar surface sits this far below the junkyard ground
		public const float PoolDepthFraction = 0.5f;  // pool floor: halfway from the tar surface to the underworld
		public const int MinPoolDepth = 60;
		public const int FloorThickness = 6;
		public const int BeachDrop = 3;               // the beach slopes this many tiles down from the land to the yard
		public const int SandDepth = 12;
		private const int EdgeMargin = 2;             // columns 0-1 are never touched
		private const int VisibleLeftWall = 4;        // Polished Metal visible inside the playable border
		private const int SkyClearance = 45;
		private const int MaxFillDepth = 90;
		private const int FallbackBeachEnd = 340;
		private const int MinPoolInterior = 40;
		private const int ConflictClearance = 4;      // rows kept between the pool floor and whatever it must not cut into
		private const int ShimmerRadius = 125;        // WorldGen.ShimmerMakeBiome works within +-genRand.Next(105, 125)
		private const int CacheFloorAboveGround = 2;  // the cache cavity floor, measured up from the yard ground

		private static readonly int[] CacheOres = {
			ItemID.CopperOre, ItemID.TinOre, ItemID.IronOre, ItemID.LeadOre,
			ItemID.SilverOre, ItemID.TungstenOre, ItemID.GoldOre, ItemID.PlatinumOre,
		};

		private ushort sand, scrap, metal, stone, sandstone;
		private int[] surface;                        // ground row per column, indexed by x - yardLeft
		private int yardLeft;

		public JunkyardPass() : base("Cogpunk: The Junkyard", 40.0) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.Junkyard");
			sand = TileID.Sand;
			stone = TileID.Stone;
			sandstone = TileID.Sandstone;
			scrap = (ushort)ModContent.TileType<RustedScrapTile>();
			metal = (ushort)ModContent.TileType<PolishedMetalTile>();

			// --- layout ---------------------------------------------------------------------------------------------
			int right = ChooseStripRight();
			int beachWidth = WorldGen.genRand.Next(BeachMinWidth, BeachMaxWidth + 1);
			int yardWidth = WorldGen.genRand.Next(YardMinWidth, YardMaxWidth + 1);
			int leftWallEnd = Main.offLimitBorderTiles + VisibleLeftWall - 1;
			int beachLeft = right - beachWidth;
			yardLeft = beachLeft - yardWidth;
			int poolLeft = leftWallEnd + 1;
			int poolRight = yardLeft - WallThickness;             // exclusive
			if (poolRight - poolLeft < MinPoolInterior) {
				SafeLog.Warn("Junkyard.TooNarrow", "Junkyard skipped: only {0} tiles of left beach available.", right);
				return;
			}

			int ground = FindGround(right, right + 12);
			if (ground < 0) {
				SafeLog.Warn("Junkyard.NoGround", "Junkyard skipped: no ground found right of the beach at x={0}.", right);
				return;
			}
			int yardGround = ground + BeachDrop;
			int poolTop = yardGround + PoolDrop;
			int top = Math.Max(30, FindHighestGround(EdgeMargin, right) - SkyClearance);
			int poolBottom = ChoosePoolBottom(poolRight, poolTop);
			progress.Set(0.1);

			// --- clear what vanilla left in the strip -----------------------------------------------------------------
			Rectangle strip = new(EdgeMargin, top, right - EdgeMargin, poolBottom + FloorThickness - top);
			// The sand fill under the old ocean can reach deeper than the pool floor on shallow worlds; chests there are
			// non-solid tiles the fill would erase, so unregister everything down to the fill limit too.
			int fillLimit = ground + BeachDrop + SandDepth + MaxFillDepth + 1;
			RemoveChestsAndSigns(new Rectangle(strip.X, strip.Y, strip.Width, Math.Max(strip.Bottom, fillLimit) - strip.Y));

			// --- pool and its walls -----------------------------------------------------------------------------------
			for (int x = EdgeMargin; x < yardLeft; x++) {
				bool wall = x <= leftWallEnd || x >= poolRight;
				for (int y = top; y < poolBottom + FloorThickness; y++) {
					if (!TileSafety.InWorld(x, y, EdgeMargin)) {
						continue;
					}
					Tile tile = Main.tile[x, y];
					tile.ClearEverything();
					if (wall) {
						if (y >= yardGround) {
							Place(tile, metal);
						}
					}
					else if (y >= poolBottom) {
						Place(tile, y < poolBottom + 2 ? sand : stone);
					}
					else if (y >= poolTop) {
						tile.LiquidType = LiquidID.Water;          // drawn as tar while in the Junkyard
						tile.LiquidAmount = byte.MaxValue;
					}
				}
			}
			progress.Set(0.45);

			// --- beach and yard ground ------------------------------------------------------------------------------
			surface = new int[right - yardLeft];
			for (int x = yardLeft; x < right; x++) {
				int s = x >= beachLeft
					? ground + (int)Math.Round((right - x) / (double)beachWidth * BeachDrop)
					: yardGround;                                     // flat: the heaps and puddles give the shape
				surface[x - yardLeft] = s;
				BuildGroundColumn(x, top, s);
			}
			progress.Set(0.6);

			// --- heaps, puddles, the cache ---------------------------------------------------------------------------
			int centre = yardLeft + yardWidth / 2;
			int centreHalf = WorldGen.genRand.Next(11, 15);
			BuildHeap(centre, centreHalf, WorldGen.genRand.Next(10, 13), WorldGen.genRand.Next(4, 7));
			BuildSideHeaps(yardLeft + 3, centre - centreHalf - 1);
			BuildSideHeaps(centre + centreHalf + 1, beachLeft - 2);
			PlaceCache(centre, yardGround - CacheFloorAboveGround);
			progress.Set(0.75);

			// --- beach dressing ---------------------------------------------------------------------------------------
			for (int i = 0; i < Math.Max(2, beachWidth / 4); i++) {
				int x = WorldGen.genRand.Next(beachLeft + 1, right - 1);
				int y = surface[x - yardLeft] + WorldGen.genRand.Next(2, 7);
				WorldGen.TileRunner(x, y, WorldGen.genRand.Next(3, 6), WorldGen.genRand.Next(2, 5), scrap);
			}
			for (int i = 0; i < 3; i++) {
				int x = WorldGen.genRand.Next(beachLeft, right);
				if (TileSafety.TryGetTile(x, surface[x - yardLeft], out Tile loose) && loose.HasTile && loose.TileType == sand) {
					loose.TileType = scrap;
				}
			}
			SmoothSurface(yardLeft, right);
			int palms = 0;
			for (int x = beachLeft + 2; x < right - 2 && palms < 4; x += WorldGen.genRand.Next(4, 7)) {
				if (WorldGen.GrowPalmTree(x, surface[x - yardLeft])) {
					palms++;
				}
			}
			progress.Set(0.9);

			// --- record --------------------------------------------------------------------------------------------
			Rectangle surfaceArea = new(EdgeMargin, top, right - EdgeMargin, yardGround + 25 - top);
			Rectangle poolArea = new(poolLeft, poolTop, poolRight - poolLeft, poolBottom - poolTop);
			JunkyardSystem.SetBounds(surfaceArea, poolArea);
			GenVars.structures?.AddProtectedStructure(strip);
			surface = null;
		}

		// ------------------------------------------------------------------------------------------------------------

		private static void Place(Tile tile, ushort type) {
			tile.HasTile = true;
			tile.TileType = type;
			tile.Slope = SlopeType.Solid;
			tile.IsHalfBlock = false;
			tile.LiquidAmount = 0;
		}

		/// <summary>First solid tile from the top, averaged over a few columns; -1 if none.</summary>
		private static int FindGround(int x0, int x1) {
			int sum = 0, count = 0;
			int from = Math.Max(20, (int)GenVars.worldSurfaceLow - 40);
			int to = Math.Min(Main.maxTilesY - 200, (int)Main.worldSurface + 60);
			for (int x = x0; x < x1; x++) {
				for (int y = from; y < to; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile) && tile.HasTile && Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType]) {
						sum += y;
						count++;
						break;
					}
				}
			}
			return count == 0 ? -1 : sum / count;
		}

		private static int FindHighestGround(int x0, int x1) {
			int best = int.MaxValue;
			int from = Math.Max(20, (int)GenVars.worldSurfaceLow - 40);
			int to = Math.Min(Main.maxTilesY - 200, (int)Main.worldSurface + 60);
			for (int x = x0; x < x1; x++) {
				for (int y = from; y < to && y < best; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile) && (tile.HasTile || tile.LiquidAmount > 0)) {
						best = y;
						break;
					}
				}
			}
			return best == int.MaxValue ? from : best;
		}

		/// <summary>Right edge (exclusive) of the strip the Junkyard rebuilds: the vanilla left beach, capped at a quarter of
		/// the world, and never into a left-side Dungeon (only possible if something undid <see cref="JunkyardLayoutPass"/>).</summary>
		public static int ChooseStripRight() {
			int right = GenVars.leftBeachEnd > 0 ? GenVars.leftBeachEnd : FallbackBeachEnd;
			right = Math.Min(right, Main.maxTilesX / 4);
			if (GenVars.dungeonSide < 0 && GenVars.dMinX > 0) {
				right = Math.Min(right, GenVars.dMinX - 20);
			}
			return right;
		}

		/// <summary>The pool floor before any conflict: halfway from the tar surface to the underworld.</summary>
		public static int MaxPoolBottom(int poolTop) {
			int bottom = poolTop + (int)((Main.UnderworldLayer - poolTop) * PoolDepthFraction);
			return Math.Clamp(bottom, poolTop + MinPoolDepth, Main.UnderworldLayer - 60);
		}

		/// <summary>
		/// Deepest allowed pool floor: <see cref="MaxPoolBottom"/>, raised above the first thing the pool and its walls
		/// would cut into: dungeon or temple brick and walls, Shimmer liquid, or the Shimmer biome around
		/// <c>GenVars.shimmerPosition</c>. One scan of the footprint, bounded by its size. (The structure map can't be
		/// asked here: <see cref="JunkyardReservePass"/> already claimed this very area.)
		/// </summary>
		private static int ChoosePoolBottom(int poolRight, int poolTop) {
			int maxBottom = MaxPoolBottom(poolTop);
			int scanLeft = EdgeMargin;
			int scanRight = Math.Min(poolRight + WallThickness, Main.maxTilesX);    // exclusive
			int scanBottom = maxBottom + FloorThickness + ConflictClearance;
			int conflict = int.MaxValue;
			for (int x = scanLeft; x < scanRight; x++) {
				for (int y = poolTop; y < scanBottom && y < conflict; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile) && IsForbidden(tile)) {
						conflict = y;
					}
				}
			}
			Vector2 shimmer = new((float)GenVars.shimmerPosition.X, (float)GenVars.shimmerPosition.Y);
			if (shimmer != Vector2.Zero && shimmer.X - ShimmerRadius < scanRight && shimmer.X + ShimmerRadius >= scanLeft) {
				conflict = Math.Min(conflict, (int)shimmer.Y - ShimmerRadius);
			}
			if (conflict == int.MaxValue) {
				return maxBottom;
			}
			int bottom = Math.Min(maxBottom, conflict - FloorThickness - ConflictClearance);
			if (bottom < poolTop + MinPoolDepth) {
				SafeLog.Warn("Junkyard.PoolConflict", "Junkyard pool kept at its minimum depth: something it must not cut into starts at y={0}.", conflict);
			}
			return Math.Max(bottom, poolTop + MinPoolDepth);
		}

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

		private static void RemoveChestsAndSigns(Rectangle area) {
			for (int i = 0; i < Main.maxChests; i++) {
				Chest chest = Main.chest[i];
				if (chest != null && area.Contains(chest.x, chest.y)) {
					Main.chest[i] = null;
				}
			}
			for (int i = 0; i < Main.sign.Length; i++) {
				Sign sign = Main.sign[i];
				if (sign != null && area.Contains(sign.x, sign.y)) {
					Main.sign[i] = null;
				}
			}
		}

		/// <summary>Air above <paramref name="ground"/>; a clean sand layer below it; then sand down to the old solid ground,
		/// so the old ocean basin can't leave water pockets or unsupported sand.</summary>
		private void BuildGroundColumn(int x, int top, int ground) {
			for (int y = top; y < ground; y++) {
				if (TileSafety.TryGetTile(x, y, out Tile air, EdgeMargin)) {
					air.ClearEverything();
				}
			}
			for (int y = ground; y < ground + SandDepth; y++) {
				if (TileSafety.TryGetTile(x, y, out Tile tile, EdgeMargin)) {
					tile.ClearEverything();
					Place(tile, sand);
				}
			}
			int depth = 0;
			int y2 = ground + SandDepth;
			for (; depth < MaxFillDepth && TileSafety.TryGetTile(x, y2, out Tile below, EdgeMargin); depth++, y2++) {
				if (below.HasTile && Main.tileSolid[below.TileType]) {
					return;                                  // reached the old ground
				}
				below.ClearEverything();
				Place(below, sand);
			}
			if (TileSafety.TryGetTile(x, y2 - 1, out Tile lid, EdgeMargin)) {
				lid.TileType = sandstone;                    // never leave sand hanging over a cave
			}
		}

		/// <summary>A half-buried heap: a pile of scrap above the ground (parabolic) and a shallower bowl of scrap below it.</summary>
		private void BuildHeap(int centreX, int halfWidth, int height, int bury) {
			int lastTop = int.MinValue;
			for (int dx = -halfWidth; dx <= halfWidth; dx++) {
				int x = centreX + dx;
				if (x - yardLeft < 0 || x - yardLeft >= surface.Length) {
					continue;
				}
				double u = dx / (double)(halfWidth + 1);
				double pile = 1.0 - u * u;                       // parabola: wide base, rounded peak (a pile, not an egg)
				double bowl = Math.Sqrt(Math.Max(0.0, pile));    // the buried part stays a round bowl
				int ground = surface[x - yardLeft];
				int heapTop = ground - (int)Math.Round(height * pile) - (pile > 0.35 && WorldGen.genRand.NextBool(3) ? 1 : 0);
				if (lastTop != int.MinValue && Math.Abs(heapTop - lastTop) > 2) {
					heapTop = lastTop + Math.Sign(heapTop - lastTop) * 2;   // no cliffs or single-tile spikes
				}
				lastTop = heapTop;
				int heapBottom = ground + (int)Math.Round(bury * bowl);
				for (int y = heapTop; y <= heapBottom; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile, EdgeMargin)) {
						tile.ClearEverything();
						Place(tile, scrap);
					}
				}
			}
		}

		/// <summary>Fills [from, to] with smaller heaps separated by gaps; gaps of 5+ tiles become water puddles.</summary>
		private void BuildSideHeaps(int from, int to) {
			int x = from;
			for (int guard = 0; guard < 32 && x < to; guard++) {
				int half = WorldGen.genRand.Next(5, 10);
				int gap = WorldGen.genRand.Next(4, 10);
				int centre = x + gap + half;
				if (centre + half > to) {
					MakePuddle(x + 1, to - 1);
					break;
				}
				MakePuddle(x + 1, x + gap - 1);
				BuildHeap(centre, half, WorldGen.genRand.Next(4, 9), WorldGen.genRand.Next(2, 5));
				x = centre + half + 1;
			}
		}

		private void MakePuddle(int x0, int x1) {
			if (x1 - x0 + 1 < 5) {
				return;
			}
			x1 = Math.Min(x1, x0 + 8);
			int depth = WorldGen.genRand.Next(2, 4);
			for (int x = x0; x <= x1; x++) {
				int ground = surface[x - yardLeft];
				int d = (x == x0 || x == x1) ? depth - 1 : depth;        // shallower rim
				for (int y = ground; y < ground + d; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile, EdgeMargin)) {
						tile.ClearEverything();
						tile.LiquidType = LiquidID.Water;
						tile.LiquidAmount = byte.MaxValue;
					}
				}
			}
		}

		/// <summary>Carves a small chamber in the central heap and places a glowing Scrappy Trunk cache with its loot.</summary>
		private void PlaceCache(int centreX, int floorY) {
			ushort trunk = (ushort)ModContent.TileType<ScrappyTrunkTile>();
			for (int attempt = 0; attempt < 3; attempt++) {
				int x = centreX - 1 + (attempt == 1 ? -2 : attempt == 2 ? 2 : 0);
				for (int dx = -1; dx <= 2; dx++) {
					for (int y = floorY - 3; y < floorY; y++) {
						if (TileSafety.TryGetTile(x + dx, y, out Tile cell, EdgeMargin)) {
							cell.ClearEverything();
						}
					}
					if (TileSafety.TryGetTile(x + dx, floorY, out Tile floor, EdgeMargin) && !floor.HasTile) {
						Place(floor, scrap);
					}
				}
				int index = WorldGen.PlaceChest(x, floorY - 1, trunk, false, ScrappyTrunkTile.CacheStyle);
				if (index >= 0 && index < Main.maxChests && Main.chest[index] != null) {
					FillCache(Main.chest[index]);
					return;
				}
			}
			SafeLog.Warn("Junkyard.CacheFailed", "Junkyard: the Scrappy Trunk cache could not be placed near x={0}.", centreX);
		}

		private static void FillCache(Chest chest) {
			int slot = 0;
			Add(chest, ref slot, ModContent.ItemType<RustedCog>(), WorldGen.genRand.Next(30, 53));
			Add(chest, ref slot, ModContent.ItemType<RustedMetal>(), WorldGen.genRand.Next(20, 29));
			Add(chest, ref slot, CacheOres[WorldGen.genRand.Next(CacheOres.Length)], 100);
		}

		private static void Add(Chest chest, ref int slot, int type, int stack) {
			if (slot >= chest.item.Length) {
				return;
			}
			chest.item[slot].SetDefaults(type);
			chest.item[slot].stack = Math.Min(stack, chest.item[slot].maxStack);
			slot++;
		}

		/// <summary>Vanilla "Smooth World" rule on the new ground: slope a surface tile toward an open side.</summary>
		private void SmoothSurface(int x0, int x1) {
			for (int x = x0 + 1; x < x1 - 1; x++) {
				int y = surface[x - x0];
				for (int n = 0; n < 16 && TileSafety.TryGetTile(x, y - 1, out Tile up, EdgeMargin) && up.HasTile; n++) {
					y--;                                     // climb to the top of a heap
				}
				if (!TileSafety.InWorld(x, y, EdgeMargin + 1)) {
					continue;
				}
				Tile tile = Main.tile[x, y];
				if (!tile.HasTile || (tile.TileType != sand && tile.TileType != scrap) || Main.tile[x, y - 1].HasTile) {
					continue;
				}
				if (!WorldGen.SolidTile(x - 1, y) && WorldGen.SolidTile(x - 1, y + 1) && WorldGen.SolidTile(x + 1, y) && !Main.tile[x + 1, y - 1].HasTile) {
					WorldGen.SlopeTile(x, y, 2);
				}
				else if (!WorldGen.SolidTile(x + 1, y) && WorldGen.SolidTile(x + 1, y + 1) && WorldGen.SolidTile(x - 1, y) && !Main.tile[x - 1, y - 1].HasTile) {
					WorldGen.SlopeTile(x, y, 1);
				}
			}
		}
	}
}
