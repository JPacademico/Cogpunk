using System;
using System.IO;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// The world point the Mysterious Map's arrow leads to (player guidance towards a structure added in a later update).
	/// <para>The structure's own world generation will call <see cref="SetTarget"/> (server or world generation) once it
	/// exists; until then, and in worlds made before it, <see cref="Target"/> is a <b>placeholder</b> computed from the
	/// world's size alone: the cavern layer, <see cref="PlaceholderX"/> of the way across from the Junkyard's (left) edge.
	/// The placeholder is never saved, so a later update can still give older worlds a real target.</para>
	/// <para>D0: a target is always clamped inside the world; saved by name, read with defaults. D2: a real target is sent
	/// with the world data (<see cref="NetSend"/>); every side can compute the placeholder itself.</para>
	/// </summary>
	public sealed class MapTargetSystem : ModSystem
	{
		public const float PlaceholderX = 0.3f;          // fraction of the world's width from the left edge
		public const float PlaceholderDepth = 0.3f;      // fraction of the way from the cavern layer to the underworld
		private const int Margin = 50;

		private static Point target;
		private static bool hasTarget;

		/// <summary>True once a real structure has registered itself (otherwise <see cref="Target"/> is the placeholder).</summary>
		public static bool HasRealTarget => hasTarget;

		/// <summary>The target tile, always inside the world.</summary>
		public static Point Target => hasTarget ? target : Placeholder();

		/// <summary>The target in world pixels (centre of the tile).</summary>
		public static Vector2 TargetWorld => Target.ToWorldCoordinates();

		/// <summary>Server or world generation: point the map at a real structure (synced with the world data).</summary>
		public static void SetTarget(Point tile) {
			target = Clamp(tile);
			hasTarget = true;
		}

		private static Point Placeholder() {
			int x = (int)(Main.maxTilesX * PlaceholderX);
			int y = (int)(Main.rockLayer + (Main.UnderworldLayer - Main.rockLayer) * PlaceholderDepth);
			return Clamp(new Point(x, y));
		}

		private static Point Clamp(Point p) {
			int maxX = Math.Max(Margin + 1, Main.maxTilesX - Margin);
			int maxY = Math.Max(Margin + 1, Main.maxTilesY - Margin);
			return new Point(Math.Clamp(p.X, Margin, maxX), Math.Clamp(p.Y, Margin, maxY));
		}

		public override void ClearWorld() {
			target = default;
			hasTarget = false;
		}

		public override void SaveWorldData(TagCompound tag) {
			if (hasTarget) {
				tag["mapTargetX"] = target.X;
				tag["mapTargetY"] = target.Y;
			}
		}

		public override void LoadWorldData(TagCompound tag) {
			hasTarget = tag.ContainsKey("mapTargetX") && tag.ContainsKey("mapTargetY");
			target = hasTarget ? Clamp(new Point(tag.GetInt("mapTargetX"), tag.GetInt("mapTargetY"))) : default;
		}

		public override void NetSend(BinaryWriter writer) {
			writer.Write(hasTarget);
			writer.Write(target.X);
			writer.Write(target.Y);
		}

		public override void NetReceive(BinaryReader reader) {
			hasTarget = reader.ReadBoolean();
			int x = reader.ReadInt32(), y = reader.ReadInt32();
			target = hasTarget ? Clamp(new Point(x, y)) : default;
		}
	}
}
