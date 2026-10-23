using System;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using ReLogic.Utilities;
using Terraria;
using Terraria.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Junkyard.Generation
{
	/// <summary>
	/// Takes the place of vanilla's "Shimmer" pass (same name, so other mods' anchors still find it) and keeps the Shimmer
	/// out of the Junkyard. Vanilla puts it 200 tiles to 11% of the world width from the edge opposite the Dungeon, which
	/// <see cref="JunkyardLayoutPass"/> makes the left, where it would overlap the Junkyard pool on most small worlds;
	/// <c>WorldGen.ShimmerMakeBiome</c> only rejects spots with evil stone, it never asks the structure map.
	/// <para>This mirrors the decompiled vanilla pass (same depth range, same 200x200 protected box, same
	/// <c>GenVars.shimmerPosition</c>) but starts the x range past <see cref="JunkyardReservePass.Area"/> plus the biome's
	/// largest radius, widening to vanilla's own fallback range (up to 20% of the width) when that leaves no room.
	/// Attempts are capped (vanilla's loop is not); if they run out, if the layout isn't the expected one, or on any
	/// exception, the original vanilla pass runs instead, so a world
	/// always gets its Shimmer (D0). The Junkyard pool still checks for it afterwards. The 10th-anniversary seed uses its
	/// own depth rules and is left to vanilla.</para>
	/// </summary>
	internal sealed class ShimmerPlacementPass : GenPass
	{
		public const string VanillaName = "Shimmer";
		private const int MaxAttempts = 1500;
		private const int BiomeRadius = 125;           // ShimmerMakeBiome clears and checks X/Y +- genRand.Next(105, 125)
		private const int ProtectedSize = 200;         // vanilla's AddProtectedStructure box around the Shimmer
		private const int Clearance = 10;

		private readonly GenPass vanilla;

		public ShimmerPlacementPass(GenPass vanilla) : base(VanillaName, vanilla.Weight) {
			this.vanilla = vanilla;
		}

		protected override void ApplyPass(GenerationProgress progress, GameConfiguration configuration) {
			bool placed = false;
			try {
				placed = TryPlace();
			}
			catch (Exception e) {
				SafeLog.Error("WorldGen.Shimmer", e);
			}
			if (!placed) {
				vanilla.Apply(progress, configuration);
			}
		}

		private static bool TryPlace() {
			Rectangle reserved = JunkyardReservePass.Area;
			if (reserved.Width <= 0 || GenVars.dungeonSide < 0 || WorldGen.tenthAnniversaryWorldGen) {
				return false;                              // not the left-Shimmer layout this pass knows: vanilla decides
			}
			int width = Main.maxTilesX;
			int minX = Math.Max(200, reserved.Right + BiomeRadius + Clearance);
			int maxX = (int)(width * 0.11);
			if (maxX <= minX) {
				maxX = (int)(width * 0.2);                 // vanilla's own fallback range after 20000 failed tries
			}
			if (maxX <= minX) {
				SafeLog.Warn("WorldGen.Shimmer.NoRoom", "No room for the Shimmer past the Junkyard (x >= {0}); vanilla places it.", minX);
				return false;
			}

			// Depth range copied from the decompiled vanilla pass.
			int minY = (int)(Main.worldSurface + Main.rockLayer) / 2 + 50;
			int maxY = (int)((double)((Main.maxTilesY - 250) * 2) + Main.rockLayer) / 3;
			if (maxY > Main.maxTilesY - 330 - 100 - 30) {
				maxY = Main.maxTilesY - 330 - 100 - 30;
			}
			if (maxY <= minY) {
				maxY = minY + 50;
			}

			for (int attempt = 0; attempt < MaxAttempts; attempt++) {
				int x = WorldGen.genRand.Next(minX, maxX);
				int y = WorldGen.genRand.Next(minY, maxY);
				if (WorldGen.ShimmerMakeBiome(x, y)) {
					GenVars.shimmerPosition = new Vector2D(x, y);
					GenVars.structures?.AddProtectedStructure(new Rectangle(x - ProtectedSize / 2, y - ProtectedSize / 2, ProtectedSize, ProtectedSize));
					return true;
				}
			}
			SafeLog.Warn("WorldGen.Shimmer.Attempts", "Shimmer not placed after {0} attempts past the Junkyard; vanilla places it.", MaxAttempts);
			return false;
		}
	}
}
