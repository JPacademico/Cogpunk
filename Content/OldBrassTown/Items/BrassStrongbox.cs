using Cogpunk.Content.OldBrassTown.Tiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>The Brass Strongbox picked up after its lock is open (<see cref="BrassStrongboxTile"/>, style 0): an ordinary
	/// chest of riveted brass. No recipe: there is one, in the bank vault of Old Brass Town.</summary>
	public class BrassStrongbox : CogpunkItem
	{
		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<BrassStrongboxTile>());
			Item.width = 32;
			Item.height = 30;
			Item.value = Item.sellPrice(silver: 40);
		}
	}
}
