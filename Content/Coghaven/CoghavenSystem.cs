using System.Collections.Generic;
using System.IO;
using Cogpunk.Content.Coghaven.Generation;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Coghaven
{
	/// <summary>
	/// Where Coghaven is. World generation registers two passes: <see cref="CoghavenSitePass"/> right after vanilla's
	/// "Floating Islands" (it claims a band of sky just left of the right ocean's beach and moves any vanilla floating island
	/// out of it) and <see cref="CoghavenPass"/> after vanilla's "Final Cleanup" (it builds the island in that band, once the
	/// terrain, the Dungeon and the trees under it exist, so it can stay clear of all of them). The island's bounding box is
	/// <see cref="Area"/>, saved by name with defaults (older worlds simply have no Coghaven) and sent with the world data,
	/// so clients know it too (D2); <see cref="Contains"/> is an O(1) test for the biome.
	/// </summary>
	public sealed class CoghavenSystem : ModSystem
	{
		private const string AfterFloatingIslands = "Floating Islands";
		private const string AfterEverything = "Final Cleanup";
		public const int BiomeMargin = 6;                    // tiles round the island that still count as Coghaven

		public static Rectangle Area { get; private set; }
		public static bool Exists => Area.Width > 0 && Area.Height > 0;

		/// <summary>The columns <see cref="CoghavenSitePass"/> claimed for this world generation (x, width; empty when it
		/// didn't run). Only meaningful while a world is being generated.</summary>
		public static Rectangle Band { get; private set; }

		public static void SetArea(Rectangle area) {
			Area = area;
		}

		public static void SetBand(Rectangle band) {
			Band = band;
		}

		public static bool Contains(Vector2 worldPosition) {
			return ContainsTile(worldPosition.ToTileCoordinates());
		}

		/// <summary>The tile lies in the island's box, give or take <see cref="BiomeMargin"/> (O(1)).</summary>
		public static bool ContainsTile(Point tile) {
			if (!Exists) {
				return false;
			}
			Rectangle zone = Area;
			zone.Inflate(BiomeMargin, BiomeMargin);
			return zone.Contains(tile);
		}

		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			Band = default;
			GenPassUtils.InsertAfter(tasks, AfterFloatingIslands, new CoghavenSitePass(), ref totalWeight);
			GenPassUtils.InsertAfter(tasks, AfterEverything, new CoghavenPass(), ref totalWeight);
		}

		public override void ClearWorld() {
			Area = default;
			Band = default;
		}

		public override void SaveWorldData(TagCompound tag) {
			if (Exists) {
				tag["area"] = new[] { Area.X, Area.Y, Area.Width, Area.Height };
			}
		}

		// Missing or malformed data (older worlds, other versions) means "no Coghaven"; never index past the array.
		public override void LoadWorldData(TagCompound tag) {
			int[] a = tag.GetIntArray("area");
			Area = a != null && a.Length == 4 && a[2] > 0 && a[3] > 0 ? new Rectangle(a[0], a[1], a[2], a[3]) : default;
		}

		public override void NetSend(BinaryWriter writer) {
			writer.Write(Area.X);
			writer.Write(Area.Y);
			writer.Write(Area.Width);
			writer.Write(Area.Height);
		}

		public override void NetReceive(BinaryReader reader) {
			int x = reader.ReadInt32(), y = reader.ReadInt32(), w = reader.ReadInt32(), h = reader.ReadInt32();
			Area = w > 0 && h > 0 ? new Rectangle(x, y, w, h) : default;
		}
	}
}
