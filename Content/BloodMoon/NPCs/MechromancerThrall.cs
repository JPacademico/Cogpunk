using System.IO;
using Cogpunk.Content.BloodMoon.Projectiles;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.BloodMoon.NPCs
{
	/// <summary>
	/// The Mechromancer's risen dead (user, 2026-11-16: "the mechromancer should summon regular zombies instead of
	/// cogskeletons"): vanilla's own Zombie (NPC 3, its fighter AI, stats and look untouched) that climbs out of one of the
	/// Mechromancer's graves (<see cref="MechromancerGrave"/>). Only zombies raised that way carry a master; every other
	/// zombie is left as vanilla made it.
	/// <list type="bullet">
	/// <item><b>The climb</b> (<see cref="RiseTicks"/>): it spawns with its head at the ground and is pushed up through it,
	/// drawn behind the tiles (vanilla's burrowing trick, <c>NPC.behindTiles</c>, decompiled <c>Main.DrawNPCs</c>), so the
	/// ground hides what is still under it; meanwhile its AI waits, it can't be hurt and it hurts nobody.</item>
	/// <item><b>Its master</b>: when the Mechromancer is gone (killed, or leaving at dawn) the zombie collapses back into the
	/// dirt (the server strikes it dead every <see cref="MasterCheckInterval"/> ticks it has no master; the strike is synced).</item>
	/// <item><b>No loot</b>: a summoned body drops nothing (no coins, items or banner kill: <see cref="PreKill"/>), like the
	/// Cogsqueletons it replaces.</item>
	/// </list>
	/// <para>D2: the master and the climb are set by the server as the zombie is made (<see cref="OnSpawn"/>, which runs inside
	/// <c>NPC.NewNPC</c>, before the spawn's sync) and ride every sync (<see cref="SendExtraAI"/>); every side counts the
	/// climb down. D0: the master index is range-checked before use; nothing spawned but client dust. D1: two ints per
	/// zombie (only zombies get this global), no allocation.</para>
	/// </summary>
	public sealed class MechromancerThrall : GlobalNPC
	{
		public const int RiseTicks = 40;
		public const int MasterCheckInterval = 30;

		/// <summary>The Mechromancer that raised it (-1: an ordinary zombie).</summary>
		public int Master = -1;

		/// <summary>Ticks of the climb left (0: out and walking).</summary>
		public int Rising;

		private float groundY;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => lateInstantiation && entity.type == NPCID.Zombie;

		public bool IsThrall => Master >= 0;

		/// <summary>Server (inside <c>NPC.NewNPC</c>): a zombie made by one of the Mechromancer's graves is its thrall and starts
		/// under the ground.</summary>
		public override void OnSpawn(NPC npc, IEntitySource source) {
			if (source is not EntitySource_Parent parent || parent.Entity is not Projectile grave       // (it is mid-Kill: no active test)
				|| grave.type != ModContent.ProjectileType<MechromancerGrave>()) {
				return;
			}
			int m = (int)grave.ai[0];
			if (m < 0 || m >= Main.maxNPCs) {
				return;
			}
			Master = m;
			Rising = RiseTicks;
			groundY = npc.Bottom.Y;
			npc.position.Y += npc.height;                       // its head at the ground line
			npc.velocity = Vector2.Zero;
			Climbing(npc);
		}

		public override void SendExtraAI(NPC npc, BitWriter bitWriter, BinaryWriter binaryWriter) {
			binaryWriter.Write((short)Master);
			binaryWriter.Write((byte)Rising);
			binaryWriter.Write(groundY);
		}

		public override void ReceiveExtraAI(NPC npc, BitReader bitReader, BinaryReader binaryReader) {
			int m = binaryReader.ReadInt16();
			int rising = binaryReader.ReadByte();
			float ground = binaryReader.ReadSingle();
			Master = m >= 0 && m < Main.maxNPCs ? m : -1;
			Rising = Master >= 0 ? System.Math.Min(rising, RiseTicks) : 0;
			groundY = float.IsFinite(ground) ? ground : npc.Bottom.Y;
		}

		private static void Climbing(NPC npc) {
			npc.behindTiles = true;
			npc.noTileCollide = true;
			npc.noGravity = true;
			npc.dontTakeDamage = true;
		}

		/// <summary>Every side, while climbing: it rises a fixed step a tick (its height over the climb) and its AI waits.</summary>
		public override bool PreAI(NPC npc) {
			if (Rising <= 0) {
				return true;
			}
			Climbing(npc);
			Rising--;
			if (Rising == 0) {
				npc.position.Y = groundY - npc.height;           // stood on the ground, exactly
				npc.velocity = Vector2.Zero;
				npc.behindTiles = false;
				npc.noTileCollide = false;
				npc.noGravity = false;
				npc.dontTakeDamage = false;
				return false;
			}
			npc.velocity = new Vector2(0f, -npc.height / (float)RiseTicks);
			if (!Main.dedServ && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(new Vector2(npc.position.X, groundY - 6f), npc.width, 6, Main.rand.NextBool(3) ? DustID.CursedTorch : DustID.Dirt,
				out Dust d)) {
				d.velocity = new Vector2(Main.rand.NextFloat(-1.2f, 1.2f), Main.rand.NextFloat(-2.4f, -0.8f));
				d.noGravity = d.type == DustID.CursedTorch;
			}
			return false;
		}

		/// <summary>Server: no master left, it falls back into the dirt (a synced instant kill: every client plays its death).</summary>
		public override void PostAI(NPC npc) {
			if (!IsThrall || Main.netMode == NetmodeID.MultiplayerClient || Rising > 0 || (Main.GameUpdateCount + (uint)npc.whoAmI) % MasterCheckInterval != 0) {
				return;
			}
			NPC m = Main.npc[Master];
			if (m.active && m.type == ModContent.NPCType<Mechromancer>() && m.life > 0) {
				return;
			}
			npc.StrikeInstantKill();
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: npc.whoAmI);
			}
		}

		/// <summary>While it climbs it touches nobody.</summary>
		public override bool CanHitPlayer(NPC npc, Player target, ref int cooldownSlot) => Rising <= 0;

		/// <summary>The climb shows the zombie standing (vanilla's first frame), not its jump.</summary>
		public override void FindFrame(NPC npc, int frameHeight) {
			if (Rising > 0) {
				npc.frame.Y = 0;
			}
		}

		/// <summary>A raised body leaves nothing: no coins, no items, no banner kill.</summary>
		public override bool PreKill(NPC npc) => !IsThrall;
	}
}
