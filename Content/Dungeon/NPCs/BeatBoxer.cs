using System;
using Cogpunk.Content.Dungeon.Items;
using Cogpunk.Content.Dungeon.Projectiles;
using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Dungeon.NPCs.BeatBoxerRigData;

namespace Cogpunk.Content.Dungeon.NPCs
{
	/// <summary>
	/// Beat-Boxer (user-set 2026-11-03, designed from the user's reference image: a boxing robot with red gloves marked with
	/// a white cross, a golden face plate and a golden microphone for a second fist): a heavy Dungeon robot that walks at
	/// the Angry Bones' pace (<see cref="WalkSpeed"/>, decompiled <c>NPC.AI_003_Fighters</c>: 1.5 px/tick) and fights with
	/// spring punches: with its target in line within <see cref="PunchReach"/> (7 tiles) it plants its feet and cocks both
	/// fists (the telegraph, <see cref="WindupTicks"/> ticks, a ratchet), then fires them one after the other on their
	/// springs (<see cref="SpringPunch"/>: the red glove, then <see cref="SecondPunchDelay"/> ticks later the golden one;
	/// always two), each reaching for where the target stood, with a strong push. Then it recovers and walks again. While it
	/// walks it jumps when its target jumps (user, 2026-11-10: <see cref="GridWalkerNPC.MirrorJump"/>).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Angry Bones, decompiled 1.4.4 NPC 31: 80 life, 8
	/// defense, 26 contact in Classic = 160 / 8 / 52 in Expert): <see cref="Life"/> life (the user's "high health"),
	/// <see cref="Defense"/> defense, <see cref="ContactDamage"/> contact, punches <see cref="PunchDamage"/>. Spawns in the
	/// Dungeon after Skeletron (<see cref="SpawnWeight"/>). Drops 2-4 <see cref="PolishedMetal"/> and, 1 in
	/// <see cref="GlovesOdds"/> (20%, user-set), the <see cref="SpringGloves"/>.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the punch cooldown, <c>ai[3]</c> the reach locked
	/// for the volley (every side reads it); the server targets, decides and fires (the punches are server projectiles
	/// that follow the boxer on every side). D1: no allocation; sounds and dust on clients.</para>
	/// </summary>
	public class BeatBoxer : GridWalkerNPC
	{
		private enum Phase { Walk, Windup, Punch, Recover }

		public const int Life = 440, ContactDamage = 40, Defense = 16;    // Expert
		public const int PunchDamage = 50;                                // Expert, each
		public const int Width = 34, Height = 48;
		public const float KnockbackResist = 0.3f;
		public const float WalkSpeed = 1.5f, WalkAccel = 0.07f, JumpSpeed = 7f;
		public const float PunchReach = 7f * 16f;                         // user-set: up to 7 tiles
		public const float PunchMinReach = 3f * 16f;
		public const float PunchHeight = 3f * 16f;                        // the target within this many px up or down
		public const int WindupTicks = 24;
		public const int SecondPunchDelay = 12;
		public const int PunchTicks = SecondPunchDelay + SpringPunch.Lifetime;
		public const int RecoverTicks = 20;
		public const int PunchCooldown = 90;
		public const float WalkAnimDistance = 4f;                         // px of travel per walk frame
		public const float SpawnWeight = 0.08f;
		public const int GlovesOdds = 5;                                  // 20% (user-set)

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "BeatBoxer_GoreHead", "BeatBoxer_GoreGlove", "BeatBoxer_GoreMic" };

		private Phase CurrentPhase => (Phase)State;
		private ref float Cooldown => ref NPC.ai[2];
		private ref float Reach => ref NPC.ai[3];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.TheDungeon;

		/// <summary>The fist's shoulder in world space (rig data, mirrored when it faces right): where a spring is fixed.</summary>
		public Vector2 Shoulder(int arm) {
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			float x = arm == SpringPunch.NearArm ? R.NearShoulderX : R.FarShoulderX;
			float y = arm == SpringPunch.NearArm ? R.NearShoulderY : R.FarShoulderY;
			return NPC.Bottom + new Vector2(x * -dir, y);
		}

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
			CogpunkSets.Mechanical[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		public override void SetDefaults() {
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Item.buyPrice(silver: 3);
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			if (!spawnInfo.Player.ZoneDungeon || !NPC.downedBoss3 || spawnInfo.Water
				|| !TileSafety.TryGetTile(spawnInfo.SpawnTileX, spawnInfo.SpawnTileY - 1, out Tile tile) || !Main.wallDungeon[tile.WallType]) {
				return 0f;
			}
			return SpawnWeight;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<PolishedMetal>(), 1, 2, 4));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<SpringGloves>(), GlovesOdds));
		}

		protected override void UpdateState() {
			if (Cooldown > 0f) {
				Cooldown--;
			}
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.Windup:
					Run(0, 0f, WalkAccel * 3f, JumpSpeed);
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(SoundID.Item37 with { Pitch = -0.5f, Volume = 0.7f, MaxInstances = 3 }, NPC.Center);   // the springs cocked: a clank
					}
					if (IsAuthority && Timer >= WindupTicks) {
						ChangeState((int)Phase.Punch);
						Fire(SpringPunch.NearArm);
					}
					break;
				case Phase.Punch:
					Run(0, 0f, WalkAccel * 3f, JumpSpeed);
					if (IsAuthority && Timer == SecondPunchDelay) {
						Fire(SpringPunch.FarArm);
					}
					if (IsAuthority && Timer >= PunchTicks) {
						Cooldown = PunchCooldown;
						ChangeState((int)Phase.Recover);
					}
					break;
				case Phase.Recover:
					Run(0, 0f, WalkAccel * 3f, JumpSpeed);
					if (IsAuthority && Timer >= RecoverTicks) {
						ChangeState((int)Phase.Walk);
					}
					break;
				default:
					Run(target != null ? dir : 0, WalkSpeed, WalkAccel, JumpSpeed);
					MirrorJump(target);                             // it jumps when its target jumps (user, 2026-11-10)
					FaceMotion(dir);
					float adx = Math.Abs(dx);
					if (IsAuthority && target != null && Grounded && Cooldown <= 0f && adx <= PunchReach + Width * 0.5f
						&& Math.Abs(target.Center.Y - Shoulder(SpringPunch.NearArm).Y) < PunchHeight
						&& Collision.CanHitLine(NPC.Top, 1, 1, target.position, target.width, target.height)) {
						NPC.direction = NPC.spriteDirection = dir;
						Reach = MathHelper.Clamp(adx - Width * 0.25f, PunchMinReach, PunchReach);
						ChangeState((int)Phase.Windup);
					}
					break;
			}
		}

		/// <summary>Server: one spring punch along the facing, as far as the locked <see cref="Reach"/>.</summary>
		private void Fire(int arm) {
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			int damage = ExpertStats.HostileProjectile(NPC, PunchDamage);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), Shoulder(arm), new Vector2(dir, 0f), ModContent.ProjectileType<SpringPunch>(),
				damage, 0f, out _, Main.myPlayer, NPC.whoAmI, arm, Math.Max(PunchMinReach, Reach));
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Windup:
					return R.Windup + (Timer < WindupTicks / 2 ? 0 : 1);
				case Phase.Punch:
					return Timer < SecondPunchDelay ? R.PunchNear : R.PunchFar;
				case Phase.Recover:
					return R.Idle;
			}
			if (!Grounded) {
				return R.Walk + 2;
			}
			if (Math.Abs(NPC.velocity.X) > 0.15f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= WalkAnimDistance * R.WalkFrames) {
					NPC.frameCounter -= WalkAnimDistance * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / WalkAnimDistance) % R.WalkFrames;
			}
			return R.Idle + (int)(Timer / 16f) % 2;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 14;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.GoldCoin : DustID.Iron, out _);
			}
			if (NPC.life <= 0) {
				foreach (string name in GoreNames) {
					if (Mod.TryFind(name, out ModGore gore)) {
						SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.position + new Vector2(Main.rand.Next(NPC.width), Main.rand.Next(NPC.height)),
							NPC.velocity * 0.5f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
					}
				}
			}
		}
	}
}
