using System.IO;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Terraria.ModLoader;

namespace Cogpunk
{
	// Entry point. Keep this class thin: engine code lives in Core/, gameplay in Content/<Slice>/.
	// Named CogpunkMod (not Cogpunk) so the type never shadows the root namespace.
	public class CogpunkMod : Mod
	{
		public static CogpunkMod Instance { get; private set; }

		public override void Load() {
			Instance = this;
			SafeLog.Init(Logger);
		}

		public override void PostSetupContent() {
			// All ILoadable packets are registered by now; give them their network IDs.
			PacketRegistry.Seal();
		}

		public override void Unload() {
			PacketRegistry.Clear();
			CogpunkClientConfig.Instance = null;
			CogpunkServerConfig.Instance = null;
			SafeLog.Clear();
			Instance = null;
		}

		public override void HandlePacket(BinaryReader reader, int whoAmI) {
			PacketRegistry.Dispatch(reader, whoAmI);
		}
	}
}
