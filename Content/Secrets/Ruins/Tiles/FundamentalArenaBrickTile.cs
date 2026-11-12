using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Tiles
{
	/// <summary>
	/// Ancient Brick: the Fundamental Ruins' arena (2026-11-11), slate ashlar with verdigris in its joints, an older and harder stone than the ruins' brick (it reads as different on purpose).
	/// <para>Unbreakable (user-set 2026-11-11: "the blocks of the main arena should be unbreakable"): no pickaxe, no
	/// explosion, no hammer, no actuator (vanilla's actuators ask <c>WorldGen.CanKillTile</c>, decompiled
	/// <c>Wiring.DeActive</c>), nothing placed over it, and world generation can't clear it; it drops nothing. Merges with the
	/// ruins' other blocks (<see cref="RuinBlocks.Merge"/>).</para>
	/// </summary>
	public class FundamentalArenaBrickTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;
			TileID.Sets.CanBeClearedDuringGeneration[Type] = false;
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			RuinBlocks.Merge(Type);
			DustType = DustID.Stone;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(61, 66, 78), CreateMapEntryName());
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
