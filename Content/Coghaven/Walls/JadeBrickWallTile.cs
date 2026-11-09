using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Walls
{
	/// <summary>Jade Brick Wall (2026-11-06): the jade bricks a shade darker: Coghaven's terraces and the pagoda. A placeable wall that makes valid housing.</summary>
	public class JadeBrickWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.GemEmerald;
			AddMapEntry(new Color(18, 70, 58));
			RegisterItemDrop(ModContent.ItemType<Items.JadeBrickWall>());
		}
	}
}
