using System;
using System.IO;
using Cogpunk.Content.Furniture;
using Cogpunk.Content.Junkyard;
using Cogpunk.Content.Scrap.Tiles;
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
	/// The two ways Trash-Tr0m wakes up.
	/// <list type="bullet">
	/// <item><b>The Junkyard Cache</b> (<see cref="ScrappyTrunkTile"/>, style 1, locked until the <see cref="Items.LostKey"/>
	/// opens it): until Trash-Tr0m's first defeat, right-clicking it without the key wakes the guardian (afterwards it just
	/// stays locked; the server re-checks the downed flag), which bursts up <b>from under the central heap</b>:
	/// its ground line is the yard ground beneath the heap (<see cref="CacheGroundRows"/> under the cache's floor, where
	/// world generation buries it), the heap's Rusted Scrap above that line is blown away over
	/// <see cref="TrashTr0m.BurstTicks"/> ticks (<see cref="ClearHeapRows"/>; the column holding the cache up is kept), and
	/// players near the cache are thrown back (<see cref="TrashTr0mPlayer"/>).</item>
	/// <item><b>Junkbait</b> (<see cref="Junkyard.Items.Junkbait"/>), used inside the Junkyard: it climbs out of the ground
	/// <see cref="ItemSpawnDistance"/> in front of the player (<see cref="FindItemGround"/>); no tiles are broken.</item>
	/// </list>
	/// <para>D2: the client only asks (<see cref="TrashTr0mSummonPacket"/>, <see cref="TrashTr0mBaitPacket"/>); the server
	/// (or singleplayer) validates everything the request names (an active, living player, in reach of a real cache or
	/// inside the Junkyard, no Trash-Tr0m alive) and spawns with <c>SafeSpawn</c> (critical). A client re-asks at most once
	/// per <see cref="RequestCooldown"/> ticks. D0: every tile scan has a fixed bound and is bounds-checked.</para>
	/// </summary>
	public static class TrashTr0mSummon
	{
		public const float MaxReach = 20f * 16f;
		public const int RequestCooldown = 60;
		public const int CacheGroundRows = 4;              // the yard ground is 4 rows under the cache's top (JunkyardPass)
		public const int BurstHalfWidth = 15;              // columns either side of the cache that the burst clears
		public const int BurstRows = 14;                   // rows above the ground line it clears (the heap is 10-13 high)
		public const int PedestalScan = 6;
		public const int ItemSpawnDistance = 24;           // tiles in front of the player
		public const int ItemScanUp = 20, ItemScanDown = 40;
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

		// ------------------------------------------------------------------------------------------------------------
		// The cache
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>Client side of a key-less right-click on the locked cache (<paramref name="left"/>, <paramref name="top"/> = its top-left tile).
		/// Once Trash-Tr0m has been defeated the cache no longer wakes it: it just stays locked until the Lost Key opens it.</summary>
		public static void Request(Player player, int left, int top) {
			if (TrashTr0mSystem.Downed) {
				SoundEngine.PlaySound(SoundID.Unlock with { Pitch = -0.9f, Volume = 0.6f }, new Vector2(left * 16 + 16, top * 16 + 16));
				Main.NewText(Language.GetTextValue("Mods.Cogpunk.NPCs.TrashTr0m.CacheLocked"), 223, 185, 78);
				return;
			}
			if (NPC.AnyNPCs(ModContent.NPCType<TrashTr0m>())) {
				Main.NewText(Language.GetTextValue("Mods.Cogpunk.NPCs.TrashTr0m.CacheGuarded"), 190, 120, 80);
				return;
			}
			if (CoolingDown()) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Unlock with { Pitch = -0.6f }, new Vector2(left * 16 + 16, top * 16 + 16));
			if (Main.netMode == NetmodeID.SinglePlayer) {
				TrySpawn(player.whoAmI, left, top);
			}
			else {
				ModContent.GetInstance<TrashTr0mSummonPacket>().Send(left, top);
			}
		}

		/// <summary>Server or singleplayer: validates the request and spawns the boss under the heap that holds the cache.</summary>
		internal static bool TrySpawn(int playerIndex, int left, int top) {
			if (TrashTr0mSystem.Downed || !ValidPlayer(playerIndex, out Player player) || !IsCache(left, top)) {
				return false;
			}
			Vector2 cacheCentre = new(left * 16 + 16, top * 16 + 16);
			if (Vector2.DistanceSquared(player.Center, cacheCentre) > MaxReach * MaxReach) {
				return false;
			}
			int ground = top + CacheGroundRows;
			if (!TileSafety.InWorld(left, ground, 20)) {
				return false;
			}
			var source = new EntitySource_TileInteraction(player, left, top);
			return Spawn(source, left * 16 + 16, ground * 16, playerIndex, fromHeap: true);
		}

		private static bool IsCache(int left, int top) {
			return TileSafety.TryGetTile(left, top, out Tile tile, 1) && tile.HasTile
				&& tile.TileType == ModContent.TileType<ScrappyTrunkTile>() && tile.TileFrameX / 36 == ScrappyTrunkTile.CacheStyle;
		}

		/// <summary>
		/// Server or singleplayer, during the burst: clears band <paramref name="step"/> of <paramref name="steps"/> of the
		/// heap above the boss's ground line (top band first). Only Rusted Scrap, the heap's own tile, and never the tiles
		/// holding a container up, so the cache is left standing on its pedestal. Tiles are cleared directly instead of
		/// mined (no drops, no per-tile dust or sound: the clients throw their own debris), then reframed and sent as one
		/// tile square per band (at most (2 x 15 + 3) x 6 tiles).
		/// </summary>
		internal static void ClearHeapRows(Vector2 bottom, int step, int steps) {
			if (Main.netMode == NetmodeID.MultiplayerClient || steps <= 0 || step < 0 || step >= steps) {
				return;
			}
			int cx = (int)(bottom.X / 16f);
			int ground = (int)(bottom.Y / 16f);
			int rowsPerStep = (BurstRows + steps - 1) / steps;
			int y0 = ground - BurstRows + step * rowsPerStep;
			int y1 = Math.Min(y0 + rowsPerStep - 1, ground - 1);
			int x0 = cx - BurstHalfWidth;
			int x1 = cx + BurstHalfWidth;
			if (y1 < y0 || !TileSafety.InWorld(x0, y0) || !TileSafety.InWorld(x1, y1)) {
				return;
			}
			ushort scrap = (ushort)ModContent.TileType<RustedScrapTile>();
			bool changed = false;
			for (int y = y0; y <= y1; y++) {
				for (int x = x0; x <= x1; x++) {
					Tile tile = Main.tile[x, y];
					if (tile.HasTile && tile.TileType == scrap && !HoldsUpContainer(x, y, scrap)) {
						tile.ClearTile();
						changed = true;
					}
				}
			}
			if (!changed) {
				return;
			}
			WorldGen.RangeFrame(x0 - 1, y0 - 1, x1 + 1, y1 + 1);
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendTileSquare(-1, x0 - 1, y0 - 1, x1 - x0 + 3, y1 - y0 + 3);
			}
		}

		/// <summary>True for a scrap tile in an unbroken column under a container (within <see cref="PedestalScan"/> tiles).</summary>
		private static bool HoldsUpContainer(int x, int y, ushort scrap) {
			for (int k = 1; k <= PedestalScan; k++) {
				if (!TileSafety.TryGetTile(x, y - k, out Tile above) || !above.HasTile) {
					return false;
				}
				if (Main.tileContainer[above.TileType] || TileID.Sets.BasicChest[above.TileType]) {
					return true;
				}
				if (above.TileType != scrap) {
					return false;
				}
			}
			return false;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Junkbait
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>True where Junkbait can be used: inside the Junkyard, with no Trash-Tr0m alive and ground to climb out of.</summary>
		public static bool CanUseBait(Player player) {
			return player != null && player.active && JunkyardSystem.Contains(player.Center) && !NPC.AnyNPCs(ModContent.NPCType<TrashTr0m>())
				&& FindItemGround(player, out _, out _);
		}

		/// <summary>Owner side of a Junkbait use.</summary>
		public static void RequestFromBait(Player player) {
			if (player.whoAmI != Main.myPlayer) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.6f, Volume = 0.6f }, player.Center);
			if (Main.netMode == NetmodeID.SinglePlayer) {
				TrySpawnFromBait(player.whoAmI);
			}
			else if (!CoolingDown()) {
				ModContent.GetInstance<TrashTr0mBaitPacket>().Send();
			}
		}

		/// <summary>Server or singleplayer: it climbs out of the ground in front of the player.</summary>
		internal static bool TrySpawnFromBait(int playerIndex) {
			if (!ValidPlayer(playerIndex, out Player player) || !JunkyardSystem.Contains(player.Center)) {
				return false;
			}
			if (!FindItemGround(player, out int x, out int ground)) {
				return false;
			}
			return Spawn(player.GetSource_ItemUse(player.HeldItem), x * 16 + 8, ground * 16, playerIndex, fromHeap: false);
		}

		/// <summary>
		/// A surface for the emergence: <see cref="ItemSpawnDistance"/> tiles in front of the player, else behind, else under
		/// them. At most 3 x (<see cref="ItemScanUp"/> + <see cref="ItemScanDown"/>) bounds-checked reads.
		/// </summary>
		public static bool FindItemGround(Player player, out int x, out int ground) {
			int px = (int)(player.Center.X / 16f);
			int py = (int)(player.Bottom.Y / 16f);
			int dir = player.direction >= 0 ? 1 : -1;
			for (int i = 0; i < 3; i++) {
				x = px + (i == 0 ? dir * ItemSpawnDistance : i == 1 ? -dir * ItemSpawnDistance : 0);   // ahead, behind, under
				for (int y = py - ItemScanUp; y <= py + ItemScanDown; y++) {
					if (Ground(x, y) && !Ground(x, y - 1) && TileSafety.InWorld(x, y, 60)) {
						ground = y;
						return true;
					}
				}
			}
			x = ground = 0;
			return false;
		}

		private static bool Ground(int x, int y) {
			return TileSafety.TryGetTile(x, y, out Tile tile, 1) && tile.HasTile && !tile.IsActuated
				&& (Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType]);
		}

		// ------------------------------------------------------------------------------------------------------------

		private static bool ValidPlayer(int playerIndex, out Player player) {
			player = null;
			if (Main.netMode == NetmodeID.MultiplayerClient || playerIndex < 0 || playerIndex >= Main.maxPlayers) {
				return false;
			}
			player = Main.player[playerIndex];
			return player.active && !player.dead && !NPC.AnyNPCs(ModContent.NPCType<TrashTr0m>());
		}

		private static bool Spawn(IEntitySource source, int x, int bottom, int target, bool fromHeap) {
			int type = ModContent.NPCType<TrashTr0m>();
			if (!SafeSpawn.TryNewNPC(source, x, bottom, type, out NPC boss, ai2: fromHeap ? 1f : 0f, target: target, critical: true)) {
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
	}

	/// <summary>Client -> server: "I touched the Junkyard Cache at (left, top) without its key". Two shorts; validated by <see cref="TrashTr0mSummon.TrySpawn"/>.</summary>
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

	/// <summary>Client -> server: "I used Junkbait". No payload: the sender is the player; validated by <see cref="TrashTr0mSummon.TrySpawnFromBait"/>.</summary>
	public sealed class TrashTr0mBaitPacket : CogpunkPacket
	{
		public void Send() {
			Begin().Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			if (Main.netMode != NetmodeID.Server) {
				return;
			}
			TrashTr0mSummon.TrySpawnFromBait(sender);
		}
	}
}
