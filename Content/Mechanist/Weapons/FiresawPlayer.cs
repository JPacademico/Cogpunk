using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// Which way the <see cref="Firesaw"/>'s current swing goes (user, 2026-11-10: "slash like a sword ... like the melee
	/// rework mods"): swings held one after another alternate, a down-slash then an up-slash; a pause (more than
	/// <see cref="ResetGap"/> ticks between two swings) starts again with a down-slash.
	/// <para>D2: flipped in <see cref="Firesaw.UseItem"/>, which vanilla calls once per use on every client that plays the
	/// player's item use (decompiled <c>Player.ApplyItemTime</c>), so every side poses the same swing; a remote client that
	/// misses a use only draws one swing the other way round (the hits are the owner's). No packet, no allocation.</para>
	/// </summary>
	public sealed class FiresawPlayer : ModPlayer
	{
		public const int ResetGap = 20;

		/// <summary>True while the current swing goes up.</summary>
		public bool Upswing;
		private uint lastSwing;

		public void BeginSwing(Player player) {
			uint now = Main.GameUpdateCount;
			bool chained = now - lastSwing <= (uint)(player.itemAnimationMax + ResetGap);
			Upswing = chained && !Upswing;
			lastSwing = now;
		}
	}
}
