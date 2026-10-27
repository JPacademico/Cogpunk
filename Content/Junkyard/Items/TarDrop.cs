using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Junkyard.Items
{
	/// <summary>Tar Drop: a glossy blob of the Junkyard's tar, dropped by <see cref="NPCs.LivingTar"/>. A material.</summary>
	public class TarDrop : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 25;
		}

		public override void SetDefaults() {
			Item.width = 16;
			Item.height = 16;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(copper: 10);
			Item.rare = ItemRarityID.White;
		}
	}
}
