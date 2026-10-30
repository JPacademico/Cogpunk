using Cogpunk.Content.Junkyard;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Summon
{
	/// <summary>
	/// Fishing with a <see cref="Scrapworm"/> (user-set 2026-10-28: "like the Truffle Worm is used to summon Duke
	/// Fishron"). Vanilla hard-codes the Truffle Worm (decompiled <c>Projectile.FishingCheck</c>, bait 2673); a modded bait
	/// goes through the public hook instead: <see cref="CatchFish"/> runs on the bobber owner's client after vanilla rolled
	/// its catch, and an <c>npcSpawn</c> makes the bobber bite with that NPC, which vanilla pulls out where the bobber is
	/// (<c>Player.ItemCheck_CheckFishingBobber_PullBobber</c>: <c>NPC.NewNPC</c> in singleplayer, message 130 "fish out NPC"
	/// to the server in multiplayer, D2). So Tar Tyrant rises from the tar at the bobber.
	/// <list type="bullet">
	/// <item>In the Junkyard's tar (water inside <see cref="JunkyardSystem"/>, not lava or honey) with no Tar Tyrant alive:
	/// the bite is Tar Tyrant.</item>
	/// <item>Anywhere else, or with one alive: no bite at all (never a fish: it would be the best bait in the game).</item>
	/// </list>
	/// The bait is always consumed when that bite is pulled (<see cref="CanConsumeBait"/>), like the Truffle Worm.
	/// </summary>
	public sealed class ScrapwormFishing : ModPlayer
	{
		public override void CatchFish(FishingAttempt attempt, ref int itemDrop, ref int npcSpawn, ref AdvancedPopupRequest sonar, ref Vector2 sonarPosition) {
			if (attempt.playerFishingConditions.BaitItemType != ModContent.ItemType<Scrapworm>()) {
				return;
			}
			itemDrop = 0;
			npcSpawn = 0;
			if (attempt.inLava || attempt.inHoney || !JunkyardSystem.ContainsTile(new Point(attempt.X, attempt.Y))) {
				return;
			}
			int tyrant = ModContent.NPCType<TarTyrant>();
			if (NPC.AnyNPCs(tyrant)) {
				return;
			}
			npcSpawn = tyrant;
		}

		public override bool? CanConsumeBait(Item bait) {
			return bait.type == ModContent.ItemType<Scrapworm>() ? true : null;
		}
	}
}
