using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Walls
{
	/// <summary>Palace Flagstone Wall (2026-11-06): the pavers a shade darker, behind the pagoda's rooms, the shrine and the
	/// terraces of Coghaven. A placeable wall that makes valid housing.</summary>
	public class PalaceFlagstoneWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.Stone;
			AddMapEntry(new Color(104, 84, 64));
			RegisterItemDrop(ModContent.ItemType<Items.PalaceFlagstoneWall>());
		}
	}
}
