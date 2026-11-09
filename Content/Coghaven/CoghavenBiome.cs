using Cogpunk.Core.UI;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven
{
	/// <summary>
	/// Coghaven (user-set 2026-11-06): a floating island twice the size of a vanilla cloud island, always over the right side
	/// of the map just before the ocean's beach, a base of cloud and cogs that steam turbines seem to hold up, and on it a
	/// steampunk jade palace in red, bronze and jade, built like a dungeon (<see cref="Generation.CoghavenPass"/>). Active
	/// in and around the island's box (<see cref="CoghavenSystem.Contains"/>, O(1)); entering shows the biome title banner to
	/// the local player only.
	/// <para>A T4 area (user, 2026-11-06: "not locked by anything, but the enemies should have a T4 equivalent difficulty",
	/// the pre-Wall-of-Flesh endgame of docs/balance's tier table): vanilla's spawns are off on the island
	/// (<see cref="CoghavenSpawnRules"/>) and only its own enemies come, the Imperial Defender and the Jade Golem. No music
	/// of its own yet: the sky's stays. Medium priority, so its scene (and later its music) wins over the sky's.</para>
	/// </summary>
	public class CoghavenBiome : ModBiome
	{
		public override SceneEffectPriority Priority => SceneEffectPriority.BiomeMedium;

		public override bool IsBiomeActive(Player player) {
			return CoghavenSystem.Contains(player.Center);
		}

		public override void OnEnter(Player player) {
			// OnEnter runs wherever this player's biomes are updated; the banner is UI for the local player only (D2).
			if (!Main.dedServ && player.whoAmI == Main.myPlayer) {
				BiomeTitleSystem.Show(DisplayName);
			}
		}
	}
}
