using System.Collections.Generic;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Manuals
{
	/// <summary>
	/// The crafting knowledge a character has read from <see cref="CraftingManual"/>s (2026-11-17), saved with the character by
	/// each manual's class name (D0 rule 9: by name, never by id; an old character loads with none). The future crafting
	/// mechanic asks <see cref="Knows"/>. Owner-side data: nothing else reads it, so nothing is synced.
	/// </summary>
	public sealed class ManualPlayer : ModPlayer
	{
		private const string SaveKey = "Learned";
		private const int MaxSaved = 256;                        // D0: a cap on what a save can make us hold

		private HashSet<string> learned;

		public override void Initialize() {
			learned = new HashSet<string>();
		}

		public bool Knows(string knowledge) => learned != null && knowledge != null && learned.Contains(knowledge);

		/// <summary>True if <paramref name="knowledge"/> was new.</summary>
		public bool Learn(string knowledge) => learned != null && !string.IsNullOrEmpty(knowledge) && learned.Count < MaxSaved && learned.Add(knowledge);

		public override void SaveData(TagCompound tag) {
			if (learned != null && learned.Count > 0) {
				tag[SaveKey] = new List<string>(learned);
			}
		}

		public override void LoadData(TagCompound tag) {
			learned ??= new HashSet<string>();
			learned.Clear();
			if (!tag.ContainsKey(SaveKey)) {
				return;
			}
			foreach (string knowledge in tag.GetList<string>(SaveKey)) {
				if (!string.IsNullOrEmpty(knowledge) && learned.Count < MaxSaved) {
					learned.Add(knowledge);
				}
			}
		}
	}
}
