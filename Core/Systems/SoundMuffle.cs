using System;
using Terraria;
using Terraria.Audio;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// Muffled hearing for a moment, with a ringing over it (first used by the Fungimancer's rainbow mushroom blast, user
	/// 2026-11-25: "tinnitus rigging sound that briefly muflles the other game sounds"). <see cref="Muffle"/> on a client: for its
	/// length every sound effect and ambient sound plays at <see cref="Floor"/> of its volume, easing back to full over the last
	/// <see cref="EaseTicks"/>, and the music dips (vanilla's own track fade, <c>Main.musicFade</c>, which vanilla brings back up
	/// by itself); the <see cref="Tinnitus"/> ring is never muffled. Nothing touches the player's saved volume settings.
	/// <para>The volume itself is scaled by <see cref="Hooks.SoundMuffleHooks"/> (a detour: tModLoader has no hook on a playing
	/// sound's volume). D1: nothing per tick but a countdown.</para>
	/// </summary>
	public sealed class SoundMuffle : ModSystem
	{
		public const float Floor = 0.2f;
		public const int EaseTicks = 40;

		/// <summary>The ringing in the ears (Assets/Sounds/Bosses/Tinnitus.wav: two close high tones beating, fading out).</summary>
		public static readonly SoundStyle Tinnitus = new("Cogpunk/Assets/Sounds/Bosses/Tinnitus") { Volume = 0.6f, MaxInstances = 1 };

		private static int ticksLeft;

		/// <summary>How loud other sounds play now (1: normal).</summary>
		public static float Factor => ticksLeft <= 0 ? 1f : ticksLeft >= EaseTicks ? Floor : Floor + (1f - Floor) * (1f - ticksLeft / (float)EaseTicks);

		/// <summary>Muffles for <paramref name="ticks"/> (clients only; a longer one wins) and dips the music.</summary>
		public static void Muffle(int ticks) {
			if (Main.dedServ || ticks <= 0) {
				return;
			}
			ticksLeft = Math.Max(ticksLeft, Math.Min(ticks, 300));
			if (Main.curMusic >= 0 && Main.curMusic < Main.musicFade.Length) {
				Main.musicFade[Main.curMusic] = Math.Min(Main.musicFade[Main.curMusic], 0.25f);
			}
		}

		public override void PostUpdateEverything() {
			if (ticksLeft > 0) {
				ticksLeft--;
			}
		}

		public override void ClearWorld() {
			ticksLeft = 0;
		}

		public override void Unload() {
			ticksLeft = 0;
		}
	}
}
