using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard
{
	/// <summary>
	/// No vanilla enemies or critters spawn in the Junkyard: it is reserved for Cogpunk's own creatures (the Rust Collector
	/// and the Living Tar), which add themselves to the pool through <c>ModNPC.SpawnChance</c> with
	/// <see cref="SurfaceSpawnWeight"/>, and spawn at the jungle's rate (<see cref="EditSpawnRate"/>).
	/// <para>Decompiled <c>NPCLoader.ChooseSpawn</c>: entry 0 of the pool is "let vanilla choose"; every vanilla natural
	/// spawn (surface, ocean, water, Blood Moon, Eclipse, Pumpkin and Frost Moon...) goes through it, and an empty pool
	/// simply skips that spawn attempt. Only entry 0 is removed, so other mods' spawns are untouched. Invasions and the
	/// lunar pillars also go through entry 0 and are kept: without their enemies they could never progress.</para>
	/// <para>Tested against the spawn tile, not the player, so a player standing just outside still gets no vanilla
	/// spawns inside the Junkyard, and one inside it still gets them outside. O(1) rectangle test (D1); runs on the
	/// server or in singleplayer, where vanilla spawns NPCs (D2).</para>
	/// <para><b>Rate</b> (user-set 2026-10-26: "the same rate enemies spawn at in the jungle"): a player inside the
	/// Junkyard gets exactly vanilla's jungle modifiers (decompiled <c>NPC.SpawnNPC</c>: spawnRate x0.4 and maxSpawns x1.5
	/// with no town NPCs nearby, x0.55/x1.4 with one, x0.7/x1.3 with two, x0.85/x1.2 with more). tModLoader calls
	/// <c>EditSpawnRate</c> after vanilla's own modifiers. Spawns still happen only outside the screen: vanilla's safe range
	/// (<c>NPC.safeRangeX/Y</c>) is untouched.</para>
	/// </summary>
	public sealed class JunkyardSpawnRules : GlobalNPC
	{
		private const int VanillaPoolEntry = 0;
		/// <summary>Living Tar weight at the pool's edge and at the far (beach) end of the yard; the Rust Collector is 1.</summary>
		public const float TarWeightAtPool = 1.2f, TarWeightFar = 0.15f;

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

		public override void EditSpawnRate(Player player, ref int spawnRate, ref int maxSpawns) {
			if (player == null || !JunkyardSystem.Contains(player.Center)) {
				return;
			}
			float town = player.townNPCs;
			float rate = town == 0f ? 0.4f : town == 1f ? 0.55f : town == 2f ? 0.7f : 0.85f;
			float max = town == 0f ? 1.5f : town == 1f ? 1.4f : town == 2f ? 1.3f : 1.2f;
			spawnRate = System.Math.Max(1, (int)(spawnRate * rate));   // feeds Main.rand.Next: must stay positive (D0)
			maxSpawns = (int)(maxSpawns * max);
		}

		/// <summary><paramref name="weight"/> for a spawn on solid ground in the Junkyard's surface strip (not in the tar
		/// pool, not in water); 0 anywhere else. O(1) rectangle tests (D1).</summary>
		public static float SurfaceSpawnWeight(NPCSpawnInfo info, float weight) {
			if (info.Water || info.Invasion || InPillarZone(info.Player)) {
				return 0f;
			}
			Point tile = new(info.SpawnTileX, info.SpawnTileY);
			return JunkyardSystem.SurfaceArea.Contains(tile) && !JunkyardSystem.PoolArea.Contains(tile) ? weight : 0f;
		}

		/// <summary>Living Tar's weight: <see cref="TarWeightAtPool"/> next to the tar pool, falling linearly to
		/// <see cref="TarWeightFar"/> at the beach end of the yard.</summary>
		public static float TarSideWeight(NPCSpawnInfo info) {
			Rectangle pool = JunkyardSystem.PoolArea;
			Rectangle surface = JunkyardSystem.SurfaceArea;
			float span = System.Math.Max(1, surface.Right - pool.Right);
			float t = MathHelper.Clamp((info.SpawnTileX - pool.Right) / span, 0f, 1f);
			return MathHelper.Lerp(TarWeightAtPool, TarWeightFar, t);
		}

		private static bool InPillarZone(Player player) {
			return player != null && (player.ZoneTowerSolar || player.ZoneTowerVortex || player.ZoneTowerNebula || player.ZoneTowerStardust);
		}
	}
}
