using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>Tarnished Brass Ore (see <see cref="Tiles.TarnishedBrassOreTile"/>): smelted into <see cref="TarnishedBrassBar"/>.</summary>
	public class TarnishedBrassOre : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<Tiles.TarnishedBrassOreTile>());
			Item.value = Item.sellPrice(silver: 1);
			Item.rare = ItemRarityID.Green;
		}
	}
}
