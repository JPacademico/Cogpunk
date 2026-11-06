using System.Collections.Generic;
using System.IO;
using Cogpunk.Content.OldBrassTown.Generation;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.OldBrassTown
{
	/// <summary>
	/// Where Old Brass Town is. World generation (<see cref="OldBrassTownPass"/>) records the cavern's outer bounds (the
	/// shell included); the town is the ellipse inscribed in that rectangle, so <see cref="ContainsTile"/> is an O(1) test
	/// instead of a tile count. Saved by name with defaults (older worlds simply have no town) and sent with the world
	/// data, so clients know the bounds too (D2).
	/// </summary>
	public sealed class OldBrassTownSystem : ModSystem
	{
		/// <summary>The vanilla pass the town follows: late, after vanilla's micro biomes, like the Junkyard and Calamity's
		/// Sunken Sea, so nothing vanilla places afterwards lands inside it (only "Water Plants", "Stalac", "Remove Broken
		/// Traps" and "Final Cleanup" follow, none of which touches the town's own tiles).</summary>
		private const string AfterVanilla = "Micro Biomes";

		public static Rectangle Area { get; private set; }
		public static bool Exists => Area.Width > 0 && Area.Height > 0;

		public static void SetArea(Rectangle area) {
			Area = area;
		}

		public static bool Contains(Vector2 worldPosition) {
			return ContainsTile(worldPosition.ToTileCoordinates());
		}

		/// <summary>Inside the ellipse inscribed in <see cref="Area"/>.</summary>
		public static bool ContainsTile(Point tile) {
			if (!Exists || !Area.Contains(tile)) {
				return false;
			}
			float rx = Area.Width * 0.5f, ry = Area.Height * 0.5f;
			float dx = (tile.X + 0.5f - (Area.X + rx)) / rx;
			float dy = (tile.Y + 0.5f - (Area.Y + ry)) / ry;
			return dx * dx + dy * dy <= 1f;
		}

		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			GenPassUtils.InsertAfter(tasks, AfterVanilla, new OldBrassTownPass(), ref totalWeight);
		}

		public override void ClearWorld() {
			Area = default;
		}

		public override void SaveWorldData(TagCompound tag) {
			if (Exists) {
				tag["area"] = new[] { Area.X, Area.Y, Area.Width, Area.Height };
			}
		}

		// Missing or malformed data (older worlds, other versions) means "no town"; never index past the array.
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
