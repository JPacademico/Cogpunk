using System.IO;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.Chat;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Secrets
{
	/// <summary>
	/// Waking the Fundamental Stones, the puzzle's last two layers (user, 2026-11-24: "the first step is translating then how to
	/// activate the stones then which order to activate"; the translation is <see cref="GhedalariScript.Translated"/>).
	/// <list type="bullet">
	/// <item><b>How each stone wakes</b>: Westworld's (the sun) when a Honeyfin is dropped next to it (user: "to activate the
	/// player has to just drop a honey fin next to it"; the server looks for one every <see cref="ScanTicks"/> ticks within
	/// <see cref="FishReachX"/> x <see cref="FishReachY"/> tiles and takes one fish); the tar pit's (the fleur) as soon as it is
	/// touched (user: "should only say "..." and activate right upon interaction"); the ruins' and the two stones still to be
	/// placed: their riddles are to come (they stay sealed until then).</item>
	/// <item><b>The order</b> (<see cref="Order"/>, my call: sun, fleur, mountain, cross, wave, which the Last Ghedalari spells
	/// out in sigils): a stone woken out of turn puts every stone back to sleep (user: "in case a player activates the stones
	/// in the wrong order all of them just deactivate to be activated again"); with all five awake the world is
	/// <see cref="Aligned"/> (its reward is to come).</item>
	/// </list>
	/// An awake stone's cuts glow gold instead of blue (<see cref="FundamentalStoneTile"/>); a client that sees a stone wake or
	/// fall asleep plays it (<see cref="Seen"/>), and the toucher of a stone woken out of turn sees it flare and die out at once.
	/// <para>D2: the server decides (a client's touch is a <see cref="StoneTouchPacket"/>, checked: that stone at that spot, the
	/// sender alive within reach); the stones' states are world flags (saved by name, sent with the world data). D0: indices
	/// and tiles checked, the item loop bounded by <see cref="Main.maxItems"/>, the tile search by its box. D1: the server's
	/// scan runs twice a second and stops at once while Westworld's stone is sealed or awake; no allocation.</para>
	/// </summary>
	public sealed class FundamentalStoneAwakening : ModSystem
	{
		/// <summary>The order the stones wake in, by stone (my call; hinted in the Last Ghedalari's sixth phrase).</summary>
		public static readonly int[] Order = { FundamentalStones.Westworld, FundamentalStones.TarPit, FundamentalStones.Ruins, 3, 4 };

		public const int ScanTicks = 30;
		public const int FishReachX = 4, FishReachY = 6;          // tiles round a dropped fish searched for the sun stone
		public const float TouchReach = 20f * 16f;               // the server's check of a touch (vanilla reach + lag slack)
		public const int RejectTicks = 45;                       // the flare of a stone touched out of turn (the toucher's)

		private static readonly int[] awakeFlags = new int[FundamentalStones.Count];
		private static int alignedFlag = -1;
		private static int scanTimer;
		private static readonly sbyte[] seen = new sbyte[FundamentalStones.Count];   // clients: -1 unseen, 0 asleep, 1 awake
		private static int rejectStone = -1, rejectAge;

		public override void Load() {
			for (int k = 0; k < FundamentalStones.Count; k++) {
				awakeFlags[k] = WorldFlagSystem.Register("StoneAwake" + (k + 1));
			}
			alignedFlag = WorldFlagSystem.Register("StonesAligned");
		}

		public override void ClearWorld() {
			scanTimer = 0;
			rejectStone = -1;
			ResetSeen();
		}

		/// <summary>A new world: no stone seen yet (so a world loaded with stones awake plays nothing).</summary>
		public static void ResetSeen() {
			for (int k = 0; k < seen.Length; k++) {
				seen[k] = -1;
			}
		}

		public static bool Awake(int stone) => stone >= 0 && stone < FundamentalStones.Count && WorldFlagSystem.Get(awakeFlags[stone]);

		public static int AwakeCount {
			get {
				int n = 0;
				for (int k = 0; k < FundamentalStones.Count; k++) {
					if (Awake(k)) {
						n++;
					}
				}
				return n;
			}
		}

		/// <summary>All five stones woke in their order (for good).</summary>
		public static bool Aligned => WorldFlagSystem.Get(alignedFlag);

		/// <summary>The stone that must wake next (stones only ever wake in order, so the awake ones are the order's first ones).</summary>
		public static int Next {
			get {
				int n = AwakeCount;
				return n < Order.Length ? Order[n] : -1;
			}
		}

		/// <summary>The stone wakes when touched (the tar pit's).</summary>
		public static bool WakesOnTouch(int stone) => stone == FundamentalStones.TarPit;

		/// <summary>The local player read stone <paramref name="stone"/> (its top-left tile at <paramref name="left"/>,
		/// <paramref name="top"/>): one that wakes on a touch asks the server to wake it. Out of turn, the toucher sees it flare
		/// and die out (predicted here from the world's flags; the server decides the same).</summary>
		public static void RequestTouch(int stone, int left, int top) {
			if (!WakesOnTouch(stone) || FundamentalStones.Sealed(stone) || Awake(stone)) {
				return;
			}
			if (Next != stone && !Main.dedServ) {
				rejectStone = stone;
				rejectAge = 0;
				Vector2 centre = new(left * 16f + FundamentalStoneTile.Width * 8f, top * 16f + FundamentalStoneTile.Height * 8f);
				SoundEngine.PlaySound(SoundID.Item29 with { Pitch = -0.2f, Volume = 0.7f }, centre);
			}
			if (Main.netMode == NetmodeID.SinglePlayer) {
				TryWake(stone);
			}
			else if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<StoneTouchPacket>().Send(stone, left, top);
			}
		}

		/// <summary>Server or singleplayer: stone <paramref name="stone"/> wakes if it is the next in the order; out of turn,
		/// every stone falls asleep. The world data goes to every client.</summary>
		public static void TryWake(int stone) {
			if (Main.netMode == NetmodeID.MultiplayerClient || stone < 0 || stone >= FundamentalStones.Count
				|| FundamentalStones.Sealed(stone) || Awake(stone)) {
				return;
			}
			if (Next == stone) {
				WorldFlagSystem.Flag(awakeFlags[stone]) = true;
				if (AwakeCount >= FundamentalStones.Count && !Aligned) {
					WorldFlagSystem.Flag(alignedFlag) = true;
					Announce("Mods.Cogpunk.Secrets.StonesAligned");
				}
			}
			else {
				bool any = AwakeCount > 0;
				for (int k = 0; k < FundamentalStones.Count; k++) {
					WorldFlagSystem.Flag(awakeFlags[k]) = false;
				}
				if (any) {
					Announce("Mods.Cogpunk.Secrets.StonesAsleep");
				}
			}
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.WorldData);
			}
		}

		private static void Announce(string key) {
			Color colour = new(223, 185, 78);
			if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey(key), colour);
			}
			else {
				Main.NewText(Language.GetTextValue(key), colour);
			}
		}

		/// <summary>Server or singleplayer: a Honeyfin lying next to Westworld's stone (unsealed, asleep) is taken, and the
		/// stone wakes.</summary>
		public override void PostUpdateWorld() {
			if (++scanTimer < ScanTicks) {
				return;
			}
			scanTimer = 0;
			int sun = FundamentalStones.Westworld;
			if (Awake(sun) || FundamentalStones.Sealed(sun) || Next != sun) {
				return;
			}
			for (int i = 0; i < Main.maxItems; i++) {
				Item item = Main.item[i];
				if (!item.active || item.type != ItemID.Honeyfin || item.stack <= 0 || !StoneNear(item.Center, sun)) {
					continue;
				}
				if (--item.stack <= 0) {
					item.TurnToAir();
				}
				if (Main.netMode == NetmodeID.Server) {
					NetMessage.SendData(MessageID.SyncItem, -1, -1, null, i);
				}
				TryWake(sun);
				return;
			}
		}

		/// <summary>Stone <paramref name="stone"/> stands within <see cref="FishReachX"/> x <see cref="FishReachY"/> tiles of
		/// <paramref name="position"/> (world px).</summary>
		private static bool StoneNear(Vector2 position, int stone) {
			int cx = (int)(position.X / 16f), cy = (int)(position.Y / 16f);
			int type = ModContent.TileType<FundamentalStoneTile>();
			for (int x = cx - FishReachX; x <= cx + FishReachX; x++) {
				for (int y = cy - FishReachY; y <= cy + FishReachY; y++) {
					if (TileSafety.TryGetTile(x, y, out Tile tile) && tile.HasTile && tile.TileType == type
						&& tile.TileFrameX / FundamentalStoneTile.StyleWidth == stone) {
						return true;
					}
				}
			}
			return false;
		}

		// --- what clients see --------------------------------------------------------------------------------------------

		/// <summary>Clients: the stone's top-left tile is drawn this frame (<see cref="FundamentalStoneTile.DrawEffects"/>); a
		/// stone this client saw asleep that is now awake wakes here (and the other way round), once.</summary>
		public static void Seen(int stone, int left, int top) {
			if (stone < 0 || stone >= FundamentalStones.Count) {
				return;
			}
			bool awake = Awake(stone);
			sbyte was = seen[stone];
			seen[stone] = (sbyte)(awake ? 1 : 0);
			if (was < 0 || was == seen[stone]) {
				return;
			}
			Vector2 centre = new(left * 16f + FundamentalStoneTile.Width * 8f, top * 16f + FundamentalStoneTile.Height * 8f);
			if (awake) {
				SoundEngine.PlaySound(SoundID.Item29 with { Pitch = -0.35f }, centre);
				SoundEngine.PlaySound(SoundID.Item4 with { Pitch = -0.5f, Volume = 0.6f }, centre);
				Burst(centre, DustID.GoldFlame, 30, -1f);
			}
			else {
				SoundEngine.PlaySound(SoundID.Item27 with { Pitch = -0.7f, Volume = 0.8f }, centre);
				Burst(centre, DustID.Smoke, 18, 0.5f);
			}
		}

		private static void Burst(Vector2 centre, int dust, int count, float rise) {
			for (int k = 0; k < count && CogpunkClientConfig.RollEffect(); k++) {
				if (SafeSpawn.TryNewDust(centre - new Vector2(28f, 40f), 56, 80, dust, out Dust d)) {
					d.noGravity = true;
					d.velocity = new Vector2(Main.rand.NextFloat(-1.2f, 1.2f), rise * Main.rand.NextFloat(0.5f, 2f));
					d.scale = 1.2f;
				}
			}
		}

		/// <summary>The toucher's flare of a stone touched out of turn: 1 at the touch, fading to 0 over
		/// <see cref="RejectTicks"/> (0 for any other stone).</summary>
		public static float Flare(int stone) => stone == rejectStone && rejectAge < RejectTicks ? 1f - rejectAge / (float)RejectTicks : 0f;

		public override void PostUpdateEverything() {
			if (rejectStone < 0 || Main.dedServ) {
				return;
			}
			if (++rejectAge == RejectTicks / 2) {
				SoundEngine.PlaySound(SoundID.Item27 with { Pitch = -0.7f, Volume = 0.7f }, Main.LocalPlayer.Center);
			}
			if (rejectAge >= RejectTicks) {
				rejectStone = -1;
			}
		}
	}

	/// <summary>A client touched a stone that wakes on a touch: its number and its top-left tile (a byte and two shorts). The
	/// server acts only if that tile is that stone and the sender's living player stands within reach of it.</summary>
	public sealed class StoneTouchPacket : CogpunkPacket
	{
		public void Send(int stone, int left, int top) {
			ModPacket packet = Begin();
			packet.Write((byte)stone);
			packet.Write((short)left);
			packet.Write((short)top);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			int stone = reader.ReadByte();
			int left = reader.ReadInt16(), top = reader.ReadInt16();
			if (Main.netMode != NetmodeID.Server || stone >= FundamentalStones.Count || !FundamentalStoneAwakening.WakesOnTouch(stone)
				|| sender < 0 || sender >= Main.maxPlayers) {
				return;
			}
			Player player = Main.player[sender];
			if (!player.active || player.dead || !TileSafety.TryGetTile(left, top, out Tile tile) || !tile.HasTile
				|| tile.TileType != ModContent.TileType<FundamentalStoneTile>()
				|| FundamentalStoneTile.StyleAt(left, top, out int x0, out int y0) != stone || x0 != left || y0 != top) {
				return;
			}
			Vector2 centre = new(left * 16f + FundamentalStoneTile.Width * 8f, top * 16f + FundamentalStoneTile.Height * 8f);
			if (Vector2.DistanceSquared(player.Center, centre) > FundamentalStoneAwakening.TouchReach * FundamentalStoneAwakening.TouchReach) {
				return;
			}
			FundamentalStoneAwakening.TryWake(stone);
		}
	}
}
