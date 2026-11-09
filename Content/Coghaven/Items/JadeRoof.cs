using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>The block (see <see cref="Tiles.JadeRoofTile"/>): mined in Coghaven.</summary>
	public class JadeRoof : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.JadeRoofTile>());
			Item.value = Item.sellPrice(copper: 20);
		}
	}
}
