using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard
{
	/// <summary>
	/// No vanilla enemies or critters spawn in the Junkyard: it is reserved for Cogpunk's own creatures, which add
	/// themselves to the pool through <c>ModNPC.SpawnChance</c>.
	/// <para>Decompiled <c>NPCLoader.ChooseSpawn</c>: entry 0 of the pool is "let vanilla choose"; every vanilla natural
	/// spawn (surface, ocean, water, Blood Moon, Eclipse, Pumpkin and Frost Moon...) goes through it, and an empty pool
	/// simply skips that spawn attempt. Only entry 0 is removed, so other mods' spawns are untouched. Invasions and the
	/// lunar pillars also go through entry 0 and are kept: without their enemies they could never progress.</para>
	/// <para>Tested against the spawn tile, not the player, so a player standing just outside still gets no vanilla
	/// spawns inside the Junkyard, and one inside it still gets them outside. O(1) rectangle test (D1); runs on the
	/// server or in singleplayer, where vanilla spawns NPCs (D2).</para>
	/// </summary>
	public sealed class JunkyardSpawnRules : GlobalNPC
	{
		private const int VanillaPoolEntry = 0;

		// EditSpawnPool is a global hook (decompiled ChooseSpawn enumerates every override, not per entity), so this
		// global never needs to attach to an NPC instance.
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			return false;
		}

		public override void EditSpawnPool(IDictionary<int, float> pool, NPCSpawnInfo spawnInfo) {
			if (spawnInfo.Invasion || InPillarZone(spawnInfo.Player)) {
				return;
			}
			if (JunkyardSystem.ContainsTile(new Point(spawnInfo.SpawnTileX, spawnInfo.SpawnTileY))) {
				pool.Remove(VanillaPoolEntry);
			}
		}

		private static bool InPillarZone(Player player) {
			return player != null && (player.ZoneTowerSolar || player.ZoneTowerVortex || player.ZoneTowerNebula || player.ZoneTowerStardust);
		}
	}
}
