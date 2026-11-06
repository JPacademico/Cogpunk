using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Walls
{
	/// <summary>Brass Sandstone Wall (2026-11-03): the darker strata behind Old Brass Town's cavern, and a placeable wall
	/// (vanilla's wall frame layout, art/oldbrasstown/make_oldbrasstown_art.py).</summary>
	public class BrassSandstoneWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.Sand;
			AddMapEntry(new Color(120, 82, 50));
			RegisterItemDrop(ModContent.ItemType<Items.BrassSandstoneWall>());
		}
	}
}
