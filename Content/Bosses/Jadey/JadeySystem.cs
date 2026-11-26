using Cogpunk.Core.Systems;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey
{
	/// <summary>
	/// Jadey's world state (2026-11-16). <see cref="Downed"/> is a <see cref="WorldFlagSystem"/> flag (saved by name, sent with
	/// the world data), set by <see cref="Jadey.OnKill"/>: from then on the Jade Vault opens like any chest instead of waking
	/// her (<see cref="Coghaven.Tiles.CoghavenChestTile"/>). <see cref="TryGetBoss"/> finds the living boss in O(1) (she
	/// reports her index every tick), for her projectiles and her minions.
	/// </summary>
	public sealed class JadeySystem : ModSystem
	{
		public const string DownedFlagName = "DownedJadey";

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
			Jadey.ForgetArena();                                 // the next world's vault is measured afresh
			bossIndex = -1;
			JadeySummon.ResetCooldown();
		}

		/// <summary>Called by a living Jadey every tick on every side.</summary>
		internal static void Track(int whoAmI) {
			bossIndex = whoAmI;
			bossSeen = Main.GameUpdateCount;
		}

		/// <summary>The living Jadey, if one updated within the last two ticks.</summary>
		public static bool TryGetBoss(out Jadey boss) {
			boss = null;
			if (bossIndex < 0 || bossIndex >= Main.maxNPCs || Main.GameUpdateCount - bossSeen > 2) {
				return false;
			}
			NPC npc = Main.npc[bossIndex];
			if (!npc.active || npc.ModNPC is not Jadey j) {
				bossIndex = -1;
				return false;
			}
			boss = j;
			return true;
		}
	}
}
