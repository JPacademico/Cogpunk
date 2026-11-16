using System;
using Cogpunk.Content.Bosses.Jadey;
using Cogpunk.Content.Coghaven.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.Enums;
using Terraria.GameContent.ObjectInteractions;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Coghaven.Tiles
{
	/// <summary>
	/// Coghaven's chests (2026-11-16; follows ExampleMod 1.4.4's ExampleChest and the Junkyard Cache,
	/// <see cref="Furniture.ScrappyTrunkTile"/>). Three styles (art/coghaven/make_coghaven_chests_art.py):
	/// <list type="number">
	/// <item><b>Pagoda Chest</b> (style 0): red lacquer under a little roof of jade tiles; the craftable one
	/// (<see cref="PagodaChest"/>), and what the locked one becomes once opened.</item>
	/// <item><b>Locked Pagoda Chest</b> (style 1): the pagoda's treasure (user: "the pagoda chest on coghaven should be locked
	/// and can only be opened with a key obtained on hardmode (just like default terraria biome chests of the dungeon)"):
	/// only the <see cref="PagodaKey"/> opens it, which it uses up, and the chest becomes a plain Pagoda Chest with its loot
	/// (vanilla's <c>Chest.Unlock</c> moves a modded chest one style back, and <c>MessageID.LockAndUnlock</c> syncs it, as
	/// the Lost Key does the Junkyard Cache). Without the key it stays shut. Locked (<see cref="IsLockedChest"/>), so
	/// quick-stacking skips it (decompiled <c>Chest.PutItemInNearbyChest</c>).</item>
	/// <item><b>Jade Vault</b> (style 2): the chest in the middle of the Jade Vault (user: "behave like trashtr0m chest were if
	/// the player tries to open it summons a boss ... The chest can only be oppened after Jadey has been killed"): while
	/// Jadey has never been defeated in this world (<see cref="JadeySystem.Downed"/>) it is sealed, its soul seal glowing, and
	/// a touch wakes her (<see cref="JadeySummon.Request"/>; it says so if she is already awake); from then on it opens like
	/// any chest. It can't be broken while sealed.</item>
	/// </list>
	/// <para>World generation fills both chests through vanilla's own sky-island loot as Dynasty chests and turns them into
	/// these (<see cref="Generation.CoghavenChests"/>). D2: the unlock is vanilla's message; the vault's seal is a world flag
	/// sent with the world data, read on every side; the summon goes to the server as a packet. D0: every index from a tile
	/// is checked; light and sparkles on clients only.</para>
	/// </summary>
	public class CoghavenChestTile : CogpunkTile
	{
		public const int PagodaStyle = 0, LockedPagodaStyle = 1, VaultStyle = 2;

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

			DustType = DustID.GemEmerald;
			AdjTiles = new int[] { TileID.Containers };

			AddMapEntry(new Color(168, 44, 42), this.GetLocalization("MapEntry0"), MapChestName);
			AddMapEntry(new Color(126, 30, 36), this.GetLocalization("MapEntry1"), MapChestName);
			AddMapEntry(new Color(58, 166, 118), this.GetLocalization("MapEntry2"), MapChestName);
			RegisterItemDrop(ModContent.ItemType<PagodaChest>(), PagodaStyle, LockedPagodaStyle, VaultStyle);

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

		public static int StyleOf(Tile tile) => tile.TileFrameX / 36;

		/// <summary>Shut to anyone without its key (style 1), or sealed until Jadey's first defeat (style 2).</summary>
		public static bool IsLocked(Tile tile) {
			int style = StyleOf(tile);
			return style == LockedPagodaStyle || (style == VaultStyle && !JadeySystem.Downed);
		}

		public override ushort GetMapOption(int i, int j) => (ushort)Math.Clamp(StyleOf(Main.tile[i, j]), 0, 2);

		public override LocalizedText DefaultContainerName(int frameX, int frameY) => this.GetLocalization("MapEntry" + Math.Clamp(frameX / 36, 0, 2));

		public override bool HasSmartInteract(int i, int j, SmartInteractScanSettings settings) => true;

		public override bool IsLockedChest(int i, int j) => IsLocked(Main.tile[i, j]);

		/// <summary>Only the locked pagoda chest is ever unlocked (the key is checked and used up in <see cref="RightClick"/>);
		/// runs on the client that used it and on the server (<c>MessageID.LockAndUnlock</c>); the default adjustment turns
		/// style 1 into style 0. The vault is never "unlocked": its seal is the world flag.</summary>
		public override bool UnlockChest(int i, int j, ref short frameXAdjustment, ref int dustType, ref bool manual) {
			if (StyleOf(Main.tile[i, j]) != LockedPagodaStyle) {
				return false;
			}
			dustType = DustType;
			return true;
		}

		/// <summary>The sealed vault can't be broken (its loot is Jadey's to guard); the others follow vanilla's chest rule.</summary>
		public override bool CanKillTile(int i, int j, ref bool blockDamaged) {
			return !(StyleOf(Main.tile[i, j]) == VaultStyle && !JadeySystem.Downed);
		}

		public override bool CanExplode(int i, int j) => !IsLocked(Main.tile[i, j]);

		public override void NumDust(int i, int j, bool fail, ref int num) {
			num = 1;
		}

		public override void KillMultiTile(int i, int j, int frameX, int frameY) {
			Chest.DestroyChest(i, j);
		}

		/// <summary>Clients: the sealed vault's soul seal glows jade, a slow pulse.</summary>
		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			Tile tile = Main.tile[i, j];
			if (StyleOf(tile) != VaultStyle || JadeySystem.Downed) {
				return;
			}
			float pulse = 0.25f + 0.2f * MathF.Sin(Main.GameUpdateCount * 0.05f);
			r = Math.Max(r, pulse * 0.25f);
			g = Math.Max(g, pulse);
			b = Math.Max(b, pulse * 0.6f);
		}

		public override void DrawEffects(int i, int j, SpriteBatch spriteBatch, ref TileDrawInfo drawData) {
			Tile tile = Main.tile[i, j];
			if (StyleOf(tile) != VaultStyle || JadeySystem.Downed || tile.TileFrameX % 36 != 0 || tile.TileFrameY != 0 || Main.gamePaused
				|| !Main.rand.NextBool(30) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			if (SafeSpawn.TryNewDust(new Vector2(i * 16 + 6, j * 16 + 8), 20, 16, DustID.GemEmerald, out Dust d)) {
				d.noGravity = true;
				d.velocity = new Vector2(0f, -0.8f);
				d.scale = 0.8f;
			}
		}

		// --- chest UI (ExampleMod ExampleChest; a locked or sealed chest never reaches the opening code) ----------------

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
			int style = StyleOf(tile);
			if (style == LockedPagodaStyle) {
				int key = ModContent.ItemType<PagodaKey>();
				if (player.HasItemInInventoryOrOpenVoidBag(key)) {
					if (Chest.Unlock(left, top) && player.ConsumeItem(key, includeVoidBag: true)) {
						if (Main.netMode == NetmodeID.MultiplayerClient) {
							NetMessage.SendData(MessageID.LockAndUnlock, number2: 1f, number3: left, number4: top);   // 1 = unlock
						}
					}
				}
				else {
					SoundEngine.PlaySound(SoundID.Unlock with { Pitch = -0.9f, Volume = 0.5f }, new Vector2(left * 16 + 16, top * 16 + 16));
					Main.NewText(Language.GetTextValue("Mods.Cogpunk.Tiles.CoghavenChestTile.PagodaLocked"), 140, 201, 176);
				}
				return true;
			}
			if (style == VaultStyle && !JadeySystem.Downed) {
				JadeySummon.Request(player, left, top);
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
			int style = StyleOf(tile);
			player.cursorItemIconID = -1;
			if (style == LockedPagodaStyle && player.HasItemInInventoryOrOpenVoidBag(ModContent.ItemType<PagodaKey>())) {
				player.cursorItemIconID = ModContent.ItemType<PagodaKey>();   // like vanilla's key icon over a locked chest
				player.cursorItemIconText = "";
			}
			else if (style == VaultStyle && !JadeySystem.Downed) {
				player.cursorItemIconText = Language.GetTextValue("Mods.Cogpunk.Tiles.CoghavenChestTile.VaultSealed");
			}
			else if (chest < 0) {
				player.cursorItemIconText = Language.GetTextValue("LegacyChestType.0");
			}
			else {
				string defaultName = TileLoader.DefaultContainerName(tile.TileType, tile.TileFrameX, tile.TileFrameY);
				player.cursorItemIconText = Main.chest[chest].name.Length > 0 ? Main.chest[chest].name : defaultName;
				if (player.cursorItemIconText == defaultName) {
					player.cursorItemIconID = ModContent.ItemType<PagodaChest>();
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
