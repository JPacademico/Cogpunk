using System.Collections.Generic;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Events
{
	/// <summary>
	/// Natural spawns during a <see cref="CogpunkInvasion"/>, vanilla's invasion rules (decompiled <c>NPC.SpawnNPC</c>):
	/// a player in the invasion's zone (<see cref="CogpunkInvasion.RollZone"/>) gets spawnRate 20 and maxSpawns
	/// <c>defaultMaxSpawns x (2 + 0.3 x active players)</c>, and only the invasion's roster spawns
	/// (<see cref="CogpunkInvasion.FillPool"/>; entry 0, vanilla's own choice, is dropped like every other entry). Pillar
	/// zones keep their pillar spawns, as in vanilla. The Cogpunk boss rule wins: no spawns near a living boss
	/// (<see cref="BossNPC.IsFightNear"/>, D3 boss-fight rules).
	/// <para>The zone is rolled once per player per tick (<see cref="ZoneOf"/>, cached), so <c>EditSpawnRate</c> and
	/// <c>EditSpawnPool</c>, and other code asking the same tick (the Junkyard's spawn rules), agree on the 2-in-3 roll.
	/// Server and singleplayer only, where vanilla spawns NPCs (D2). Both hooks are global (decompiled
	/// <c>NPCLoader.EditSpawnRate/ChooseSpawn</c> enumerate every override), so this never attaches to an NPC (D1).</para>
	/// </summary>
	public sealed class InvasionRules : GlobalNPC
	{
		/// <summary>Vanilla's <c>NPC.defaultMaxSpawns</c> (private, decompiled: 5, never reassigned).</summary>
		public const int VanillaDefaultMaxSpawns = 5;

		private static readonly CogpunkInvasion[] zone = new CogpunkInvasion[Main.maxPlayers];
		private static readonly uint[] zoneTick = new uint[Main.maxPlayers];
		private static uint playersTick;
		private static int activePlayers;

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			return false;
		}

		public override void Unload() {
			System.Array.Clear(zone);
			System.Array.Clear(zoneTick);
		}

		/// <summary>Server: the running invasion whose zone <paramref name="player"/> is in this tick, or null.</summary>
		internal static CogpunkInvasion ZoneOf(Player player) {
			if (player == null || (uint)player.whoAmI >= Main.maxPlayers || !CogpunkInvasion.AnyActive) {
				return null;
			}
			int i = player.whoAmI;
			uint now = Main.GameUpdateCount + 1;            // + 1: tick 0 must not look already cached
			if (zoneTick[i] != now) {
				zoneTick[i] = now;
				zone[i] = null;
				var all = CogpunkInvasion.All;
				for (int k = 0; k < all.Count && zone[i] == null; k++) {
					if (all[k].RollZone(player)) {
						zone[i] = all[k];
					}
				}
			}
			return zone[i];
		}

		private static int ActivePlayers() {
			uint now = Main.GameUpdateCount + 1;
			if (playersTick != now) {
				playersTick = now;
				activePlayers = 0;
				foreach (Player p in Main.ActivePlayers) {
					activePlayers++;
				}
			}
			return activePlayers;
		}

		public override void EditSpawnRate(Player player, ref int spawnRate, ref int maxSpawns) {
			if (ZoneOf(player) == null || BossNPC.IsFightNear(player.Center, BossNPC.SpawnBlockRange)) {
				return;
			}
			maxSpawns = (int)(VanillaDefaultMaxSpawns * (2f + 0.3f * ActivePlayers()));
			spawnRate = 20;
		}

		public override void EditSpawnPool(IDictionary<int, float> pool, NPCSpawnInfo spawnInfo) {
			Player player = spawnInfo.Player;
			CogpunkInvasion invasion = ZoneOf(player);
			if (invasion == null || player.ZoneTowerSolar || player.ZoneTowerVortex || player.ZoneTowerNebula || player.ZoneTowerStardust) {
				return;
			}
			pool.Clear();
			invasion.FillPool(pool, spawnInfo);
		}
	}

	/// <summary>
	/// Invasion progress: a roster NPC killed while its invasion runs takes <see cref="CogpunkInvasion.KillValue"/> off the
	/// size (vanilla does this in <c>NPC.NPCLoot</c>, which runs where <c>OnKill</c> runs: server or singleplayer). Attaches
	/// only to roster NPCs (D1).
	/// </summary>
	public sealed class InvasionKillCredit : GlobalNPC
	{
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			if (!lateInstantiation) {
				return false;
			}
			var all = CogpunkInvasion.All;
			for (int i = 0; i < all.Count; i++) {
				if (all[i].KillValue(entity.type) > 0) {
					return true;
				}
			}
			return false;
		}

		public override void OnKill(NPC npc) {
			var all = CogpunkInvasion.All;
			for (int i = 0; i < all.Count; i++) {
				if (all[i].Active) {
					all[i].Credit(all[i].KillValue(npc.type));
				}
			}
		}
	}

	/// <summary>
	/// One invasion at a time: vanilla's invasion items (decompiled <c>Player.ItemCheck_UseEventItems</c>: the Goblin Battle
	/// Standard, the Pirate Map and the Snow Globe, which vanilla refuses while its own invasion runs) are refused while a
	/// Cogpunk invasion runs, so they are not used up for nothing. <see cref="CogpunkInvasion.Active"/> is synced, so the
	/// client that uses the item agrees with the server.
	/// </summary>
	public sealed class InvasionItemGuard : GlobalItem
	{
		public override bool AppliesToEntity(Item entity, bool lateInstantiation) {
			return entity.type == ItemID.GoblinBattleStandard || entity.type == ItemID.PirateMap || entity.type == ItemID.SnowGlobe;
		}

		public override bool CanUseItem(Item item, Player player) {
			return !CogpunkInvasion.AnyActive;
		}
	}
}
