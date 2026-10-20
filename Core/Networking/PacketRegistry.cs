using System;
using System.Collections.Generic;
using System.IO;
using Cogpunk.Core.Safety;

namespace Cogpunk.Core.Networking
{
	/// <summary>
	/// Assigns IDs to <see cref="CogpunkPacket"/>s and routes incoming packets to them.
	/// A malformed or unknown packet is logged (rate-limited) and dropped; it never crashes the game (D0).
	/// </summary>
	internal static class PacketRegistry
	{
		private const int MaxPacketTypes = byte.MaxValue + 1;

		private static readonly List<CogpunkPacket> packets = new();
		private static bool sealedIds;

		internal static void Register(CogpunkPacket packet) {
			if (sealedIds) {
				throw new InvalidOperationException($"Packet {packet.GetType().FullName} registered after IDs were sealed.");
			}
			packets.Add(packet);
		}

		/// <summary>
		/// Sorts by full type name (ordinal) and assigns IDs. tModLoader already autoloads in name order;
		/// sorting again keeps IDs identical on every machine even if that ever changes.
		/// A load-time exception here is intentional: tModLoader reports it cleanly, unlike a runtime desync.
		/// </summary>
		internal static void Seal() {
			if (packets.Count > MaxPacketTypes) {
				throw new InvalidOperationException($"Cogpunk has {packets.Count} packet types; the byte ID limit is {MaxPacketTypes}.");
			}
			packets.Sort(static (a, b) => string.CompareOrdinal(a.GetType().FullName, b.GetType().FullName));
			for (int i = 0; i < packets.Count; i++) {
				packets[i].Id = (byte)i;
			}
			sealedIds = true;
		}

		internal static void Clear() {
			packets.Clear();
			sealedIds = false;
		}

		internal static void Dispatch(BinaryReader reader, int sender) {
			int id = -1;
			try {
				id = reader.ReadByte();
				if (!sealedIds || id >= packets.Count) {
					SafeLog.Warn("Net.UnknownPacket", "Dropped packet with unknown id {0} from sender {1}.", id, sender);
					return;
				}
				packets[id].Receive(reader, sender);
			}
			catch (Exception e) {
				string name = id >= 0 && id < packets.Count ? packets[id].GetType().Name : "unknown";
				SafeLog.Error("Net.Receive." + name, e);
			}
		}
	}
}
