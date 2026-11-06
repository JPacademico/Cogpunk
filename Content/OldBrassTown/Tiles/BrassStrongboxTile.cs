using Cogpunk.Content.OldBrassTown.Items;
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

namespace Cogpunk.Content.OldBrassTown.Tiles
{
	/// <summary>
	/// The Brass Strongbox (user-set 2026-11-04: "the chest inside the house on the town ... opened by the Sheriff's Key"):
	/// the bank vault's chest in Old Brass Town, generated locked (style 1) and full of vanilla gold-chest loot plus the
	/// Sheriff's Revolver and a Broken Whistle (<see cref="Generation.OldBrassTownChests"/>). The <see cref="SheriffsKey"/>
	/// from the town's buried cache opens it and is used up, like a Golden Key on a locked Dungeon chest; once open it is an
	/// ordinary chest (style 0) that can be picked up (<see cref="BrassStrongbox"/>) and can't be locked again (no second
	/// key exists).
	/// <para>Set up like ExampleMod 1.4.4's <c>ExampleChest</c> (its locked style, <c>RightClick</c>, <c>MouseOver</c>, the
	/// chest list kept in <c>KillMultiTile</c>); vanilla unlocks a modded chest by moving its frame 36 px left (decompiled
	/// <c>Chest.Unlock</c>: style 1 -> 0). D2: the unlock is the client's, sent as <c>MessageID.LockAndUnlock</c>; opening goes
	/// through <c>MessageID.RequestChestOpen</c> as for vanilla chests.</para>
	/// </summary>
	public class BrassStrongboxTile : CogpunkTile
	{
		public const int LockedStyle = 1;

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

			DustType = DustID.Gold;
			AdjTiles = new int[] { TileID.Containers };
			VanillaFallbackOnModDeletion = TileID.Containers;

			AddMapEntry(new Color(184, 138, 51), this.GetLocalization("MapEntry0"), MapChestName);
			AddMapEntry(new Color(127, 135, 148), this.GetLocalization("MapEntry1"), MapChestName);

			RegisterItemDrop(ModContent.ItemType<BrassStrongbox>(), 1);     // the locked style (it can't be broken while locked, but just in case)
			RegisterItemDrop(ItemID.Chest);

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
			TileObjectData.newTile.AnchorBottom = new AnchorData(AnchorType.SolidTile | AnchorType.SolidWithTop | AnchorType.SolidSide, TileObjectData.newTile.Width, 0);
			TileObjectData.addTile(Type);
		}

		public override ushort GetMapOption(int i, int j) => (ushort)(Main.tile[i, j].TileFrameX / 36);

		public override LocalizedText DefaultContainerName(int frameX, int frameY) => this.GetLocalization("MapEntry" + frameX / 36);

		public override bool HasSmartInteract(int i, int j, SmartInteractScanSettings settings) => true;

		public override bool IsLockedChest(int i, int j) => Main.tile[i, j].TileFrameX / 36 == LockedStyle;

		public override bool UnlockChest(int i, int j, ref short frameXAdjustment, ref int dustType, ref bool manual) {
			dustType = DustID.Gold;
			return true;
		}

		// Nothing locks it again: the only key is used up opening it.
		public override bool LockChest(int i, int j, ref short frameXAdjustment, ref bool manual) => false;

		public static string MapChestName(string name, int i, int j) {
			int left = i, top = j;
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

		public override void NumDust(int i, int j, bool fail, ref int num) {
			num = 1;
		}

		public override void KillMultiTile(int i, int j, int frameX, int frameY) {
			Chest.DestroyChest(i, j);
		}

		public override bool RightClick(int i, int j) {
			Player player = Main.LocalPlayer;
			Tile tile = Main.tile[i, j];
			Main.mouseRightRelease = false;
			int left = i, top = j;
			if (tile.TileFrameX % 36 != 0) {
				left--;
			}
			if (tile.TileFrameY != 0) {
				top--;
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
			bool isLocked = Chest.IsLocked(left, top);
			if (Main.netMode == NetmodeID.MultiplayerClient && !isLocked) {
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
			else if (isLocked) {
				int key = ModContent.ItemType<SheriffsKey>();
				if (player.HasItemInInventoryOrOpenVoidBag(key) && Chest.Unlock(left, top) && player.ConsumeItem(key, includeVoidBag: true)) {
					if (Main.netMode == NetmodeID.MultiplayerClient) {
						NetMessage.SendData(MessageID.LockAndUnlock, number2: 1f, number3: left, number4: top);   // 1 = unlock
					}
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
			int left = i, top = j;
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
					player.cursorItemIconID = Main.tile[left, top].TileFrameX / 36 == LockedStyle ? ModContent.ItemType<SheriffsKey>() : ModContent.ItemType<BrassStrongbox>();
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
