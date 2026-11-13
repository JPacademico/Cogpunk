using Cogpunk.Content.Coghaven.Items;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven
{
	/// <summary>
	/// The Koi comes only out of Coghaven's pond (user, 2026-11-12: "add a new fish called Koi, it can only be fished on
	/// coghaven pond"). Vanilla rolls the catch first (decompiled <c>Projectile.FishingCheck_RollItemDrop</c>); in the sky an
	/// uncommon roll that isn't the Angler's quest fish becomes the Damselfish. Here, in fresh water inside Coghaven
	/// (<see cref="CoghavenSystem.ContainsTile"/>, the bobber's tile; the island's only water is its pond), that roll is the
	/// <see cref="Koi"/> instead. Crates, quest fish, junk and enemy catches are left alone.
	/// <para>The pond holds 84 water tiles since the same request (<see cref="Generation.CoghavenPass.PondDepth"/>): vanilla
	/// won't fish in fewer than 75. Worlds made before keep the old 30-tile pond, where vanilla says "Not Enough Water".</para>
	/// <para>D2: <c>CatchFish</c> runs on the bobber owner's client after vanilla's roll, and vanilla then gives the item as it
	/// would its own (as the Scrapworm, <see cref="Bosses.TarTyrant.Summon.ScrapwormFishing"/>). D1: an O(1) box test.</para>
	/// </summary>
	public sealed class KoiFishing : ModPlayer
	{
		public override void CatchFish(FishingAttempt attempt, ref int itemDrop, ref int npcSpawn, ref AdvancedPopupRequest sonar, ref Vector2 sonarPosition) {
			if (!attempt.uncommon || attempt.crate || attempt.inLava || attempt.inHoney || npcSpawn > 0) {
				return;
			}
			if (itemDrop <= 0 || itemDrop == attempt.questFish) {
				return;
			}
			if (!CoghavenSystem.ContainsTile(new Point(attempt.X, attempt.Y))) {
				return;
			}
			itemDrop = ModContent.ItemType<Koi>();
		}
	}
}
