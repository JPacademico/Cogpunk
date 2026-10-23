using Cogpunk.Content.Junkyard.Tiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Items
{
	/// <summary>Placeable <see cref="PolishedMetalTile"/>. Decorative only for now; mined from the Junkyard pool walls.</summary>
	public class PolishedMetal : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<PolishedMetalTile>());
			Item.width = 16;
			Item.height = 16;
			Item.value = Item.sellPrice(copper: 20);
			Item.rare = ItemRarityID.Blue;
		}
	}
}
