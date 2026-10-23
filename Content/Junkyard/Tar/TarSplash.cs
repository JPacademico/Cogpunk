using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// Tar splash droplets: what flies up when something enters the tar (<see cref="TarWaterStyle.GetSplashDust"/>), and
	/// the drips falling off a player with <see cref="TarPlague"/>. Moves and fades like vanilla's water splash
	/// (<c>UpdateType = DustID.Water</c>). Sheet: 3 frames of 8x8 at the modded-dust default offsets (decompiled
	/// <c>DustLoader.SetupDust</c>: frame X 0, Y 0/10/20).
	/// </summary>
	public class TarSplash : ModDust
	{
		public override void SetStaticDefaults() {
			UpdateType = DustID.Water;
		}
	}
}
