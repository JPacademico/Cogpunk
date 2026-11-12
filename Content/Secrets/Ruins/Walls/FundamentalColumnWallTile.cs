using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Walls
{
	/// <summary>Fluted column drums (2026-11-10b): the ruins' pillars, two tiles wide, behind everything. Art: art/secrets/make_fundamental_ruins_art.py.</summary>
	public class FundamentalColumnWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.Stone;
			AddMapEntry(new Color(42, 94, 82));
			RegisterItemDrop(ModContent.ItemType<Items.FundamentalColumnWall>());
		}
	}
}
