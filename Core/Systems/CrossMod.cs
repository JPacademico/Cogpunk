using System;
using Cogpunk.Core.Safety;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// Optional integration with other mods (Boss Checklist, Census, ...) through <c>Mod.Call</c> only.
	/// No hard dependency: if the other mod is missing, outdated or throws, Cogpunk carries on (D0).
	/// Call from <c>PostSetupContent</c> (see ExampleMod <c>ModIntegrationsSystem</c> for the argument formats).
	/// </summary>
	public static class CrossMod
	{
		public static bool IsLoaded(string modName) {
			return ModLoader.HasMod(modName);
		}

		/// <summary>Calls <paramref name="modName"/>'s <c>Mod.Call</c>; returns false if the mod is absent or the call fails.</summary>
		public static bool TryCall(string modName, out object result, params object[] args) {
			result = null;
			if (!ModLoader.TryGetMod(modName, out Mod mod)) {
				return false;
			}
			try {
				result = mod.Call(args);
				return true;
			}
			catch (Exception e) {
				SafeLog.Error("CrossMod." + modName, e);
				return false;
			}
		}
	}
}
