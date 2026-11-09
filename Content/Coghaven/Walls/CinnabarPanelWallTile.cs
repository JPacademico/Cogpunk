using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Walls
{
	/// <summary>Cinnabar Panel Wall (2026-11-06): red lacquered panels with gilt corner studs: the palace's rooms. A placeable wall that makes valid housing.</summary>
	public class CinnabarPanelWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.DynastyWood;
			AddMapEntry(new Color(84, 20, 28));
			RegisterItemDrop(ModContent.ItemType<Items.CinnabarPanelWall>());
		}
	}
}
