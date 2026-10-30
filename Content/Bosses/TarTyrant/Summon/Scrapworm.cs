using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Summon
{
	/// <summary>
	/// Scrapworm bait (user-set 2026-10-28): the caught <see cref="ScrapwormCritter"/> (vanilla's captured-critter setup:
	/// release it by using it). On a hook in the Junkyard's tar it calls Tar Tyrant instead of a fish, the way the Truffle
	/// Worm calls Duke Fishron in the ocean (<see cref="ScrapwormFishing"/>); anywhere else nothing bites it, so it is never
	/// a super bait. Consumed when the boss is pulled out.
	/// </summary>
	public class Scrapworm : CogpunkItem
	{
		public const int BaitPower = 50;                    // Master Bait's: the tyrant bites soon

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;
			ItemID.Sets.SortingPriorityBossSpawns[Type] = 12;
		}

		public override void SetDefaults() {
			Item.DefaultToCapturedCritter(ModContent.NPCType<ScrapwormCritter>());
			Item.width = 26;
			Item.height = 24;
			Item.bait = BaitPower;
			Item.value = Item.sellPrice(silver: 20);
			Item.rare = ItemRarityID.Orange;
		}
	}
}
