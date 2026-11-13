using Cogpunk.Content.Combinator.Items;
using Cogpunk.Content.Combinator.UI;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.Enums;
using Terraria.GameContent.ObjectInteractions;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Combinator.Tiles
{
	/// <summary>
	/// The Combinator (user-set 2026-11-12: "a new hardmode crafting station called The Combinator; a new interactable core
	/// hard mode progression mechanic"): a 4x3 steam press of brass and iron, a hopper on each side (the base's and the
	/// augment's), a turning cog and a gauge over the press, a furnace window glowing under it and the output tray in front.
	/// Right click opens its window (<see cref="CombinatorUISystem.Toggle"/>), as vanilla's stations open on a right click with
	/// a smart-interact outline; it is also a crafting station for recipes that will name it. Animated like the Rust Polisher
	/// (<see cref="Frames"/> frames on a <see cref="FrameHeight"/> px stride, advanced in <see cref="AnimateTile"/>: O(1),
	/// shared by every Combinator).
	/// <para>D2: the window is the clicking client's. D0: the top-left is found from the frame, bounded by the 4x3 size.</para>
	/// </summary>
	public class CombinatorTile : CogpunkTile
	{
		public const int Width = 4, Height = 3;
		public const int Frames = 4, TicksPerFrame = 6;
		public const int FrameHeight = 56;                // 16 + 2 + 16 + 2 + 18 + 2

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = false;
			Main.tileLighted[Type] = true;
			TileID.Sets.HasOutlines[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;
			TileID.Sets.IgnoredByNpcStepUp[Type] = true;
			DustType = DustID.Copper;
			AnimationFrameHeight = FrameHeight;

			TileObjectData.newTile.CopyFrom(TileObjectData.Style3x3);
			TileObjectData.newTile.Width = Width;
			TileObjectData.newTile.Origin = new Point16(1, Height - 1);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 16, 18 };
			TileObjectData.newTile.AnchorBottom = new AnchorData(AnchorType.SolidTile | AnchorType.SolidWithTop | AnchorType.SolidSide, Width, 0);
			TileObjectData.newTile.LavaDeath = false;
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(205, 163, 63), CreateMapEntryName());
		}

		public override bool HasSmartInteract(int i, int j, SmartInteractScanSettings settings) => true;

		public override void NumDust(int i, int j, bool fail, ref int num) {
			num = fail ? 1 : 3;
		}

		public override void AnimateTile(ref int frame, ref int frameCounter) {
			if (++frameCounter >= TicksPerFrame) {
				frameCounter = 0;
				frame = (frame + 1) % Frames;
			}
		}

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			r = 0.30f;                                    // the furnace window
			g = 0.18f;
			b = 0.06f;
		}

		/// <summary>The station's top-left tile from any of its tiles (the frame's offset within the 4x3 block).</summary>
		public static Point TopLeft(int i, int j) {
			Tile tile = Main.tile[i, j];
			return new Point(i - tile.TileFrameX / 18 % Width, j - tile.TileFrameY % FrameHeight / 18);
		}

		public override bool RightClick(int i, int j) {
			CombinatorUISystem.Toggle(TopLeft(i, j));
			return true;
		}

		public override void MouseOver(int i, int j) {
			Player player = Main.LocalPlayer;
			player.noThrow = 2;
			player.cursorItemIconEnabled = true;
			player.cursorItemIconID = ModContent.ItemType<TheCombinator>();
		}
	}
}
