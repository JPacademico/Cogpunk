using System;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Content.OldBrassTown.Minions;
using Cogpunk.Content.OldBrassTown.Projectiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.OldBrassTown.NPCs.SheriffRigData;

namespace Cogpunk.Content.OldBrassTown.NPCs
{
	/// <summary>
	/// Sheriff (user-set 2026-11-04: "a sheriff robot mini boss with three sheriff stars that float above him and attack the
	/// player then come back to him (every 2 seconds); he also shoots at the player, 6 bullets then reload like the bandits;
	/// hard to kill; a chance to drop the Sheriff Badge; a rare spawn"), Old Brass Town's lawman. He walks at the target
	/// until he is within <see cref="KeepRange"/>; with the target in sight within <see cref="SightRange"/> he draws (the
	/// telegraph, <see cref="AimTicks"/> ticks, the hammer cocked), fires <see cref="Shots"/> rounds one every
	/// <see cref="ShotInterval"/> ticks at the target as it is then (within <see cref="MaxAimAngle"/> of level), then stands
	/// his ground and reloads for <see cref="ReloadTicks"/> ticks (a lawman doesn't run: that is his opening).
	/// <para>His three <see cref="SheriffStar"/>s float over his hat on their own clock: every <see cref="StarCycle"/> ticks
	/// (2 s) they flash and chime for <see cref="StarTelegraph"/> ticks, then fly at the target one after another
	/// (<see cref="StarStagger"/> ticks apart, each at where the target was as it left) and come back to their places.</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Dark Mage, the Old One's Army's pre-Hardmode
	/// mini-boss, decompiled 1.4.4 NPC 564: 800 life, 18 defense, 40 contact in Classic = 1600 / 18 / 80 in Expert):
	/// <see cref="Life"/> life, <see cref="Defense"/> defense, no knockback (the user's "hard to kill"),
	/// <see cref="ContactDamage"/> contact, bullets <see cref="BulletDamage"/>, stars <see cref="StarDamage"/>. A rare spawn
	/// in Old Brass Town (<see cref="SpawnWeight"/>, one at a time). A mini-boss (<see cref="CogpunkSets.Miniboss"/>: the Metal
	/// Wrench's riposte clashes on him). Drops 1 in <see cref="BadgeOdds"/> the <see cref="SheriffBadge"/>, 4-8 Tarnished Brass
	/// Bars and his coins.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the shots fired, <c>ai[3]</c> the stars' clock
	/// (every side counts it; the server's value rides each sync); the server targets, decides, fires and keeps his stars (a
	/// fixed scan every <see cref="StarCheckInterval"/> ticks respawns a missing one through <see cref="SafeSpawn"/>). D1: no
	/// allocation; sounds and dust on clients.</para>
	/// </summary>
	public class Sheriff : GridWalkerNPC
	{
		private enum Phase { Walk, Aim, Shoot, Reload }

		public const int Life = 1600, ContactDamage = 40, Defense = 20;    // Expert
		public const int BulletDamage = 34, StarDamage = 36;              // Expert, each
		public const int Width = 26, Height = 52;
		public const float WalkSpeed = 1.1f, WalkAccel = 0.06f, JumpSpeed = 7.5f;
		public const float SightRange = 36f * 16f;
		public const float KeepRange = 10f * 16f;
		public const int AimTicks = 30;                                     // the telegraph (D3: >= 30 at T0-T4)
		public const int Shots = 6;                                         // user-set
		public const int ShotInterval = 12;
		public const int ShootTicks = Shots * ShotInterval;
		public const int ReloadTicks = 120;
		public const float BulletSpeed = 8f;                                // px per update: 16 px/tick (RustyBullet updates twice a tick)
		public const float ShotSpread = 0.03f;
		public const float MaxAimAngle = 0.7f;
		public const float LevelBand = 0.22f;
		public const int MuzzleFlashTicks = 5;
		public const int StarCount = 3;                                     // user-set
		public const int StarCycle = 120;                                   // "every 2 seconds" (user-set)
		public const int StarTelegraph = 30;
		public const int StarStagger = 8;
		public const int StarCheckInterval = 60;
		public const float SpawnWeight = 0.04f;                             // "a rare spawn" (user-set)
		public const int BadgeOdds = 3;
		public const float WalkAnimDistance = R.WalkStep;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "Sheriff_GoreHat", "Sheriff_GoreHead", "Sheriff_GoreBadge" };

		private Phase CurrentPhase => (Phase)State;
		private ref float ShotsFired => ref NPC.ai[2];

		/// <summary>The stars' clock (0 .. <see cref="StarCycle"/> - 1): their telegraph, launches and returns follow it.</summary>
		public ref float StarClock => ref NPC.ai[3];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<OldBrassTownBiome>().ModBiomeBestiaryInfoElement;

		/// <summary>Where star <paramref name="slot"/> floats over his hat (world space): a little arc, the middle one higher,
		/// bobbing by whole pixels.</summary>
		public Vector2 StarHome(int slot) {
			float x = (slot - 1) * 24f;
			float y = R.HatTopY - 16f - (slot == 1 ? 8f : 0f) - (Main.GameUpdateCount / 20 + slot) % 2 * 2f;
			return NPC.Bottom + new Vector2(x, y);
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
			CogpunkSets.Miniboss[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0f;                       // "hard to kill": he doesn't budge
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Item.buyPrice(gold: 1);
			NPC.rarity = 3;                                 // the Lifeform Analyzer calls him out
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			return NPC.AnyNPCs(Type) ? 0f : OldBrassTownSpawnRules.TownSpawnWeight(spawnInfo, SpawnWeight);
		}

		public override void OnSpawn(IEntitySource source) {
			if (IsAuthority) {
				KeepStars();
			}
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<SheriffBadge>(), BadgeOdds));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<TarnishedBrassBar>(), 1, 4, 8));
		}

		protected override void UpdateState() {
			Retarget();
			Player target = Target;
			if (target != null) {
				if (++StarClock >= StarCycle) {
					StarClock = 0f;
				}
			}
			else {
				StarClock = 0f;                             // nobody to chase: the stars just float
			}
			if (IsAuthority && Timer % StarCheckInterval == 0f) {
				KeepStars();
			}
			if (!Main.dedServ && target != null) {
				StarSounds();
			}
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.Aim:
					Run(0, 0f, WalkAccel * 3f, JumpSpeed);
					NPC.direction = NPC.spriteDirection = dir;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(SoundID.Unlock with { Pitch = -0.2f, Volume = 0.8f, MaxInstances = 3 }, NPC.Center);
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
						ChangeState((int)Phase.Reload);
					}
					break;
				case Phase.Reload:
					Run(0, 0f, WalkAccel * 3f, JumpSpeed);
					NPC.direction = NPC.spriteDirection = dir;
					if (!Main.dedServ && Timer % 20f == 10f) {
						SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = -0.4f, Volume = 0.7f, MaxInstances = 3 }, NPC.Center);   // a cartridge in
					}
					if (IsAuthority && Timer >= ReloadTicks) {
						ChangeState((int)Phase.Walk);
					}
					break;
				default:
					float adx = Math.Abs(dx);
					Run(target != null && adx > KeepRange ? dir : 0, WalkSpeed, WalkAccel, JumpSpeed);
					FaceMotion(dir);
					if (IsAuthority && target != null && Grounded && Timer > 20f
						&& Vector2.DistanceSquared(target.Center, NPC.Center) < SightRange * SightRange
						&& Collision.CanHitLine(Muzzle(dir, 0), 1, 1, target.position, target.width, target.height)) {
						NPC.direction = NPC.spriteDirection = dir;
						ChangeState((int)Phase.Aim);
					}
					break;
			}
		}

		/// <summary>Server: his three stars exist (a fixed scan of the projectiles, every <see cref="StarCheckInterval"/>
		/// ticks; a missing slot is spawned again through <see cref="SafeSpawn"/>, which refuses rather than overwrite).</summary>
		private void KeepStars() {
			int type = ModContent.ProjectileType<SheriffStar>();
			int present = 0;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == type && (int)p.ai[0] == NPC.whoAmI) {
					int slot = (int)p.ai[1];
					if (slot >= 0 && slot < StarCount) {
						present |= 1 << slot;
					}
				}
			}
			int damage = ExpertStats.HostileProjectile(NPC, StarDamage);
			for (int slot = 0; slot < StarCount; slot++) {
				if ((present & (1 << slot)) == 0) {
					SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), StarHome(slot), Vector2.Zero, type, damage, 2f, out _, Main.myPlayer,
						NPC.whoAmI, slot);
				}
			}
		}

		/// <summary>Clients: the stars' chime as their telegraph starts and a whoosh as each one flies.</summary>
		private void StarSounds() {
			int clock = (int)StarClock;
			if (clock == 1) {
				SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = 0.5f, Volume = 0.8f, MaxInstances = 2 }, NPC.Center);
			}
			for (int slot = 0; slot < StarCount; slot++) {
				if (clock == StarTelegraph + slot * StarStagger) {
					SoundEngine.PlaySound(SoundID.Item1 with { Pitch = 0.7f, Volume = 0.6f, MaxInstances = 3 }, StarHome(slot));
				}
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
			float angle = (float)Math.Atan2(to.Y, Math.Abs(to.X) + 0.01f);
			return angle < -LevelBand ? 1 : (angle > LevelBand ? 2 : 0);
		}

		private Vector2 Muzzle(int dir, int aim) {
			int x = aim == 1 ? R.MuzzleUpX : aim == 2 ? R.MuzzleDownX : R.MuzzleLevelX;
			int y = aim == 1 ? R.MuzzleUpY : aim == 2 ? R.MuzzleDownY : R.MuzzleLevelY;
			return NPC.Bottom + new Vector2(x * -dir, y);
		}

		private void Fire(Player target) {
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			Vector2 from = Muzzle(dir, AimIndex());
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item41 with { Pitch = -0.5f, Volume = 0.8f, MaxInstances = 4 }, from);
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
				case Phase.Reload:
					return R.Reload + (int)(Timer / 10f) % R.ReloadFrames;
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
			return R.Idle + (int)(Timer / 20f) % R.IdleFrames;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 18;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Gold : DustID.Iron, out _);
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
