using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Items
{
	/// <summary>Rune Brick: mined from the Fundamental Ruins' arena (2026-11-10b); its runes keep glowing.</summary>
	public class FundamentalRune : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.FundamentalRuneTile>());
			Item.value = Item.sellPrice(copper: 20);
		}
	}
}
