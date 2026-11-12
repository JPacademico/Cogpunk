using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Items
{
	/// <summary>Coralstone: mined from the Fundamental Ruins (2026-11-10b).</summary>
	public class FundamentalCoral : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.FundamentalCoralTile>());
			Item.value = Item.sellPrice(copper: 20);
		}
	}
}
