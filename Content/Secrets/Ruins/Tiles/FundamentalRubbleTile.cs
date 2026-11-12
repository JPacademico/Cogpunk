using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Tiles
{
	/// <summary>
	/// Rubble: the collapses that close the Fundamental Ruins' tunnels (user-set 2026-11-11: "the left one leading to tunnels
	/// with some blocked passages that have to be mined out to progress into the main arena chamber"). Broken stone with dark
	/// gaps, ragged where it shows, so a collapse reads at a glance; any pickaxe clears it (a little slower than stone) and it
	/// gives back Fundamental Bricks. Merges with the ruins' other blocks. Art: art/secrets/make_fundamental_ruins_art.py.
	/// </summary>
	public class FundamentalRubbleTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			RuinBlocks.Merge(Type);
			MineResist = 1.5f;
			DustType = DustID.Stone;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(42, 70, 66), CreateMapEntryName());
			RegisterItemDrop(ModContent.ItemType<Items.FundamentalBrick>());
		}
	}
}
