using System;
using Cogpunk.Content.Underworld.Projectiles;
using Cogpunk.Core.Configs;
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
using R = Cogpunk.Content.Underworld.NPCs.DragoneteMiudoRigData;

namespace Cogpunk.Content.Underworld.NPCs
{
	/// <summary>
	/// Dragonete Miúdo, a baby dragon of the Underworld (user-set 2026-11-11b: "add a new enemy to the hell biome called
	/// Dragonete miudo it should be a baby dragon that spits fire bolts at a distance and if it misses it comes flying trying
	/// to bite the player"; the numbers and the timing are my calls). It keeps its distance, hovering
	/// <see cref="HoverDistance"/> to one side of its target and <see cref="HoverHeight"/> above; every
	/// <see cref="SpitCooldown"/> ticks, with the target in sight within <see cref="SpitRange"/>, it inhales (the telegraph,
	/// <see cref="InhaleTicks"/> ticks: its head rears, its chest swells, its throat glows) and spits a fire bolt
	/// (<see cref="DragoneteFireBolt"/>) at where the target stands. If the bolt misses (it burns out or hits a wall without
	/// touching anyone) the dragonet screeches and rears (<see cref="RearTicks"/>, the second telegraph) and swoops at the
	/// target with its jaws open, steering after it (<see cref="SwoopSpeed"/>, <see cref="SwoopSteer"/>, up to
	/// <see cref="SwoopMaxTicks"/>); reaching the target it snaps its jaws (the bite: x<see cref="BiteMultiplier"/> contact),
	/// then flies back up and away (<see cref="RetreatTicks"/>) to spit again.
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchors the Demon, terraria.wiki.gg: 120 life, 8 defense, 32
	/// contact, 42 Demon Sickle in Classic = 240 / 8 / 64 / 84 in Expert, and the Fire Imp: 70 life, 16 defense, 30 contact
	/// = 140 / 16 / 60): <see cref="Life"/> life, <see cref="Defense"/> defense, <see cref="ContactDamage"/> contact (84
	/// biting), a <see cref="BoltDamage"/> bolt that may set the target on fire. Immune to lava and fire. Spawns anywhere in
	/// the Underworld (<see cref="SpawnWeight"/>), before and after Hardmode. Drops the Demon's coins.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the side it hovers on; the server targets, spits and
	/// decides every change, and learns of a miss from its own bolt (<see cref="BoltMissed"/>: the bolt's hit hook runs only
	/// on the hit player's client, decompiled <c>PlayerLoader.OnHurt</c>, so the bolt judges a hit on the server by its own
	/// overlap); every side flies from the synced state. D1: no allocation; sounds, dust and light on clients.</para>
	/// </summary>
	public class DragoneteMiudo : GridWalkerNPC
	{
		private enum Phase { Hover, Inhale, Spit, Rear, Swoop, Bite, Retreat }

		public const int Life = 200, ContactDamage = 60, Defense = 12;      // Expert
		public const float BiteMultiplier = 1.4f;                            // 84 in Expert
		public const int BoltDamage = 56;                                     // Expert, ExpertStats.HostileProjectile
		public const int Width = 44, Height = 40;
		public const float KnockbackResist = 0.6f;
		public const float HoverDistance = 15f * 16f, HoverHeight = 5f * 16f;
		public const float HoverSpeed = 3.6f, HoverAccel = 0.1f;
		public const int SpitCooldown = 110;
		public const float SpitRange = 34f * 16f;
		public const int InhaleTicks = 36;                                    // the telegraph (D3: >= 30 at T0-T4)
		public const int SpitTicks = 18;
		public const float BoltSpeed = 7.5f;
		public const int RearTicks = 30;                                      // the bite's telegraph
		public const int SwoopMaxTicks = 55;
		public const float SwoopSpeed = 9f, SwoopSteer = 0.08f;
		public const int BiteTicks = 15;
		public const int RetreatTicks = 45;
		public const float RetreatSpeed = 5f;
		public const int FlapTicks = 3;                     // 2026-11-19: ten drawn in-betweens a beat (was six of 4 ticks): 30 ticks a beat
		public const float SpawnWeight = 0.12f;
		/// <summary>The sprite's mass (head and body) sits this far ahead of its origin, game px: the hitbox is centred on it.</summary>
		public const float AnchorShift = 7f;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "DragoneteMiudo_GoreHead", "DragoneteMiudo_GoreWing", "DragoneteMiudo_GoreTail" };
		private static readonly SoundStyle Flap = SoundID.Item32 with { Pitch = 0.2f, Volume = 0.35f, MaxInstances = 3 };
		private static readonly SoundStyle Breath = SoundID.DD2_DrakinBreathIn with { Pitch = 0.5f, Volume = 0.6f, MaxInstances = 3 };
		private static readonly SoundStyle Shot = SoundID.DD2_DrakinShot with { Pitch = 0.45f, Volume = 0.7f, MaxInstances = 3 };
		private static readonly SoundStyle Screech = SoundID.DD2_WyvernScream with { Pitch = 0.8f, Volume = 0.5f, MaxInstances = 3 };
		private static readonly SoundStyle Snap = SoundID.Item1 with { Pitch = -0.3f, Volume = 0.8f, MaxInstances = 3 };

		private bool missed;                                                  // server: its last bolt missed

		private Phase CurrentPhase => (Phase)State;
		private ref float Side => ref NPC.ai[2];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.TheUnderworld;
		protected override float GlowStrength => CurrentPhase == Phase.Inhale || CurrentPhase == Phase.Spit ? 1f : 0.8f;

		/// <summary>The origin drawn behind the hitbox's centre (the head leads), and the whole sprite up a pixel on the wings'
		/// down-beat (every plane together: no plane's pixels change, check_flicker).</summary>
		protected override Vector2 DrawAnchor {
			get {
				int face = NPC.spriteDirection == 0 ? -1 : NPC.spriteDirection;
				float bob = Frame >= R.Fly + 4 && Frame <= R.Fly + 6 ? -2f : 0f;   // lifted as the wings push down
				return NPC.Bottom + new Vector2(-AnchorShift * face, bob);
			}
		}

		private bool Biting => CurrentPhase == Phase.Swoop || CurrentPhase == Phase.Bite;

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
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.OnFire] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.OnFire3] = true;
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.noGravity = true;
			NPC.lavaImmune = true;
			NPC.HitSound = SoundID.DD2_DrakinHurt with { Pitch = 0.4f };
			NPC.DeathSound = SoundID.DD2_DrakinDeath with { Pitch = 0.4f };
			NPC.value = 300f;                                                 // the Demon's
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player p = spawnInfo.Player;
			return p.ZoneUnderworldHeight && !spawnInfo.PlayerInTown && !spawnInfo.Invasion ? SpawnWeight : 0f;
		}

		/// <summary>Server: its bolt burned out or hit a wall without touching anyone (<see cref="DragoneteFireBolt"/>).</summary>
		public void BoltMissed() {
			missed = true;
		}

		protected override void UpdateState() {
			Retarget();
			Player target = Target;
			NPC.damage = Biting ? (int)(NPC.defDamage * BiteMultiplier) : NPC.defDamage;
			if (target == null) {
				NPC.velocity.Y = Math.Max(NPC.velocity.Y - 0.1f, -HoverSpeed);   // nothing to hunt: it climbs away
				NPC.EncourageDespawn(10);
				FaceMotion(NPC.direction == 0 ? -1 : NPC.direction);
				return;
			}
			int toTarget = target.Center.X >= NPC.Center.X ? 1 : -1;
			switch (CurrentPhase) {
				case Phase.Inhale:
					NPC.velocity *= 0.9f;
					NPC.direction = NPC.spriteDirection = toTarget;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(Breath, NPC.Center);
					}
					if (!Main.dedServ && Main.rand.NextBool(4) && CogpunkClientConfig.RollEffect()) {
						SafeSpawn.TryNewDust(Mouth() - new Vector2(4f), 8, 8, DustID.Torch, out _, 0f, -1f);
					}
					if (IsAuthority && Timer >= InhaleTicks) {
						SpitBolt(target);
						ChangeState((int)Phase.Spit);
					}
					break;
				case Phase.Spit:
					NPC.velocity *= 0.92f;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(Shot, NPC.Center);
					}
					if (IsAuthority && Timer >= SpitTicks) {
						ChangeState((int)Phase.Hover);
					}
					break;
				case Phase.Rear:
					NPC.velocity = Vector2.Lerp(NPC.velocity, new Vector2(-toTarget * 1.5f, -1.5f), 0.1f);   // rears up and back
					NPC.direction = NPC.spriteDirection = toTarget;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(Screech, NPC.Center);
					}
					if (IsAuthority && Timer >= RearTicks) {
						ChangeState((int)Phase.Swoop);
					}
					break;
				case Phase.Swoop:
					DoSwoop(target);
					break;
				case Phase.Bite:
					NPC.velocity *= 0.9f;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(Snap, NPC.Center);
					}
					if (IsAuthority && Timer >= BiteTicks) {
						ChangeState((int)Phase.Retreat);
					}
					break;
				case Phase.Retreat:
					NPC.velocity = Vector2.Lerp(NPC.velocity, new Vector2(-toTarget * RetreatSpeed * 0.6f, -RetreatSpeed), 0.08f);
					FaceMotion(toTarget);
					FlapEffects();
					if (IsAuthority && Timer >= RetreatTicks) {
						ChangeState((int)Phase.Hover);
					}
					break;
				default:
					DoHover(target, toTarget);
					break;
			}
		}

		/// <summary>Holds a spot to one side of the target and above it; the server spits when the cooldown is over and the
		/// target is in sight, or rears for a swoop when its last bolt missed.</summary>
		private void DoHover(Player target, int toTarget) {
			if (IsAuthority && Side == 0f) {
				Side = NPC.Center.X >= target.Center.X ? 1f : -1f;
				NPC.netUpdate = true;
			}
			float side = Side >= 0f ? 1f : -1f;
			Vector2 goal = target.Center + new Vector2(side * HoverDistance, -HoverHeight + MathF.Sin(Timer * 0.06f) * 10f);
			if (NPC.collideX || NPC.collideY) {
				goal.Y -= 64f;                                                 // up and over what blocks it
			}
			Vector2 want = (goal - NPC.Center).SafeNormalize(Vector2.Zero) * Math.Min(HoverSpeed, Vector2.Distance(goal, NPC.Center) * 0.1f);
			NPC.velocity = Vector2.Lerp(NPC.velocity, want, HoverAccel);
			NPC.direction = NPC.spriteDirection = toTarget;
			FlapEffects();
			if (!IsAuthority) {
				return;
			}
			if (missed) {
				missed = false;
				ChangeState((int)Phase.Rear);
				return;
			}
			if (Timer >= SpitCooldown && Vector2.DistanceSquared(target.Center, NPC.Center) < SpitRange * SpitRange
				&& Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height)) {
				Side = NPC.Center.X >= target.Center.X ? 1f : -1f;            // it keeps the side it is on
				ChangeState((int)Phase.Inhale);
			}
		}

		/// <summary>Jaws open, after the target, turning gently (a sidestep beats it); reaching the target it bites, passing it,
		/// hitting a wall or running out of time it gives up (server).</summary>
		private void DoSwoop(Player target) {
			Vector2 want = (target.Center - NPC.Center).SafeNormalize(new Vector2(NPC.direction, 0f)) * SwoopSpeed;
			NPC.velocity = Vector2.Lerp(NPC.velocity, want, SwoopSteer);
			NPC.direction = NPC.spriteDirection = NPC.velocity.X >= 0f ? 1 : -1;
			if (!Main.dedServ && Timer % 4f == 0f && CogpunkClientConfig.RollEffect()) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.Torch, out _, -NPC.velocity.X * 0.2f, -NPC.velocity.Y * 0.2f);
			}
			if (!IsAuthority) {
				return;
			}
			Rectangle jaws = NPC.Hitbox;
			jaws.Inflate(6, 6);
			if (jaws.Intersects(target.Hitbox)) {
				ChangeState((int)Phase.Bite);
				return;
			}
			bool passed = Timer > 10f && Vector2.Dot(target.Center - NPC.Center, NPC.velocity) < 0f;
			if (Timer >= SwoopMaxTicks || passed || (Timer > 6f && (NPC.collideX || NPC.collideY))) {
				ChangeState((int)Phase.Retreat);
			}
		}

		/// <summary>The mouth in the world (the rig's point, mirrored for the way it faces).</summary>
		private Vector2 Mouth() {
			int face = NPC.spriteDirection == 0 ? -1 : NPC.spriteDirection;
			return DrawAnchor + new Vector2(-R.MouthX * face, R.MouthY);
		}

		/// <summary>Server: one bolt from the mouth at where the target stands (its hit or miss comes back through
		/// <see cref="BoltMissed"/>).</summary>
		private void SpitBolt(Player target) {
			Vector2 from = Mouth();
			if (!Collision.CanHitLine(NPC.Center, 1, 1, from, 1, 1)) {
				from = NPC.Center;
			}
			Vector2 velocity = (target.Center - from).SafeNormalize(new Vector2(NPC.direction, 0f)) * BoltSpeed;
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, velocity, ModContent.ProjectileType<DragoneteFireBolt>(),
				ExpertStats.HostileProjectile(NPC, BoltDamage), 0f, out _, -1, NPC.whoAmI);
		}

		private void FlapEffects() {
			if (!Main.dedServ && (int)Timer % (FlapTicks * R.FlyFrames) == 1) {
				SoundEngine.PlaySound(Flap, NPC.Center);
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Inhale:
					return R.Inhale + Math.Min(R.InhaleFrames - 1, (int)(Timer / (InhaleTicks / 3f)));
				case Phase.Spit:
					return R.Spit + Math.Min(R.SpitFrames - 1, (int)(Timer / (SpitTicks / 3f)));
				case Phase.Swoop:
					return R.Swoop + (int)(Timer / 4f) % R.SwoopFrames;
				case Phase.Bite:
					return R.Bite + Math.Min(R.BiteFrames - 1, (int)(Timer / (BiteTicks / 3f)));
				case Phase.Rear:
					return R.Fly + (int)(Timer / (FlapTicks - 1)) % R.FlyFrames;   // a faster beat as it rears
			}
			return R.Fly + (int)((Timer + NPC.whoAmI * 2) / FlapTicks) % R.FlyFrames;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 14;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Torch : DustID.Blood, out _);
			}
			if (NPC.life <= 0) {
				foreach (string name in GoreNames) {
					if (Mod.TryFind(name, out ModGore gore)) {
						SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.position + new Vector2(Main.rand.Next(NPC.width), Main.rand.Next(NPC.height)),
							NPC.velocity * 0.5f + Main.rand.NextVector2Circular(2f, 2f), gore.Type, out _);
					}
				}
			}
		}
	}
}
