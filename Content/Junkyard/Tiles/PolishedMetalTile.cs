using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tiles
{
	/// <summary>
	/// Welded, patched-up metal plating. Decorative for now; generated as the walls of the Junkyard's deep pool.
	/// Needs Hellstone-bar-tier pick power (Molten Pickaxe, 100%) and ignores explosives, so the pool can't be opened early.
	/// </summary>
	public class PolishedMetalTile : CogpunkTile
	{
		public const int PickaxePower = 100;    // Molten Pickaxe = 100% (terraria.wiki.gg); Deathbringer Pickaxe = 70% can't

		public override void SetStaticDefaults() {
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			Main.tileBrick[Type] = true;

			MinPick = PickaxePower;
			MineResist = 2f;
			DustType = DustID.Iron;
			HitSound = SoundID.Tink;

			RegisterItemDrop(ModContent.ItemType<Items.PolishedMetal>());
			AddMapEntry(new Color(127, 135, 148), CreateMapEntryName());
		}

		public override bool CanExplode(int i, int j) {
			return false;
		}
	}
}
