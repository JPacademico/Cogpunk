using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Tiles
{
	/// <summary>
	/// Tarnished Brass Plating (2026-11-03): riveted brass sheets with patina, Old Brass Town's roofs and signs. A building
	/// block, rolled from Tarnished Brass Bars at a Furnace.
	/// </summary>
	public class TarnishedBrassPlatingTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;   // later world-gen features (micro biomes, other mods) keep off the town
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			MineResist = 1.5f;
			DustType = DustID.Gold;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(206, 162, 64), CreateMapEntryName());
			RegisterItemDrop(ModContent.ItemType<Items.TarnishedBrassPlating>());
		}
	}
}
