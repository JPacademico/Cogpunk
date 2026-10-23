using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Scrap.Items
{
	/// <summary>Crafting material from extractinating <see cref="RustedScrap"/> (33%, 1-4 per find).</summary>
	public class RustedMetal : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 25;
		}

		public override void SetDefaults() {
			Item.width = 24;
			Item.height = 20;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(copper: 80);
			Item.rare = ItemRarityID.White;
		}
	}
}
