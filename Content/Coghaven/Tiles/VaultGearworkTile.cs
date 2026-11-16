using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Tiles
{
	/// <summary>
	/// Vault Gearwork (2026-11-16): the Jade Vault's shell, Jadey's arena under the Main Hall (user: "the arena room should be
	/// unbreakable"): the island's bronze gearwork a shade darker, its gear rack inlaid with jade teeth
	/// (art/coghaven/make_coghaven_art.py), so the hardened shell reads apart from the breakable core round it.
	/// <para>Unbreakable, as the Fundamental Ruins' arena (<see cref="Secrets.Ruins.Tiles.FundamentalArenaBrickTile"/>): no
	/// pickaxe, no explosion, no actuator (vanilla's actuators ask <c>WorldGen.CanKillTile</c>, decompiled
	/// <c>Wiring.DeActive</c>), no slope or hammer, nothing placed over it, and world generation can't clear it; it drops
	/// nothing (no item). It merges with Bronze Gearwork both ways so the core and the shell meet as one clump.</para>
	/// </summary>
	public class VaultGearworkTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;
			TileID.Sets.CanBeClearedDuringGeneration[Type] = false;
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			int gearwork = ModContent.TileType<BronzeGearworkTile>();
			Main.tileMerge[Type][gearwork] = true;
			Main.tileMerge[gearwork][Type] = true;
			DustType = DustID.Copper;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(114, 74, 27), CreateMapEntryName());
		}

		public override bool CanKillTile(int i, int j, ref bool blockDamaged) {
			blockDamaged = false;
			return false;
		}

		public override bool CanExplode(int i, int j) => false;

		public override bool CanReplace(int i, int j, int tileTypeBeingPlaced) => false;

		public override bool Slope(int i, int j) => false;
	}
}
