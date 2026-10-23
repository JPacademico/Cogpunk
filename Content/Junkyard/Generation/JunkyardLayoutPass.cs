using Cogpunk.Core.WorldGeneration;
using Terraria;
using Terraria.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Junkyard.Generation
{
	/// <summary>
	/// Keeps the Dungeon away from the Junkyard, which always replaces the left beach: on worlds where vanilla rolled the
	/// Dungeon onto the left, the whole left/right layout is mirrored so the Dungeon goes right instead.
	/// <para>Runs right after vanilla "Reset", where every side-dependent choice is made (decompiled <c>WorldGen</c>
	/// "Reset" pass) and before "Terrain" reads any of it: <c>dungeonSide</c>, the jungle origin, the snow strip, both
	/// beach widths (the beach opposite the Dungeon is 40 tiles wider, the other 20) and the Dungeon's x. Mirroring each
	/// value gives exactly what vanilla would have rolled for a right-side Dungeon, in every special seed too (the drunk
	/// world's snow swap and the remix jungle range are symmetric), and uses no random numbers, so the rest of the world
	/// still follows the seed.</para>
	/// <para>Consequence: the Jungle, the Shimmer and the Jungle Temple are always on the left (vanilla keeps them opposite
	/// the Dungeon); <see cref="ShimmerPlacementPass"/> moves the Shimmer clear of the Junkyard.</para>
	/// </summary>
	internal sealed class JunkyardLayoutPass : SafeGenPass
	{
		public JunkyardLayoutPass() : base("Cogpunk: Junkyard Layout", 0.1) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			if (GenVars.dungeonSide >= 0) {
				return;                                      // already on the right (or not rolled: leave vanilla alone)
			}
			int width = Main.maxTilesX;
			GenVars.dungeonSide = 1;
			GenVars.jungleOriginX = width - GenVars.jungleOriginX;

			int snowLeft = GenVars.snowOriginLeft;
			GenVars.snowOriginLeft = width - GenVars.snowOriginRight;
			GenVars.snowOriginRight = width - snowLeft;

			int leftBeachEnd = GenVars.leftBeachEnd;
			GenVars.leftBeachEnd = width - GenVars.rightBeachStart;
			GenVars.rightBeachStart = width - leftBeachEnd;

			GenVars.dungeonLocation = width - GenVars.dungeonLocation;
		}
	}
}
