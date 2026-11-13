using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent.ObjectInteractions;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Mechanist.Stations
{
	/// <summary>
	/// Steam Injector (Injetor de Vapor), a Mechanist buff station (user, 2026-11-12: "sold by the friendo-bot npc costing 35
	/// gold; upon use (right mouse), it gives +10 max steam and -5% steam consumption"): a 2x3 brass pressure tank on a
	/// cast-iron foot, a gauge, a valve wheel on top and a hose ending in a big brass injector needle. Used like vanilla's
	/// stations (decompiled <c>Player.TileInteractionsUse</c>: <c>AddBuff</c> + a sound on the right click, a smart-interact
	/// outline): right click for <see cref="SteamInjection"/>, which lasts until death
	/// (<see cref="Furniture.BuffStationRules"/>).
	/// <para>D2: <see cref="RightClick"/> runs on the clicking player's own client, which adds the buff to its local player
	/// (vanilla then syncs the buff list); the hiss and the puff are client effects. D0: one buff, no spawns but client dust
	/// through <see cref="SafeSpawn"/>; the frame's top-left is found from the tile's frame, bounded by the 2x3 size.</para>
	/// </summary>
	public class SteamInjectorTile : CogpunkTile
	{
		public const int Width = 2, Height = 3;
		public const int BuffTicks = 108000;                 // vanilla's station time; it never counts down (until death)

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = true;
			TileID.Sets.HasOutlines[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;
			TileID.Sets.IgnoredByNpcStepUp[Type] = true;
			DustType = DustID.Copper;

			TileObjectData.newTile.CopyFrom(TileObjectData.Style2xX);
			TileObjectData.newTile.Height = Height;
			TileObjectData.newTile.Origin = new Point16(0, Height - 1);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 16, 18 };
			TileObjectData.newTile.LavaDeath = true;
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(184, 138, 51), CreateMapEntryName());
		}

		public override bool HasSmartInteract(int i, int j, SmartInteractScanSettings settings) => true;

		public override void NumDust(int i, int j, bool fail, ref int num) {
			num = fail ? 1 : 3;
		}

		public override bool RightClick(int i, int j) {
			Player player = Main.LocalPlayer;
			player.AddBuff(ModContent.BuffType<SteamInjection>(), BuffTicks);
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item13 with { Pitch = -0.2f, Volume = 0.8f }, new Vector2(i * 16 + 8, j * 16 + 8));   // the hiss
				SoundEngine.PlaySound(SoundID.Item149 with { Pitch = 0.3f, Volume = 0.6f }, new Vector2(i * 16 + 8, j * 16 + 8));
				Puff(i, j);
			}
			return true;
		}

		public override void MouseOver(int i, int j) {
			Player player = Main.LocalPlayer;
			player.noThrow = 2;
			player.cursorItemIconEnabled = true;
			player.cursorItemIconID = ModContent.ItemType<SteamInjector>();
		}

		/// <summary>A puff of steam out of the valve on top (client only).</summary>
		private static void Puff(int i, int j) {
			if (!CogpunkClientConfig.RollEffect() || !TileSafety.TryGetTile(i, j, out Tile tile)) {
				return;
			}
			int left = i - tile.TileFrameX / 18 % Width;
			int top = j - tile.TileFrameY / 18 % Height;
			Vector2 valve = new(left * 16 + 16, top * 16 + 2);
			for (int k = 0; k < 10; k++) {
				if (SafeSpawn.TryNewDust(valve - new Vector2(4f, 4f), 8, 8, DustID.Smoke, out Dust d, 0f, -1.5f, 90, new Color(238, 241, 243), 1.2f)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-1.2f, 1.2f), Main.rand.NextFloat(-2.4f, -0.8f));
					d.noGravity = true;
				}
			}
		}
	}
}
