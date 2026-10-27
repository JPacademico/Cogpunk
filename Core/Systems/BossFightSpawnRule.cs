using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// Project rule (user, 2026-10-26): no natural enemy spawns during a Cogpunk boss fight. While a boss that inherits
	/// <see cref="BossNPC"/> is alive, players within <see cref="BossNPC.SpawnBlockRange"/> of it get <c>maxSpawns = 0</c>.
	/// Decompiled <c>NPC.SpawnNPC</c>: a player only gets a natural spawn while <c>nearbyActiveNPCs &lt; maxSpawns</c>, so
	/// 0 stops them all (critters, events and invasions included) and nothing else; <c>spawnRate</c> is left alone
	/// (it feeds <c>Main.rand.Next</c>, which must stay positive, D0). Minions a boss spawns itself don't go through
	/// natural spawning and still appear. Players far from the fight keep their spawns.
	/// <para>EditSpawnRate is a global hook (decompiled <c>NPCLoader.EditSpawnRate</c> enumerates every override, not per
	/// entity), so this global never attaches to an NPC (D1). Runs where vanilla spawns NPCs: server or singleplayer (D2),
	/// the same side the bosses report from.</para>
	/// </summary>
	public sealed class BossFightSpawnRule : GlobalNPC
	{
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			return false;
		}

		public override void EditSpawnRate(Player player, ref int spawnRate, ref int maxSpawns) {
			if (player != null && BossNPC.IsFightNear(player.Center, BossNPC.SpawnBlockRange)) {
				maxSpawns = 0;
			}
		}
	}
}
