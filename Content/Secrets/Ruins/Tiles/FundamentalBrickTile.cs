using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Tiles
{
	/// <summary>
	/// Fundamental Brick: the Fundamental Ruins' sea-worn teal ashlar (2026-11-10b), carved with wave scrolls.
	/// <para>Merges with the ruins' other blocks (<see cref="RuinBlocks.Merge"/>: one clump, no seam between them, D4). Not a
	/// general placement tile: later world generation keeps off the ruins. Art: art/secrets/make_fundamental_ruins_art.py.</para>
	/// </summary>
	public class FundamentalBrickTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			RuinBlocks.Merge(Type);
			DustType = DustID.Stone;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(71, 145, 126), CreateMapEntryName());
			RegisterItemDrop(ModContent.ItemType<Items.FundamentalBrick>());
		}
	}
}
