using Cogpunk.Core.UI;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown
{
	/// <summary>
	/// Old Brass Town (user-set 2026-11-03): an abandoned old-west mining town in a cavern of the underground desert, the
	/// way Calamity places the Sunken Sea there (see <see cref="Generation.OldBrassTownPass"/>). Active inside the cavern
	/// recorded by <see cref="OldBrassTownSystem"/> (an O(1) ellipse test). Entering it shows the biome title banner to
	/// the local player only.
	/// <para>Its enemies (user, 2026-11-04): no vanilla spawns inside the town (<see cref="OldBrassTownSpawnRules"/>), only
	/// its own: the Brass Bandit, the Mechanical Bull, the Dinamitrom and, rarely, the Sheriff mini-boss. Its boss comes later;
	/// the underground desert's music and background stay until then. Medium priority, so the town's scene wins over the
	/// underground desert's once it has music.</para>
	/// </summary>
	public class OldBrassTownBiome : ModBiome
	{
		public override SceneEffectPriority Priority => SceneEffectPriority.BiomeMedium;

		public override bool IsBiomeActive(Player player) {
			return OldBrassTownSystem.Contains(player.Center);
		}

		public override void OnEnter(Player player) {
			// OnEnter runs wherever this player's biomes are updated; the banner is UI for the local player only (D2).
			if (!Main.dedServ && player.whoAmI == Main.myPlayer) {
				BiomeTitleSystem.Show(DisplayName);
			}
		}
	}
}
