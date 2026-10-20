using System.IO;
using Terraria.ModLoader;

namespace Cogpunk.Core.Networking
{
	/// <summary>
	/// Base class for every Cogpunk network message: one class per message.
	/// Instances are autoloaded (ILoadable) and get a byte ID in a deterministic order,
	/// so the server and every client always agree on IDs.
	/// </summary>
	/// <example>
	/// <code>
	/// public class PressureSyncPacket : CogpunkPacket
	/// {
	/// 	public void Send(int player, byte pressure, int toClient = -1, int ignoreClient = -1) {
	/// 		ModPacket packet = Begin();
	/// 		packet.Write((byte)player);
	/// 		packet.Write(pressure);
	/// 		packet.Send(toClient, ignoreClient);
	/// 	}
	///
	/// 	public override void Receive(BinaryReader reader, int sender) {
	/// 		byte player = reader.ReadByte();
	/// 		byte pressure = reader.ReadByte();
	/// 		// Validate before use: player &lt; Main.maxPlayers, Main.player[player].active ...
	/// 	}
	/// }
	/// // Usage: ModContent.GetInstance&lt;PressureSyncPacket&gt;().Send(...);
	/// </code>
	/// </example>
	public abstract class CogpunkPacket : ILoadable
	{
		/// <summary>Network ID, assigned by <see cref="PacketRegistry.Seal"/> in PostSetupContent.</summary>
		public byte Id { get; internal set; }

		public void Load(Mod mod) {
			PacketRegistry.Register(this);
		}

		public void Unload() {
		}

		/// <summary>Creates a packet with this message's ID already written.</summary>
		protected ModPacket Begin() {
			ModPacket packet = CogpunkMod.Instance.GetPacket();
			packet.Write(Id);
			return packet;
		}

		/// <summary>
		/// Read exactly what the sender wrote, in the same order, and validate every index
		/// (players, NPCs, projectiles, tiles) before using it. Exceptions thrown here are
		/// caught and logged by <see cref="PacketRegistry"/>, and the packet is dropped.
		/// </summary>
		/// <param name="sender">On the server: the sending client's index. On clients: 256 (the server).</param>
		public abstract void Receive(BinaryReader reader, int sender);
	}
}
