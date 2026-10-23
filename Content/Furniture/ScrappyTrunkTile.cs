using System;
using Cogpunk.Content.Bosses.TrashTr0m;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.Enums;
using Terraria.GameContent.ObjectInteractions;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Furniture
{
	/// <summary>
	/// Scrappy Trunk: a riveted scrap-metal chest (follows ExampleMod 1.4.4 ExampleChest).
	/// <para>Style 0 is the craftable trunk. Style 1 is the <b>cache</b> that world generation buries (e.g. the Junkyard's
	/// central heap): it pulses with a faint brass glow every <see cref="PulsePeriod"/> ticks and sparkles at the surface
	/// above it, so players notice a buried one. Breaking a cache drops a normal trunk. All glow is client-side.</para>
	/// <para>A cache is <b>sealed</b> until Trash-Tr0m is defeated (<see cref="TrashTr0mSystem.Downed"/>): it reports
	/// itself locked (<see cref="IsLockedChest"/>), so quick-stacking skips it (decompiled <c>Chest.PutItemInNearbyChest</c>)
	/// and no key opens it (<see cref="UnlockChest"/>), and right-clicking it wakes the boss
	/// (<see cref="TrashTr0mSummon.Request"/>) instead of opening it. A chest with items can't be broken, so the loot
	/// stays put.</para>
	/// </summary>
	public class ScrappyTrunkTile : CogpunkTile
	{
		public const int CacheStyle = 1;
		public const int PulsePeriod = 120;            // one pulse every 2 s
		private const int PulseLength = 40;
		private const int SparkleScanLimit = 24;       // tiles searched upward for open air above a buried cache

		private static uint lastSparkleTick;
		private static Point lastSparkleAt;

		public override void SetStaticDefaults() {
			Main.tileSpelunker[Type] = true;
			Main.tileContainer[Type] = true;
			Main.tileShine2[Type] = true;
			Main.tileShine[Type] = 1200;
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileOreFinderPriority[Type] = 500;
			TileID.Sets.HasOutlines[Type] = true;
			TileID.Sets.BasicChest[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;
			TileID.Sets.AvoidedByNPCs[Type] = true;
			TileID.Sets.InteractibleByNPCs[Type] = true;
			TileID.Sets.IsAContainer[Type] = true;
			TileID.Sets.FriendlyFairyCanLureTo[Type] = true;
			TileID.Sets.GeneralPlacementTiles[Type] = false;

			DustType = DustID.Copper;
			AdjTiles = new int[] { TileID.Containers };

			AddMapEntry(new Color(147, 68, 31), this.GetLocalization("MapEntry0"), MapChestName);
			AddMapEntry(new Color(184, 138, 51), this.GetLocalization("MapEntry1"), MapChestName);
			RegisterItemDrop(ModContent.ItemType<ScrappyTrunk>(), CacheStyle);   // a broken cache gives a normal trunk

			TileObjectData.newTile.CopyFrom(TileObjectData.Style2x2);
			TileObjectData.newTile.Origin = new Point16(0, 1);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 18 };
			TileObjectData.newTile.HookCheckIfCanPlace = new PlacementHook(Chest.FindEmptyChest, -1, 0, true);
			TileObjectData.newTile.HookPostPlaceMyPlayer = new PlacementHook(Chest.AfterPlacement_Hook, -1, 0, false);
			TileObjectData.newTile.AnchorInvalidTiles = new int[] {
				TileID.MagicalIceBlock, TileID.Boulder, TileID.BouncyBoulder, TileID.LifeCrystalBoulder, TileID.RollingCactus
			};
			TileObjectData.newTile.StyleHorizontal = true;
			TileObjectData.newTile.LavaDeath = false;
			TileObjectData.newTile.AnchorBottom = new AnchorData(AnchorType.SolidTile | AnchorType.SolidWithTop | AnchorType.SolidSide,
				TileObjectData.newTile.Width, 0);
			TileObjectData.addTile(Type);
		}

		private static bool IsCache(Tile tile) => tile.TileFrameX / 36 == CacheStyle;

		/// <summary>True for a cache whose guardian, Trash-Tr0m, hasn't been defeated in this world yet.</summary>
		public static bool IsSealed(Tile tile) => IsCache(tile) && !TrashTr0mSystem.Downed;

		public override ushort GetMapOption(int i, int j) => (ushort)(Main.tile[i, j].TileFrameX / 36);

		public override LocalizedText DefaultContainerName(int frameX, int frameY) => this.GetLocalization("MapEntry" + frameX / 36);

		public override bool HasSmartInteract(int i, int j, SmartInteractScanSettings settings) => true;

		public override bool IsLockedChest(int i, int j) => IsSealed(Main.tile[i, j]);

		// Only the guardian's defeat unseals a cache; keys never turn it into a plain trunk.
		public override bool UnlockChest(int i, int j, ref short frameXAdjustment, ref int dustType, ref bool manual) => false;

		public override void NumDust(int i, int j, bool fail, ref int num) {
			num = 1;
		}

		public override void KillMultiTile(int i, int j, int frameX, int frameY) {
			Chest.DestroyChest(i, j);
		}

		// --- glow (client only; ModifyLight and DrawEffects never run on a dedicated server) ---------------------------

		/// <summary>0..1 brightness of the cache pulse: a 40-tick swell at the start of every 120-tick period.</summary>
		public static float Pulse() {
			uint t = Main.GameUpdateCount % PulsePeriod;
			return t < PulseLength ? MathF.Sin(MathF.PI * t / PulseLength) : 0f;
		}

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			if (!IsCache(Main.tile[i, j])) {
				return;
			}
			float glow = 0.12f + 0.75f * Pulse();       // faint base glow, brighter swell
			r = Math.Max(r, glow);
			g = Math.Max(g, glow * 0.72f);
			b = Math.Max(b, glow * 0.3f);
		}

		public override void DrawEffects(int i, int j, Microsoft.Xna.Framework.Graphics.SpriteBatch spriteBatch, ref TileDrawInfo drawData) {
			Tile tile = Main.tile[i, j];
			if (!IsCache(tile) || tile.TileFrameX % 36 != 0 || tile.TileFrameY != 0 || Main.gamePaused) {
				return;                                  // top-left tile of a cache only
			}
			uint now = Main.GameUpdateCount;
			if (now % PulsePeriod != 0 || (now == lastSparkleTick && lastSparkleAt == new Point(i, j))) {
				return;                                  // once per pulse, even when drawn several times per update
			}
			lastSparkleTick = now;
			lastSparkleAt = new Point(i, j);
			// Find the open air above the (possibly buried) cache and sparkle there.
			int y = j - 1;
			for (int n = 0; n < SparkleScanLimit && TileSafety.TryGetTile(i, y, out Tile above) && above.HasTile && Main.tileSolid[above.TileType]; n++) {
				y--;
			}
			Vector2 at = new Vector2(i * 16 + 16, y * 16 + 8);
			for (int k = 0; k < 4; k++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(10f, 4f), 20, 8, DustID.TreasureSparkle, out Dust dust)) {
					dust.velocity *= 0.2f;
					dust.noGravity = true;
				}
			}
		}

		// --- chest UI (ExampleMod ExampleChest; a sealed cache never reaches the opening code) -----------------------

		public static string MapChestName(string name, int i, int j) {
			int left = i;
			int top = j;
			Tile tile = Main.tile[i, j];
			if (tile.TileFrameX % 36 != 0) {
				left--;
			}
			if (tile.TileFrameY != 0) {
				top--;
			}
			int chest = Chest.FindChest(left, top);
			if (chest < 0) {
				return Language.GetTextValue("LegacyChestType.0");
			}
			return Main.chest[chest].name == "" ? name : name + ": " + Main.chest[chest].name;
		}

		public override bool RightClick(int i, int j) {
			Player player = Main.LocalPlayer;
			Tile tile = Main.tile[i, j];
			Main.mouseRightRelease = false;
			int left = i;
			int top = j;
			if (tile.TileFrameX % 36 != 0) {
				left--;
			}
			if (tile.TileFrameY != 0) {
				top--;
			}
			if (IsSealed(tile)) {
				TrashTr0mSummon.Request(player, left, top);   // the cache stays shut; its guardian wakes up
				return true;
			}

			player.CloseSign();
			player.SetTalkNPC(-1);
			Main.npcChatCornerItem = 0;
			Main.npcChatText = "";
			if (Main.editChest) {
				SoundEngine.PlaySound(SoundID.MenuTick);
				Main.editChest = false;
				Main.npcChatText = string.Empty;
			}
			if (player.editedChestName) {
				NetMessage.SendData(MessageID.SyncPlayerChest, text: NetworkText.FromLiteral(Main.chest[player.chest].name), number: player.chest, number2: 1f);
				player.editedChestName = false;
			}

			if (Main.netMode == NetmodeID.MultiplayerClient) {
				if (left == player.chestX && top == player.chestY && player.chest != -1) {
					player.chest = -1;
					Recipe.FindRecipes();
					SoundEngine.PlaySound(SoundID.MenuClose);
				}
				else {
					NetMessage.SendData(MessageID.RequestChestOpen, number: left, number2: top);
					Main.stackSplit = 600;
				}
			}
			else {
				int chest = Chest.FindChest(left, top);
				if (chest != -1) {
					Main.stackSplit = 600;
					if (chest == player.chest) {
						player.chest = -1;
						SoundEngine.PlaySound(SoundID.MenuClose);
					}
					else {
						SoundEngine.PlaySound(player.chest < 0 ? SoundID.MenuOpen : SoundID.MenuTick);
						player.OpenChest(left, top, chest);
					}
					Recipe.FindRecipes();
				}
			}
			return true;
		}

		public override void MouseOver(int i, int j) {
			Player player = Main.LocalPlayer;
			Tile tile = Main.tile[i, j];
			int left = i;
			int top = j;
			if (tile.TileFrameX % 36 != 0) {
				left--;
			}
			if (tile.TileFrameY != 0) {
				top--;
			}
			int chest = Chest.FindChest(left, top);
			player.cursorItemIconID = -1;
			if (chest < 0) {
				player.cursorItemIconText = Language.GetTextValue("LegacyChestType.0");
			}
			else {
				string defaultName = TileLoader.DefaultContainerName(tile.TileType, tile.TileFrameX, tile.TileFrameY);
				player.cursorItemIconText = Main.chest[chest].name.Length > 0 ? Main.chest[chest].name : defaultName;
				if (player.cursorItemIconText == defaultName) {
					player.cursorItemIconID = ModContent.ItemType<ScrappyTrunk>();
					player.cursorItemIconText = "";
				}
			}
			player.noThrow = 2;
			player.cursorItemIconEnabled = true;
		}

		public override void MouseOverFar(int i, int j) {
			MouseOver(i, j);
			Player player = Main.LocalPlayer;
			if (player.cursorItemIconText == "") {
				player.cursorItemIconEnabled = false;
				player.cursorItemIconID = ItemID.None;
			}
		}
	}
}
