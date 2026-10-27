using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Junkyard.Tiles
{
	/// <summary>
	/// Rust Polisher: a 3x3 bench grinder of salvaged parts (a cast-iron base, a brass motor on a belt drive, a big buffing
	/// wheel spinning against a rusted plate, a pressure gauge and a steam stack). A crafting station: for now it turns
	/// 2 Rusted Metal into Polished Metal (<see cref="Items.PolishedMetal"/>).
	/// <para>Animated like ExampleMod 1.4.4's animated tiles: <see cref="Frames"/> frames on a <see cref="FrameHeight"/> px
	/// stride (CoordinateHeights 16, 16, 18: the base sinks 2 px into the floor), advanced every <see cref="TicksPerFrame"/>
	/// ticks in <see cref="AnimateTile"/> (O(1), shared by every polisher). The motor glows faintly.</para>
	/// </summary>
	public class RustPolisherTile : CogpunkTile
	{
		public const int Frames = 6;
		public const int TicksPerFrame = 4;
		public const int FrameHeight = 56;                // 16 + 2 + 16 + 2 + 18 + 2

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = true;
			Main.tileLighted[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;
			TileID.Sets.IgnoredByNpcStepUp[Type] = true;

			DustType = DustID.Iron;
			AnimationFrameHeight = FrameHeight;

			TileObjectData.newTile.CopyFrom(TileObjectData.Style3x3);
			TileObjectData.newTile.Origin = new Point16(1, 2);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 16, 18 };
			TileObjectData.newTile.LavaDeath = true;
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(184, 138, 51), CreateMapEntryName());
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

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			r = 0.22f;                                    // the motor's warm glow
			g = 0.16f;
			b = 0.06f;
		}
	}
}
