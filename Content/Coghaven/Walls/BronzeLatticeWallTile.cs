using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Walls
{
	/// <summary>Bronze Lattice Wall (2026-11-06): a see-through bronze fret lattice (the square 'hui' pattern): the palace's windows. A placeable wall that makes valid housing.</summary>
	public class BronzeLatticeWallTile : CogpunkWall
	{
		public override void SetStaticDefaults() {
			Main.wallHouse[Type] = true;
			DustType = DustID.Copper;
			AddMapEntry(new Color(138, 93, 34));
			RegisterItemDrop(ModContent.ItemType<Items.BronzeLatticeWall>());
		}
	}
}
