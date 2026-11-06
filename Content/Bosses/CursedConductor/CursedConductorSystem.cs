using Cogpunk.Core.Systems;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor
{
	/// <summary>
	/// The Cursed Conductor's world state: <see cref="Downed"/> is a <see cref="WorldFlagSystem"/> flag (saved by name, sent
	/// with the world data) set by <see cref="CursedConductor.OnKill"/>.
	/// </summary>
	public sealed class CursedConductorSystem : ModSystem
	{
		public const string DownedFlagName = "DownedCursedConductor";

		private static int downedFlag = -1;

		public static bool Downed => WorldFlagSystem.Get(downedFlag);

		public static ref bool DownedFlag => ref WorldFlagSystem.Flag(downedFlag);

		public override void Load() {
			downedFlag = WorldFlagSystem.Register(DownedFlagName);
		}

		public override void Unload() {
			downedFlag = -1;
		}
	}
}
