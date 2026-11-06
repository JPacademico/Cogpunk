using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Tiles
{
	/// <summary>
	/// Weathered Planks (2026-11-03): the sun-bleached boards Old Brass Town is built of. A building block, crafted from wood
	/// at a Sawmill.
	/// </summary>
	public class WeatheredPlankTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;   // later world-gen features (micro biomes, other mods) keep off the town
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			DustType = DustID.WoodFurniture;
			AddMapEntry(new Color(126, 98, 76), CreateMapEntryName());
			RegisterItemDrop(ModContent.ItemType<Items.WeatheredPlank>());
		}
	}
}
