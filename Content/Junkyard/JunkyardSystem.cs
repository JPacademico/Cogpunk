using System.Collections.Generic;
using System.IO;
using Cogpunk.Content.Furniture;
using Cogpunk.Content.Junkyard.Generation;
using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Map;
using Cogpunk.Core.Safety;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.Default;
using Terraria.ModLoader.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Junkyard
{
	/// <summary>
	/// Where the Junkyard is. World generation (<see cref="JunkyardPass"/>) records two tile rectangles: the surface strip
	/// (beach + junkyard + the air over the pool) and the pool. <see cref="JunkyardBiome"/> tests the player against them,
	/// an O(1) check instead of a tile count. Saved by name with defaults (older worlds simply have no Junkyard) and sent
	/// with the world data, so clients know the bounds too (D2).
	/// </summary>
	public sealed class JunkyardSystem : ModSystem
	{
		public static Rectangle SurfaceArea { get; private set; }
		public static Rectangle PoolArea { get; private set; }
		public static bool Exists => SurfaceArea.Width > 0;

		/// <summary>The vanilla pass the Junkyard follows; it must run after the Rusted Scrap heaps so it can overwrite the
		/// left-beach heap.</summary>
		private const string AfterScrapHeaps = "Cogpunk: Rusted Scrap Heaps";
		private const string AfterVanilla = "Micro Biomes";
		private const string VanillaReset = "Reset";
		private const string VanillaTerrain = "Terrain";
		private const int LegacyPetroleumRows = 8;
		public static void SetBounds(Rectangle surface, Rectangle pool) {
			SurfaceArea = surface;
			PoolArea = pool;
		}

		public static bool Contains(Vector2 worldPosition) {
			return ContainsTile(worldPosition.ToTileCoordinates());
		}

		public static bool ContainsTile(Point tile) {
			return Exists && (SurfaceArea.Contains(tile) || PoolArea.Contains(tile));
		}

		/// <summary>
		/// Keeps vanilla's big structures away from the Junkyard before building it: the Dungeon goes right
		/// (<see cref="JunkyardLayoutPass"/>), the footprint is claimed in the structure map (<see cref="JunkyardReservePass"/>)
		/// and the Shimmer is placed past it (<see cref="ShimmerPlacementPass"/>). Then <see cref="JunkyardPass"/> builds it.
		/// </summary>
		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			JunkyardReservePass.ResetArea();
			if (tasks.Exists(static t => t.Name == VanillaReset)) {
				// Mirroring the layout is only safe before "Terrain"; appended at the end it would scramble a finished world.
				GenPassUtils.InsertAfter(tasks, VanillaReset, new JunkyardLayoutPass(), ref totalWeight);
			}
			GenPassUtils.InsertAfter(tasks, VanillaTerrain, new JunkyardReservePass(), ref totalWeight);
			GenPassUtils.Replace(tasks, ShimmerPlacementPass.VanillaName, static vanilla => new ShimmerPlacementPass(vanilla));
			bool heapsPresent = tasks.Exists(static t => t.Name == AfterScrapHeaps);
			GenPassUtils.InsertAfter(tasks, heapsPresent ? AfterScrapHeaps : AfterVanilla, new JunkyardPass(), ref totalWeight);
		}

		/// <summary>
		/// Worlds made before 2026-10-23 capped the pool with 8 rows of Petroleum tiles; the pool is all tar (water) now,
		/// and tModLoader keeps the removed tiles as <see cref="UnloadedNonSolidTile"/> placeholders. Turns those back into
		/// pool water. Runs where the world is loaded (server or singleplayer; clients get the tiles afterwards), once per
		/// load, over at most the pool's width x <see cref="LegacyPetroleumRows"/> bounds-checked tiles (D0).
		/// </summary>
		public override void PostWorldLoad() {
			if (Main.netMode == NetmodeID.MultiplayerClient || !Exists) {
				return;
			}
			AddMissingCacheItems();
			int placeholder = ModContent.TileType<UnloadedNonSolidTile>();
			Rectangle pool = PoolArea;
			int converted = 0;
			for (int x = pool.Left; x < pool.Right; x++) {
				for (int y = pool.Top; y < pool.Top + LegacyPetroleumRows && y < pool.Bottom; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile, 1) && tile.HasTile && tile.TileType == placeholder) {
						tile.ClearTile();
						tile.LiquidType = LiquidID.Water;
						tile.LiquidAmount = byte.MaxValue;
						converted++;
					}
				}
			}
			if (converted > 0) {
				SafeLog.Info("Junkyard.PetroleumMigrated", "Junkyard: an older world's Petroleum layer was turned into tar (pool water).");
			}
		}

		/// <summary>What the Junkyard Cache holds besides materials (user-set 2026-10-26): the Polisher Schematic and the
		/// Mysterious Map.</summary>
		public static int[] CacheQuestItems() => new[] { ModContent.ItemType<PolisherSchematic>(), ModContent.ItemType<MysteriousMap>() };

		/// <summary>
		/// Worlds generated before the cache held the Polisher Schematic and the Mysterious Map: a cache that is still
		/// locked (never opened, so its loot is untouched) gets whichever is missing, in its first empty slots. Idempotent
		/// (an item already inside is never added twice), so it simply runs on every load: one pass over
		/// <c>Main.maxChests</c> chest slots with an O(1) rectangle test each (D0, D1). Server or singleplayer; chest items
		/// reach clients when they open the chest.
		/// </summary>
		private static void AddMissingCacheItems() {
			int trunk = ModContent.TileType<ScrappyTrunkTile>();
			int[] quest = CacheQuestItems();
			for (int i = 0; i < Main.maxChests; i++) {
				Chest chest = Main.chest[i];
				if (chest == null || !ContainsTile(new Point(chest.x, chest.y))
					|| !TileSafety.TryGetTile(chest.x, chest.y, out Tile tile) || !tile.HasTile || tile.TileType != trunk
					|| !ScrappyTrunkTile.IsLocked(tile)) {
					continue;
				}
				int added = 0;
				foreach (int type in quest) {
					added += EnsureItem(chest, type) ? 1 : 0;
				}
				if (added > 0) {
					SafeLog.Info("Junkyard.CacheMigrated", "Junkyard: an older world's cache got the Polisher Schematic and the Mysterious Map.");
				}
			}
		}

		/// <summary>Puts one <paramref name="type"/> in the first empty slot unless the chest already holds one. True if added.</summary>
		private static bool EnsureItem(Chest chest, int type) {
			int empty = -1;
			for (int k = 0; k < chest.item.Length; k++) {
				Item item = chest.item[k];
				if (item != null && !item.IsAir && item.type == type) {
					return false;
				}
				if (empty < 0 && (item == null || item.IsAir)) {
					empty = k;
				}
			}
			if (empty < 0) {
				return false;                                // a full cache: leave it alone
			}
			chest.item[empty] ??= new Item();
			chest.item[empty].SetDefaults(type);
			chest.item[empty].stack = 1;
			return true;
		}

		public override void ClearWorld() {
			SurfaceArea = default;
			PoolArea = default;
		}

		public override void SaveWorldData(TagCompound tag) {
			if (Exists) {
				tag["surface"] = ToArray(SurfaceArea);
				tag["pool"] = ToArray(PoolArea);
			}
		}

		public override void LoadWorldData(TagCompound tag) {
			SurfaceArea = FromArray(tag.GetIntArray("surface"));
			PoolArea = FromArray(tag.GetIntArray("pool"));
		}

		public override void NetSend(BinaryWriter writer) {
			Write(writer, SurfaceArea);
			Write(writer, PoolArea);
		}

		public override void NetReceive(BinaryReader reader) {
			SurfaceArea = Read(reader);
			PoolArea = Read(reader);
		}

		private static int[] ToArray(Rectangle r) => new[] { r.X, r.Y, r.Width, r.Height };

		// Missing or malformed data (older worlds, other versions) means "no Junkyard"; never index past the array.
		private static Rectangle FromArray(int[] a) {
			if (a == null || a.Length != 4 || a[2] <= 0 || a[3] <= 0) {
				return default;
			}
			return new Rectangle(a[0], a[1], a[2], a[3]);
		}

		private static void Write(BinaryWriter writer, Rectangle r) {
			writer.Write(r.X);
			writer.Write(r.Y);
			writer.Write(r.Width);
			writer.Write(r.Height);
		}

		private static Rectangle Read(BinaryReader reader) {
			int x = reader.ReadInt32(), y = reader.ReadInt32(), w = reader.ReadInt32(), h = reader.ReadInt32();
			return w > 0 && h > 0 ? new Rectangle(x, y, w, h) : default;
		}
	}
}
