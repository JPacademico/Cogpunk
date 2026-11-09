using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Tiles
{
	/// <summary>
	/// Jade in the rock: nuggets of green jade set in grey stone, the block a <see cref="Items.Jade"/> is mined from (user,
	/// 2026-11-09: "same behaviour and spawn as other default gems"). Set up like vanilla's gem tiles (decompiled 1.4.4
	/// <c>Main</c>: the Emerald, tile 65: solid, blocks light, <c>tileStone</c> so it frames and merges as stone, a sparkle
	/// (<c>tileShine</c> 900, <c>tileShine2</c>), the spelunker glow; any pickaxe mines it; no ore-finder entry, as vanilla's gems
	/// have none). Placed by <see cref="Generation.JadeGemPass"/>. Art: art/gems/make_jade_art.py (a seamless block, D4 rule 7).
	/// </summary>
	public class JadeTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			Main.tileStone[Type] = true;
			Main.tileShine2[Type] = true;
			Main.tileShine[Type] = 900;
			Main.tileSpelunker[Type] = true;
			DustType = DustID.GemEmerald;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(58, 166, 118), CreateMapEntryName());
			RegisterItemDrop(ModContent.ItemType<Items.Jade>());
		}
	}
}
