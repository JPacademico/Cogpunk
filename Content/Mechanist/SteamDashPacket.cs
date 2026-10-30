using System.IO;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// Owner -> server -> other clients: a steam dash started (player, direction), so they show its looks. Two bytes.
	/// The server only relays a dash for the sender's own player and validates the index (D0); positions and velocity
	/// arrive with vanilla's player sync as usual.
	/// </summary>
	public sealed class SteamDashPacket : CogpunkPacket
	{
		public void Send(int player, int dir, int ignoreClient = -1) {
			ModPacket packet = Begin();
			packet.Write((byte)player);
			packet.Write((sbyte)(dir >= 0 ? 1 : -1));
			packet.Send(-1, ignoreClient);
		}

		public override void Receive(BinaryReader reader, int sender) {
			int player = reader.ReadByte();
			int dir = reader.ReadSByte();
			if (player >= Main.maxPlayers || !Main.player[player].active) {
				SafeLog.Warn("Net.SteamDash.BadPlayer", "Dropped a steam dash packet for player {0}.", player);
				return;
			}
			if (Main.netMode == NetmodeID.Server) {
				if (player != sender) {
					SafeLog.Warn("Net.SteamDash.Spoof", "Dropped a steam dash packet from client {0} for player {1}.", sender, player);
					return;
				}
				Main.player[player].GetModPlayer<SteamDashPlayer>().StartDash(dir);
				Send(player, dir, ignoreClient: sender);
				return;
			}
			if (player != Main.myPlayer) {
				Main.player[player].GetModPlayer<SteamDashPlayer>().StartDash(dir);
			}
		}
	}
}
