using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Terraria;
using Terraria.Audio;
using Terraria.ModLoader;

namespace Cogpunk.Core.Hooks
{
	/// <summary>
	/// The volume scaling behind <see cref="SoundMuffle"/>.
	/// <para>Why this lives in Core/Hooks: tModLoader has no hook on a playing sound's volume. Vanilla sets it every tick in
	/// <c>ActiveSound.Update</c> (decompiled: position falloff x the style's volume x the sound's volume x the player's volume
	/// setting, then <c>Sound.Volume</c>), so this detours that method and scales the result after the original runs, only while
	/// a muffle lasts, never music and never the ringing itself. If the detour can't be applied (a tModLoader update renamed the
	/// method), one error is logged and nothing is muffled (D0 rule 14). Clients only; tModLoader removes <c>On_</c> detours when
	/// the mod unloads.</para>
	/// </summary>
	public sealed class SoundMuffleHooks : ModSystem
	{
		public override void Load() {
			if (Main.dedServ) {
				return;
			}
			try {
				On_ActiveSound.Update += MuffleSound;
			}
			catch (Exception e) {
				SafeLog.Error("Hooks.SoundMuffle", e);
			}
		}

		private static void MuffleSound(On_ActiveSound.orig_Update orig, ActiveSound self) {
			orig(self);
			float factor = SoundMuffle.Factor;
			if (factor >= 1f || self?.Sound == null || self.Sound.IsDisposed || self.Style.Type == SoundType.Music
				|| self.Style.SoundPath == SoundMuffle.Tinnitus.SoundPath) {
				return;
			}
			self.Sound.Volume = Math.Clamp(self.Sound.Volume * factor, 0f, 1f);
		}
	}
}
