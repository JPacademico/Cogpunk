using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets.Ruins.Tiles
{
	/// <summary>
	/// Kelp hanging from the Fundamental Ruins' vaults (2026-11-10b): a strand of 1x1 pieces, each hanging from a solid block
	/// or the piece above. Three strands (frame x, from the column, so a strand keeps its look and neighbours differ) and two pieces (frame y: a
	/// stalk, or the tip when nothing hangs under it). Cut by anything that swings or hits it, like vines; a piece left with
	/// nothing to hang from falls (and so does all of the strand under it), as vanilla's vines do.
	/// <para>D0: <see cref="TileFrame"/> reads its neighbours through <see cref="TileSafety"/>; a strand is at most as long as
	/// world generation made it, so the fall is bounded. D1: O(1) per tile.</para>
	/// </summary>
	public class FundamentalKelpTile : CogpunkTile
	{
		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileCut[Type] = true;
			Main.tileNoFail[Type] = true;
			Main.tileLavaDeath[Type] = true;
			Main.tileNoAttach[Type] = true;
			TileID.Sets.GeneralPlacementTiles[Type] = false;
			DustType = DustID.GrassBlades;
			HitSound = SoundID.Grass;
			AddMapEntry(new Color(42, 94, 82), CreateMapEntryName());
		}

		/// <summary>A piece holds on to a solid block (not a platform) or the kelp above it.</summary>
		public static bool CanHang(int i, int j, int type) {
			if (!TileSafety.TryGetTile(i, j - 1, out Tile above) || !above.HasTile) {
				return false;
			}
			return above.TileType == type || (Main.tileSolid[above.TileType] && !Main.tileSolidTop[above.TileType]);
		}

		public override bool TileFrame(int i, int j, ref bool resetFrame, ref bool noBreak) {
			if (!CanHang(i, j, Type)) {
				WorldGen.KillTile(i, j);
				return false;
			}
			Tile tile = Main.tile[i, j];
			bool tip = !TileSafety.TryGetTile(i, j + 1, out Tile below) || !below.HasTile || below.TileType != Type;
			tile.TileFrameX = (short)(i % 3 * 18);              // one strand all the way down; neighbours differ
			tile.TileFrameY = (short)(tip ? 18 : 0);
			return false;
		}
	}
}
