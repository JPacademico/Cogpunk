using System;
using System.Collections.Generic;
using System.IO;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// Ore blocks players placed (2026-11-18, user: "ensure no exploits"): "Mine and Craft"'s extra ore
	/// (<see cref="ResearchGlobalTile"/>) is for ore found in the world, not ore set down and mined again (each round trip would
	/// make 10% more, forever). The placing client tells the server (<see cref="PlacedOrePacket"/>; singleplayer: at once); the
	/// server (or singleplayer) keeps the spots, saved with the world, and forgets each when its block breaks. A placed ore that
	/// breaks drops only itself.
	/// <para>D0: at most <see cref="MaxSpots"/> spots (past that the oldest go: a mined-out spot is forgotten anyway); every
	/// coordinate checked (<see cref="TileSafety"/>). D1: a hash lookup per ore drop.</para>
	/// </summary>
	public sealed class PlacedOres : ModSystem
	{
		public const int MaxSpots = 200000;
		private static readonly HashSet<int> spots = new();
		private static readonly Queue<int> order = new();

		public static int Key(int i, int j) => i * 8192 + j;

		public override void ClearWorld() {
			spots.Clear();
			order.Clear();
		}

		public override void SaveWorldData(TagCompound tag) {
			if (spots.Count > 0) {
				tag["PlacedOres"] = new List<int>(spots);
			}
		}

		public override void LoadWorldData(TagCompound tag) {
			spots.Clear();
			order.Clear();
			if (!tag.ContainsKey("PlacedOres")) {
				return;
			}
			foreach (int k in tag.GetList<int>("PlacedOres")) {
				if (spots.Count >= MaxSpots) {
					break;
				}
				if (spots.Add(k)) {
					order.Enqueue(k);
				}
			}
		}

		/// <summary>The server (or singleplayer): an ore block was placed at (i, j).</summary>
		public static void Mark(int i, int j) {
			if (Main.netMode == NetmodeID.MultiplayerClient || !TileSafety.TryGetTile(i, j, out Tile t) || !t.HasTile
				|| t.TileType >= TileID.Sets.Ore.Length || !TileID.Sets.Ore[t.TileType]) {
				return;
			}
			int k = Key(i, j);
			if (!spots.Add(k)) {
				return;
			}
			order.Enqueue(k);
			while (spots.Count > MaxSpots && order.Count > 0) {
				spots.Remove(order.Dequeue());
			}
		}

		/// <summary>The server (or singleplayer): whether (i, j) held a placed ore; forgets it (its block is breaking).</summary>
		public static bool Take(int i, int j) => spots.Remove(Key(i, j));
	}

	/// <summary>The placing client: an ore block it placed (tModLoader's <c>PlaceInWorld</c> runs on the placing client).</summary>
	public sealed class PlacedOreGlobalTile : GlobalTile
	{
		public override void PlaceInWorld(int i, int j, int type, Item item) {
			if (type < 0 || type >= TileID.Sets.Ore.Length || !TileID.Sets.Ore[type]) {
				return;
			}
			if (Main.netMode == NetmodeID.SinglePlayer) {
				PlacedOres.Mark(i, j);
			}
			else if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<PlacedOrePacket>().Send(i, j);
			}
		}
	}

	/// <summary>Client -> server: "I placed an ore block at (i, j)". Two shorts, checked (D0 rule 7); the server re-reads the
	/// tile itself.</summary>
	public sealed class PlacedOrePacket : CogpunkPacket
	{
		public void Send(int i, int j) {
			ModPacket packet = Begin();
			packet.Write((short)i);
			packet.Write((short)j);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			int i = reader.ReadInt16();
			int j = reader.ReadInt16();
			if (Main.netMode == NetmodeID.Server) {
				PlacedOres.Mark(i, j);
			}
		}
	}
}
