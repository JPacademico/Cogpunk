using Cogpunk.Core.UI;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// The Fundamental Ruins (user-set 2026-11-10b: "a new area called Fundamental Ruins; it should always generate replacing a
	/// random spider nest area on the world; it should have double the normal spider nest area size and a Fundamental Stone in
	/// a special room arena in the middle; disable normal enemy spawn in the area as we will add our enemies later ... like
	/// ancient ruins (based on World of Warcraft's ancient naga ruins, with small puddles of water)"). Built by
	/// <see cref="Generation.FundamentalRuinsPass"/>. Active in its box (<see cref="FundamentalRuinsSystem.Contains"/>, O(1));
	/// entering shows the biome title to the local player. High priority: it sits in the caverns, among other underground
	/// biomes, and wins over them. No music of its own yet.
	/// </summary>
	public class FundamentalRuinsBiome : ModBiome
	{
		public override SceneEffectPriority Priority => SceneEffectPriority.BiomeHigh;

		public override bool IsBiomeActive(Player player) => FundamentalRuinsSystem.Contains(player.Center);

		public override void OnEnter(Player player) {
			if (!Main.dedServ && player.whoAmI == Main.myPlayer) {
				BiomeTitleSystem.Show(DisplayName);
			}
		}
	}
}
