using System;
using Cogpunk.Core.Safety;
using Terraria.IO;
using Terraria.WorldBuilding;

namespace Cogpunk.Core.WorldGeneration
{
	/// <summary>
	/// Base for every Cogpunk world-generation pass. If a pass throws, the error is logged and world
	/// creation continues without that feature, instead of failing the whole world (D0).
	/// Rules for <see cref="Generate"/>: use only <c>WorldGen.genRand</c>, check bounds with
	/// <see cref="TileSafety.InWorld"/>, and give every retry loop a fixed attempt cap.
	/// </summary>
	public abstract class SafeGenPass : GenPass
	{
		protected SafeGenPass(string name, double loadWeight) : base(name, loadWeight) {
		}

		protected sealed override void ApplyPass(GenerationProgress progress, GameConfiguration configuration) {
			try {
				Generate(progress, configuration);
			}
			catch (Exception e) {
				SafeLog.Error("WorldGen." + Name, e);
			}
		}

		protected abstract void Generate(GenerationProgress progress, GameConfiguration configuration);
	}
}
