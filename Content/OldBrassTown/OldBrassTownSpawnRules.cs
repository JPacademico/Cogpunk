using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown
{
	/// <summary>
	/// Old Brass Town's spawns (user, 2026-11-04: "remove normal enemy spawn on the Old Brass Town biome and add new
	/// enemies"): no vanilla enemy or critter spawns inside the town; only its own outlaws and machines do (the Brass Bandit,
	/// the Mechanical Bull, the Dinamitrom and, rarely, the Sheriff), which ask <see cref="TownSpawnWeight"/> in their
	/// <c>SpawnChance</c>.
	/// <para>Same rule as the Junkyard (decompiled <c>NPCLoader.ChooseSpawn</c>): pool entry 0 is "let vanilla choose", so
	/// removing it drops every vanilla natural spawn and leaves other mods' entries alone. Invasions and the lunar pillars are
	/// kept (without their enemies they could never progress). Tested against the spawn tile (an O(1) ellipse test, D1), on
	/// the server or in singleplayer where vanilla spawns NPCs (D2). The rate is the underground desert's own.</para>
	/// </summary>
	public sealed class OldBrassTownSpawnRules : GlobalNPC
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
			if (OldBrassTownSystem.ContainsTile(new Point(spawnInfo.SpawnTileX, spawnInfo.SpawnTileY))) {
				pool.Remove(VanillaPoolEntry);
			}
		}

		/// <summary><paramref name="weight"/> for a spawn on a tile inside the town (not in water, no invasion or pillar
		/// zone); 0 anywhere else. O(1) (D1).</summary>
		public static float TownSpawnWeight(NPCSpawnInfo info, float weight) {
			if (info.Water || info.Invasion || InPillarZone(info.Player)) {
				return 0f;
			}
			return OldBrassTownSystem.ContainsTile(new Point(info.SpawnTileX, info.SpawnTileY)) ? weight : 0f;
		}

		private static bool InPillarZone(Player player) {
			return player != null && (player.ZoneTowerSolar || player.ZoneTowerVortex || player.ZoneTowerNebula || player.ZoneTowerStardust);
		}
	}
}
