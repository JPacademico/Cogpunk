using System.IO;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Events
{
	/// <summary>
	/// Server -> clients: a Cogpunk invasion's state (running, kills left, size at the start), sent when it starts, on every
	/// kill (with <c>report</c>: show the progress bar, vanilla's message 78) and when it ends. Five bytes; joining players
	/// get the same values with the world data (<see cref="CogpunkInvasion.NetSend"/>). A client never sends it; one that
	/// arrives on the server, or names an unknown invasion, is dropped (D0).
	/// </summary>
	public sealed class InvasionStatePacket : CogpunkPacket
	{
		public void Send(CogpunkInvasion invasion, bool report) {
			if (Main.netMode != NetmodeID.Server || invasion == null || invasion.Index < 0) {
				return;
			}
			ModPacket packet = Begin();
			packet.Write((byte)invasion.Index);
			packet.Write((byte)((invasion.Active ? 1 : 0) | (report ? 2 : 0)));
			packet.Write((ushort)invasion.Size);
			packet.Write((ushort)invasion.SizeStart);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			int index = reader.ReadByte();
			byte flags = reader.ReadByte();
			int size = reader.ReadUInt16();
			int start = reader.ReadUInt16();
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				SafeLog.Warn("Net.InvasionState.FromClient", "Dropped an invasion state packet sent by client {0}.", sender);
				return;
			}
			if (index >= CogpunkInvasion.All.Count) {
				SafeLog.Warn("Net.InvasionState.BadIndex", "Dropped an invasion state packet for unknown invasion {0}.", index);
				return;
			}
			CogpunkInvasion.All[index].Receive((flags & 1) != 0, size, start, (flags & 2) != 0);
		}
	}
}
