using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Tiles
{
	/// <summary>
	/// Rune Brick: deep blue stone carved with runes that still glow (2026-11-10b), lining the ruins' arena (<c>_Glow</c>: the runes' light, breathing slowly).
	/// <para>Merges with the ruins' other blocks (<see cref="RuinBlocks.Merge"/>: one clump, no seam between them, D4). Not a
	/// general placement tile: later world generation keeps off the ruins. Art: art/secrets/make_fundamental_ruins_art.py.</para>
	/// </summary>
	public class FundamentalRuneTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			RuinBlocks.Merge(Type);
			DustType = DustID.Cobalt;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(46, 58, 100), CreateMapEntryName());
			RegisterItemDrop(ModContent.ItemType<Items.FundamentalRune>());
			Main.tileLighted[Type] = true;
		}

		private static ReLogic.Content.Asset<Microsoft.Xna.Framework.Graphics.Texture2D> glow;

		public override void Load() {
			glow = Core.Visuals.DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		/// <summary>The runes' light: a slow breath, like the Fundamental Stone's.</summary>
		public static float Breath(int i, int j) => 0.75f + 0.25f * System.MathF.Sin(Main.GlobalTimeWrappedHourly * 1.2f + (i + j) * 0.35f);

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			float k = Breath(i, j);
			r = 0.04f * k;
			g = 0.09f * k;
			b = 0.24f * k;
		}

		public override void PostDraw(int i, int j, Microsoft.Xna.Framework.Graphics.SpriteBatch spriteBatch) {
			RuinBlocks.DrawGlow(glow, i, j, spriteBatch, Color.White * Breath(i, j));
		}
	}
}
