using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven
{
	/// <summary>
	/// Coghaven's spawns (user, 2026-11-06: "disable normal enemy spawn on Coghaven, as we will add our new enemies";
	/// "Coghaven should be a T4 difficulty area, not locked by anything, its enemies at T4"): no vanilla enemy or critter
	/// spawns on the island; only its own (the Jade Golem; the Imperial Defender was removed 2026-11-11), which ask <see cref="SpawnWeight"/> in
	/// their <c>SpawnChance</c>. Nothing gates them: they spawn from the first night of a world.
	/// <para>The Junkyard's and Old Brass Town's rule (decompiled <c>NPCLoader.ChooseSpawn</c>): pool entry 0 is "let vanilla
	/// choose", so removing it drops every vanilla natural spawn (the sky's harpies and wyverns included) and leaves other
	/// mods' entries alone. Invasions and the lunar pillars are kept. Tested against the spawn tile (an O(1) box test, D1),
	/// on the server or in singleplayer where vanilla spawns NPCs (D2).</para>
	/// </summary>
	public sealed class CoghavenSpawnRules : GlobalNPC
	{
		private const int VanillaPoolEntry = 0;

		// EditSpawnPool is a global hook (decompiled ChooseSpawn enumerates every override), so this global never attaches
		// to an NPC instance.
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			return false;
		}

		public override void EditSpawnPool(IDictionary<int, float> pool, NPCSpawnInfo spawnInfo) {
			if (spawnInfo.Invasion || InPillarZone(spawnInfo.Player)) {
				return;
			}
			if (CoghavenSystem.ContainsTile(new Point(spawnInfo.SpawnTileX, spawnInfo.SpawnTileY))) {
				pool.Remove(VanillaPoolEntry);
			}
		}

		/// <summary><paramref name="weight"/> for a spawn on a tile in Coghaven (not in water, no invasion or pillar zone); 0
		/// anywhere else. O(1) (D1).</summary>
		public static float SpawnWeight(NPCSpawnInfo info, float weight) {
			if (info.Water || info.Invasion || InPillarZone(info.Player)) {
				return 0f;
			}
			return CoghavenSystem.ContainsTile(new Point(info.SpawnTileX, info.SpawnTileY)) ? weight : 0f;
		}

		private static bool InPillarZone(Player player) {
			return player != null && (player.ZoneTowerSolar || player.ZoneTowerVortex || player.ZoneTowerNebula || player.ZoneTowerStardust);
		}
	}
}
