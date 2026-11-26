using System;
using System.IO;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Combat
{
	/// <summary>
	/// A crit kill slows time around it (user, 2026-11-25: "when a player kills an enemy with a critical hit it should do 0.33
	/// seconds of slow motion (our slow motion effect) for everything arround in a 1.5x screen size area (so it does not affect
	/// entities or players that are too far away). make sure that it does not cause desync errors or bugs and ensure
	/// multiplayer compatibility (it should be a global setting so the owner of the world should control if it enables or
	/// disables) and make it so it has a 12 seconds cooldown before being able to activate again").
	/// <list type="bullet">
	/// <item>What: <see cref="Ticks"/> real ticks (0.7 s since 2026-11-26) of <see cref="SlowMotion"/>'s zone (eased down to
	/// 80% slower, the Metal Wrench's speed, and smoothly back up) over a rectangle 1.5 times vanilla's largest view (<c>Main.maxScreenW</c> x <c>Main.maxScreenH</c>, 1920 x 1200:
	/// <see cref="ZoneHalf"/>), centred on the enemy; everything whose centre is outside runs on.</item>
	/// <item>Which kills: a hit flagged critical that takes an enemy's life to 0 (any weapon, projectile or minion), where the
	/// enemy is one vanilla counts as a kill (<c>NPC.ExcludedFromDeathTally</c> false: no projectile-like or temporary NPCs),
	/// not friendly, not a critter, not a dummy, not from a statue; a worm counts once, when its head's life is gone.</item>
	/// <item>Cooldown: <see cref="CooldownTicks"/> (12 s) for the whole world (user, 2026-11-25: "its supposed to be
	/// worldwide"): after any crit kill's slow motion, no other starts anywhere for 12 s.</item>
	/// <item>Setting: <see cref="CogpunkServerConfig.CritKillSlowMotion"/> (the world's host, default on).</item>
	/// </list>
	/// <para>D2, decided by the server alone: every client's strike reaches the server with its crit flag (decompiled
	/// <c>MessageBuffer</c> case 28 reads <c>HitInfo.Crit</c> and calls <c>StrikeNPC(hit, fromNet: true)</c>, which runs
	/// <c>HitEffect(hit)</c> and then <c>checkDead</c>), so the server marks the crit kill in <see cref="CritKillNPC.HitEffect"/>,
	/// confirms it in <c>OnKill</c> (the NPC really died: a boss that refuses its death never counts), checks the setting and
	/// the world's cooldown, starts its own zone and sends one <see cref="CritSlowMotionPacket"/> (the spot) to every client,
	/// which starts the same zone. The server and the clients hold back the same entities for the same number of ticks, a few
	/// ticks apart (the packet's trip), so positions converge as soon as it ends; nothing else is changed.
	/// D0: the packet's spot is checked (finite, inside the world); the zone array is fixed and capped (<see cref="SlowMotion"/>).
	/// D1: two flags per NPC; nothing per tick but a cooldown countdown on the server.</para>
	/// </summary>
	public sealed class CritKillSlowMotion : ModSystem
	{
		/// <summary>0.7 s (user-set 2026-11-26: "they should last 0.7 seconds now"; 0.33 s before), eased in and out by
		/// <see cref="SlowMotion.Speed"/>.</summary>
		public const int Ticks = 42;

		/// <summary>12 s (user-set).</summary>
		public const int CooldownTicks = 12 * 60;

		/// <summary>Half of 1.5 x (1920 x 1200), world px (user-set "1.5x screen size area").</summary>
		public static readonly Vector2 ZoneHalf = new(1920f * 1.5f / 2f, 1200f * 1.5f / 2f);

		private static int cooldown;                                    // the server's: ticks until the next may start

		/// <summary>An enemy whose crit kill counts (type-level tests; <c>SpawnedFromStatue</c> is checked at the kill).</summary>
		public static bool Counts(NPC npc) {
			return npc != null && !npc.friendly && !npc.townNPC && !npc.CountsAsACritter && !npc.immortal && npc.lifeMax > 5
				&& !npc.ExcludedFromDeathTally();
		}

		/// <summary>The server (or singleplayer): <paramref name="killer"/>'s crit just killed an enemy at <paramref name="at"/>.</summary>
		public static void OnCritKill(Vector2 at, int killer) {
			if (Main.netMode == NetmodeID.MultiplayerClient || !CogpunkServerConfig.CritSlowMotionOn) {
				return;
			}
			if (killer < 0 || killer >= Main.maxPlayers || !Main.player[killer].active || cooldown > 0) {
				return;
			}
			if (!float.IsFinite(at.X) || !float.IsFinite(at.Y)) {
				return;
			}
			cooldown = CooldownTicks;
			Begin(at);
			if (Main.netMode == NetmodeID.Server) {
				ModContent.GetInstance<CritSlowMotionPacket>().Send(at);
			}
		}

		/// <summary>Every side: the zone, and on clients a deep chime at the spot (a mana chime two octaves down: time
		/// stretching).</summary>
		internal static void Begin(Vector2 at) {
			if (!SlowMotion.StartZone(at, ZoneHalf, Ticks)) {
				return;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item29 with { Pitch = -1f, Volume = 0.45f, MaxInstances = 2 }, at);
			}
		}

		public override void PostUpdateWorld() {
			if (cooldown > 0) {
				cooldown--;
			}
		}

		public override void ClearWorld() {
			cooldown = 0;
		}
	}

	/// <summary>Marks a crit kill where the strike is applied for real (the server, or singleplayer) and starts the slow
	/// motion when the enemy dies (<see cref="CritKillSlowMotion"/>).</summary>
	public sealed class CritKillNPC : GlobalNPC
	{
		private bool critKilled;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => lateInstantiation && CritKillSlowMotion.Counts(entity);

		public override void HitEffect(NPC npc, NPC.HitInfo hit) {
			if (Main.netMode == NetmodeID.MultiplayerClient || !hit.Crit || hit.InstantKill) {
				return;
			}
			NPC root = npc.realLife >= 0 && npc.realLife < Main.maxNPCs && Main.npc[npc.realLife].active ? Main.npc[npc.realLife] : npc;
			if (root.life <= 0 && root.TryGetGlobalNPC(out CritKillNPC mark)) {
				mark.critKilled = true;
			}
		}

		public override void OnKill(NPC npc) {
			if (Main.netMode == NetmodeID.MultiplayerClient || !critKilled) {
				return;
			}
			critKilled = false;
			if (!npc.SpawnedFromStatue) {
				CritKillSlowMotion.OnCritKill(npc.Center, npc.lastInteraction);
			}
		}
	}

	/// <summary>A crit kill's slow motion (server -> every client): the spot, two floats. Checked: finite, inside the world
	/// (D0 rule 7); only the server sends it.</summary>
	public sealed class CritSlowMotionPacket : CogpunkPacket
	{
		public void Send(Vector2 at) {
			if (Main.netMode != NetmodeID.Server) {
				return;
			}
			ModPacket packet = Begin();
			packet.Write(at.X);
			packet.Write(at.Y);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			float x = reader.ReadSingle();
			float y = reader.ReadSingle();
			if (Main.netMode != NetmodeID.MultiplayerClient || !float.IsFinite(x) || !float.IsFinite(y)) {
				return;
			}
			if (x < 0f || y < 0f || x > Main.maxTilesX * 16f || y > Main.maxTilesY * 16f) {
				return;
			}
			CritKillSlowMotion.Begin(new Vector2(x, y));
		}
	}
}
