using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Junkyard.Map
{
	/// <summary>
	/// Mysterious Map: found in the Junkyard Cache. While it is the held item, a brass compass arrow circles the player and
	/// points the way to a structure that a later update adds (<see cref="Core.Systems.MapTargetSystem"/>; drawn by
	/// <see cref="MysteriousMapArrowLayer"/>). It does nothing else.
	/// </summary>
	public class MysteriousMap : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 32;
			Item.height = 28;
			Item.maxStack = 1;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Green;
		}
	}
}
