using System;
using Cogpunk.Content.Coghaven.Tiles;
using Cogpunk.Content.Coghaven.Walls;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using B = Cogpunk.Content.Coghaven.Generation.CoghavenBlueprints;

namespace Cogpunk.Content.Coghaven.Generation
{
	/// <summary>
	/// Opens the two arches of a Coghaven built before 2026-11-26 (user: "the two archs at the right and left of coghaven have
	/// solid wall instead of background walls so the payer needs to break or go up arround it"): new worlds get the gate's and
	/// the pavilion's posts as background where people walk (the blueprints: air on the Cinnabar Panel Wall), and an older world
	/// gets the same, once, on its first world tick.
	/// <list type="number">
	/// <item>The island's surface row is found from the gate's first post: in that column of the island, the lowest Cinnabar
	/// Lacquer block standing on the post's Palace Flagstone plinth and the terrace under it, with the three other posts' lacquer
	/// on the same row (the old layout; anything else, and nothing changes).</item>
	/// <item>Every cell the blueprints now leave open on the panel wall ('.') in the gate and the pavilion loses its block if,
	/// and only if, that block is Cinnabar Lacquer (a player's own building there is left alone), and gets the panel wall.</item>
	/// </list>
	/// A world flag remembers it ran (matched or not), and a new world sets it as it is generated, so it never looks again.
	/// <para>D0: bounded loops (the island's rows, the two blueprints' cells), every tile through <see cref="TileSafety"/>,
	/// framed afterwards. D2: the server (or a single player) edits and sends the changed area to clients
	/// (<c>NetMessage.SendTileSquare</c>); clients joining later get it with the world.</para>
	/// </summary>
	public sealed class CoghavenArchRetrofit : ModSystem
	{
		private static int flag = -1;

		public override void Load() {
			flag = WorldFlagSystem.Register("CoghavenArchesOpened");
		}

		public override void PostWorldGen() {
			WorldFlagSystem.Flag(flag) = true;                  // a new world is built with the open arches
		}

		public override void PostUpdateWorld() {
			if (flag < 0 || WorldFlagSystem.Get(flag)) {
				return;
			}
			WorldFlagSystem.Flag(flag) = true;                  // once, whether it matches or not
			if (!CoghavenSystem.Exists) {
				return;
			}
			try {
				Open();
			}
			catch (Exception e) {
				SafeLog.Warn("Coghaven.ArchRetrofit", "Opening Coghaven's arches failed and was skipped: {0}", e.Message);
			}
		}

		private static void Open() {
			ushort lacquer = (ushort)ModContent.TileType<CinnabarLacquerTile>();
			ushort flagstone = (ushort)ModContent.TileType<PalaceFlagstoneTile>();
			ushort panel = (ushort)ModContent.WallType<CinnabarPanelWallTile>();
			int left = CoghavenSystem.Area.X;
			int gateX = left + B.GateX;
			int surface = FindSurface(gateX, lacquer, flagstone);
			if (surface < 0) {
				return;                                         // not the old layout (or not found): leave it
			}
			int changed = Apply(B.Gate, gateX, surface, lacquer, panel) + Apply(B.Pavilion, left + B.PavilionX, surface, lacquer, panel);
			if (changed == 0) {
				return;
			}
			int x0 = Math.Max(TileSafety.EditMargin, gateX - 1), x1 = Math.Min(Main.maxTilesX - TileSafety.EditMargin - 1, left + B.PavilionX + Width(B.Pavilion));
			int y0 = Math.Max(TileSafety.EditMargin, surface - Math.Max(B.Gate.Length, B.Pavilion.Length)), y1 = Math.Min(Main.maxTilesY - TileSafety.EditMargin - 1, surface + 1);
			WorldGen.RangeFrame(x0, y0, x1, y1);
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendTileSquare(-1, gateX, surface - B.Gate.Length, Width(B.Gate) + 1, B.Gate.Length + 2);
				NetMessage.SendTileSquare(-1, left + B.PavilionX, surface - B.Pavilion.Length, Width(B.Pavilion) + 1, B.Pavilion.Length + 2);
			}
			SafeLog.Info("Coghaven.ArchRetrofit", $"Coghaven: opened {changed} cells of its gate and pavilion posts.");   // once a world
		}

		private static int Width(string[] plan) => plan.Length > 0 ? plan[0].Length : 0;

		/// <summary>The island's surface row from the gate's first post (see the class summary), or -1.</summary>
		private static int FindSurface(int gateX, ushort lacquer, ushort flagstone) {
			int post = gateX + 2;
			int top = CoghavenSystem.Area.Top, bottom = CoghavenSystem.Area.Bottom;
			for (int y = bottom; y >= top; y--) {
				if (Is(post, y, lacquer) && Is(post, y + 1, flagstone) && Is(post, y + 2, flagstone)
					&& Is(gateX + 8, y, lacquer) && Is(gateX + 16, y, lacquer) && Is(gateX + 22, y, lacquer)) {
					return y + 2;                                // the terrace row: the plan's last row
				}
			}
			return -1;
		}

		private static bool Is(int x, int y, ushort type) {
			return TileSafety.TryGetTile(x, y, out Tile tile, TileSafety.EditMargin) && tile.HasTile && tile.TileType == type;
		}

		/// <summary>The plan's open-on-the-panel cells ('.') that still hold Cinnabar Lacquer: cleared to the panel wall.</summary>
		private static int Apply(string[] plan, int x0, int surface, ushort lacquer, ushort panel) {
			int y0 = surface - (plan.Length - 1);
			int changed = 0;
			for (int row = 0; row < plan.Length; row++) {
				string line = plan[row];
				for (int col = 0; col < line.Length; col++) {
					if (line[col] != '.' || !TileSafety.TryGetTile(x0 + col, y0 + row, out Tile tile, TileSafety.EditMargin)
						|| !tile.HasTile || tile.TileType != lacquer) {
						continue;
					}
					tile.ClearTile();
					if (tile.WallType == WallID.None) {
						tile.WallType = panel;
					}
					changed++;
				}
			}
			return changed;
		}
	}
}
