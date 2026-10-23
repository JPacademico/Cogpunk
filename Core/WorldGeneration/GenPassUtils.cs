using System;
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
			int index = IndexOf(tasks, anchorName);
			if (index < 0) {
				SafeLog.Warn("WorldGen.MissingAnchor:" + anchorName, "Pass '{0}' not found; appending '{1}' at the end.", anchorName, pass.Name);
				tasks.Add(pass);
			}
			else {
				tasks.Insert(index + 1, pass);
			}
			totalWeight += pass.Weight;
		}

		/// <summary>
		/// Swaps the pass named <paramref name="name"/> for <paramref name="wrap"/>(original), in place, so passes anchored
		/// to it still find it. The wrapper keeps the original to fall back on. World generation builds a fresh pass list
		/// every time (decompiled <c>WorldGen.GenerateWorld</c>), so wrappers never stack. Returns false (and logs once)
		/// when the pass is missing; nothing changes then.
		/// </summary>
		public static bool Replace(List<GenPass> tasks, string name, Func<GenPass, GenPass> wrap) {
			int index = IndexOf(tasks, name);
			if (index < 0) {
				SafeLog.Warn("WorldGen.MissingPass:" + name, "Pass '{0}' not found; it was not replaced.", name);
				return false;
			}
			tasks[index] = wrap(tasks[index]);
			return true;
		}

		private static int IndexOf(List<GenPass> tasks, string name) {
			for (int i = 0; i < tasks.Count; i++) {
				if (tasks[i].Name == name) {
					return i;
				}
			}
			return -1;
		}
	}
}
