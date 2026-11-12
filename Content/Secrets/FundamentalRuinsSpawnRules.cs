using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// The Fundamental Ruins' spawns (user, 2026-11-10b: "disable normal enemy spawn on the area as we will add our enemies
	/// later"): no natural spawn in the ruins' box. vanilla's (pool entry 0, decompiled <c>NPCLoader.ChooseSpawn</c>: "let
	/// vanilla choose") and Cogpunk's own enemies of other places (the Underground's) are removed; other mods' are left
	/// alone, as Coghaven's rule does. The ruins have no enemy of their own again: the Rhino Beetle (2026-11-11) moved to the
	/// Hardmode jungle the same day (user: "make the rhino a rare enemy of the jungle on hardmode instead of the ruins now");
	/// an enemy added for the ruins later asks <see cref="SpawnWeight"/> and must be kept out of the removal below. Invasions and the
	/// lunar pillars are kept. O(1) box test on the spawn tile (D1), on the server or in singleplayer (D2).
	/// </summary>
	public sealed class FundamentalRuinsSpawnRules : GlobalNPC
	{
		private const int VanillaPoolEntry = 0;

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => false;   // a global hook only

		public override void EditSpawnPool(IDictionary<int, float> pool, NPCSpawnInfo spawnInfo) {
			if (spawnInfo.Invasion || InPillarZone(spawnInfo.Player)
				|| !FundamentalRuinsSystem.ContainsTile(new Point(spawnInfo.SpawnTileX, spawnInfo.SpawnTileY))) {
				return;
			}
			pool.Remove(VanillaPoolEntry);
			foreach (ModNPC npc in Mod.GetContent<ModNPC>()) {
				pool.Remove(npc.Type);                             // the ruins' own enemies are still to come
			}
		}

		/// <summary><paramref name="weight"/> for a spawn on a tile in the ruins (no invasion or pillar zone); 0 elsewhere.</summary>
		public static float SpawnWeight(NPCSpawnInfo info, float weight) {
			if (info.Invasion || InPillarZone(info.Player)) {
				return 0f;
			}
			return FundamentalRuinsSystem.ContainsTile(new Point(info.SpawnTileX, info.SpawnTileY)) ? weight : 0f;
		}

		private static bool InPillarZone(Player player) {
			return player != null && (player.ZoneTowerSolar || player.ZoneTowerVortex || player.ZoneTowerNebula || player.ZoneTowerStardust);
		}
	}
}
