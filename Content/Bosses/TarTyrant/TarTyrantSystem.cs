using Cogpunk.Core.Systems;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant
{
	/// <summary>
	/// Tar Tyrant's world state and a cheap way to find the living boss. <see cref="Downed"/> is a
	/// <see cref="WorldFlagSystem"/> flag (saved by name, sent with the world data) set by <see cref="TarTyrant.OnKill"/>.
	/// <see cref="TryGetBoss"/>: the boss reports its index every tick (<see cref="Track"/>), so the Scrapworm's fishing
	/// check finds it in O(1) (D1).
	/// </summary>
	public sealed class TarTyrantSystem : ModSystem
	{
		public const string DownedFlagName = "DownedTarTyrant";

		private static int downedFlag = -1;
		private static int bossIndex = -1;
		private static uint bossSeen;

		public static bool Downed => WorldFlagSystem.Get(downedFlag);

		public static ref bool DownedFlag => ref WorldFlagSystem.Flag(downedFlag);

		public override void Load() {
			downedFlag = WorldFlagSystem.Register(DownedFlagName);
		}

		public override void Unload() {
			downedFlag = -1;
			bossIndex = -1;
		}

		public override void OnWorldUnload() {
			bossIndex = -1;
		}

		/// <summary>Called by a living Tar Tyrant every tick on every side.</summary>
		internal static void Track(int whoAmI) {
			bossIndex = whoAmI;
			bossSeen = Main.GameUpdateCount;
		}

		/// <summary>The living Tar Tyrant, if one updated within the last two ticks.</summary>
		public static bool TryGetBoss(out TarTyrant boss) {
			boss = null;
			if (bossIndex < 0 || bossIndex >= Main.maxNPCs || Main.GameUpdateCount - bossSeen > 2) {
				return false;
			}
			NPC npc = Main.npc[bossIndex];
			if (!npc.active || npc.ModNPC is not TarTyrant t) {
				bossIndex = -1;
				return false;
			}
			boss = t;
			return true;
		}
	}
}
