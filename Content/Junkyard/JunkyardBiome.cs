using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.UI;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard
{
	/// <summary>
	/// The Junkyard: replaces the left-side beach and ocean (see <see cref="Generation.JunkyardPass"/>). Active inside the
	/// bounds recorded by <see cref="JunkyardSystem"/>. Entering it shows the biome title banner to the local player only.
	/// <para>While it is active, water is drawn as steaming tar (<see cref="TarWaterStyle"/>, the way Calamity's Sulphurous
	/// Sea recolours its water) and burns with <see cref="TarPlague"/> (<see cref="TarPlayer"/>). Vanilla enemies and
	/// critters don't spawn here (<see cref="JunkyardSpawnRules"/>). Music and background are still vanilla's ocean ones
	/// for now (ZoneBeach stays true here).</para>
	/// </summary>
	public class JunkyardBiome : ModBiome
	{
		public override SceneEffectPriority Priority => SceneEffectPriority.BiomeLow;

		// Null on a dedicated server (water styles only load on clients), which is what tModLoader expects there.
		public override ModWaterStyle WaterStyle => ModContent.GetInstance<TarWaterStyle>();

		public override bool IsBiomeActive(Player player) {
			return JunkyardSystem.Contains(player.Center);
		}

		public override void OnEnter(Player player) {
			// OnEnter runs wherever this player's biomes are updated; the banner is UI for the local player only (D2).
			if (!Main.dedServ && player.whoAmI == Main.myPlayer) {
				BiomeTitleSystem.Show(DisplayName);
			}
		}
	}
}
