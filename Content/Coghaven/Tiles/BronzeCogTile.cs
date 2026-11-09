using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.Enums;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Coghaven.Tiles
{
	/// <summary>
	/// Bronze Cog (2026-11-06): a 6x6 bronze cog with a jade hub that turns standing on its axle: the two tiles under its
	/// middle hold it (no wall needed behind it, so in the open sky its corners stay clear). Coghaven's island is "a base of
	/// cloud and cogs" (user): they turn in sockets on its flanks, by the Main Hall's throne, in its engine deck and on the
	/// pagoda's mast.
	/// <para>Animated: <see cref="Frames"/> frames of 5 degrees (its six spokes repeat every 60 degrees) on a
	/// <see cref="FrameHeight"/> px stride, a frame every <see cref="TicksPerFrame"/> ticks, so it turns once in 9.6 s.
	/// Style 0 turns clockwise, style 1 (the second column of the sheet, world generation's meshing partner) the other way:
	/// <see cref="AnimateIndividualTile"/> reads the frames backwards for it. O(1), no allocation.</para>
	/// </summary>
	public class BronzeCogTile : CogpunkTile
	{
		public const int Size = 6;
		public const int Frames = 12;
		public const int TicksPerFrame = 8;
		public const int FrameHeight = Size * 18;               // 108
		public const int StyleWidth = Size * 18;                // 108: style 1 is the second column

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = false;
			TileID.Sets.DisableSmartCursor[Type] = true;

			DustType = DustID.Gold;
			AnimationFrameHeight = FrameHeight;

			TileObjectData.newTile.Width = Size;
			TileObjectData.newTile.Height = Size;
			TileObjectData.newTile.Origin = new Point16(2, Size - 1);
			TileObjectData.newTile.AnchorBottom = new AnchorData(AnchorType.SolidTile | AnchorType.SolidWithTop | AnchorType.SolidSide, 2, 2);
			TileObjectData.newTile.UsesCustomCanPlace = true;
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 16, 16, 16, 16, 16 };
			TileObjectData.newTile.CoordinateWidth = 16;
			TileObjectData.newTile.CoordinatePadding = 2;
			TileObjectData.newTile.StyleHorizontal = true;
			TileObjectData.newTile.LavaDeath = false;
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(205, 163, 63), CreateMapEntryName());
			RegisterItemDrop(ModContent.ItemType<Items.BronzeCog>());     // every style (style 1 has no item of its own)
		}

		public override void NumDust(int i, int j, bool fail, ref int num) {
			num = fail ? 1 : 3;
		}

		public override void AnimateTile(ref int frame, ref int frameCounter) {
			if (++frameCounter >= TicksPerFrame) {
				frameCounter = 0;
				frame = (frame + 1) % Frames;
			}
		}

		public override void AnimateIndividualTile(int type, int i, int j, ref int frameXOffset, ref int frameYOffset) {
			if (Main.tile[i, j].TileFrameX >= StyleWidth) {
				frameXOffset = -StyleWidth;                     // style 1 draws style 0's art...
				frameYOffset = (Frames - 1 - Main.tileFrame[type]) * FrameHeight;   // ...turning the other way
			}
		}
	}
}
