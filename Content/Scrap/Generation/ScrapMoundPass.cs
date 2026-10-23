using System;
using System.Collections.Generic;
using Cogpunk.Content.Scrap.Tiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Scrap.Generation
{
	/// <summary>
	/// Places exactly one small Rusted Scrap heap (3–6 tiles high) on the surface of each biome found on the
	/// <b>left half</b> of the world (ocean beach, forest, snow, desert, jungle, corruption/crimson, mushroom,
	/// hallow in special seeds). Never on the right half.
	/// <para>Grounding is guaranteed: every heap column is built bottom-up from a solid natural surface tile,
	/// and a column stops at the first tile that fails to place, so no scrap can float.</para>
	/// <para>Conflict-free: a site is only used if its footprint is natural biome soil, the heap volume plus two
	/// tiles of headroom holds nothing but air or harmless plants (grass, vines, thorns), there is no liquid, and it is away from the
	/// spawn point and the dungeon. Trees, chests, pots, cacti and structures are never overwritten.</para>
	/// </summary>
	internal sealed class ScrapMoundPass : SafeGenPass
	{
		public const int MinHeight = 3;
		public const int MaxHeight = 6;

		private enum SurfaceBiome : byte
		{
			None, Ocean, Forest, Snow, Desert, Jungle, Corruption, Crimson, Mushroom, Hallow
		}

		private const int EdgeMargin = 42;           // keep clear of the world border (vanilla keeps ~40 tiles)
		private const int SpawnClearance = 40;
		private const int DungeonClearance = 60;
		private const int Headroom = 2;              // free tiles required above the heap
		private const int MaxSitesPerBiome = 600;    // hard cap on site checks per biome (D0: bounded search)
		private const int VanillaBeachWidth = 380;   // fallback if GenVars.leftBeachEnd is unset

		private int left;
		private int[] groundY;
		private SurfaceBiome[] biomes;
		private readonly int[] profile = new int[(2 * (MaxHeight + 1)) + 1];
		private int halfWidth;

		public ScrapMoundPass() : base("Cogpunk: Rusted Scrap Heaps", 10.0) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.ScrapMounds");

			left = EdgeMargin;
			int right = Main.maxTilesX / 2;  // left half only
			int scanTop = Math.Max(10, (int)GenVars.worldSurfaceLow - 10);  // below floating islands (they sit ≥ 50 tiles higher)
			int scanBottom = Math.Min(Main.maxTilesY - 50, (int)Main.worldSurface + 30);
			int beachEnd = GenVars.leftBeachEnd > 0 ? GenVars.leftBeachEnd : VanillaBeachWidth;

			int columns = right - left;
			if (columns <= 0 || scanBottom <= scanTop) {
				return;
			}
			groundY = new int[columns];
			biomes = new SurfaceBiome[columns];
			for (int i = 0; i < columns; i++) {
				ClassifyColumn(left + i, scanTop, scanBottom, beachEnd, out groundY[i], out biomes[i]);
			}
			progress.Set(0.3);

			ushort scrap = (ushort)ModContent.TileType<RustedScrapTile>();
			List<(int start, int end, SurfaceBiome biome)> segments = FindSegments(columns);
			int placed = 0;
			int biomesSeen = 0;
			foreach (SurfaceBiome biome in Enum.GetValues<SurfaceBiome>()) {
				if (biome == SurfaceBiome.None) {
					continue;
				}
				List<(int start, int end, SurfaceBiome biome)> candidates = segments.FindAll(s => s.biome == biome);
				if (candidates.Count == 0) {
					continue;
				}
				biomesSeen++;
				candidates.Sort((a, b) => (b.end - b.start).CompareTo(a.end - a.start));  // longest first
				if (TryPlaceHeap(candidates, biome, scrap)) {
					placed++;
				}
				else {
					SafeLog.Info("WorldGen.ScrapMounds.NoSite." + biome, $"No valid surface site for a scrap heap in {biome}.");
				}
			}
			progress.Set(1.0);
			SafeLog.Info("WorldGen.ScrapMounds", $"Placed {placed} scrap heaps for {biomesSeen} left-side surface biomes.");
		}

		/// <summary>First solid, non-platform tile from the top; any liquid above it disqualifies the column.</summary>
		private static void ClassifyColumn(int x, int top, int bottom, int beachEnd, out int ground, out SurfaceBiome biome) {
			ground = -1;
			biome = SurfaceBiome.None;
			for (int y = top; y <= bottom; y++) {
				Tile tile = Main.tile[x, y];
				if (tile.LiquidAmount > 0) {
					return;
				}
				if (!tile.HasTile || !Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType]) {
					continue;  // air, plants, tree trunks, platforms: keep looking down
				}
				ground = y;
				biome = BiomeOf(tile.TileType, x, beachEnd);
				return;
			}
		}

		private static SurfaceBiome BiomeOf(ushort type, int x, int beachEnd) {
			switch (type) {
				case TileID.Grass:
					return SurfaceBiome.Forest;
				case TileID.CorruptGrass:
				case TileID.Ebonstone:
				case TileID.Ebonsand:
				case TileID.CorruptSandstone:
				case TileID.CorruptHardenedSand:
				case TileID.CorruptIce:
				case TileID.CorruptJungleGrass:
					return SurfaceBiome.Corruption;
				case TileID.CrimsonGrass:
				case TileID.Crimstone:
				case TileID.Crimsand:
				case TileID.CrimsonSandstone:
				case TileID.CrimsonHardenedSand:
				case TileID.FleshIce:
				case TileID.CrimsonJungleGrass:
					return SurfaceBiome.Crimson;
				case TileID.SnowBlock:
				case TileID.IceBlock:
					return SurfaceBiome.Snow;
				case TileID.JungleGrass:
				case TileID.Mud:
					return SurfaceBiome.Jungle;
				case TileID.Sand:
				case TileID.HardenedSand:
				case TileID.Sandstone:
					return x < beachEnd ? SurfaceBiome.Ocean : SurfaceBiome.Desert;
				case TileID.MushroomGrass:
					return SurfaceBiome.Mushroom;
				case TileID.HallowedGrass:
				case TileID.Pearlsand:
				case TileID.Pearlstone:
				case TileID.HallowedIce:
					return SurfaceBiome.Hallow;
				default:
					return SurfaceBiome.None;  // bricks, wood, clouds, living trees, exposed dirt/stone...
			}
		}

		/// <summary>
		/// Plants a heap may replace. An explicit list on purpose: vanilla's Main.tileCut also covers pots, herbs,
		/// Life Fruit and Queen Bee larvae (decompiled Main.cs), which must never be destroyed by world generation.
		/// </summary>
		private static bool IsClearablePlant(ushort type) {
			switch (type) {
				case TileID.Plants:
				case TileID.Plants2:
				case TileID.CorruptPlants:
				case TileID.CrimsonPlants:
				case TileID.HallowedPlants:
				case TileID.HallowedPlants2:
				case TileID.JunglePlants:
				case TileID.JunglePlants2:
				case TileID.MushroomPlants:
				case TileID.Vines:
				case TileID.JungleVines:
				case TileID.HallowedVines:
				case TileID.CrimsonVines:
				case TileID.VineFlowers:
				case TileID.MushroomVines:
				case TileID.CorruptThorns:
				case TileID.CrimsonThorns:
				case TileID.JungleThorns:
					return true;
				default:
					return false;
			}
		}

		private List<(int start, int end, SurfaceBiome biome)> FindSegments(int columns) {
			var segments = new List<(int, int, SurfaceBiome)>();
			int start = 0;
			for (int i = 1; i <= columns; i++) {
				if (i == columns || biomes[i] != biomes[start]) {
					if (biomes[start] != SurfaceBiome.None) {
						segments.Add((start, i - 1, biomes[start]));
					}
					start = i;
				}
			}
			return segments;
		}

		private bool TryPlaceHeap(List<(int start, int end, SurfaceBiome biome)> segments, SurfaceBiome biome, ushort scrap) {
			// Roll the size, then fall back to smaller heaps and looser flatness rather than skipping the biome.
			// Worst case per biome: 4 heights x 2 passes x MaxSitesPerBiome checks.
			for (int height = WorldGen.genRand.Next(MinHeight, MaxHeight + 1); height >= MinHeight; height--) {
				BuildProfile(height);
				for (int pass = 0; pass < 2; pass++) {
					bool strict = pass == 0;
					int checks = 0;
					foreach ((int start, int end, SurfaceBiome _) in segments) {
						int centre = (start + end) / 2;
						int span = ((end - start) / 2) + 1;
						for (int offset = 0; offset < span; offset++) {
							for (int sign = 1; sign >= -1; sign -= 2) {
								if (++checks > MaxSitesPerBiome) {
									goto NextAttempt;
								}
								int column = centre + (offset * sign);
								if (column >= start && column <= end && IsValidSite(column, biome, strict)) {
									Build(column, scrap);
									return true;
								}
								if (offset == 0) {
									break;
								}
							}
						}
					}
				NextAttempt:;
				}
			}
			return false;
		}

		/// <summary>Heap column heights: peak in the middle, ragged steps of at most 2 down to 1 at the edges.</summary>
		private void BuildProfile(int height) {
			halfWidth = height + WorldGen.genRand.Next(0, 2);
			profile[halfWidth] = height;
			for (int side = -1; side <= 1; side += 2) {
				int previous = height;
				for (int k = 1; k <= halfWidth; k++) {
					double t = k / (halfWidth + 0.5);
					int target = (int)Math.Round(height * (1.0 - Math.Pow(t, 1.6)));
					if (WorldGen.genRand.NextBool(3)) {
						target--;
					}
					int h = Math.Clamp(target, 1, previous);
					h = Math.Max(h, previous - 2);
					profile[halfWidth + (side * k)] = h;
					previous = h;
				}
			}
		}

		private bool IsValidSite(int centreIndex, SurfaceBiome biome, bool strict) {
			int first = centreIndex - halfWidth;
			int last = centreIndex + halfWidth;
			if (first < 0 || last >= groundY.Length) {
				return false;
			}
			int worldCentre = left + centreIndex;
			if (Math.Abs(worldCentre - Main.spawnTileX) < SpawnClearance + halfWidth) {
				return false;
			}
			if (Main.dungeonX > 0 && Math.Abs(worldCentre - Main.dungeonX) < DungeonClearance + halfWidth) {
				return false;
			}

			int maxStep = strict ? 1 : 2;
			int maxRange = strict ? 2 : 3;
			int minGround = int.MaxValue;
			int maxGround = int.MinValue;
			for (int i = first; i <= last; i++) {
				int g = groundY[i];
				if (g < 0 || biomes[i] != biome) {
					return false;
				}
				if (i > first && Math.Abs(g - groundY[i - 1]) > maxStep) {
					return false;
				}
				minGround = Math.Min(minGround, g);
				maxGround = Math.Max(maxGround, g);
			}
			if (maxGround - minGround > maxRange) {
				return false;
			}

			for (int i = first; i <= last; i++) {
				int x = left + i;
				int g = groundY[i];
				int columnHeight = profile[i - first];
				for (int y = g - columnHeight - Headroom; y < g; y++) {
					if (!TileSafety.TryGetTile(x, y, out Tile tile, margin: 10)) {
						return false;
					}
					if (tile.LiquidAmount > 0 || (tile.HasTile && !IsClearablePlant(tile.TileType))) {
						return false;
					}
				}
			}
			return true;
		}

		private void Build(int centreIndex, ushort scrap) {
			int first = centreIndex - halfWidth;
			int last = centreIndex + halfWidth;
			for (int i = first; i <= last; i++) {
				int x = left + i;
				int g = groundY[i];
				int columnHeight = profile[i - first];

				for (int y = g - columnHeight - Headroom; y < g; y++) {  // clear grass, flowers, vines (validated above)
					if (Main.tile[x, y].HasTile) {
						WorldGen.KillTile(x, y, noItem: true);
					}
				}
				Tile ground = Main.tile[x, g];                         // sit flush: no slope/half block underneath
				ground.Slope = SlopeType.Solid;
				ground.IsHalfBlock = false;

				for (int y = g - 1; y >= g - columnHeight; y--) {       // bottom-up, so nothing can float
					if (!WorldGen.PlaceTile(x, y, scrap, mute: true, forced: true)) {
						break;
					}
				}
			}
			// Bevel the outline of the heap with slopes now that every column exists.
			for (int i = first; i <= last; i++) {
				int x = left + i;
				int top = groundY[i] - profile[i - first];
				if (Main.tile[x, top].HasTile && Main.tile[x, top].TileType == scrap) {
					Tile.SmoothSlope(x, top, applyToNeighbors: false);
				}
			}
		}
	}
}
