using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.Bestiary;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.BloodMoon.NPCs.CogsqueletonRigData;

namespace Cogpunk.Content.BloodMoon.NPCs
{
	/// <summary>
	/// Cogsqueleton (Engrenoesqueleto), the skeleton the <see cref="Mechromancer"/> raises (user-set 2026-11-12: "summon
	/// cogsqueletons"; the rest my calls): old bone held together with brass, a cog for a heart (art/bloodmoon/
	/// make_cogsqueleton_art.py). It <b>climbs out</b> of its grave for <see cref="RiseTicks"/> ticks (harmless and
	/// untouchable: D3, no contact damage while it spawns), then <b>walks</b> at the closest player like vanilla's
	/// skeletons, jumping walls. It is its master's: when the Mechromancer is gone (dead, or left at dawn) it
	/// <b>crumbles</b> (<see cref="CrumbleTicks"/>).
	/// <para>Stats (Expert; docs/balance/npcs.csv): vanilla's Skeleton (terraria.wiki.gg: 60 life, 8 defense, 20 contact in
	/// Classic = 120 / 8 / 40 in Expert): <see cref="Life"/> / <see cref="Defense"/> / <see cref="ContactDamage"/>, knockback
	/// taken x0.5 (the Skeleton's). No loot, no coins (a summoned minion, like the Goblin Summoner's apparitions); never
	/// spawns on its own.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> its master's index (set at the spawn, synced); the
	/// server targets, decides and removes it; the walk runs on every side. D0: removed through a synced deactivation, never a
	/// kill (no loot, no banner count); every phase finite.</para>
	/// </summary>
	public class Cogsqueleton : GridWalkerNPC
	{
		private enum Phase { Rise, Walk, Crumble }

		public const int Life = 110, ContactDamage = 40, Defense = 10;     // Expert
		public const int RiseTicks = 40;                                   // 4 frames x 10
		public const int CrumbleTicks = 20;
		public const float WalkSpeed = 1.5f, WalkAccel = 0.08f, JumpSpeed = 7f;
		public const int MasterCheckInterval = 30;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "Cogsqueleton_GoreSkull", "Cogsqueleton_GoreCog", "Cogsqueleton_GoreBone" };

		private Phase CurrentPhase => (Phase)State;
		private int Master => (int)NPC.ai[2];
		private float walked;

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Events.BloodMoon;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			far = near = glow = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // bone and brass
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Bleeding] = true;
		}

		public override void SetDefaults() {
			NPC.width = 18;                                  // vanilla's Skeleton
			NPC.height = 40;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0.5f;
			NPC.HitSound = SoundID.NPCHit2;
			NPC.DeathSound = SoundID.NPCDeath2;
			NPC.value = 0f;
			NPC.npcSlots = 0f;                               // a summon: it never blocks natural spawns
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) => 0f;

		/// <summary>Is its master still about? (every side: the master's index rides the spawn's sync)</summary>
		private bool MasterAlive() {
			int m = Master;
			return m >= 0 && m < Main.maxNPCs && Main.npc[m].active && Main.npc[m].type == ModContent.NPCType<Mechromancer>() && Main.npc[m].alpha < 200;
		}

		protected override void UpdateState() {
			if (IsAuthority && CurrentPhase != Phase.Crumble && Timer % MasterCheckInterval == 0f && !MasterAlive()) {
				ChangeState((int)Phase.Crumble);
			}
			switch (CurrentPhase) {
				case Phase.Rise:
					NPC.dontTakeDamage = true;
					NPC.damage = 0;
					NPC.velocity.X = 0f;
					if (!Main.dedServ && Timer % 4f == 1f) {
						SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(4f, 6f), NPC.width + 8, 6, Timer % 8f == 1f ? DustID.Dirt : DustID.CursedTorch,
							out _);
					}
					if (IsAuthority && Timer >= RiseTicks) {
						ChangeState((int)Phase.Walk);
					}
					break;
				case Phase.Crumble:
					NPC.dontTakeDamage = true;
					NPC.damage = 0;
					NPC.velocity.X *= 0.8f;
					if (!Main.dedServ && Timer == 1f) {
						Crumble();
					}
					if (IsAuthority && Timer >= CrumbleTicks) {
						NPC.active = false;
						if (Main.netMode == NetmodeID.Server) {
							NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
						}
					}
					break;
				default:
					NPC.dontTakeDamage = false;
					NPC.damage = NPC.defDamage;
					Retarget();
					Player target = Target;
					int dir = target != null ? (target.Center.X >= NPC.Center.X ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
					Run(target != null ? dir : 0, WalkSpeed, WalkAccel, JumpSpeed);
					FaceMotion(dir);
					walked += Math.Abs(NPC.velocity.X);
					break;
			}
		}

		/// <summary>Clients: it falls apart where it stands, bones and a cog clattering down, its soul fire going out.</summary>
		private void Crumble() {
			SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = 0.2f, Volume = 0.7f, MaxInstances = 4 }, NPC.Center);
			for (int i = 0; i < 12; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.CursedTorch : DustID.Bone, out _);
			}
			SpawnGores();
		}

		private void SpawnGores() {
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center + new Vector2(0f, -10f + i * 8f), Main.rand.NextVector2Circular(2f, 2f),
						gore.Type, out _);
				}
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Rise:
					return R.Rise + Math.Min(R.RiseFrames - 1, (int)(Timer / (RiseTicks / R.RiseFrames)));
				default:
					return Math.Abs(NPC.velocity.X) < 0.1f ? R.Walk : R.Walk + (int)(walked / R.WalkStep) % R.WalkFrames;
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < (NPC.life > 0 ? 3 : 14); i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.Bone, out _);
			}
			if (NPC.life <= 0) {
				SpawnGores();
			}
		}
	}
}
