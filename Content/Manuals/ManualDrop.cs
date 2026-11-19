using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Manuals
{
	/// <summary>
	/// A boss's <see cref="CraftingManual"/> (user, 2026-11-17: "on jadey first kill she should always drop a jade-shaper
	/// manual ... it should drop individually (one for every player, like the boss bags)"): on the first defeat in a world, every
	/// mode, one copy for each player who fought (<see cref="SafeSpawn.TryDropInstanced"/>: vanilla's boss-bag delivery,
	/// decompiled <c>CommonCode.DropItemLocalPerClientAndSetNPCMoneyTo0</c>, without the money reset, so Classic keeps its coins).
	/// The manual's own world flag (<see cref="CraftingManual.DroppedFlag"/>) marks it dropped, set on the server the moment it
	/// drops and sent with the world data (as <c>AlarmHeadDrop</c> and the Combinator's <c>BlueprintDrop</c> do); a world that
	/// had already beaten the boss before manuals existed gets its copy from the next defeat. Loot runs on the server or in
	/// singleplayer (D2).
	/// </summary>
	public sealed class ManualDrop : ItemDropWithConditionRule
	{
		private readonly int flag;

		private ManualDrop(int itemType, int flag) : base(itemType, 1, 1, 1, new FirstDropCondition(flag)) {
			this.flag = flag;
		}

		/// <summary>The rule for manual <typeparamref name="T"/> (built once, at loot setup).</summary>
		public static ManualDrop Of<T>() where T : CraftingManual {
			T manual = ModContent.GetInstance<T>();
			return new ManualDrop(manual.Type, manual.DroppedFlag);
		}

		public override ItemDropAttemptResult TryDroppingItem(DropAttemptInfo info) {
			if (info.npc == null || WorldFlagSystem.Get(flag)) {
				return new ItemDropAttemptResult { State = ItemDropAttemptResultState.DoesntFillConditions };
			}
			SafeSpawn.TryDropInstanced(info.npc, itemId, 1);
			WorldFlagSystem.Flag(flag) = true;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.WorldData);
			}
			return new ItemDropAttemptResult { State = ItemDropAttemptResultState.Success };
		}

		private sealed class FirstDropCondition : IItemDropRuleCondition
		{
			private readonly int flag;

			public FirstDropCondition(int flag) {
				this.flag = flag;
			}

			public bool CanDrop(DropAttemptInfo info) => !WorldFlagSystem.Get(flag);

			public bool CanShowItemDropInUI() => true;

			public string GetConditionDescription() => Language.GetTextValue("Mods.Cogpunk.DropConditions.ManualFirstKill");
		}
	}
}
