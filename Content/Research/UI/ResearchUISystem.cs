using Cogpunk.Content.Research.Tiles;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.UI;

namespace Cogpunk.Content.Research.UI
{
	/// <summary>
	/// Opens and closes the research window (user, 2026-11-18: right click the table "and it should open a menu with nodes").
	/// It is one of vanilla's full-screen "fancy" interfaces, the Bestiary's kind (<c>IngameFancyUI.OpenUIState</c>: decompiled
	/// 1.4.4, "Modders can use this to display a non-gameplay UI"), so vanilla hides the inventory under it, closes it on the
	/// inventory key or Escape, and draws the mouse text. It also closes when its player dies or walks out of the table's reach,
	/// or the table goes.
	/// <para>D2: client-local (each player reads their own research). D0: the table is re-checked every tick
	/// (<see cref="TileSafety"/>); the window is made once and reused (D1).</para>
	/// </summary>
	public sealed class ResearchUISystem : ModSystem
	{
		private static ResearchUIState state;
		public static Point Table { get; private set; }

		public static bool IsOpen => Main.inFancyUI && state != null && Main.InGameUI?.CurrentState == state;

		public override void Unload() {
			state = null;
		}

		public override void ClearWorld() {
			if (IsOpen) {
				IngameFancyUI.Close();
			}
		}

		/// <summary>The table at <paramref name="topLeft"/> was right-clicked by the local player.</summary>
		public static void Open(Point topLeft) {
			if (Main.dedServ) {
				return;
			}
			Table = topLeft;
			state ??= new ResearchUIState();
			IngameFancyUI.OpenUIState(state);
			SoundEngine.PlaySound(SoundID.MenuOpen);
		}

		public override void UpdateUI(GameTime gameTime) {
			if (!IsOpen) {
				return;
			}
			Player player = Main.LocalPlayer;
			bool keep = player.active && !player.dead && TableStands() && player.IsInInteractionRangeToMultiTileHitbox(Table.X + 1, Table.Y + 1);
			if (!keep) {
				IngameFancyUI.Close();
			}
		}

		private static bool TableStands() {
			return TileSafety.TryGetTile(Table.X, Table.Y, out Tile tile) && tile.HasTile && tile.TileType == ModContent.TileType<AncientResearchTableTile>();
		}
	}
}
