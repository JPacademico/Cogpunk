using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.QualityOfLife
{
	/// <summary>
	/// Every stackable item stacks to <see cref="Stack"/> (user, 2026-11-25: "stackable itens stacks should stack up to 9999
	/// (like the QoL mod that does this) in our mod, so theres no need for player to instal a separate mod"): vanilla's, Cogpunk's
	/// and other mods' items whose stack is over 1 and under 9999 get 9999 as they are set up (an item that doesn't stack stays
	/// that way). Coins are left alone: vanilla turns 100 of a coin into the next one (decompiled <c>Player.DoCoins</c> checks a
	/// stack of exactly 100), and the platinum coin already stacks to 9999.
	/// <para>D0: only ever raises a stack (an old save's stacks always fit); D1: once per item set-up, no per-tick work.
	/// D2: item stats are the same on every side (every client runs the same set-up).</para>
	/// </summary>
	public sealed class MaxStack : GlobalItem
	{
		public const int Stack = 9999;

		public override bool AppliesToEntity(Item entity, bool lateInstantiation) =>
			lateInstantiation && entity.maxStack > 1 && entity.maxStack < Stack;

		public override void SetDefaults(Item item) {
			int t = item.type;
			if (t > ItemID.None && t < ItemID.Sets.CommonCoin.Length && ItemID.Sets.CommonCoin[t]) {
				return;
			}
			if (item.maxStack > 1 && item.maxStack < Stack) {
				item.maxStack = Stack;
			}
		}
	}
}
