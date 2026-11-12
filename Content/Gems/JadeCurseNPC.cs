using System;
using System.IO;
using Cogpunk.Content.Gems.Buffs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems
{
	/// <summary>
	/// The jade curse (user-set 2026-11-09, the <see cref="Items.JadeStaff"/>'s: "jade curse decreases attack speed by 5% and
	/// stacks; on 3 stacks it should petrify the enemy in jade for 2.5 seconds (turning them jade green for the duration);
	/// while petrified they can still take damage and die, but the curse can't apply again on the same enemy for 10 seconds;
	/// it should apply to bosses and mini bosses but with double the stacks needed for petrification").
	/// <list type="bullet">
	/// <item>Every bolt that hits adds a stack (<see cref="JadeCurse"/>, refreshed for <see cref="CurseTicks"/> ticks a hit;
	/// the stacks go when it runs out). Each stack slows the enemy's attacks by <see cref="SlowPerStack"/>: enemies have no
	/// attack-speed stat, so its AI is skipped that share of its ticks (it keeps moving on its momentum; its timers, and so
	/// its attacks, run slower).</item>
	/// <item>At <see cref="Stacks"/> (<see cref="BossStacks"/> for bosses and mini-bosses,
	/// <see cref="CogpunkSets.IsBossOrMiniboss"/>) it turns to jade (<see cref="JadePetrified"/>, <see cref="PetrifyTicks"/>
	/// ticks): its AI stops (it falls if it walks, hangs if it flies), its animation stops, it can't touch anyone, it is drawn
	/// jade green, and it still takes damage and dies. From then on it can't be cursed for <see cref="WardTicks"/> ticks
	/// (<see cref="JadeWard"/>; my call: counted from the petrification).</item>
	/// <item>A boss or worm in parts (<c>realLife</c>) is cursed as one: the stacks are the root's, and the whole body turns
	/// to jade together (a frozen head would otherwise drag a moving tail).</item>
	/// <item>A boss or mini-boss can be turned to jade <see cref="BossPetrifyLimit"/> times (user, 2026-11-10: "the jade
	/// curse can only apply 3 times on bosses, then they become immune for the rest of the fight"); after the third it takes
	/// no more stacks, so no slow either, for as long as it lives (a fight is one NPC's life; a boss that despawns and is
	/// summoned again starts fresh). My call: mini-bosses count, as they did for the doubled stacks.</item>
	/// </list>
	/// <para>D2: the hit is the bolt's owner's; the server (or singleplayer) counts the stacks (<see cref="JadeCursePacket"/>
	/// from a client), adds the buffs (vanilla syncs NPC buffs from the server, decompiled <c>NPC.AddBuff</c>/<c>DelBuff</c>:
	/// message 54) and sends the stack count to the clients, so every side skips the same share of ticks and freezes the
	/// same NPCs. D0: every index checked; a client's request must name an active NPC near its own player; NPCs immune to the
	/// curse are left alone. D1: three fields per NPC, no allocation; the skip is one add a tick.</para>
	/// </summary>
	public sealed class JadeCurseNPC : GlobalNPC
	{
		public const int CurseTicks = 300;             // my call: a stack lasts 5 s unless another hit refreshes it
		public const int Stacks = 3, BossStacks = 6;   // user-set
		public const int PetrifyTicks = 150;           // user-set: 2.5 s
		public const int WardTicks = 600;              // user-set: no curse again for 10 s
		public const int BossPetrifyLimit = 3;         // user-set 2026-11-10: three times a fight, then immune
		public const float SlowPerStack = 0.05f;      // user-set: 5% slower attacks a stack
		public const float RequestRange = 3000f;      // a client may curse only NPCs this near its own player
		public static readonly Color Jade = new(96, 214, 150);

		/// <summary>The curse's stacks on this NPC (the root's count for a body in parts; synced from the server).</summary>
		public byte JadeStacks;

		/// <summary>Server: how many times this NPC (the root of a body in parts) has been turned to jade. A boss or mini-boss
		/// that reaches <see cref="BossPetrifyLimit"/> is immune to the curse for the rest of its life, which is the fight.</summary>
		public byte Petrifications;
		private float skip;
		private bool wasPetrified;
		private Rectangle petrifyFrame;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => lateInstantiation && !entity.townNPC;

		/// <summary>The NPC a part belongs to (itself unless it is a linked part of a living whole).</summary>
		public static NPC Root(NPC npc) {
			int root = npc.realLife;
			return root >= 0 && root < Main.maxNPCs && Main.npc[root].active ? Main.npc[root] : npc;
		}

		public static bool Petrified(NPC npc) => npc.HasBuff(ModContent.BuffType<JadePetrified>()) || Root(npc).HasBuff(ModContent.BuffType<JadePetrified>());

		/// <summary>The bolt's owner, as it hits: the server counts it (directly in singleplayer).</summary>
		public static void Hit(NPC npc) {
			if (npc == null || !npc.active) {
				return;
			}
			if (Main.netMode == NetmodeID.SinglePlayer) {
				Apply(npc);
			}
			else if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<JadeCursePacket>().SendHit(npc.whoAmI);
			}
		}

		/// <summary>Server or singleplayer: one stack on the root; at its count, the whole body turns to jade and is warded.</summary>
		public static void Apply(NPC npc) {
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}
			NPC root = Root(npc);
			int curse = ModContent.BuffType<JadeCurse>(), stone = ModContent.BuffType<JadePetrified>(), ward = ModContent.BuffType<JadeWard>();
			if (!root.active || root.buffImmune[curse] || root.HasBuff(ward) || root.HasBuff(stone)
				|| !root.TryGetGlobalNPC(out JadeCurseNPC jade)) {
				return;
			}
			bool boss = CogpunkSets.IsBossOrMiniboss(root);
			if (boss && jade.Petrifications >= BossPetrifyLimit) {
				return;                                          // spent: immune for the rest of the fight (user, 2026-11-10)
			}
			int need = boss ? BossStacks : Stacks;
			jade.JadeStacks = (byte)Math.Min(byte.MaxValue, jade.JadeStacks + 1);
			if (jade.JadeStacks >= need) {
				jade.JadeStacks = 0;
				jade.Petrifications = (byte)Math.Min(byte.MaxValue, jade.Petrifications + 1);
				int index = root.FindBuffIndex(curse);
				if (index >= 0) {
					root.DelBuff(index);                         // synced (message 54) on the server
				}
				Turn(root, stone, PetrifyTicks);
				Turn(root, ward, WardTicks);
			}
			else {
				root.AddBuff(curse, CurseTicks);
			}
			if (Main.netMode == NetmodeID.Server) {
				ModContent.GetInstance<JadeCursePacket>().SendStacks(root.whoAmI, jade.JadeStacks);
			}
		}

		/// <summary>A buff on the root and every living part linked to it (at most every NPC slot once).</summary>
		private static void Turn(NPC root, int buff, int ticks) {
			root.AddBuff(buff, ticks);
			foreach (NPC part in Main.ActiveNPCs) {
				if (part.whoAmI != root.whoAmI && part.realLife == root.whoAmI) {
					part.AddBuff(buff, ticks);
				}
			}
		}

		/// <summary>Every side: turned to jade it does nothing (it falls if it walks); cursed, its AI skips
		/// <see cref="SlowPerStack"/> of its ticks a stack.</summary>
		public override bool PreAI(NPC npc) {
			if (Petrified(npc)) {
				npc.velocity.X = 0f;
				if (npc.noGravity) {
					npc.velocity.Y = 0f;
				}
				return false;
			}
			NPC root = Root(npc);
			byte stacks = root.TryGetGlobalNPC(out JadeCurseNPC jade) ? jade.JadeStacks : (byte)0;
			if (stacks == 0) {
				skip = 0f;
				return true;
			}
			skip += SlowPerStack * stacks;
			if (skip >= 1f) {
				skip -= 1f;
				return false;
			}
			return true;
		}

		/// <summary>Every side: the stacks go when the curse runs out; clients mark the turn to jade and back.</summary>
		public override void PostAI(NPC npc) {
			if (JadeStacks > 0 && !npc.HasBuff(ModContent.BuffType<JadeCurse>())) {
				JadeStacks = 0;
			}
			bool stone = Petrified(npc);
			if (stone != wasPetrified) {
				wasPetrified = stone;
				if (stone) {
					petrifyFrame = npc.frame;
				}
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item27 with { Pitch = stone ? -0.5f : 0.1f, Volume = 0.8f }, npc.Center);
					Shards(npc, stone ? 10 : 18);
				}
			}
		}

		/// <summary>Frozen in place: the frame it was turned to jade in (vanilla's animation runs before this).</summary>
		public override void FindFrame(NPC npc, int frameHeight) {
			if (wasPetrified && petrifyFrame.Height > 0) {
				npc.frame = petrifyFrame;
			}
		}

		public override bool CanHitPlayer(NPC npc, Player target, ref int cooldownSlot) => !Petrified(npc);

		/// <summary>Clients: jade green while turned to stone; a jade mote now and then for each stack.</summary>
		public override void DrawEffects(NPC npc, ref Color drawColor) {
			if (Petrified(npc)) {
				float light = (drawColor.R + drawColor.G + drawColor.B) / (3f * 255f);
				drawColor = new Color((int)(Jade.R * (0.35f + 0.65f * light)), (int)(Jade.G * (0.35f + 0.65f * light)),
					(int)(Jade.B * (0.35f + 0.65f * light)), drawColor.A);
				return;
			}
			byte stacks = Root(npc).TryGetGlobalNPC(out JadeCurseNPC jade) ? jade.JadeStacks : (byte)0;
			if (stacks > 0 && Main.rand.NextBool(Math.Max(2, 14 - stacks * 3)) && CogpunkClientConfig.RollEffect()) {
				if (SafeSpawn.TryNewDust(npc.position, npc.width, npc.height, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity = new Vector2(0f, -0.6f);
					d.scale = 0.8f;
				}
			}
		}

		private static void Shards(NPC npc, int count) {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(npc.position, npc.width, npc.height, DustID.GemEmerald, out Dust d)) {
					d.velocity = Main.rand.NextVector2Circular(3f, 3f);
					d.noGravity = Main.rand.NextBool();
					d.scale = 1.2f;
				}
			}
		}
	}

	/// <summary>The jade curse's network messages: client -> server, "my bolt hit NPC n" (a short; the server checks it is
	/// an active NPC near the sender's player); server -> clients, "NPC n has s stacks" (a short and a byte).</summary>
	public sealed class JadeCursePacket : CogpunkPacket
	{
		private const byte Hit = 0, Stacks = 1;

		public void SendHit(int npc) {
			ModPacket packet = Begin();
			packet.Write(Hit);
			packet.Write((short)npc);
			packet.Send();
		}

		public void SendStacks(int npc, byte stacks) {
			ModPacket packet = Begin();
			packet.Write(Stacks);
			packet.Write((short)npc);
			packet.Write(stacks);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			byte kind = reader.ReadByte();
			int index = reader.ReadInt16();
			byte stacks = kind == Stacks ? reader.ReadByte() : (byte)0;
			if (index < 0 || index >= Main.maxNPCs || !Main.npc[index].active) {
				return;
			}
			NPC npc = Main.npc[index];
			if (kind == Hit && Main.netMode == NetmodeID.Server) {
				if (sender < 0 || sender >= Main.maxPlayers || !Main.player[sender].active
					|| Vector2.DistanceSquared(Main.player[sender].Center, npc.Center) > JadeCurseNPC.RequestRange * JadeCurseNPC.RequestRange) {
					return;
				}
				JadeCurseNPC.Apply(npc);
			}
			else if (kind == Stacks && Main.netMode == NetmodeID.MultiplayerClient && npc.TryGetGlobalNPC(out JadeCurseNPC jade)) {
				jade.JadeStacks = stacks;
			}
		}
	}
}
