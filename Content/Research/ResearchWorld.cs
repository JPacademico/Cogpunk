using System;
using System.Collections.Generic;
using System.IO;
using Cogpunk.Core.Events;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Terraria;
using Terraria.GameContent.Events;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// The world's side of the knowledge tasks (user, 2026-11-18): "every first boss or miniboss kill on the world should give a
	/// knowledge point to players on the world (only first kill)" and "finishing a event (100%) for the first time should give
	/// one (to every player)". The server (or singleplayer) remembers which bosses and events this world has already paid for
	/// (saved with the world, by name), and on a first tells every player in the world (<see cref="ResearchGrantPacket"/>);
	/// each character takes a point once per boss or event (<see cref="ResearchPlayer.Grant(string, string, int)"/>).
	/// <list type="bullet">
	/// <item>Bosses and mini-bosses (<see cref="ResearchGlobalNPC"/>): <c>npc.boss</c> or <see cref="CogpunkSets.Miniboss"/>
	/// (terraria.wiki.gg's mini-bosses: the Old One's Army's Dark Mage, Ogre and Betsy, the Flying Dutchman, the Pumpkin and
	/// Frost Moons' bosses, the Martian Saucer; Cogpunk's own mark themselves), counted on the part that finishes them: the
	/// last Eater of Worlds segment, the second Twin, Moon Lord's core, Golem's body, the Saucer's core; parts that share a
	/// life with a head never count.</item>
	/// <item>Events, polled every <see cref="PollInterval"/> ticks: vanilla's own "defeated" flags (the Goblin Army, the
	/// Frost Legion, the Pirates, Martian Madness, each of the Old One's Army's three tiers), the Pumpkin and Frost Moons
	/// reaching their last wave (15 and 20: they have no other end; my reading of "100%"), and every Cogpunk invasion's flag
	/// (the Mech Army). Events this world finished before (before this update too) are noted when the world loads and pay
	/// nothing.</item>
	/// </list>
	/// <para>D0: the saved list is capped; packet indices validated. D2: server decides, every client grants its own player.</para>
	/// </summary>
	public sealed class ResearchWorld : ModSystem
	{
		public const int PollInterval = 60;
		private const int MaxSaved = 1024;
		public const int PumpkinMoonLastWave = 15, FrostMoonLastWave = 20;

		/// <summary>Vanilla's events, by their id in a <see cref="ResearchGrantPacket"/>; Cogpunk's invasions follow from
		/// <see cref="InvasionBase"/> (their index).</summary>
		public static readonly string[] VanillaEvents = { "GoblinArmy", "FrostLegion", "PirateInvasion", "MartianMadness", "OldOnesArmy1",
			"OldOnesArmy2", "OldOnesArmy3", "PumpkinMoon", "FrostMoon" };
		public const int InvasionBase = 32;

		private static readonly HashSet<string> paid = new();
		private static bool noted;
		private static int gemStaffsFlag = -1;

		/// <summary>"Bundle Up!"'s reveal (user, 2026-11-18: "appears when a any player has obtained all pre hardmode gem staffs
		/// (globally)"): a player of this world has had all seven (<see cref="ResearchPlayer.AllGemStaffs"/>); a world flag,
		/// saved with the world and synced to every client (<see cref="WorldFlagSystem"/>), so the node shows for everyone.</summary>
		public static bool AllGemStaffs => WorldFlagSystem.Get(gemStaffsFlag);

		public override void Load() {
			gemStaffsFlag = WorldFlagSystem.Register("AllGemStaffs");
		}

		/// <summary>The owner's client: its player has had all seven gem staffs. Singleplayer sets the flag; a client asks the
		/// server (<see cref="GemStaffsPacket"/>).</summary>
		public static void ReportAllGemStaffs() {
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<GemStaffsPacket>().Send();
				return;
			}
			SetAllGemStaffs();
		}

		/// <summary>The server (or singleplayer): the flag set, and the world data sent so every client sees the node.</summary>
		public static void SetAllGemStaffs() {
			if (Main.netMode == NetmodeID.MultiplayerClient || gemStaffsFlag < 0 || WorldFlagSystem.Get(gemStaffsFlag)) {
				return;
			}
			WorldFlagSystem.Flag(gemStaffsFlag) = true;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.WorldData);
			}
		}

		public override void ClearWorld() {
			paid.Clear();
			noted = false;
		}

		public override void SaveWorldData(TagCompound tag) {
			if (paid.Count > 0) {
				tag["ResearchPaid"] = new List<string>(paid);
			}
		}

		public override void LoadWorldData(TagCompound tag) {
			paid.Clear();
			if (!tag.ContainsKey("ResearchPaid")) {
				return;
			}
			foreach (string s in tag.GetList<string>("ResearchPaid")) {
				if (!string.IsNullOrEmpty(s) && paid.Count < MaxSaved) {
					paid.Add(s);
				}
			}
		}

		/// <summary>The server (or singleplayer): a boss or mini-boss just died.</summary>
		public static void OnBossKilled(NPC npc) {
			int type = CanonicalBoss(npc);
			if (type <= 0) {
				return;
			}
			string key = KnowledgeTasks.Boss(type);
			if (paid.Count < MaxSaved && paid.Add(key)) {
				ResearchGrantPacket.ToAll(ResearchGrantPacket.Kind.Boss, type);
			}
		}

		/// <summary>The NPC type a boss kill is counted under, or 0 when this death doesn't finish a boss or mini-boss.</summary>
		public static int CanonicalBoss(NPC npc) {
			if (npc == null || npc.type <= NPCID.None) {
				return 0;
			}
			int t = npc.type;
			switch (t) {
				case NPCID.EaterofWorldsHead:
				case NPCID.EaterofWorldsBody:
				case NPCID.EaterofWorldsTail:
					foreach (NPC other in Main.ActiveNPCs) {
						if (other.whoAmI != npc.whoAmI && other.life > 0 && (other.type == NPCID.EaterofWorldsHead || other.type == NPCID.EaterofWorldsBody
							|| other.type == NPCID.EaterofWorldsTail)) {
							return 0;                                // segments still alive: not the end
						}
					}
					return NPCID.EaterofWorldsHead;
				case NPCID.Retinazer:
				case NPCID.Spazmatism:
					int twin = t == NPCID.Retinazer ? NPCID.Spazmatism : NPCID.Retinazer;
					foreach (NPC other in Main.ActiveNPCs) {
						if (other.type == twin && other.life > 0) {
							return 0;
						}
					}
					return NPCID.Retinazer;
				case NPCID.MoonLordHead:
				case NPCID.MoonLordHand:
				case NPCID.MoonLordFreeEye:
				case NPCID.GolemHead:
				case NPCID.GolemHeadFree:
				case NPCID.GolemFistLeft:
				case NPCID.GolemFistRight:
				case NPCID.WallofFleshEye:
				case NPCID.SkeletronHand:
				case NPCID.PrimeCannon:
				case NPCID.PrimeSaw:
				case NPCID.PrimeVice:
				case NPCID.PrimeLaser:
				case NPCID.PirateShipCannon:
				case NPCID.PumpkingBlade:
				case NPCID.MartianSaucer:
				case NPCID.MartianSaucerCannon:
				case NPCID.MartianSaucerTurret:
					return 0;                                        // parts: their boss counts when it falls
			}
			if (npc.realLife >= 0 && npc.realLife != npc.whoAmI) {
				return 0;                                            // a part sharing its head's life
			}
			bool mini = t < CogpunkSets.Miniboss.Length && CogpunkSets.Miniboss[t];
			return npc.boss || mini ? t : 0;
		}

		/// <summary>The server (or singleplayer): notes events already finished when the world loads (no points), then pays for
		/// new ones as they finish.</summary>
		public override void PostUpdateWorld() {
			if (Main.GameUpdateCount % PollInterval != 0) {
				return;
			}
			bool first = !noted;
			noted = true;
			for (int k = 0; k < VanillaEvents.Length; k++) {
				if (VanillaDone(k)) {
					Pay(KnowledgeTasks.Event(VanillaEvents[k]), k, first);
				}
			}
			IReadOnlyList<CogpunkInvasion> invasions = CogpunkInvasion.All;
			for (int k = 0; k < invasions.Count && InvasionBase + k < 256; k++) {
				if (invasions[k].Downed) {
					Pay(KnowledgeTasks.Event(invasions[k].Name), InvasionBase + k, first);
				}
			}
		}

		private static bool VanillaDone(int k) => k switch {
			0 => NPC.downedGoblins,
			1 => NPC.downedFrost,
			2 => NPC.downedPirates,
			3 => NPC.downedMartians,
			4 => DD2Event.DownedInvasionT1,
			5 => DD2Event.DownedInvasionT2,
			6 => DD2Event.DownedInvasionT3,
			7 => Main.pumpkinMoon && NPC.waveNumber >= PumpkinMoonLastWave,
			8 => Main.snowMoon && NPC.waveNumber >= FrostMoonLastWave,
			_ => false,
		};

		private static void Pay(string key, int eventId, bool silently) {
			if (paid.Count >= MaxSaved || !paid.Add(key) || silently) {
				return;
			}
			ResearchGrantPacket.ToAll(ResearchGrantPacket.Kind.Event, eventId);
		}

		/// <summary>An event's saved name and its reason line, from its packet id (any side).</summary>
		public static bool EventName(int id, out string name, out string reason) {
			name = null;
			reason = null;
			if (id >= 0 && id < VanillaEvents.Length) {
				name = VanillaEvents[id];
				reason = KnowledgeTasks.EventReason(name);
				return true;
			}
			int k = id - InvasionBase;
			IReadOnlyList<CogpunkInvasion> invasions = CogpunkInvasion.All;
			if (k >= 0 && k < invasions.Count) {
				name = invasions[k].Name;
				reason = Terraria.Localization.Language.GetTextValue("Mods.Cogpunk.Research.Tasks.Event", invasions[k].DisplayName?.Value ?? name);
				return true;
			}
			return false;
		}
	}

	/// <summary>
	/// A knowledge task done (server -> one client or all): which kind and its argument (the boss's NPC type, the event's id).
	/// Each client grants its own player (<see cref="ResearchPlayer.Grant(string, string, int)"/>). In singleplayer it is
	/// applied at once. A kind byte and an int; the NPC type and event id are validated on receipt (D0 rule 7).
	/// </summary>
	public sealed class ResearchGrantPacket : CogpunkPacket
	{
		public enum Kind : byte { Boss, Event, PinkSlime, Gnome }

		/// <summary>The server (or singleplayer): every player in the world.</summary>
		public static void ToAll(Kind kind, int arg) {
			if (Main.netMode == NetmodeID.SinglePlayer) {
				Apply(kind, arg);
				return;
			}
			if (Main.netMode == NetmodeID.Server) {
				ModContent.GetInstance<ResearchGrantPacket>().Send(kind, arg, -1);
			}
		}

		/// <summary>The server (or singleplayer): one player (a kill of theirs).</summary>
		public static void ToPlayer(int player, Kind kind) {
			if (player < 0 || player >= Main.maxPlayers || !Main.player[player].active) {
				return;
			}
			if (Main.netMode == NetmodeID.SinglePlayer) {
				if (player == Main.myPlayer) {
					Apply(kind, 0);
				}
				return;
			}
			if (Main.netMode == NetmodeID.Server) {
				ModContent.GetInstance<ResearchGrantPacket>().Send(kind, 0, player);
			}
		}

		private void Send(Kind kind, int arg, int toClient) {
			ModPacket packet = Begin();
			packet.Write((byte)kind);
			packet.Write(arg);
			packet.Send(toClient);
		}

		public override void Receive(BinaryReader reader, int sender) {
			Kind kind = (Kind)reader.ReadByte();
			int arg = reader.ReadInt32();
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				return;                                          // the server sends these; it never takes them
			}
			Apply(kind, arg);
		}

		private static void Apply(Kind kind, int arg) {
			if (Main.dedServ || Main.myPlayer < 0 || Main.myPlayer >= Main.maxPlayers) {
				return;
			}
			Player me = Main.LocalPlayer;
			if (me == null || !me.active) {
				return;
			}
			ResearchPlayer r = me.GetModPlayer<ResearchPlayer>();
			switch (kind) {
				case Kind.Boss:
					if (arg > NPCID.None && arg < NPCLoader.NPCCount) {
						r.Grant(KnowledgeTasks.Boss(arg), KnowledgeTasks.BossReason(arg));
					}
					break;
				case Kind.Event:
					if (ResearchWorld.EventName(arg, out string name, out string reason)) {
						r.Grant(KnowledgeTasks.Event(name), reason);
					}
					break;
				case Kind.PinkSlime:
					r.Grant(KnowledgeTasks.PinkSlime);
					break;
				case Kind.Gnome:
					r.Grant(KnowledgeTasks.Gnome);
					break;
			}
		}
	}

	/// <summary>A client's player has had all seven pre-Hardmode gem staffs (client -> server; no payload): the server sets
	/// <see cref="ResearchWorld.AllGemStaffs"/> (once; later ones are ignored). Only from an active player (D0 rule 7).</summary>
	public sealed class GemStaffsPacket : CogpunkPacket
	{
		public void Send() {
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				return;
			}
			Begin().Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			if (Main.netMode != NetmodeID.Server || sender < 0 || sender >= Main.maxPlayers || !Main.player[sender].active) {
				return;
			}
			ResearchWorld.SetAllGemStaffs();
		}
	}

	/// <summary>A player's unlocked research nodes (client -> server for its own player; server -> the other clients), as
	/// bits: a count byte and that many bytes (at most <see cref="ResearchNodes.MaxNodes"/> / 8). Validated (D0 rule 7).</summary>
	public sealed class ResearchSyncPacket : CogpunkPacket
	{
		public void Send(int player, byte[] mask, int toClient = -1, int ignoreClient = -1) {
			if (Main.netMode == NetmodeID.SinglePlayer) {
				return;
			}
			int n = Math.Min(mask.Length, ResearchNodes.MaxNodes / 8);
			ModPacket packet = Begin();
			packet.Write((byte)player);
			packet.Write((byte)n);
			packet.Write(mask, 0, n);
			packet.Send(toClient, ignoreClient);
		}

		public override void Receive(BinaryReader reader, int sender) {
			int player = reader.ReadByte();
			int n = reader.ReadByte();
			byte[] mask = reader.ReadBytes(n);
			if (player < 0 || player >= Main.maxPlayers || mask.Length != n || n > ResearchNodes.MaxNodes / 8) {
				return;
			}
			if (Main.netMode == NetmodeID.Server && player != sender) {
				return;                                          // a client speaks only for its own player
			}
			Player p = Main.player[player];
			if (p == null || (Main.netMode == NetmodeID.Server && !p.active)) {
				return;
			}
			p.GetModPlayer<ResearchPlayer>().ApplyMask(mask);
			if (Main.netMode == NetmodeID.Server) {
				Send(player, mask, -1, sender);                  // tell everyone else
			}
		}
	}

	/// <summary>Kills that count for research (the server or singleplayer, where loot and <c>OnKill</c> run): a boss or
	/// mini-boss's first defeat in the world (<see cref="ResearchWorld"/>), and "killing a pink slime" (Pinky,
	/// <c>NPCID.Pinky</c>) or "a gnome" (<c>NPCID.Gnome</c>) for the player who killed it (vanilla's
	/// <c>lastInteraction</c>).</summary>
	public sealed class ResearchGlobalNPC : GlobalNPC
	{
		/// <summary>Only bosses, mini-boss parts, the slime type Pinky is made from and gnomes (D1: a narrow global).</summary>
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			if (!lateInstantiation) {
				return false;
			}
			int t = entity.type;
			return entity.boss || t == NPCID.BlueSlime || t == NPCID.Gnome
				|| (t > NPCID.None && t < CogpunkSets.Miniboss.Length && CogpunkSets.Miniboss[t])
				|| (t > NPCID.None && t < NPCID.Sets.ShouldBeCountedAsBoss.Length && NPCID.Sets.ShouldBeCountedAsBoss[t])
				|| t == NPCID.EaterofWorldsHead || t == NPCID.EaterofWorldsBody || t == NPCID.EaterofWorldsTail
				|| t == NPCID.Retinazer || t == NPCID.Spazmatism || t == NPCID.MoonLordCore || t == NPCID.GolemHead || t == NPCID.Golem
				|| t == NPCID.MartianSaucerCore || t == NPCID.WallofFlesh;
		}

		public override void OnKill(NPC npc) {
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}
			if (CogpunkSets.IsBossOrMiniboss(npc)) {
				ResearchWorld.OnBossKilled(npc);
			}
			if (npc.netID == NPCID.Pinky) {
				ResearchGrantPacket.ToPlayer(npc.lastInteraction, ResearchGrantPacket.Kind.PinkSlime);
			}
			else if (npc.type == NPCID.Gnome) {
				ResearchGrantPacket.ToPlayer(npc.lastInteraction, ResearchGrantPacket.Kind.Gnome);
			}
		}
	}

	/// <summary>"Mine and Craft" (user-set 2026-11-18: "a chance to double nugget while mining any ore (10%)"): when an ore
	/// block drops (the server or singleplayer, vanilla's <c>KillTile</c> drops), the player nearest to it (who mined it)
	/// with the node gets one more of that ore, <see cref="ResearchNodes.DoubleOreChance"/> of the time. The ore item for
	/// each ore block is found once (the item that places it).</summary>
	public sealed class ResearchGlobalTile : GlobalTile
	{
		private static int[] oreItemOfTile;

		/// <summary>Once content is set up (<see cref="ResearchNodes"/>): each ore block's item.</summary>
		public static void BuildOreTable() {
			oreItemOfTile = new int[TileLoader.TileCount];
			for (int type = 1; type < ItemLoader.ItemCount; type++) {
				if (!ContentSamples.ItemsByType.TryGetValue(type, out Item sample)) {
					continue;
				}
				int t = sample.createTile;
				if (t >= 0 && t < oreItemOfTile.Length && t < TileID.Sets.Ore.Length && TileID.Sets.Ore[t] && oreItemOfTile[t] == 0) {
					oreItemOfTile[t] = type;
				}
			}
		}

		public override void Unload() {
			oreItemOfTile = null;
		}

		public override void Drop(int i, int j, int type) {
			if (Main.netMode == NetmodeID.MultiplayerClient || oreItemOfTile == null || type < 0 || type >= oreItemOfTile.Length
				|| oreItemOfTile[type] <= 0) {
				return;
			}
			if (PlacedOres.Take(i, j)) {
				return;                                          // a player set this ore down: no extra (2026-11-18, no exploits)
			}
			int p = Player.FindClosest(new Microsoft.Xna.Framework.Vector2(i * 16f, j * 16f), 16, 16);
			if (p < 0 || p >= Main.maxPlayers || !Main.player[p].active
				|| !Main.player[p].GetModPlayer<ResearchPlayer>().Has(ResearchNodes.MineAndCraft)) {
				return;
			}
			if (Main.rand.NextFloat() < ResearchNodes.DoubleOreChance) {
				SafeSpawn.TryNewItem(new Terraria.DataStructures.EntitySource_TileBreak(i, j), new Microsoft.Xna.Framework.Rectangle(i * 16, j * 16, 16, 16),
					oreItemOfTile[type], 1, out _);
			}
		}
	}
}
