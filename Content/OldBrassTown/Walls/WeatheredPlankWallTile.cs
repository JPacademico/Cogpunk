using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Walls
{
	/// <summary>Weathered Plank Wall (2026-11-03): the board walls inside Old Brass Town's buildings, and a placeable wall
	/// that makes valid housing.</summary>
	public class WeatheredPlankWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.WoodFurniture;
			AddMapEntry(new Color(74, 52, 40));
			RegisterItemDrop(ModContent.ItemType<Items.WeatheredPlankWall>());
		}
	}
}
