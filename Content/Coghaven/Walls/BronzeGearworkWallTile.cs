using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Walls
{
	/// <summary>Bronze Gearwork Wall (2026-11-06): dark bronze machinery: the engine deck inside Coghaven's island, and the walls the big cogs turn on. A placeable wall that makes valid housing.</summary>
	public class BronzeGearworkWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.Copper;
			AddMapEntry(new Color(90, 58, 23));
			RegisterItemDrop(ModContent.ItemType<Items.BronzeGearworkWall>());
		}
	}
}
