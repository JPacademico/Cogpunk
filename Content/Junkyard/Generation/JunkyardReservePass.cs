using System;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Junkyard.Generation
{
	/// <summary>
	/// Claims the Junkyard's future footprint as a protected structure right after vanilla "Terrain", before any structure
	/// is placed. Everything that asks <c>GenVars.structures.CanPlace</c> first (cabins, shrines, enchanted sword shrines,
	/// campsites, jungle shrines, other mods' structures) then stays out instead of being built and later erased by
	/// <see cref="JunkyardPass"/>. The Dungeon and the Shimmer don't ask; <see cref="JunkyardLayoutPass"/> and
	/// <see cref="ShimmerPlacementPass"/> handle those.
	/// <para>The area is a safe over-estimate made before the beach exists: from the top of the world down to below the
	/// deepest possible pool floor, and from the world edge to <see cref="Padding"/> tiles past the vanilla left beach.
	/// Every vanilla structure that checks the map retries with a fixed cap or picks elsewhere, so it never blocks
	/// generation (D0 rule 3).</para>
	/// </summary>
	internal sealed class JunkyardReservePass : SafeGenPass
	{
		public const int Padding = 30;
		private const int BeachGroundBelowSurface = 15;    // the beach ground never sits deeper than this under worldSurface

		/// <summary>The reserved rectangle (tile coordinates) for this world generation; empty when the pass didn't run.</summary>
		public static Rectangle Area { get; private set; }

		public JunkyardReservePass() : base("Cogpunk: Junkyard Reservation", 0.1) {
		}

		/// <summary>Called before every world generation, so a previous world's area never leaks into the next.</summary>
		public static void ResetArea() {
			Area = default;
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			int right = JunkyardPass.ChooseStripRight() + Padding;
			int deepestTop = (int)Main.worldSurface + BeachGroundBelowSurface + JunkyardPass.BeachDrop + JunkyardPass.PoolDrop;
			int deepestFloor = JunkyardPass.MaxPoolBottom(deepestTop) + JunkyardPass.FloorThickness;
			int bottom = Math.Min(deepestFloor + Padding, Main.maxTilesY - 1);
			if (right <= 0 || bottom <= 0 || GenVars.structures == null) {
				return;
			}
			Area = new Rectangle(0, 0, right, bottom);
			GenVars.structures.AddProtectedStructure(Area);
		}
	}
}
