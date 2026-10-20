using System;
using System.Collections.Generic;
using System.IO;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// Per-world boolean flags (bosses downed, biomes generated, events seen), saved by name and synced to clients.
	/// <para>Register in a content type's <c>Load()</c>: <c>id = WorldFlagSystem.Register("DownedBoilerheart");</c>.
	/// Read with <c>WorldFlagSystem.Get(id)</c>. Set a boss kill in <c>OnKill</c> with
	/// <c>NPC.SetEventFlagCleared(ref WorldFlagSystem.Flag(id), -1);</c>. For any other change made
	/// on the server, call <c>NetMessage.SendData(MessageID.WorldData)</c> afterwards.</para>
	/// <para>Flags are saved by name, so adding, removing or reordering flags never corrupts a world.
	/// Names that are no longer registered are kept and re-saved instead of being lost.</para>
	/// </summary>
	public sealed class WorldFlagSystem : ModSystem
	{
		private const string SaveKey = "flags";

		private static readonly List<string> names = new();
		private static readonly Dictionary<string, int> idsByName = new();
		private static bool[] values = Array.Empty<bool>();
		private static readonly List<string> unknownSavedFlags = new();
		private static bool discardedFlag;

		/// <summary>Registers a flag and returns its id. Call during Load, before content setup finishes.</summary>
		public static int Register(string name) {
			if (idsByName.TryGetValue(name, out int existing)) {
				return existing;
			}
			int id = names.Count;
			names.Add(name);
			idsByName[name] = id;
			Array.Resize(ref values, names.Count);
			return id;
		}

		public static bool Get(int id) {
			return (uint)id < (uint)values.Length && values[id];
		}

		/// <summary>
		/// Reference to the flag, for <c>NPC.SetEventFlagCleared(ref ..., -1)</c>. An invalid id returns a
		/// throwaway value and logs a warning instead of throwing, because this runs on boss kills (D0).
		/// </summary>
		public static ref bool Flag(int id) {
			if ((uint)id < (uint)values.Length) {
				return ref values[id];
			}
			SafeLog.Warn("WorldFlags.BadId", "Flag id {0} is not registered; the change was ignored.", id);
			discardedFlag = false;
			return ref discardedFlag;
		}

		public override void Unload() {
			names.Clear();
			idsByName.Clear();
			values = Array.Empty<bool>();
			unknownSavedFlags.Clear();
		}

		public override void ClearWorld() {
			Array.Clear(values);
			unknownSavedFlags.Clear();
		}

		public override void SaveWorldData(TagCompound tag) {
			var saved = new List<string>(unknownSavedFlags);
			for (int i = 0; i < values.Length; i++) {
				if (values[i]) {
					saved.Add(names[i]);
				}
			}
			if (saved.Count > 0) {
				tag[SaveKey] = saved;
			}
		}

		public override void LoadWorldData(TagCompound tag) {
			if (!tag.ContainsKey(SaveKey)) {
				return;
			}
			// Save data is a trust boundary: a corrupted tag must not stop the world from loading (D0).
			try {
				IList<string> saved = tag.GetList<string>(SaveKey);
				foreach (string name in saved) {
					if (idsByName.TryGetValue(name, out int id)) {
						values[id] = true;
					}
					else {
						unknownSavedFlags.Add(name);
					}
				}
			}
			catch (Exception e) {
				SafeLog.Error("WorldFlags.Load", e);
			}
		}

		// Both sides run the same mod build, so registration order (and therefore ids) match.
		// The count is still written first so a mismatch is detected and logged instead of misreading the stream.
		public override void NetSend(BinaryWriter writer) {
			writer.Write((ushort)values.Length);
			for (int i = 0; i < values.Length; i += 8) {
				byte packed = 0;
				for (int bit = 0; bit < 8 && i + bit < values.Length; bit++) {
					if (values[i + bit]) {
						packed |= (byte)(1 << bit);
					}
				}
				writer.Write(packed);
			}
		}

		public override void NetReceive(BinaryReader reader) {
			int count = reader.ReadUInt16();
			if (count != values.Length) {
				SafeLog.Warn("WorldFlags.CountMismatch", "Server sent {0} world flags but {1} are registered locally.", count, values.Length);
			}
			for (int i = 0; i < count; i += 8) {
				byte packed = reader.ReadByte();
				for (int bit = 0; bit < 8 && i + bit < count; bit++) {
					int id = i + bit;
					if (id < values.Length) {
						values[id] = (packed & (1 << bit)) != 0;
					}
				}
			}
		}
	}
}
