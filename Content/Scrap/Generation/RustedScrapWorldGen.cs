using System.Collections.Generic;
using Cogpunk.Core.WorldGeneration;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Scrap.Generation
{
	/// <summary>
	/// Registers the Rusted Scrap passes (new worlds only):
	/// <list type="bullet">
	/// <item><see cref="ScrapNodePass"/> right after vanilla "Silt", so every later pass treats the scrap like the silt it replaced.</item>
	/// <item><see cref="ScrapMoundPass"/> after "Micro Biomes", once trees, plants and structures exist, so the heaps can avoid them.</item>
	/// </list>
	/// </summary>
	public sealed class RustedScrapWorldGen : ModSystem
	{
		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			GenPassUtils.InsertAfter(tasks, "Silt", new ScrapNodePass(), ref totalWeight);
			GenPassUtils.InsertAfter(tasks, "Micro Biomes", new ScrapMoundPass(), ref totalWeight);
		}
	}
}
