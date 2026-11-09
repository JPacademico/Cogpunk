using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Coghaven.Generation
{
	/// <summary>
	/// Claims Coghaven's site (user-set 2026-11-06: "always on the right side of the map, before the beach ocean biome;
	/// ensure no conflicts on generation logic"). Runs right after vanilla's "Floating Islands".
	/// <list type="number">
	/// <item>The island's columns: <see cref="CoghavenBlueprints.IslandWidth"/> wide, its right edge <see cref="BeachGap"/>
	/// tiles left of <c>GenVars.rightBeachStart</c> (where vanilla's right beach begins, decompiled "Reset": 300-340 tiles
	/// from the world's edge plus the Dungeon side's extra width), with <see cref="BandMargin"/> spare on each side: the
	/// band.</item>
	/// <item>Vanilla floating islands and lakes (decompiled "Floating Islands": centres between 10% and 90% of the width, 180
	/// tiles apart, no more than <c>worldSurfaceLow - 50</c> high, at most 100-150 tiles across) that reach into the band
	/// are moved out of it: their tiles are cleared (only the island's own kinds: clouds, dirt, snow, sand and the cloud
	/// wall, only in the sky above every hill) and the same vanilla generator (<c>CloudIsland</c>, <c>CloudLake</c>, the
	/// drunk world's snow and desert islands) builds it again at a spot chosen by vanilla's own rules, outside the band; its
	/// entry in <c>GenVars.floatingIslandHouseX/Y</c> is updated, so vanilla's "Floating Island Houses" builds its house
	/// there. Should no spot be found (it never happens on the standard sizes) the island is dropped and its house turned
	/// off, rather than left inside the band.</item>
	/// <item>The band's sky is reserved with <c>GenVars.structures.AddProtectedStructure</c>, so every generator that asks
	/// (micro biomes, other mods) stays out of it, and recorded for <see cref="CoghavenPass"/>.</item>
	/// </list>
	/// <para>D0: <see cref="SafeGenPass"/> catches any failure (world creation continues without Coghaven); every loop is
	/// bounded (<see cref="RelocateAttempts"/>, the box sizes); every tile through <see cref="TileSafety"/>; vanilla's island
	/// arrays are indexed only below <c>numIslandHouses</c> and their length.</para>
	/// </summary>
	internal sealed class CoghavenSitePass : SafeGenPass
	{
		public const int BeachGap = 12;              // tiles between the island's right edge and the beach
		public const int BandMargin = 24;            // spare columns each side of the island
		public const int WorldMargin = 60;
		public const int MinWorldWidth = 1500;
		public const int VanillaReach = 90;          // a vanilla island's half-width, at most (100-150 across, drifting)
		public const int ClearAbove = 60, ClearBelow = 36;   // the cleared box round a vanilla island's recorded centre
		public const int RelocateAttempts = 600;
		public const int VanillaSpacing = 180;       // decompiled: islands 180 apart
		public const int CentreKeepOut = 150;        // decompiled: none within 150 of the world's middle
		public const int FloodCap = 60000;           // cells a removal may visit (a vanilla island is about 4000)

		public CoghavenSitePass() : base("Cogpunk: Coghaven Site", 2.0) {
		}

		/// <summary>The island's columns for this world: [left, left + width).</summary>
		public static bool ChooseColumns(out int left, out int right) {
			int beach = GenVars.rightBeachStart > 0 ? GenVars.rightBeachStart : Main.maxTilesX - 380;
			right = beach - BeachGap - 1;
			left = right - CoghavenBlueprints.IslandWidth + 1;
			if (left < WorldMargin + BandMargin || right > Main.maxTilesX - WorldMargin - BandMargin) {
				return false;
			}
			return true;
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			CoghavenSystem.SetBand(default);
			if (Main.maxTilesX < MinWorldWidth || !ChooseColumns(out int left, out int right)) {
				SafeLog.Warn("Coghaven.NoRoom", "Coghaven skipped: no room for it before the right beach (world {0} wide).", Main.maxTilesX);
				return;
			}
			Rectangle band = new(left - BandMargin, 0, right - left + 1 + 2 * BandMargin, Math.Max(1, (int)GenVars.worldSurfaceLow - 10));
			int moved = 0;
			int count = Math.Min(GenVars.numIslandHouses, Math.Min(GenVars.floatingIslandHouseX.Length, GenVars.floatingIslandHouseY.Length));
			for (int k = 0; k < count; k++) {
				int x = GenVars.floatingIslandHouseX[k];
				if (x + VanillaReach >= band.Left && x - VanillaReach <= band.Right) {
					Relocate(k, band, count);
					moved++;
				}
			}
			ClearLeftovers(band);
			GenVars.structures?.AddProtectedStructure(band);
			CoghavenSystem.SetBand(band);
			if (moved > 0) {
				SafeLog.Info("WorldGen.CoghavenSite", $"Coghaven: moved {moved} vanilla floating island(s) out of columns {band.Left}-{band.Right}.");
			}
		}

		/// <summary>The kinds of tile vanilla's floating islands are made of (decompiled CloudIsland, CloudLake,
		/// SnowCloudIsland, DesertCloudIsland).</summary>
		private static bool IsIslandTile(ushort type) {
			return IsCloud(type) || type == TileID.Dirt || type == TileID.Grass || type == TileID.SnowBlock || type == TileID.IceBlock
				|| type == TileID.Sand || type == TileID.HardenedSand || type == TileID.Sandstone;
		}

		/// <summary>Clouds are never terrain: they can be cleared anywhere in the sky.</summary>
		private static bool IsCloud(ushort type) {
			return type == TileID.Cloud || type == TileID.RainCloud || type == TileID.SnowCloud;
		}

		/// <summary>Nothing below this row is ever touched: every hill is lower (dunes may rise a little above vanilla's
		/// <c>worldSurfaceLow</c>, so a margin is kept, and dirt or sand is only removed when it is connected to a cloud).</summary>
		private static int SkyFloor => (int)GenVars.worldSurfaceLow - 20;

		/// <summary>Removes a vanilla island: its body (every island-kind tile 8-connected to a cloud of it, a bounded flood
		/// fill: dirt, snow or sand is only ever removed together with the cloud it sits on), then any cloud, cloud wall or
		/// water left in its box (the little clouds vanilla scatters above an island).</summary>
		private static void RemoveIsland(int x0, int y0, int x1, int y1) {
			y0 = Math.Max(y0, TileSafety.EditMargin);
			y1 = Math.Min(y1, SkyFloor);
			if (y1 <= y0) {
				return;
			}
			Point[] stack = new Point[FloodCap];
			int top = 0, visited = 0;
			for (int x = x0; x <= x1; x++) {
				for (int y = y0; y <= y1; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile seed, TileSafety.EditMargin) && seed.HasTile && IsCloud(seed.TileType) && top < FloodCap) {
						stack[top++] = new Point(x, y);
					}
				}
			}
			while (top > 0 && visited < FloodCap * 4) {
				Point p = stack[--top];
				if (!TileSafety.TryGetTile(p.X, p.Y, out Tile tile, TileSafety.EditMargin) || !tile.HasTile || !IsIslandTile(tile.TileType)) {
					continue;
				}
				tile.ClearTile();
				visited++;
				for (int dx = -1; dx <= 1; dx++) {
					for (int dy = -1; dy <= 1; dy++) {
						int nx = p.X + dx, ny = p.Y + dy;
						if ((dx != 0 || dy != 0) && nx >= x0 && nx <= x1 && ny >= y0 && ny <= y1 && top < FloodCap) {
							stack[top++] = new Point(nx, ny);
						}
					}
				}
			}
			ClearSky(x0, y0, x1, y1);
		}

		/// <summary>Clouds, cloud walls and water in the sky part of a box (never below <see cref="SkyFloor"/>).</summary>
		private static void ClearSky(int x0, int y0, int x1, int y1) {
			y1 = Math.Min(y1, SkyFloor);
			for (int x = x0; x <= x1; x++) {
				for (int y = Math.Max(y0, TileSafety.EditMargin); y <= y1; y++) {
					if (!TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin)) {
						continue;
					}
					if (tile.HasTile && IsCloud(tile.TileType)) {
						tile.ClearTile();
					}
					if (tile.WallType == WallID.Cloud) {
						tile.WallType = WallID.None;
					}
					if (tile.LiquidAmount > 0 && tile.LiquidType == LiquidID.Water) {
						tile.LiquidAmount = 0;
					}
				}
			}
		}

		/// <summary>Anything of a vanilla island still inside the band (an island wider than the estimate): its clouds,
		/// walls and water.</summary>
		private static void ClearLeftovers(Rectangle band) {
			RemoveIsland(band.Left, 0, band.Right - 1, SkyFloor);
		}

		private static void Relocate(int k, Rectangle band, int count) {
			int ox = GenVars.floatingIslandHouseX[k], oy = GenVars.floatingIslandHouseY[k];
			RemoveIsland(ox - VanillaReach - 5, oy - ClearAbove, ox + VanillaReach + 5, oy + ClearBelow);
			int lo = (int)(Main.maxTilesX * 0.1), hi = (int)(Main.maxTilesX * 0.9);
			for (int attempt = 0; attempt < RelocateAttempts && hi > lo; attempt++) {
				int x = WorldGen.genRand.Next(lo, hi);
				if (Math.Abs(x - Main.maxTilesX / 2) < CentreKeepOut) {
					continue;
				}
				if (x + VanillaReach + 10 >= band.Left && x - VanillaReach - 10 <= band.Right) {
					continue;                                   // stay out of Coghaven's band
				}
				bool crowded = false;
				for (int j = 0; j < count && !crowded; j++) {
					crowded = j != k && Math.Abs(x - GenVars.floatingIslandHouseX[j]) < VanillaSpacing;
				}
				if (crowded) {
					continue;
				}
				int ground = -1;
				for (int y = 200; y < Main.worldSurface && y < Main.maxTilesY - 1; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile t) && t.HasTile) {
						ground = y;
						break;
					}
				}
				if (ground - 100 <= 91) {
					continue;                                   // vanilla's own range, genRand.Next(90, ground - 100)
				}
				int y0 = Math.Min(WorldGen.genRand.Next(90, ground - 100), (int)GenVars.worldSurfaceLow - 50);
				if (y0 < 60) {
					continue;
				}
				Build(k, x, y0);
				GenVars.floatingIslandHouseX[k] = x;
				GenVars.floatingIslandHouseY[k] = y0;
				return;
			}
			GenVars.skyLake[k] = true;                          // no spot: no island, and no house floating in the band
			SafeLog.Warn("Coghaven.IslandDropped", "Coghaven: vanilla floating island {0} found no other spot and was removed.", k);
		}

		/// <summary>The island vanilla would have made (decompiled "Floating Islands": a lake, the drunk world's snow (style 3)
		/// and desert (style 1) islands, else a cloud island).</summary>
		private static void Build(int k, int x, int y) {
			if (k < GenVars.skyLake.Length && GenVars.skyLake[k]) {
				WorldGen.CloudLake(x, y);
				return;
			}
			int style = k < GenVars.floatingIslandStyle.Length ? GenVars.floatingIslandStyle[k] : 0;
			if (style == 3) {
				WorldGen.SnowCloudIsland(x, y);
			}
			else if (style == 1) {
				WorldGen.DesertCloudIsland(x, y);
			}
			else {
				WorldGen.CloudIsland(x, y);
			}
		}
	}
}
