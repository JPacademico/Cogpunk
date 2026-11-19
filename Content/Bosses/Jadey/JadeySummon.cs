using System.IO;
using Cogpunk.Content.Coghaven.Tiles;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.Chat;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey
{
	/// <summary>
	/// How Jadey wakes (user, 2026-11-16: "the chest should ... behave like trashtr0m chest were if the player tries to open it
	/// summons a boss"): right-clicking the sealed Jade Vault (<see cref="CoghavenChestTile"/>, style 2) before her first defeat.
	/// She appears <see cref="SpawnRows"/> tiles over the vault, in the middle of the arena, and plays her intro.
	/// <para>D2: the client only asks (<see cref="JadeySummonPacket"/>); the server (or singleplayer) validates everything the
	/// request names (an active, living player within <see cref="MaxReach"/> of a real sealed vault, Jadey not yet defeated and
	/// not alive) and spawns her with <see cref="SafeSpawn"/> (critical: the boss itself). A client asks at most once per
	/// <see cref="RequestCooldown"/> ticks. D0: tile reads bounds-checked; packet fields are shorts, validated.</para>
	/// <para>Again with the Jade Incense (2026-11-17, user: "add a boss summon for friendo-bot to sell after defeating Jadey";
	/// <see cref="Items.JadeIncense"/>): burnt inside a vault's hall (<see cref="FindVault"/>: a bounded search for the vault
	/// chest round the player, then <see cref="Jadey.ArenaFor"/>), it asks for her the same way, flagged as an incense call:
	/// the server then accepts a defeated Jadey and checks the player stands in that vault's hall instead of the reach.</para>
	/// </summary>
	public static class JadeySummon
	{
		public const float MaxReach = 20f * 16f;
		public const int RequestCooldown = 60;
		public const int SpawnRows = 7;
		public const int SearchHalfWidth = 32, SearchHalfHeight = 20;   // tiles round the player (the hall is 48 x 16)
		private static readonly Color AwokenColor = new(175, 75, 255);       // vanilla's "has awoken!" colour

		private static uint lastRequest;
		private static bool requested;
		private static int cachedLeft = -1, cachedTop = -1;          // the last vault found (clients and singleplayer)

		internal static void ResetCooldown() {
			requested = false;
			cachedLeft = cachedTop = -1;
		}

		private static bool CoolingDown() {
			if (requested && Main.GameUpdateCount - lastRequest < RequestCooldown) {
				return true;
			}
			requested = true;
			lastRequest = Main.GameUpdateCount;
			return false;
		}

		/// <summary>Client side of a touch on the sealed vault (<paramref name="left"/>, <paramref name="top"/> = its top-left).</summary>
		public static void Request(Player player, int left, int top) {
			if (NPC.AnyNPCs(ModContent.NPCType<Jadey>())) {
				Main.NewText(Language.GetTextValue("Mods.Cogpunk.NPCs.Jadey.VaultGuarded"), 140, 201, 176);
				return;
			}
			if (CoolingDown()) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Unlock with { Pitch = -0.4f }, new Vector2(left * 16 + 16, top * 16 + 16));
			if (Main.netMode == NetmodeID.SinglePlayer) {
				TrySpawn(player.whoAmI, left, top, false);
			}
			else {
				ModContent.GetInstance<JadeySummonPacket>().Send(left, top, false);
			}
		}

		/// <summary>Client side of a Jade Incense burnt in the vault (<paramref name="left"/>, <paramref name="top"/> from
		/// <see cref="FindVault"/>). The item's use already checked she isn't here.</summary>
		public static void RequestByItem(Player player, int left, int top) {
			if (Main.netMode == NetmodeID.SinglePlayer) {
				TrySpawn(player.whoAmI, left, top, true);
			}
			else if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<JadeySummonPacket>().Send(left, top, true);
			}
		}

		/// <summary>The vault whose hall <paramref name="player"/> stands in: its chest's top-left tile. A bounded search
		/// (<see cref="SearchHalfWidth"/> x <see cref="SearchHalfHeight"/> tiles each way, every tile bounds-checked) that
		/// remembers the last vault found, so a second use checks one spot first.</summary>
		public static bool FindVault(Player player, out int left, out int top) {
			left = top = -1;
			if (player == null || !player.active) {
				return false;
			}
			if (cachedLeft >= 0 && IsVault(cachedLeft, cachedTop) && InHall(player, cachedLeft, cachedTop)) {
				left = cachedLeft;
				top = cachedTop;
				return true;
			}
			Point p = player.Center.ToTileCoordinates();
			for (int y = p.Y - SearchHalfHeight; y <= p.Y + SearchHalfHeight; y++) {
				for (int x = p.X - SearchHalfWidth; x <= p.X + SearchHalfWidth; x++) {
					if (IsVault(x, y) && InHall(player, x, y)) {
						left = cachedLeft = x;
						top = cachedTop = y;
						return true;
					}
				}
			}
			return false;
		}

		private static bool InHall(Player player, int left, int top) {
			Rectangle hall = Jadey.ArenaFor(left, top);
			return hall.Contains(player.Center.ToPoint());
		}

		/// <summary>Server or singleplayer: validates the request and wakes Jadey over the vault. <paramref name="byIncense"/>:
		/// a Jade Incense call (she may have been defeated; the player must stand in that vault's hall).</summary>
		internal static bool TrySpawn(int playerIndex, int left, int top, bool byIncense) {
			if (Main.netMode == NetmodeID.MultiplayerClient || (JadeySystem.Downed && !byIncense) || playerIndex < 0 || playerIndex >= Main.maxPlayers) {
				return false;
			}
			Player player = Main.player[playerIndex];
			int type = ModContent.NPCType<Jadey>();
			if (!player.active || player.dead || NPC.AnyNPCs(type) || !IsVault(left, top)) {
				return false;
			}
			if (byIncense) {
				if (!InHall(player, left, top)) {
					return false;
				}
			}
			else {
				Vector2 vault = new(left * 16 + 16, top * 16 + 16);
				if (Vector2.DistanceSquared(player.Center, vault) > MaxReach * MaxReach) {
					return false;
				}
			}
			var source = new EntitySource_TileInteraction(player, left, top);
			int bottom = (top - SpawnRows) * 16;
			if (!SafeSpawn.TryNewNPC(source, left * 16 + 16, bottom, type, out NPC boss, ai2: left, ai3: top, target: playerIndex, critical: true)) {
				return false;
			}
			if (Main.netMode == NetmodeID.SinglePlayer) {
				Main.NewText(Language.GetTextValue("Announcement.HasAwoken", boss.TypeName), AwokenColor);
			}
			else if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey("Announcement.HasAwoken", boss.GetTypeNetName()), AwokenColor);
			}
			return true;
		}

		/// <summary>The top-left tile of a Jade Vault (sealed until her first defeat: <see cref="JadeySystem.Downed"/>).</summary>
		private static bool IsVault(int left, int top) {
			return TileSafety.TryGetTile(left, top, out Tile tile, 1) && tile.HasTile && tile.TileType == ModContent.TileType<CoghavenChestTile>()
				&& tile.TileFrameX == CoghavenChestTile.VaultStyle * 36 && tile.TileFrameY == 0;
		}
	}

	/// <summary>Client -> server: "I touched the Jade Vault at (left, top)" or "I burnt a Jade Incense in it". Two shorts and a
	/// bool; validated by <see cref="JadeySummon.TrySpawn"/>.</summary>
	public sealed class JadeySummonPacket : CogpunkPacket
	{
		public void Send(int left, int top, bool byIncense) {
			ModPacket packet = Begin();
			packet.Write((short)left);
			packet.Write((short)top);
			packet.Write(byIncense);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			short left = reader.ReadInt16();
			short top = reader.ReadInt16();
			bool byIncense = reader.ReadBoolean();
			if (Main.netMode != NetmodeID.Server) {
				return;
			}
			JadeySummon.TrySpawn(sender, left, top, byIncense);
		}
	}
}
