using Cogpunk.Content.Coghaven.Dusts;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.Enums;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Coghaven.Tiles
{
	/// <summary>
	/// Lift Turbine (2026-11-06, user: "a base of cloud and cogs with steam turbines that emit smoke, to look like it's what
	/// keeps the island flying (no actual gravity)"): a 4x6 brass turbine that hangs from the ceiling (the underside of
	/// Coghaven, where <see cref="Generation.CoghavenPass"/> bolts five of them), its rotor turning behind the intake window
	/// over the fire inside, smoke pouring down out of its nozzle. Purely a look: nothing lifts anything.
	/// <para>Animated like ExampleMod 1.4.4's animated tiles: <see cref="Frames"/> frames on a <see cref="FrameHeight"/> px
	/// stride, <see cref="TicksPerFrame"/> ticks each (a multiple of 4: tiles are redrawn every 4 updates), shared by every
	/// turbine (O(1) in <see cref="AnimateTile"/>). The fire and the nozzle glow through <c>_Glow</c> at full brightness
	/// (ExampleMod's animated glowmask tile), the nozzle lights its surroundings.</para>
	/// <para>The smoke: <see cref="TurbineSmoke"/> puffs from the nozzle's middle cell, in <see cref="EmitParticles"/> (only
	/// on clients, only for drawn tiles, at the frequency vanilla allows for the lighting mode), one roll in
	/// <see cref="SmokeOneIn"/> and the effects setting (D1). The glow texture is cached once on clients (D1, D0: never
	/// touched on a dedicated server).</para>
	/// </summary>
	public class LiftTurbineTile : CogpunkTile
	{
		public const int Width = 4, Height = 6;
		public const int Frames = 4;
		public const int TicksPerFrame = 4;
		public const int FrameHeight = Height * 18;             // 108
		public const int SmokeOneIn = 2;

		private static Asset<Texture2D> glow;

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = false;
			Main.tileLighted[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;

			DustType = DustID.Gold;
			AnimationFrameHeight = FrameHeight;

			TileObjectData.newTile.Width = Width;
			TileObjectData.newTile.Height = Height;
			TileObjectData.newTile.Origin = new Point16(1, 0);
			TileObjectData.newTile.AnchorTop = new AnchorData(AnchorType.SolidTile | AnchorType.SolidSide, Width, 0);
			TileObjectData.newTile.AnchorBottom = AnchorData.Empty;
			TileObjectData.newTile.UsesCustomCanPlace = true;
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 16, 16, 16, 16, 16 };
			TileObjectData.newTile.CoordinateWidth = 16;
			TileObjectData.newTile.CoordinatePadding = 2;
			TileObjectData.newTile.LavaDeath = false;
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(184, 138, 51), CreateMapEntryName());
			if (!Main.dedServ) {
				glow = DepthLayers.RequestOptional(Texture + "_Glow");
			}
		}

		public override void Unload() {
			glow = null;
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
			int row = Main.tile[i, j].TileFrameY % FrameHeight / 18;
			if (row >= Height - 2) {
				r = 0.7f;                                       // the nozzle's ember ring
				g = 0.38f;
				b = 0.12f;
			}
			else if (row >= 2) {
				r = 0.25f;                                      // the fire behind the window
				g = 0.13f;
				b = 0.04f;
			}
		}

		public override void EmitParticles(int i, int j, Tile tile, short tileFrameX, short tileFrameY, Color tileLight, bool visible) {
			if (!visible || tileFrameX % (Width * 18) != 18 || tileFrameY % FrameHeight != (Height - 1) * 18) {
				return;                                         // only the nozzle's middle cell smokes
			}
			if (!Main.rand.NextBool(SmokeOneIn) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			Vector2 nozzle = new(i * 16 + 16f, j * 16 + 14f);   // the nozzle's mouth: between the two middle columns
			if (SafeSpawn.TryNewDust(nozzle - new Vector2(6f, 0f), 12, 4, ModContent.DustType<TurbineSmoke>(), out Dust puff)) {
				puff.velocity = new Vector2(Main.rand.NextFloat(-0.6f, 0.6f), Main.rand.NextFloat(1.3f, 2.1f));   // a billowing plume
			}
		}

		public override void PostDraw(int i, int j, SpriteBatch spriteBatch) {
			if (glow?.IsLoaded != true) {
				return;
			}
			Tile tile = Main.tile[i, j];
			Vector2 zero = Main.drawToScreen ? Vector2.Zero : new Vector2(Main.offScreenRange);
			int frameY = tile.TileFrameY + Main.tileFrame[Type] * FrameHeight;
			Rectangle source = new(tile.TileFrameX, frameY, 16, 16);
			if (source.Bottom > glow.Value.Height) {
				return;
			}
			Vector2 at = new Vector2(i * 16 - (int)Main.screenPosition.X, j * 16 - (int)Main.screenPosition.Y) + zero;
			spriteBatch.Draw(glow.Value, at, source, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
		}
	}
}
