using Cogpunk.Content.Research.Items;
using Cogpunk.Content.Research.UI;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.Enums;
using Terraria.GameContent.ObjectInteractions;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Research.Tiles
{
	/// <summary>
	/// The Ancient Research Table (user-set 2026-11-18: "this research table structure can be interacted with right click and it
	/// should open a menu with nodes"): a 3x2 oak table with clay pots of ink and the ancient book open on it, glowing jade. Right
	/// click opens the research window (<see cref="ResearchUISystem.Open"/>) with a smart-interact outline, as vanilla's stations;
	/// it counts as a table for housing. A soft jade light.
	/// <para>D2: the window is the clicking client's; each player's research is their own. D0: the top-left is found from the
	/// frame, bounded by the 3x2 size.</para>
	/// </summary>
	public class AncientResearchTableTile : CogpunkTile
	{
		public const int Width = 3, Height = 2;

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = true;
			Main.tileLighted[Type] = true;
			Main.tileTable[Type] = true;
			Main.tileSolidTop[Type] = true;
			TileID.Sets.HasOutlines[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;
			TileID.Sets.IgnoredByNpcStepUp[Type] = true;
			AddToArray(ref TileID.Sets.RoomNeeds.CountsAsTable);
			AdjTiles = new int[] { TileID.Tables };
			DustType = DustID.WoodFurniture;

			TileObjectData.newTile.CopyFrom(TileObjectData.Style3x2);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 18 };
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(110, 60, 30), CreateMapEntryName());
		}

		public override bool HasSmartInteract(int i, int j, SmartInteractScanSettings settings) => true;

		public override void NumDust(int i, int j, bool fail, ref int num) {
			num = fail ? 1 : 3;
		}

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			Tile tile = Main.tile[i, j];
			if (tile.TileFrameY == 0 && tile.TileFrameX % 54 == 18) {      // the middle top tile: the book
				r = 0.10f;
				g = 0.30f;
				b = 0.22f;
			}
		}

		/// <summary>The table's top-left tile from any of its tiles.</summary>
		public static Point TopLeft(int i, int j) {
			Tile tile = Main.tile[i, j];
			return new Point(i - tile.TileFrameX % 54 / 18, j - tile.TileFrameY / 18);
		}

		public override bool RightClick(int i, int j) {
			ResearchUISystem.Open(TopLeft(i, j));
			return true;
		}

		public override void MouseOver(int i, int j) {
			Player player = Main.LocalPlayer;
			player.noThrow = 2;
			player.cursorItemIconEnabled = true;
			player.cursorItemIconID = ModContent.ItemType<AncientResearchTable>();
		}
	}
}
