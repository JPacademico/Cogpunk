using System;
using System.Collections.Generic;
using System.IO;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Chat;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Core.Events
{
	/// <summary>
	/// Base for Cogpunk invasions: events that follow vanilla's goblin army rules exactly, re-implemented because vanilla's
	/// own invasion fields only know vanilla's four invasions (decompiled <c>Main.StartInvasion</c>,
	/// <c>Main.UpdateInvasion_Inner</c>, <c>Main.InvasionWarning</c>, <c>NPC.SpawnNPC</c>, <c>NPC.NPCLoot</c>'s invasion
	/// count, <c>Main.DrawInvasionProgress</c>, tModLoader v2026.08.3.0). One subclass per invasion; the rules live here,
	/// the roster and the start condition in the subclass. <see cref="InvasionDirector"/> runs them.
	/// <list type="bullet">
	/// <item><b>Size</b> (<see cref="TryStart"/>): <see cref="BaseSize"/> + <see cref="SizePerPlayer"/> x the players with at
	/// least 5 Life Crystals (vanilla: 80 + 40n, <c>ConsumedLifeCrystals &gt;= 5</c>); no such player, no invasion.</item>
	/// <item><b>Approach</b> (<see cref="UpdateServer"/>): starts at a random world edge and moves
	/// <c>Main.desiredWorldEventsUpdateRate</c> tiles a tick towards the spawn point, warning "approaching from the
	/// west / east" at once and every 3600 ticks, then "has arrived".</item>
	/// <item><b>Spawns</b> (<see cref="InvasionRules"/>): players on the surface within 3000 px of it, or anywhere near a
	/// town NPC 2 times in 3 once it sits in the middle of the world, get only its roster, at vanilla's invasion rate
	/// (spawnRate 20, maxSpawns x(2 + 0.3 x players)).</item>
	/// <item><b>Progress</b>: each kill of a roster NPC takes <see cref="KillValue"/> off <see cref="Size"/> (vanilla's
	/// <c>NPCID.Sets.InvasionSlotCount</c>: 1, the Goblin Summoner 10); at 0 it is defeated: "has been defeated", the
	/// downed flag (<see cref="FlagName"/>, saved and synced by <see cref="WorldFlagSystem"/>), then it ends.</item>
	/// <item><b>One invasion at a time</b>, vanilla's or ours: it doesn't start while one runs, vanilla's invasion items are
	/// refused while it runs (<see cref="InvasionRules"/>), and a vanilla invasion that starts anyway (the dawn roll, a
	/// Martian Probe) is cancelled the same tick, before vanilla's first warning (<see cref="InvasionDirector"/>).</item>
	/// </list>
	/// <para>D2: the server owns the state (<see cref="Active"/>, <see cref="Size"/>, <see cref="X"/>) and saves it with
	/// the world, like vanilla's <c>invasionSize/X/Type</c>. Clients get <see cref="Active"/>, <see cref="Size"/> and
	/// <see cref="SizeStart"/> with the world data (joining players) and through <see cref="InvasionStatePacket"/> when they
	/// change (start, every kill, the end): the progress bar is all they need. D0: saved values are clamped on load.</para>
	/// </summary>
	public abstract class CogpunkInvasion : ModSystem
	{
		/// <summary>Vanilla's invasion size: 80 + 40 per player with at least 5 Life Crystals.</summary>
		public const int BaseSize = 80, SizePerPlayer = 40;
		public const int MinLifeCrystals = 5;
		/// <summary>Vanilla: the approach warning repeats every 3600 ticks.</summary>
		public const int WarnInterval = 3600;
		/// <summary>Vanilla: players within 3000 px of the invasion (horizontally) get its spawns.</summary>
		public const float ZoneRange = 3000f;
		public const int MaxSize = 10000;

		private static readonly List<CogpunkInvasion> all = new();

		/// <summary>Every loaded invasion, in load order (the index is the network id).</summary>
		public static IReadOnlyList<CogpunkInvasion> All => all;

		public int Index { get; private set; } = -1;

		/// <summary>Running (synced).</summary>
		public bool Active { get; private set; }

		/// <summary>Kills left (synced).</summary>
		public int Size { get; private set; }

		/// <summary>Size at the start (synced).</summary>
		public int SizeStart { get; private set; }

		/// <summary>Position in tiles, moving from the world edge to the spawn point (server only).</summary>
		public double X { get; private set; }

		private int warn;
		private int flagId = -1;
		private LocalizedText displayName, approachingWest, approachingEast, arrived, defeated;

		// Client display (vanilla's invasionProgressDisplayLeft / Alpha / NearInvasion), driven by InvasionProgressBar.
		internal int DisplayLeft;
		internal float Alpha;
		internal bool Near;

		/// <summary>Fraction of the invasion done, 0..1.</summary>
		public float Progress => SizeStart > 0 ? MathHelper.Clamp((SizeStart - Size) / (float)SizeStart, 0f, 1f) : 0f;

		public bool Downed => WorldFlagSystem.Get(flagId);

		public LocalizedText DisplayName => displayName;

		/// <summary>The <see cref="WorldFlagSystem"/> flag set the first time it is defeated.</summary>
		public abstract string FlagName { get; }

		/// <summary>Progression gate for the natural start (the goblin army's is a smashed Shadow Orb).</summary>
		public abstract bool CanHappen { get; }

		/// <summary>1 in N chance per dawn while <see cref="CanHappen"/> (the goblin army: 3 until its first defeat, then
		/// 30, 60 in Hardmode). 0 = never naturally.</summary>
		public abstract int NaturalChanceDenominator { get; }

		/// <summary>How many points killing <paramref name="type"/> takes off the size; 0 = not part of this invasion.</summary>
		public abstract int KillValue(int type);

		/// <summary>Fills the (already cleared) spawn pool for a player in the invasion's zone. Server only, per spawn attempt.</summary>
		public abstract void FillPool(IDictionary<int, float> pool, NPCSpawnInfo spawnInfo);

		/// <summary>Chat colour of the warnings (vanilla's invasion purple).</summary>
		public virtual Color MessageColor => new(175, 75, 255);

		/// <summary>The box behind the name on the progress bar (vanilla's are the invasion colour x 0.5).</summary>
		public virtual Color BarColor => new Color(94, 72, 131) * 0.5f;

		/// <summary>Texture path of the progress bar icon (vanilla's are about 30 px), without extension.</summary>
		public abstract string IconPath { get; }

		public Asset<Texture2D> Icon { get; private set; }

		public override void Load() {
			Index = all.Count;
			all.Add(this);
			flagId = WorldFlagSystem.Register(FlagName);
			string key = "Events." + Name + ".";
			displayName = Mod.GetLocalization(key + "DisplayName");
			approachingWest = Mod.GetLocalization(key + "ApproachingWest");
			approachingEast = Mod.GetLocalization(key + "ApproachingEast");
			arrived = Mod.GetLocalization(key + "Arrived");
			defeated = Mod.GetLocalization(key + "Defeated");
			if (!Main.dedServ && ModContent.HasAsset(IconPath)) {
				Icon = ModContent.Request<Texture2D>(IconPath);
			}
		}

		public override void Unload() {
			all.Clear();
			Index = -1;
			flagId = -1;
			Icon = null;
		}

		public override void ClearWorld() {
			Reset();
		}

		private void Reset() {
			Active = false;
			Size = SizeStart = 0;
			X = 0.0;
			warn = 0;
			DisplayLeft = 0;
			Alpha = 0f;
			Near = false;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Queries
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>Any Cogpunk invasion running.</summary>
		public static bool AnyActive {
			get {
				for (int i = 0; i < all.Count; i++) {
					if (all[i].Active) {
						return true;
					}
				}
				return false;
			}
		}

		/// <summary>The running invasion whose spawn zone <paramref name="player"/> is in (server: decided once per tick by
		/// <see cref="InvasionRules"/>), or null.</summary>
		public static CogpunkInvasion ZoneOf(Player player) => InvasionRules.ZoneOf(player);

		/// <summary>Vanilla's spawn zone test (decompiled <c>NPC.SpawnNPC</c>): on the surface, and within
		/// <see cref="ZoneRange"/> of the invasion, or, once it sits in the middle of the world, near a town NPC 2 times in 3
		/// (the roll happens here, so call it once per player per tick).</summary>
		internal bool RollZone(Player player) {
			if (!Active || Size <= 0 || !player.active || player.dead) {
				return false;
			}
			if (player.position.Y >= Main.worldSurface * 16.0 + NPC.sHeight && !Main.remixWorld) {
				return false;
			}
			double px = player.position.X;
			if (px > X * 16.0 - ZoneRange && px < X * 16.0 + ZoneRange) {
				return true;
			}
			int middle = Main.maxTilesX / 2;
			if (X >= middle - 5 && X <= middle + 5) {
				foreach (NPC npc in Main.ActiveNPCs) {
					if (npc.townNPC && Math.Abs(px - npc.Center.X) < ZoneRange) {
						return Main.rand.Next(3) != 0;
					}
				}
			}
			return false;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Server: start, update, kills, end
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>
		/// Server or singleplayer. Starts it (vanilla <c>StartInvasion</c>) unless an invasion of any kind is running or the
		/// Old One's Army is out; <paramref name="force"/> (the test command) also starts it with no player at 5 Life
		/// Crystals, sized for one.
		/// </summary>
		public bool TryStart(bool force = false) {
			if (Main.netMode == NetmodeID.MultiplayerClient || Active || AnyActive || Main.invasionType != 0 || Terraria.GameContent.Events.DD2Event.Ongoing) {
				return false;
			}
			int players = 0;
			foreach (Player p in Main.ActivePlayers) {
				if (p.ConsumedLifeCrystals >= MinLifeCrystals) {
					players++;
				}
			}
			if (players == 0) {
				if (!force) {
					return false;
				}
				players = 1;
			}
			Size = SizeStart = Math.Min(MaxSize, BaseSize + SizePerPlayer * players);
			X = Main.rand.NextBool(2) ? 0.0 : Main.maxTilesX;
			warn = 0;
			Active = true;
			Broadcast(report: false);
			return true;
		}

		/// <summary>Server or singleplayer: ends it; <paramref name="won"/> sets the downed flag and says "has been defeated".</summary>
		public void End(bool won) {
			if (Main.netMode == NetmodeID.MultiplayerClient || !Active) {
				return;
			}
			if (won) {
				Size = 0;
				Announce(defeated);
				NPC.SetEventFlagCleared(ref WorldFlagSystem.Flag(flagId), -1);
			}
			Active = false;
			Size = SizeStart = 0;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.WorldData);       // the downed flag (vanilla does the same for the goblins)
			}
			Broadcast(report: won);
		}

		/// <summary>Server, every tick (vanilla <c>UpdateInvasion_Inner</c>): the end, the approach and its warnings.</summary>
		internal void UpdateServer() {
			if (!Active) {
				return;
			}
			if (Size <= 0) {
				End(won: true);
				return;
			}
			double spawn = Main.spawnTileX;
			if (X == spawn) {
				return;
			}
			double rate = Math.Max(0.0, Main.desiredWorldEventsUpdateRate);
			if (X > spawn) {
				X -= rate;
				if (X <= spawn) {
					X = spawn;
					Announce(arrived);
					return;
				}
			}
			else {
				X += rate;
				if (X >= spawn) {
					X = spawn;
					Announce(arrived);
					return;
				}
			}
			if (rate > 0.0) {
				warn--;
			}
			if (warn <= 0) {
				warn = WarnInterval;
				Announce(X < spawn ? approachingWest : approachingEast);
			}
		}

		/// <summary>Server or singleplayer: takes <paramref name="value"/> off the size and shows everyone's progress bar
		/// (vanilla <c>ReportInvasionProgress</c> + message 78). The end is handled by the next update.</summary>
		public void Credit(int value) {
			if (Main.netMode == NetmodeID.MultiplayerClient || !Active || value <= 0) {
				return;
			}
			Size = Math.Max(0, Size - value);
			Broadcast(report: true);
		}

		private void Announce(LocalizedText text) {
			if (text == null) {
				return;
			}
			if (Main.netMode == NetmodeID.SinglePlayer) {
				Main.NewText(text.Value, MessageColor);
			}
			else if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey(text.Key), MessageColor);
			}
		}

		/// <summary>Singleplayer: applies the report locally. Server: sends the state to every client.</summary>
		private void Broadcast(bool report) {
			if (Main.netMode == NetmodeID.Server) {
				ModContent.GetInstance<InvasionStatePacket>().Send(this, report);
			}
			else if (report) {
				DisplayLeft = InvasionProgressBar.DisplayTicks;
			}
		}

		/// <summary>Client: a state packet from the server.</summary>
		internal void Receive(bool active, int size, int sizeStart, bool report) {
			Active = active;
			Size = Math.Clamp(size, 0, MaxSize);
			SizeStart = Math.Clamp(sizeStart, Size, MaxSize);
			if (report) {
				DisplayLeft = InvasionProgressBar.DisplayTicks;
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Save and sync (by name, D0: every key optional and clamped)
		// ------------------------------------------------------------------------------------------------------------

		public override void SaveWorldData(TagCompound tag) {
			if (!Active) {
				return;
			}
			tag["active"] = true;
			tag["size"] = Size;
			tag["sizeStart"] = SizeStart;
			tag["x"] = X;
		}

		public override void LoadWorldData(TagCompound tag) {
			Reset();
			try {
				if (!tag.GetBool("active")) {
					return;
				}
				int size = Math.Clamp(tag.GetInt("size"), 0, MaxSize);
				if (size <= 0) {
					return;
				}
				Active = true;
				Size = size;
				SizeStart = Math.Clamp(tag.GetInt("sizeStart"), size, MaxSize);
				double x = tag.GetDouble("x");
				X = double.IsFinite(x) ? Math.Clamp(x, 0.0, Main.maxTilesX) : Main.spawnTileX;
			}
			catch (Exception e) {
				SafeLog.Error("Invasion.Load." + Name, e);
				Reset();
			}
		}

		public override void NetSend(BinaryWriter writer) {
			writer.Write(Active);
			writer.Write((ushort)Size);
			writer.Write((ushort)SizeStart);
		}

		public override void NetReceive(BinaryReader reader) {
			bool active = reader.ReadBoolean();
			int size = reader.ReadUInt16();
			int start = reader.ReadUInt16();
			Receive(active, size, start, report: false);
		}
	}
}
