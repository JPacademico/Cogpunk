using System.Collections.Generic;
using Cogpunk.Content.Bosses.Fungimancer.Tiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Chat;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Bosses.Fungimancer
{
	/// <summary>
	/// The Fungimancer's world state: its defeat (a world flag, synced with the world data), the living boss (tracked each
	/// tick), and the rainbow mushrooms standing (user-set 2026-11-19: "only one rainbow mushroom at a time per biome"): the
	/// server keeps their tiles in a list saved with the world (no world scan), checked and pruned whenever a new one may
	/// grow (<see cref="RainbowMushroomGrowth"/>); breaking one wakes the boss there (<see cref="SpawnFrom"/>).
	/// D0: the list is capped at <see cref="MaxMushrooms"/>; every saved point is checked against the world and the tile
	/// before use; loops bounded. D2: growth and spawning are the server's; the tile change is sent as a tile square.
	/// </summary>
	public sealed class FungimancerSystem : ModSystem
	{
		public const string DownedFlagName = "DownedFungimancer";
		public const int MaxMushrooms = 64;

		private static int downedFlag = -1;
		private static int bossIndex = -1;
		private static uint bossSeen;
		private static readonly List<Point> mushrooms = new();

		public static bool Downed => WorldFlagSystem.Get(downedFlag);

		public static ref bool DownedFlag => ref WorldFlagSystem.Flag(downedFlag);

		public override void Load() {
			downedFlag = WorldFlagSystem.Register(DownedFlagName);
		}

		public override void Unload() {
			downedFlag = -1;
			bossIndex = -1;
			mushrooms.Clear();
		}

		public override void ClearWorld() {
			bossIndex = -1;
			mushrooms.Clear();
		}

		public override void SaveWorldData(TagCompound tag) {
			if (mushrooms.Count == 0) {
				return;
			}
			int[] xy = new int[mushrooms.Count * 2];
			for (int k = 0; k < mushrooms.Count; k++) {
				xy[2 * k] = mushrooms[k].X;
				xy[2 * k + 1] = mushrooms[k].Y;
			}
			tag["RainbowMushrooms"] = xy;
		}

		public override void LoadWorldData(TagCompound tag) {
			mushrooms.Clear();
			int[] xy = tag.GetIntArray("RainbowMushrooms");
			for (int k = 0; k + 1 < xy.Length && mushrooms.Count < MaxMushrooms; k += 2) {
				mushrooms.Add(new Point(xy[k], xy[k + 1]));
			}
		}

		internal static void Track(int whoAmI) {
			bossIndex = whoAmI;
			bossSeen = Main.GameUpdateCount;
		}

		/// <summary>True if a Fungimancer is alive (updated within two ticks, or found among the NPCs).</summary>
		public static bool BossAlive() {
			if (bossIndex >= 0 && bossIndex < Main.maxNPCs && Main.GameUpdateCount - bossSeen <= 2 && Main.npc[bossIndex].active
				&& Main.npc[bossIndex].ModNPC is Fungimancer) {
				return true;
			}
			return NPC.AnyNPCs(ModContent.NPCType<Fungimancer>());
		}

		private static bool IsRainbow(Point p) {
			return TileSafety.TryGetTile(p.X, p.Y, out Tile tile) && tile.HasTile && tile.TileType == ModContent.TileType<RainbowMushroomTile>();
		}

		/// <summary>Server: true if a rainbow mushroom stands within <paramref name="range"/> tiles of (<paramref name="i"/>,
		/// <paramref name="j"/>); entries whose tile is gone are dropped on the way.</summary>
		public static bool AnyNear(int i, int j, int range) {
			for (int k = mushrooms.Count - 1; k >= 0; k--) {
				Point p = mushrooms[k];
				if (!IsRainbow(p)) {
					mushrooms.RemoveAt(k);
					continue;
				}
				if (System.Math.Abs(p.X - i) <= range && System.Math.Abs(p.Y - j) <= range) {
					return true;
				}
			}
			return false;
		}

		/// <summary>Server: room for one more (the cap) after the gone ones are pruned.</summary>
		public static bool HasRoom() => mushrooms.Count < MaxMushrooms;

		public static void Add(int i, int j) {
			if (mushrooms.Count < MaxMushrooms) {
				mushrooms.Add(new Point(i, j));
			}
		}

		public static void Remove(int i, int j) {
			for (int k = mushrooms.Count - 1; k >= 0; k--) {
				if (mushrooms[k].X == i && mushrooms[k].Y == j) {
					mushrooms.RemoveAt(k);
				}
			}
		}

		/// <summary>Server or singleplayer: the rainbow mushroom at (<paramref name="i"/>, <paramref name="j"/>) was broken: the
		/// Fungimancer rises out of it (unless one is already here), with vanilla's "has awoken!" line.</summary>
		public static void SpawnFrom(int i, int j) {
			if (Main.netMode == NetmodeID.MultiplayerClient || BossAlive()) {
				return;
			}
			int type = ModContent.NPCType<Fungimancer>();
			if (!SafeSpawn.TryNewNPC(new EntitySource_TileBreak(i, j), i * 16 + 8, j * 16 + 16, type, out NPC npc, critical: true)) {
				return;
			}
			Color color = new(175, 75, 255);
			if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey("Announcement.HasAwoken", npc.GetTypeNetName()), color);
			}
			else {
				Main.NewText(Language.GetTextValue("Announcement.HasAwoken", npc.TypeName), color);
			}
		}
	}

	/// <summary>
	/// The rainbow mushroom's growth (user-set 2026-11-19: "a very rare chance for a rainbow mushroom (like a normal blue mushroom
	/// but rainbow colored on the cap) to spawn in the place of a blue mushroom on this biome (only one rainbow mushroom at a time
	/// per biome)"): each random tile update of a glowing mushroom (vanilla's <c>TileID.MushroomPlants</c>) turns it into one in
	/// <see cref="OneIn"/> (my call; a biome of ~200 mushrooms sees one about every hour of play), unless one already stands
	/// within <see cref="BiomeRange"/> tiles (one biome). Server only (vanilla runs random updates there).
	/// </summary>
	public sealed class RainbowMushroomGrowth : GlobalTile
	{
		public const int OneIn = 1500;
		public const int BiomeRange = 200;

		public override void RandomUpdate(int i, int j, int type) {
			if (type != TileID.MushroomPlants || Main.netMode == NetmodeID.MultiplayerClient || !Main.rand.NextBool(OneIn)) {
				return;
			}
			if (!TileSafety.TryGetTile(i, j, out Tile tile) || !tile.HasTile || FungimancerSystem.AnyNear(i, j, BiomeRange)
				|| !FungimancerSystem.HasRoom()) {
				return;
			}
			tile.TileType = (ushort)ModContent.TileType<RainbowMushroomTile>();
			tile.TileFrameX = (short)(Main.rand.Next(RainbowMushroomTile.Styles) * 18);
			tile.TileFrameY = 0;
			FungimancerSystem.Add(i, j);
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendTileSquare(-1, i, j, 1);
			}
		}
	}
}
