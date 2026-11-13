using System.Collections.Generic;
using Cogpunk.Content.Combinator.Combination;
using Cogpunk.Content.Combinator.Tiles;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.UI;

namespace Cogpunk.Content.Combinator.UI
{
	/// <summary>
	/// Opens and closes the Combinator's window (user-set 2026-11-12: "it should open a stylized cogpunk menu when interacted
	/// with (right mouse)") and puts it on screen as an interface layer right after vanilla's inventory, drawn and handled by
	/// <see cref="CombinatorUI"/> in vanilla's own way (vanilla draws and handles its inventory, chests and reforge slot
	/// together, in UI scale). It behaves like a chest: right click the station to open it (with the inventory; an open chest
	/// closes first, as vanilla closes one, decompiled <c>Player.Update</c>: <c>chest = -1</c>, <c>Recipe.FindRecipes</c>), right
	/// click it again, close the inventory, walk out of reach (vanilla's multi-tile reach,
	/// <c>Player.IsInInteractionRangeToMultiTileHitbox</c>), open a chest or talk to someone, die, or lose the station, and it
	/// closes, handing every slot's item back (<see cref="CombinatorPlayer.ReturnAll"/>).
	/// <para>D2: client-local UI. D0: the tile is re-checked every tick (<see cref="TileSafety"/>); textures are cached on
	/// clients at load (<see cref="CombinatorUI.Load"/>). Also installs the right-click resolver the Metal Wrench asks
	/// (<see cref="RightClickOwner"/>).</para>
	/// </summary>
	public sealed class CombinatorUISystem : ModSystem
	{
		public static bool IsOpen { get; private set; }
		public static Point Station { get; private set; }

		public override void Load() {
			RightClickOwner.Resolver = CombinationRules.RightClickTypeOf;
			if (!Main.dedServ) {
				CombinatorUI.Load();
			}
		}

		public override void Unload() {
			RightClickOwner.Resolver = null;
			layer = null;
			CombinatorUI.Unload();
			IsOpen = false;
		}

		public override void ClearWorld() {
			IsOpen = false;
		}

		/// <summary>The station at <paramref name="topLeft"/> was right-clicked by the local player.</summary>
		public static void Toggle(Point topLeft) {
			if (IsOpen && Station == topLeft) {
				Close();
				return;
			}
			Player player = Main.LocalPlayer;
			if (player.chest != -1) {
				player.chest = -1;                            // vanilla's own way to close a chest
				Recipe.FindRecipes();
			}
			if (player.talkNPC != -1) {
				player.SetTalkNPC(-1);
				Main.npcChatText = "";
			}
			Main.editSign = false;
			Main.playerInventory = true;
			Station = topLeft;
			IsOpen = true;
			CombinatorUI.OnOpen();
			SoundEngine.PlaySound(SoundID.MenuOpen);
		}

		public static void Close() {
			if (!IsOpen) {
				return;
			}
			IsOpen = false;
			CombinatorUI.OnClose();
			Main.LocalPlayer.GetModPlayer<CombinatorPlayer>().ReturnAll();
			SoundEngine.PlaySound(SoundID.MenuClose);
		}

		public override void UpdateUI(GameTime gameTime) {
			if (!IsOpen || Main.gameMenu) {
				return;
			}
			Player player = Main.LocalPlayer;
			bool keep = Main.playerInventory && !player.dead && player.chest == -1 && player.talkNPC == -1 && !Main.editSign
				&& StationStands() && player.IsInInteractionRangeToMultiTileHitbox(Station.X + 1, Station.Y + 1);
			if (!keep) {
				Close();
			}
		}

		private static bool StationStands() {
			return TileSafety.TryGetTile(Station.X, Station.Y, out Tile tile) && tile.HasTile && tile.TileType == ModContent.TileType<CombinatorTile>();
		}

		private static GameInterfaceLayer layer;                 // made once (D1: no allocation a frame)

		public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers) {
			int inventory = layers.FindIndex(static l => l.Name == "Vanilla: Inventory");
			if (inventory < 0) {
				return;
			}
			layer ??= new LegacyGameInterfaceLayer("Cogpunk: Combinator", static () => {
				if (IsOpen && Main.playerInventory) {
					CombinatorUI.Draw(Main.spriteBatch);
				}
				return true;
			}, InterfaceScaleType.UI);
			layers.Insert(inventory + 1, layer);
		}
	}
}
