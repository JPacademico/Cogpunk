using System.IO;
using Cogpunk.Content.Bosses.Jadey.NPCs;
using Cogpunk.Content.Bosses.Jadey.Projectiles;
using Cogpunk.Content.Coghaven.NPCs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Bosses.Jadey
{
	/// <summary>
	/// Jadey's jade minions (user, 2026-11-16: "this jade coin should spawn at random a jade golem, or 2 jade bats or jade beetle
	/// ... where it lands"): the island's own <see cref="JadeGolem"/>, the <see cref="JadeBat"/> and the <see cref="JadeBeetle"/>,
	/// made hers when one of her coins (<see cref="JadeCoin"/>) turns into them.
	/// <list type="bullet">
	/// <item>Her minions are lesser copies: <see cref="LifeScale"/> of their life (my call: a coin every 4 s would otherwise pile
	/// up a Golem's 720 life every 12 s on average).</item>
	/// <item>They drop nothing (no coins, items or banner kill, <see cref="PreKill"/>): they are summoned.</item>
	/// <item>When Jadey is gone (killed, or leaving) they crumble back into jade (a synced instant kill on the server, every
	/// <see cref="MasterCheckInterval"/> ticks).</item>
	/// <item>Her channel consumes them (<see cref="Jadey"/>); <see cref="Count"/> is how many she has.</item>
	/// </list>
	/// <para>D2: the server sets the master as the minion is made (<see cref="OnSpawn"/>, inside <c>NPC.NewNPC</c>, before the
	/// spawn's sync) and it rides every sync (<see cref="SendExtraAI"/>), so clients can draw her channel's streams from them.
	/// D0: indices range-checked. D1: one int per NPC of the three types.</para>
	/// </summary>
	public sealed class JadeyMinion : GlobalNPC
	{
		public const float LifeScale = 0.5f;
		public const int MasterCheckInterval = 30;

		public int Master = -1;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			return lateInstantiation && IsMinionType(entity.type);
		}

		public static bool IsMinionType(int type) {
			return type == ModContent.NPCType<JadeGolem>() || type == ModContent.NPCType<JadeBat>() || type == ModContent.NPCType<JadeBeetle>();
		}

		public bool IsMinion => Master >= 0;

		/// <summary>Is <paramref name="npc"/> one of <paramref name="master"/>'s minions (every side: the master is synced)?</summary>
		public static bool Of(NPC npc, int master) {
			return npc.active && npc.life > 0 && IsMinionType(npc.type) && npc.TryGetGlobalNPC(out JadeyMinion m) && m.Master == master;
		}

		/// <summary>How many minions <paramref name="master"/> has (one pass over the NPCs).</summary>
		public static int Count(int master) {
			int count = 0;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (Of(npc, master)) {
					count++;
				}
			}
			return count;
		}

		/// <summary>Server (inside <c>NPC.NewNPC</c>): a minion made by one of Jadey's coins is hers, and a lesser copy.</summary>
		public override void OnSpawn(NPC npc, IEntitySource source) {
			if (source is not EntitySource_Parent parent || parent.Entity is not Projectile coin || coin.type != ModContent.ProjectileType<JadeCoin>()) {
				return;
			}
			int m = (int)coin.ai[1];
			if (m < 0 || m >= Main.maxNPCs) {
				return;
			}
			Master = m;
			npc.lifeMax = System.Math.Max(1, (int)(npc.lifeMax * LifeScale));
			npc.life = npc.lifeMax;
		}

		public override void SendExtraAI(NPC npc, BitWriter bitWriter, BinaryWriter binaryWriter) {
			binaryWriter.Write((short)Master);
		}

		public override void ReceiveExtraAI(NPC npc, BitReader bitReader, BinaryReader binaryReader) {
			int m = binaryReader.ReadInt16();
			Master = m >= 0 && m < Main.maxNPCs ? m : -1;
		}

		/// <summary>Server: no Jadey left, it crumbles (a synced instant kill: every client plays its death).</summary>
		public override void PostAI(NPC npc) {
			if (!IsMinion || Main.netMode == NetmodeID.MultiplayerClient || (Main.GameUpdateCount + (uint)npc.whoAmI) % MasterCheckInterval != 0) {
				return;
			}
			NPC m = Main.npc[Master];
			if (m.active && m.type == ModContent.NPCType<Jadey>() && m.life > 0 && m.ModNPC is Jadey j && !j.IsDying) {
				return;
			}
			Consume(npc);
		}

		/// <summary>Server: the minion dies at once (synced), leaving nothing.</summary>
		public static void Consume(NPC npc) {
			if (Main.netMode == NetmodeID.MultiplayerClient || !npc.active) {
				return;
			}
			npc.StrikeInstantKill();
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: npc.whoAmI);
			}
		}

		/// <summary>A summoned minion leaves nothing: no coins, no items, no banner kill.</summary>
		public override bool PreKill(NPC npc) => !IsMinion;

		/// <summary>Clients: her minions shed a jade mote now and then, so they read as hers.</summary>
		public override void DrawEffects(NPC npc, ref Color drawColor) {
			if (IsMinion && Main.rand.NextBool(20) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(npc.position, npc.width, npc.height, DustID.GemEmerald, out Dust d)) {
				d.noGravity = true;
				d.velocity = new Vector2(0f, -0.6f);
				d.scale = 0.7f;
			}
		}
	}
}
