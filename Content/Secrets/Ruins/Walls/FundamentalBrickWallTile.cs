using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Walls
{
	/// <summary>The Fundamental Ruins' brick wall (2026-11-10b): the bond a step darker than the blocks. Art: art/secrets/make_fundamental_ruins_art.py.</summary>
	public class FundamentalBrickWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.Stone;
			AddMapEntry(new Color(23, 52, 48));
			RegisterItemDrop(ModContent.ItemType<Items.FundamentalBrickWall>());
		}
	}
}
