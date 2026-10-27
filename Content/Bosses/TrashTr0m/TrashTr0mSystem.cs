using Cogpunk.Core.Systems;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	/// <summary>
	/// Trash-Tr0m's world state and a cheap way to find the living boss.
	/// <para><see cref="Downed"/> is a <see cref="WorldFlagSystem"/> flag: saved by name, sent with the world data, set by
	/// <see cref="TrashTr0m.OnKill"/> (progression, Boss Checklist). Once it is set, the Junkyard Cache stops waking the
	/// boss and the Lost Key no longer drops (<see cref="FirstKillCondition"/>): the key from the first kill unlocks it.</para>
	/// <para><see cref="TryGetBoss"/>: the boss reports its index every tick (<see cref="Track"/>), so per-player code
	/// (<see cref="TrashTr0mPlayer"/>: suction, swallowing, the burst's knockback) reads it in O(1) instead of scanning the
	/// NPC array for every player every tick (D1). The camera locks of its intro and death go through
	/// <c>Core/Visuals/CinematicCamera</c>.</para>
	/// </summary>
	public sealed class TrashTr0mSystem : ModSystem
	{
		public const string DownedFlagName = "DownedTrashTr0m";

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
			TrashTr0mSummon.ResetCooldown();
		}

		/// <summary>Called by a living Trash-Tr0m every tick on every side.</summary>
		internal static void Track(int whoAmI) {
			bossIndex = whoAmI;
			bossSeen = Main.GameUpdateCount;
		}

		/// <summary>The living Trash-Tr0m, if one updated within the last two ticks.</summary>
		public static bool TryGetBoss(out TrashTr0m boss) {
			boss = null;
			if (bossIndex < 0 || bossIndex >= Main.maxNPCs || Main.GameUpdateCount - bossSeen > 2) {
				return false;
			}
			NPC npc = Main.npc[bossIndex];
			if (!npc.active || npc.ModNPC is not TrashTr0m t) {
				bossIndex = -1;
				return false;
			}
			boss = t;
			return true;
		}
	}
}
