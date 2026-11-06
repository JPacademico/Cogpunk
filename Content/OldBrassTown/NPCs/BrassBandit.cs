using System;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Content.OldBrassTown.Projectiles;
using Cogpunk.Content.Scrap.Items;
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
using R = Cogpunk.Content.OldBrassTown.NPCs.BrassBanditRigData;

namespace Cogpunk.Content.OldBrassTown.NPCs
{
	/// <summary>
	/// Brass Bandit (user-set 2026-11-04: "a bandit robot that shoots the player on sight with a rusty revolver: six bullets,
	/// then it runs from the player to reload"), an outlaw of Old Brass Town. It ambles towards its target; the moment the
	/// target is in sight within <see cref="SightRange"/> it draws and aims (the telegraph, <see cref="AimTicks"/> ticks: the
	/// gun held on the target, the hammer clicking back), then fans all <see cref="Shots"/> chambers, one every
	/// <see cref="ShotInterval"/> ticks, each aimed at the target as it is then (within <see cref="MaxAimAngle"/> of level:
	/// straight above or below it, a player can't be hit), and turns tail to reload, running away from the target for
	/// <see cref="ReloadTicks"/> ticks with the cylinder swung out, before it comes back for more.
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Antlion Charger, the underground desert's T2 fighter,
	/// decompiled 1.4.4 NPC 508: 110 life, 16 defense, 38 contact in Classic = 220 / 16 / 76 in Expert, value 175):
	/// <see cref="Life"/> life, <see cref="Defense"/> defense, <see cref="ContactDamage"/> contact (it fights at range),
	/// bullets <see cref="BulletDamage"/>. Spawns only in Old Brass Town (<see cref="SpawnWeight"/>, the town's commonest).
	/// Drops the anchor's coins, 1-2 Tarnished Brass Bars and 1-3 Rusted Cogs.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the shot count, <c>ai[3]</c> the direction it flees
	/// (synced with the state change); the server targets, decides and fires (bullets through <see cref="SafeSpawn"/>, damage
	/// through <see cref="ExpertStats.HostileProjectile"/>); every side runs the movement from the synced state. D1: no
	/// allocation; sounds and dust on clients.</para>
	/// </summary>
	public class BrassBandit : GridWalkerNPC
	{
		private enum Phase { Walk, Aim, Shoot, Flee }

		public const int Life = 180, ContactDamage = 30, Defense = 12;     // Expert
		public const int BulletDamage = 26;                                // Expert, per bullet
		public const int Width = 20, Height = 42;
		public const float KnockbackResist = 0.5f;
		public const float WalkSpeed = 1.4f, WalkAccel = 0.08f, JumpSpeed = 7f;
		public const float RunSpeed = 3.4f, RunAccel = 0.25f;
		public const float SightRange = 30f * 16f;                         // "shoots on sight"
		public const float KeepRange = 7f * 16f;                           // it stops closing in here
		public const int AimTicks = 30;                                     // the telegraph (D3: >= 30 at T0-T4)
		public const int Shots = 6;                                         // a six-shooter (user-set)
		public const int ShotInterval = 14;
		public const int ShootTicks = Shots * ShotInterval;
		public const int ReloadTicks = 150;                                 // running away while it reloads (user-set)
		public const float BulletSpeed = 7f;                                // px per update: 14 px/tick (RustyBullet updates twice a tick)
		public const float ShotSpread = 0.04f;                              // radians each way
		public const float MaxAimAngle = 0.7f;                              // radians from level (40 degrees)
		public const float LevelBand = 0.22f;                               // radians: the level aim frame within this
		public const int MuzzleFlashTicks = 5;
		public const float WalkAnimDistance = R.WalkStep;
		public const float SpawnWeight = 1f;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "BrassBandit_GoreHat", "BrassBandit_GoreHead", "BrassBandit_GoreGun" };

		private Phase CurrentPhase => (Phase)State;
		private ref float ShotsFired => ref NPC.ai[2];
		private ref float FleeDir => ref NPC.ai[3];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<OldBrassTownBiome>().ModBiomeBestiaryInfoElement;

		/// <summary>The muzzle flash in the glow sheet only shows for a few ticks after a shot; the eyes always.</summary>
		protected override float GlowStrength => 1f;

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
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 175f;                               // the Antlion Charger's (decompiled NPC.SetDefaults, type 508)
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) => OldBrassTownSpawnRules.TownSpawnWeight(spawnInfo, SpawnWeight);

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<TarnishedBrassBar>(), 1, 1, 2));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedCog>(), 1, 1, 3));
		}

		protected override void UpdateState() {
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.Aim:
					Run(0, 0f, WalkAccel * 3f, JumpSpeed);
					NPC.direction = NPC.spriteDirection = dir;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(SoundID.Unlock with { Pitch = 0.4f, Volume = 0.7f, MaxInstances = 3 }, NPC.Center);   // the hammer cocked
					}
					if (IsAuthority && Timer >= AimTicks) {
						ShotsFired = 0f;
						ChangeState((int)Phase.Shoot);
					}
					break;
				case Phase.Shoot:
					Run(0, 0f, WalkAccel * 3f, JumpSpeed);
					NPC.direction = NPC.spriteDirection = dir;
					if ((Timer - 1f) % ShotInterval == 0f && Timer <= ShootTicks) {
						Fire(target);
					}
					if (IsAuthority && Timer >= ShootTicks + 6) {
						FleeDir = -dir;                             // away from the target, synced with the change
						ChangeState((int)Phase.Flee);
					}
					break;
				case Phase.Flee:
					int away = FleeDir >= 0f ? 1 : -1;
					Run(away, RunSpeed, RunAccel, JumpSpeed);
					NPC.direction = NPC.spriteDirection = away;
					if (!Main.dedServ && Timer % 25f == 12f) {
						SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = -0.2f, Volume = 0.6f, MaxInstances = 3 }, NPC.Center);   // a cartridge in
					}
					if (IsAuthority && Timer >= ReloadTicks) {
						ChangeState((int)Phase.Walk);
					}
					break;
				default:
					float adx = Math.Abs(dx);
					Run(target != null && adx > KeepRange ? dir : 0, WalkSpeed, WalkAccel, JumpSpeed);
					FaceMotion(dir);
					if (IsAuthority && target != null && Grounded && Vector2.DistanceSquared(target.Center, NPC.Center) < SightRange * SightRange
						&& Collision.CanHitLine(Muzzle(dir, 0), 1, 1, target.position, target.width, target.height)) {
						NPC.direction = NPC.spriteDirection = dir;
						ChangeState((int)Phase.Aim);
					}
					break;
			}
		}

		/// <summary>Which aim frame points at the target: 0 level, 1 up, 2 down.</summary>
		private int AimIndex() {
			Player target = Target;
			if (target == null) {
				return 0;
			}
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			Vector2 to = target.Center - Muzzle(dir, 0);
			float angle = (float)Math.Atan2(to.Y, Math.Abs(to.X) + 0.01f);   // + below, - above, from the facing
			return angle < -LevelBand ? 1 : (angle > LevelBand ? 2 : 0);
		}

		/// <summary>The muzzle of an aim frame in world space (rig data, mirrored when it faces right).</summary>
		private Vector2 Muzzle(int dir, int aim) {
			int x = aim == 1 ? R.MuzzleUpX : aim == 2 ? R.MuzzleDownX : R.MuzzleLevelX;
			int y = aim == 1 ? R.MuzzleUpY : aim == 2 ? R.MuzzleDownY : R.MuzzleLevelY;
			return NPC.Bottom + new Vector2(x * -dir, y);
		}

		/// <summary>One shot: the bang and smoke on every side, the bullet from the server, aimed at the target as it is now
		/// within <see cref="MaxAimAngle"/> of level, with a little spread.</summary>
		private void Fire(Player target) {
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			Vector2 from = Muzzle(dir, AimIndex());
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item41 with { Pitch = -0.3f, Volume = 0.7f, MaxInstances = 4 }, from);
				for (int i = 0; i < 3; i++) {
					SafeSpawn.TryNewDust(from - new Vector2(3f), 6, 6, DustID.Smoke, out _, dir * 1.5f, -0.4f);
				}
			}
			if (!IsAuthority || target == null) {
				return;
			}
			ShotsFired++;
			Vector2 to = target.Center - from;
			float angle = (float)Math.Atan2(to.Y, Math.Abs(to.X) + 0.01f);
			angle = MathHelper.Clamp(angle, -MaxAimAngle, MaxAimAngle) + Main.rand.NextFloat(-ShotSpread, ShotSpread);
			Vector2 velocity = new Vector2(dir * (float)Math.Cos(angle), (float)Math.Sin(angle)) * BulletSpeed;
			int damage = ExpertStats.HostileProjectile(NPC, BulletDamage);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, velocity, ModContent.ProjectileType<RustyBullet>(), damage, 1f, out _);
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Aim:
					return R.Aim + AimIndex();
				case Phase.Shoot:
					int since = (int)(Timer - 1f) % ShotInterval;
					return (since < MuzzleFlashTicks && Timer <= ShootTicks ? R.Shoot : R.Aim) + AimIndex();
				case Phase.Flee:
					NPC.frameCounter += Math.Abs(NPC.velocity.X);
					if (NPC.frameCounter >= R.RunStep * R.ReloadFrames) {
						NPC.frameCounter -= R.RunStep * R.ReloadFrames;
					}
					return R.Reload + (int)(NPC.frameCounter / R.RunStep) % R.ReloadFrames;
			}
			if (!Grounded) {
				return R.Walk + 1;
			}
			if (Math.Abs(NPC.velocity.X) > 0.15f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= WalkAnimDistance * R.WalkFrames) {
					NPC.frameCounter -= WalkAnimDistance * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / WalkAnimDistance) % R.WalkFrames;
			}
			return R.Walk;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 12;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 2 == 0 ? DustID.Gold : DustID.Iron, out _);
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
