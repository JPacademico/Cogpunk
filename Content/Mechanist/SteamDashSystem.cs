using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>Registers the steam dash key (default F). Clients only use it; it does nothing until a manual is read.</summary>
	public sealed class SteamDashSystem : ModSystem
	{
		public static ModKeybind Keybind { get; private set; }

		public override void Load() {
			Keybind = KeybindLoader.RegisterKeybind(Mod, "SteamDash", "F");
		}

		public override void Unload() {
			Keybind = null;
		}
	}
}
