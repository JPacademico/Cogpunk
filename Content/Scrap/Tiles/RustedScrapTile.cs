using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Tiles
{
	/// <summary>
	/// Compacted junk: replaces about 10% of silt nodes underground and forms one heap per left-side surface biome
	/// (see Content/Scrap/Generation). Mined into <see cref="RustedScrap"/>, which is extractinated.
	/// </summary>
	public class RustedScrapTile : CogpunkTile
	{
		/// <summary>
		/// Gold/Platinum pickaxe tier. Vanilla gates Demonite, Crimtane and Obsidian at the same 55%
		/// (decompiled Player.cs: <c>pickPower &lt; 55</c>); Gold Pickaxe = 55%, Platinum = 59%, Tungsten = 50%.
		/// </summary>
		public const int PickaxePower = 55;

		public override void SetStaticDefaults() {
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;

			MinPick = PickaxePower;
			MineResist = 1.5f;
			DustType = DustID.Copper;
			HitSound = SoundID.Tink;

			// Left at the default (true) on purpose: during world generation the scrap behaves exactly like the
			// silt it replaced, so later vanilla passes (ores, dungeon, temples, micro biomes) are never blocked.
			// TileID.Sets.CanBeClearedDuringGeneration[Type] = true;

			RegisterItemDrop(ModContent.ItemType<RustedScrap>());
			AddMapEntry(new Color(110, 61, 36), CreateMapEntryName());  // ~10% over the sheet's mean colour, like the old entry
		}

		// Explosives would let players skip the Gold/Platinum pickaxe gate.
		public override bool CanExplode(int i, int j) {
			return false;
		}
	}
}
