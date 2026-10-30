using System.Collections.Generic;
using Cogpunk.Core.Systems;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Minions
{
	/// <summary>
	/// The Annoy-o-tron's <see cref="AlarmHead"/> (user-set 2026-10-28): 1 in <see cref="FirstOdds"/>, dropping to 1 in
	/// <see cref="LaterOdds"/> once one has dropped in this world (<see cref="AlarmHead.DroppedFlag"/>, a
	/// <see cref="WorldFlagSystem"/> flag: saved by name with the world, synced to clients).
	/// <para>D2: loot rules run on the server (or in singleplayer, decompiled <c>NPC.NPCLoot</c>); the flag is set there
	/// and sent with the world data. Luck applies as in vanilla's <see cref="CommonDrop"/>. D0: the flag id is checked by
	/// <see cref="WorldFlagSystem"/> (an unregistered id is ignored, never thrown).</para>
	/// </summary>
	public sealed class AlarmHeadDrop : CommonDrop
	{
		public const int FirstOdds = 10, LaterOdds = 100;

		public AlarmHeadDrop() : base(ModContent.ItemType<AlarmHead>(), FirstOdds) {
		}

		private static int CurrentOdds => WorldFlagSystem.Get(AlarmHead.DroppedFlag) ? LaterOdds : FirstOdds;

		public override ItemDropAttemptResult TryDroppingItem(DropAttemptInfo info) {
			chanceDenominator = CurrentOdds;
			ItemDropAttemptResult result = base.TryDroppingItem(info);
			if (result.State == ItemDropAttemptResultState.Success && !WorldFlagSystem.Get(AlarmHead.DroppedFlag)) {
				WorldFlagSystem.Flag(AlarmHead.DroppedFlag) = true;
				if (Main.netMode == NetmodeID.Server) {
					NetMessage.SendData(MessageID.WorldData);
				}
			}
			return result;
		}

		// The bestiary shows the rate this world has now (clients have the flag from the world data).
		public override void ReportDroprates(List<DropRateInfo> drops, DropRateInfoChainFeed ratesInfo) {
			chanceDenominator = CurrentOdds;
			base.ReportDroprates(drops, ratesInfo);
		}
	}
}
