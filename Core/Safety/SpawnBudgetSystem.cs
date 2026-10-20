using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Safety
{
	/// <summary>
	/// Counts free NPC and projectile slots once per tick (1,200 bool checks, no allocations), so
	/// <see cref="SafeSpawn"/> can refuse spawns before the vanilla arrays fill up. Spawns made through
	/// SafeSpawn during the same tick decrement the counters; despawns are only seen next tick (conservative).
	/// </summary>
	public sealed class SpawnBudgetSystem : ModSystem
	{
		public static int FreeNPCSlots { get; internal set; } = Main.maxNPCs;
		public static int FreeProjectileSlots { get; internal set; } = Main.maxProjectiles;

		public override void OnWorldLoad() {
			Recount();
		}

		public override void PreUpdateEntities() {
			Recount();
		}

		private static void Recount() {
			int activeNPCs = 0;
			for (int i = 0; i < Main.maxNPCs; i++) {
				if (Main.npc[i].active) {
					activeNPCs++;
				}
			}

			int activeProjectiles = 0;
			for (int i = 0; i < Main.maxProjectiles; i++) {
				if (Main.projectile[i].active) {
					activeProjectiles++;
				}
			}

			FreeNPCSlots = Main.maxNPCs - activeNPCs;
			FreeProjectileSlots = Main.maxProjectiles - activeProjectiles;
		}
	}
}
