using System;
using System.IO;
using Cogpunk.Content.Furniture;
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

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	/// <summary>
	/// Trying to open the Junkyard Cache (the <see cref="ScrappyTrunkTile"/> buried in the central scrap heap) while
	/// <see cref="TrashTr0mSystem.Downed"/> is false doesn't open it: it wakes Trash-Tr0m, who climbs out of the heap.
	/// <para>D2: the clicking client only asks (<see cref="Request"/>); the server, or singleplayer, decides and spawns
	/// (<see cref="TrySpawn"/>) after validating everything the request names: an active, living player within
	/// <see cref="MaxReach"/> of a real cache tile, no Trash-Tr0m alive and the boss not yet defeated. A client re-asks at
	/// most once per <see cref="RequestCooldown"/> ticks, and a duplicate request finds the boss already alive.</para>
	/// <para>The boss emerges from the heap right above the cache. It has no legs and props itself on its arms, so its
	/// ground line is where its hands land, about 5 tiles either side of its centre: the lowest heap surface among those
	/// columns, so the hands rest on the slopes and the torn waist sinks into the peak (never deeper than the cache's
	/// floor). At most 4 x <see cref="SurfaceScanRows"/> bounds-checked tile reads (D0).</para>
	/// </summary>
	public static class TrashTr0mSummon
	{
		public const float MaxReach = 20f * 16f;
		public const int RequestCooldown = 60;
		public const int SurfaceScanRows = 48;
		private static readonly int[] HandColumnOffsets = { -5, -4, 5, 6 };   // from the trunk's left tile; the boss is centred on its middle
		private static readonly Color AwokenColor = new(175, 75, 255);       // vanilla's "has awoken!" colour

		private static uint lastRequest;
		private static bool requested;

		internal static void ResetCooldown() {
			requested = false;
		}

		/// <summary>Client side of the cache's right-click (<paramref name="left"/>, <paramref name="top"/> = its top-left tile).</summary>
		public static void Request(Player player, int left, int top) {
			int type = ModContent.NPCType<TrashTr0m>();
			if (NPC.AnyNPCs(type)) {
				Main.NewText(Language.GetTextValue("Mods.Cogpunk.NPCs.TrashTr0m.CacheGuarded"), 190, 120, 80);
				return;
			}
			if (requested && Main.GameUpdateCount - lastRequest < RequestCooldown) {
				return;
			}
			requested = true;
			lastRequest = Main.GameUpdateCount;
			SoundEngine.PlaySound(SoundID.Unlock with { Pitch = -0.6f }, new Vector2(left * 16 + 16, top * 16 + 16));
			if (Main.netMode == NetmodeID.SinglePlayer) {
				TrySpawn(player.whoAmI, left, top);
			}
			else {
				ModContent.GetInstance<TrashTr0mSummonPacket>().Send(left, top);
			}
		}

		/// <summary>Server or singleplayer: validates the request and spawns the boss at the heap above the cache.</summary>
		internal static bool TrySpawn(int playerIndex, int left, int top) {
			if (Main.netMode == NetmodeID.MultiplayerClient || TrashTr0mSystem.Downed) {
				return false;
			}
			if (playerIndex < 0 || playerIndex >= Main.maxPlayers) {
				return false;
			}
			Player player = Main.player[playerIndex];
			if (!player.active || player.dead || !IsCache(left, top)) {
				return false;
			}
			Vector2 cacheCentre = new(left * 16 + 16, top * 16 + 16);
			if (Vector2.DistanceSquared(player.Center, cacheCentre) > MaxReach * MaxReach) {
				return false;
			}
			int type = ModContent.NPCType<TrashTr0m>();
			if (NPC.AnyNPCs(type)) {
				return false;
			}
			int ground = FindHandGround(left, top);
			var source = new EntitySource_TileInteraction(player, left, top);
			if (!SafeSpawn.TryNewNPC(source, left * 16 + 16, ground * 16, type, out NPC boss, target: playerIndex, critical: true)) {
				return false;
			}
			Announce(boss);
			return true;
		}

		private static bool IsCache(int left, int top) {
			return TileSafety.TryGetTile(left, top, out Tile tile, 1) && tile.HasTile
				&& tile.TileType == ModContent.TileType<ScrappyTrunkTile>() && tile.TileFrameX / 36 == ScrappyTrunkTile.CacheStyle;
		}

		/// <summary>The row the boss's hands rest on: the lowest heap surface under them, at most the cache's floor.</summary>
		private static int FindHandGround(int left, int top) {
			int floor = top + 2;                         // the row under the trunk
			int ground = -1;
			for (int c = 0; c < HandColumnOffsets.Length; c++) {
				int x = left + HandColumnOffsets[c];
				for (int y = Math.Max(1, top - SurfaceScanRows); y <= floor; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile, 1) && tile.HasTile
						&& Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType]) {
						ground = Math.Max(ground, y);
						break;
					}
				}
			}
			return ground < 0 ? floor : Math.Min(ground, floor);
		}

		private static void Announce(NPC boss) {
			if (Main.netMode == NetmodeID.SinglePlayer) {
				Main.NewText(Language.GetTextValue("Announcement.HasAwoken", boss.TypeName), AwokenColor);
			}
			else if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey("Announcement.HasAwoken", boss.GetTypeNetName()), AwokenColor);
			}
		}
	}

	/// <summary>Client -> server: "I tried to open the Junkyard Cache at (left, top)". Two shorts; validated by <see cref="TrashTr0mSummon.TrySpawn"/>.</summary>
	public sealed class TrashTr0mSummonPacket : CogpunkPacket
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
				return;                                      // only clients send it
			}
			TrashTr0mSummon.TrySpawn(sender, left, top);
		}
	}
}
