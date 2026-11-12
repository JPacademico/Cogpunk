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
	/// The arena's rune bricks (2026-11-11): the Rune Brick's look and glow, lining the arena's vault and its dais.
	/// <para>Unbreakable (user-set 2026-11-11: "the blocks of the main arena should be unbreakable"): no pickaxe, no
	/// explosion, no hammer, no actuator (vanilla's actuators ask <c>WorldGen.CanKillTile</c>, decompiled
	/// <c>Wiring.DeActive</c>), nothing placed over it, and world generation can't clear it; it drops nothing. Merges with the
	/// ruins' other blocks (<see cref="RuinBlocks.Merge"/>).</para>
	/// </summary>
	public class FundamentalArenaRuneTile : CogpunkTile
	{
		private const string Sheet = "Cogpunk/Content/Secrets/Ruins/Tiles/FundamentalRuneTile";
		private static Asset<Texture2D> glow;

		/// <summary>The rune brick's own sheets: it looks the same, it only can't be broken.</summary>
		public override string Texture => Sheet;

		public override void Load() {
			glow = DepthLayers.RequestOptional(Sheet + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;
			TileID.Sets.CanBeClearedDuringGeneration[Type] = false;
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			Main.tileLighted[Type] = true;
			RuinBlocks.Merge(Type);
			DustType = DustID.Cobalt;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(46, 58, 100), CreateMapEntryName());
		}

		public override bool CanKillTile(int i, int j, ref bool blockDamaged) {
			blockDamaged = false;
			return false;
		}

		public override bool CanExplode(int i, int j) => false;

		public override bool CanReplace(int i, int j, int tileTypeBeingPlaced) => false;

		public override bool Slope(int i, int j) => false;

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			float k = FundamentalRuneTile.Breath(i, j);
			r = 0.04f * k;
			g = 0.09f * k;
			b = 0.24f * k;
		}

		public override void PostDraw(int i, int j, SpriteBatch spriteBatch) {
			RuinBlocks.DrawGlow(glow, i, j, spriteBatch, Color.White * FundamentalRuneTile.Breath(i, j));
		}
	}
}
