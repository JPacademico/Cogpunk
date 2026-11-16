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
	/// </summary>
	public static class JadeySummon
	{
		public const float MaxReach = 20f * 16f;
		public const int RequestCooldown = 60;
		public const int SpawnRows = 7;
		private static readonly Color AwokenColor = new(175, 75, 255);       // vanilla's "has awoken!" colour

		private static uint lastRequest;
		private static bool requested;

		internal static void ResetCooldown() {
			requested = false;
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
				TrySpawn(player.whoAmI, left, top);
			}
			else {
				ModContent.GetInstance<JadeySummonPacket>().Send(left, top);
			}
		}

		/// <summary>Server or singleplayer: validates the request and wakes Jadey over the vault.</summary>
		internal static bool TrySpawn(int playerIndex, int left, int top) {
			if (Main.netMode == NetmodeID.MultiplayerClient || JadeySystem.Downed || playerIndex < 0 || playerIndex >= Main.maxPlayers) {
				return false;
			}
			Player player = Main.player[playerIndex];
			int type = ModContent.NPCType<Jadey>();
			if (!player.active || player.dead || NPC.AnyNPCs(type) || !IsSealedVault(left, top)) {
				return false;
			}
			Vector2 vault = new(left * 16 + 16, top * 16 + 16);
			if (Vector2.DistanceSquared(player.Center, vault) > MaxReach * MaxReach) {
				return false;
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

		/// <summary>The top-left tile of a sealed Jade Vault.</summary>
		private static bool IsSealedVault(int left, int top) {
			return TileSafety.TryGetTile(left, top, out Tile tile, 1) && tile.HasTile && tile.TileType == ModContent.TileType<CoghavenChestTile>()
				&& tile.TileFrameX == CoghavenChestTile.VaultStyle * 36 && tile.TileFrameY == 0;
		}
	}

	/// <summary>Client -> server: "I touched the Jade Vault at (left, top)". Two shorts; validated by <see cref="JadeySummon.TrySpawn"/>.</summary>
	public sealed class JadeySummonPacket : CogpunkPacket
	{
		public void Send(int left, int top) {
			ModPacket packet = Begin();
			packet.Write((short)left);
			packet.Write((short)top);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			short left = reader.ReadInt16();
			short top = reader.ReadInt16();
			if (Main.netMode != NetmodeID.Server) {
				return;
			}
			JadeySummon.TrySpawn(sender, left, top);
		}
	}
}
