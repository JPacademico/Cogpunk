using System;
using System.Collections.Generic;
using System.Reflection;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Graphics.Effects;

namespace Cogpunk.Core.Hooks
{
	/// <summary>
	/// Registers Cogpunk overlays in vanilla's <see cref="Overlays.Scene"/> and removes them again when the mod unloads.
	/// <para>Why this lives in Core/Hooks: tModLoader doesn't clean up mod overlays (decompiled <c>ModContent</c> unload
	/// code never touches <c>Overlays.Scene</c>), and <c>OverlayManager</c> has no public way to remove one. A mod type
	/// left in it keeps the whole mod assembly loaded after a reload. <see cref="Unregister"/> therefore uses reflection on
	/// one vanilla field, <c>EffectManager&lt;Overlay&gt;._effects</c> (a <c>protected internal</c> dictionary). If a
	/// vanilla update renames it, the lookup fails, one warning is logged and the overlay simply stays registered but
	/// inactive (a memory leak across reloads, never a crash) (D0 rule 14).</para>
	/// Client only: overlays are visuals, and the dedicated server never draws.
	/// </summary>
	public static class SceneOverlayRegistry
	{
		// OverlayManager only drops a fading overlay from its active list inside Update, which doesn't run in the main menu
		// where mods unload. One update with 10 s elapsed finishes vanilla's 1-second fade at once.
		private static readonly GameTime FlushFades = new(TimeSpan.Zero, TimeSpan.FromSeconds(10));

		public static void Register(string key, Overlay overlay) {
			if (Main.dedServ) {
				return;
			}
			Overlays.Scene[key] = overlay;
		}

		public static void Unregister(string key) {
			if (Main.dedServ) {
				return;
			}
			Overlay overlay = Overlays.Scene[key];
			if (overlay == null) {
				return;
			}
			if (overlay.Mode != OverlayMode.Inactive) {
				Overlays.Scene.Deactivate(key);
				Overlays.Scene.Update(FlushFades);
			}
			try {
				FieldInfo field = typeof(EffectManager<Overlay>).GetField("_effects", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
				if (field?.GetValue(Overlays.Scene) is Dictionary<string, Overlay> effects) {
					effects.Remove(key);
				}
				else {
					SafeLog.Warn("Hooks.SceneOverlay.Field", "Could not find EffectManager._effects; overlay '{0}' stays registered (inactive).", key);
				}
			}
			catch (Exception e) {
				SafeLog.Error("Hooks.SceneOverlay.Remove", e);
			}
		}
	}
}
