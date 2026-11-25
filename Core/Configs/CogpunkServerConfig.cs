using System.ComponentModel;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader.Config;

namespace Cogpunk.Core.Configs
{
	/// <summary>
	/// World-wide gameplay settings (user, 2026-11-25: "it should be a global setting so the owner of the world should control if
	/// it enables or disables"). A <see cref="ConfigScope.ServerSide"/> config: tModLoader sends the server's copy to every
	/// client as it joins and whenever it changes, so every side plays by the same rules (D2). Only the world's host may change
	/// it from inside a game (<see cref="AcceptClientChanges"/>: vanilla's <c>Main.countsAsHostForGameplay</c>, the Host &amp;
	/// Play player; a dedicated server's owner edits its config file).
	/// </summary>
	public sealed class CogpunkServerConfig : ModConfig
	{
		/// <summary>Cached instance (D1: no lookups in hot paths). Null until loaded and after unload.</summary>
		public static CogpunkServerConfig Instance { get; internal set; }

		public override ConfigScope Mode => ConfigScope.ServerSide;

		[Header("Gameplay")]
		[DefaultValue(true)]
		public bool CritKillSlowMotion;

		public override void OnLoaded() {
			Instance = this;
		}

		/// <summary>Only the host may change the world's rules (tModLoader's default would let any client).</summary>
		public override bool AcceptClientChanges(ModConfig pendingConfig, int whoAmI, ref NetworkText message) {
			if (whoAmI >= 0 && whoAmI < Main.countsAsHostForGameplay.Length && Main.countsAsHostForGameplay[whoAmI]) {
				return true;
			}
			message = NetworkText.FromKey("Mods.Cogpunk.Configs.CogpunkServerConfig.HostOnly");
			return false;
		}

		/// <summary>Crit kills slow time nearby (true when the config isn't loaded yet: its default).</summary>
		public static bool CritSlowMotionOn => Instance?.CritKillSlowMotion ?? true;
	}
}
