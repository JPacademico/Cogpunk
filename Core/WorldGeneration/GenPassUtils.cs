using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Terraria.WorldBuilding;

namespace Cogpunk.Core.WorldGeneration
{
	/// <summary>Helpers for <c>ModSystem.ModifyWorldGenTasks</c>.</summary>
	public static class GenPassUtils
	{
		/// <summary>
		/// Inserts <paramref name="pass"/> after the vanilla pass named <paramref name="anchorName"/>
		/// (for example "Shinies"). If another mod removed or renamed it, the pass is appended at the end
		/// and a warning is logged, so the world still generates (D0).
		/// </summary>
		public static void InsertAfter(List<GenPass> tasks, string anchorName, GenPass pass, ref double totalWeight) {
			int index = -1;
			for (int i = 0; i < tasks.Count; i++) {
				if (tasks[i].Name == anchorName) {
					index = i;
					break;
				}
			}

			if (index < 0) {
				SafeLog.Warn("WorldGen.MissingAnchor:" + anchorName, "Pass '{0}' not found; appending '{1}' at the end.", anchorName, pass.Name);
				tasks.Add(pass);
			}
			else {
				tasks.Insert(index + 1, pass);
			}
			totalWeight += pass.Weight;
		}
	}
}
