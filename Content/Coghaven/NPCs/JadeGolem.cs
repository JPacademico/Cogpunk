using System;
using Cogpunk.Content.Coghaven.Projectiles;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
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
using R = Cogpunk.Content.Coghaven.NPCs.JadeGolemRigData;

namespace Cogpunk.Content.Coghaven.NPCs
{
	/// <summary>
	/// Jade Golem (Golem de Jade), a Coghaven enemy (user-set 2026-11-06, from the user's reference image: "a slow tanky jade
	/// golem that does heavy contact damage and stops every 5 seconds to charge a precise jade green electric ray that does
	/// great damage at great range; he should charge for 1.5 seconds, and his arm should point in the direction he is aiming,
	/// following the targeted player dynamically"). He lumbers at his target (<see cref="WalkSpeed"/>). After
	/// <see cref="WalkTicks"/> of walking (5 s), with his target within <see cref="RayRange"/> and in sight, he stops and
	/// charges for <see cref="ChargeTicks"/> (1.5 s, the telegraph, D3): his near arm swings up and follows the player
	/// (one 15-degree frame every <see cref="AimSweepTicks"/> ticks), the charge gathers in his fist, his eyes, heart and
	/// runes brighten, and a faint dotted line shows exactly where he aims. He aims where his mark was
	/// <see cref="AimDelayTicks"/> ticks ago (user, 2026-11-09: "a delay of 0.75 seconds for the tracking of the jade golem
	/// laser so it is not very punitive and tracks the player movement with a delayed time, not perfect lock-on"), so a
	/// player who keeps moving stays ahead of the arm. For the last <see cref="LockTicks"/> ticks the aim locks (the line
	/// blinks: the moment to move), then the <see cref="JadeRay"/> fires along it. He recovers (<see cref="RecoverTicks"/>)
	/// and walks on. Drops 1-2 <see cref="Gems.Items.Jade"/> 1 time in <see cref="JadeOdds"/> (user-set 2026-11-09: 25%).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; Coghaven is a T4 area: the anchor is the Bone Serpent's head,
	/// decompiled 1.4.4 NPC 39: 300 life / 12 defense / 36 contact in Classic = 600 / 12 / 72 in Expert; the ray against the
	/// Demon's scythe, 21 x 2 = 42 a hit in every mode): <see cref="Life"/> life, <see cref="Defense"/> defense,
	/// <see cref="ContactDamage"/> contact ("heavy"), immune to knockback ("tanky"), the ray <see cref="RayDamage"/>
	/// ("great"). Spawns only in Coghaven (<see cref="CoghavenSpawnRules.SpawnWeight"/>).</para>
	/// <para>D2: ai[0]/ai[1] state and timer, ai[2] the ticks walked, ai[3] the locked aim (radians below forward), all
	/// synced; the server decides, locks and spawns the ray (its angle and length go with it). The arm's sweep while he
	/// tracks is the same rule on every side from synced positions (visual only, localAI[0]); every side keeps its own
	/// trail of where the mark has been (<see cref="RecordMark"/>), and only the server's trail decides the lock. D1: the
	/// trail is a fixed array made per golem in <see cref="SetDefaults"/>, no allocation per tick; the aim line's raycast
	/// runs on clients only while he charges and is capped. Art: art/coghaven/make_jade_golem_art.py.</para>
	/// </summary>
	public class JadeGolem : GridWalkerNPC
	{
		private enum Phase { Walk, Charge, Lock, Fire, Recover }

		public const int Life = 720, ContactDamage = 90, Defense = 22;
		public const float WalkSpeed = 0.7f, WalkAccel = 0.04f, JumpSpeed = 6.5f;
		public const int WalkTicks = 300;                                    // user-set: stops every 5 s
		public const int ChargeTicks = 90;                                   // user-set: charges for 1.5 s
		public const int LockTicks = 18;                                     // the charge's last 0.3 s: the aim stops following
		public const int TrackTicks = ChargeTicks - LockTicks;
		public const int FireTicks = JadeRay.Lifetime, RecoverTicks = 30;
		public const int RayDamage = 100;                                    // Expert, through ExpertStats.HostileProjectile
		public const float RayRange = JadeRay.MaxLength;
		public const int AimSweepTicks = 3;
		public const int AimDelayTicks = 45;                                 // user-set 2026-11-09: the aim trails the mark by 0.75 s
		public const int JadeOdds = 4, JadeMin = 1, JadeMax = 2;             // user-set 2026-11-09: 1-2 Jade, 25%
		public const float SpawnWeight = 0.5f;                               // half the Imperial Defender's: the rarer of the two
		public const float Value = 1200f;                                    // the Bone Serpent's (decompiled NPC 39: value 1200)
		private const int HangingAim = R.AimFrames - 1;                     // the aim frame nearest the hanging arm (straight down)
		private const int NodeSize = 16, OrbSize = 24, OrbFrames = 5, Gap = 2;
		private const float AimDotSpacing = 14f;

		private static Asset<Texture2D> far, near, glow, node, orb;
		private static readonly string[] GoreNames = { "JadeGolem_GoreHead", "JadeGolem_GoreFist", "JadeGolem_GoreHeart", "JadeGolem_GoreCrystal" };

		private Phase CurrentPhase => (Phase)State;
		private ref float Walked => ref NPC.ai[2];
		private ref float LockedAim => ref NPC.ai[3];
		private ref float ArmFrame => ref NPC.localAI[0];

		// where the mark has been, one point a tick (every side; made per golem in SetDefaults: a ModNPC clone would share
		// an array made anywhere else with its template)
		private Vector2[] markTrail;
		private int markHead, markCount, markWho = -1;

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override int Columns => R.Columns;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement;

		/// <summary>Eyes, heart and runes: steady while he walks, brightening (and flickering) as the charge gathers.</summary>
		protected override float GlowStrength {
			get {
				if (CurrentPhase == Phase.Charge || CurrentPhase == Phase.Lock) {
					float charge = Math.Min(1f, (CurrentPhase == Phase.Lock ? TrackTicks + Timer : Timer) / ChargeTicks);
					return 0.7f + 0.3f * charge - (Timer % 6f < 2f ? 0.08f : 0f);
				}
				return 0.7f;
			}
		}

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
			node = DepthLayers.RequestOptional("Cogpunk/Content/Coghaven/Projectiles/JadeRay");
			orb = DepthLayers.RequestOptional("Cogpunk/Content/Coghaven/Projectiles/JadeRay_Orb");
		}

		public override void Unload() {
			far = near = glow = node = orb = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // stone
		}

		public override void SetDefaults() {
			NPC.width = 56;                                 // the barrel torso and the head's top (D4: matched hitbox; v2, 2026-11-09)
			NPC.height = 104;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0f;
			NPC.HitSound = SoundID.NPCHit41;
			NPC.DeathSound = SoundID.NPCDeath43;
			NPC.value = Value;
			NPC.aiStyle = -1;
			SpawnModBiomes = new[] { ModContent.GetInstance<CoghavenBiome>().Type };
			markTrail = new Vector2[AimDelayTicks + 1];
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), JadeOdds, JadeMin, JadeMax));
		}

		/// <summary>Every side, every tick: the mark's centre goes on the trail (a new mark starts a fresh trail).</summary>
		private void RecordMark(Player target) {
			if (markTrail == null || target == null) {
				markCount = 0;
				markWho = -1;
				return;
			}
			if (target.whoAmI != markWho) {
				markWho = target.whoAmI;
				markCount = 0;
			}
			markTrail[markHead] = target.Center;
			markHead = (markHead + 1) % markTrail.Length;
			if (markCount < markTrail.Length) {
				markCount++;
			}
		}

		/// <summary>Where the mark was <see cref="AimDelayTicks"/> ticks ago (or as far back as the trail goes): the point he
		/// aims at.</summary>
		private Vector2 DelayedMark(Player target) {
			if (markTrail == null || markCount == 0 || target.whoAmI != markWho) {
				return target.Center;
			}
			int n = markTrail.Length;
			Vector2 oldest = markTrail[((markHead - markCount) % n + n) % n];
			return MathSafety.IsFinite(oldest) ? oldest : target.Center;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			return CoghavenSpawnRules.SpawnWeight(spawnInfo, SpawnWeight);
		}

		public override void OnSpawn(IEntitySource source) {
			if (IsAuthority) {
				Walked = Main.rand.Next(WalkTicks);          // a pair doesn't fire in step; WalkTicks > 0 (const)
				NPC.netUpdate = true;
			}
		}

		/// <summary>The angle from <paramref name="from"/> to <paramref name="to"/>, radians below "forward" (-pi/2 straight
		/// up, pi/2 straight down): the side he faces doesn't matter.</summary>
		private static float Elevation(Vector2 from, Vector2 to) {
			Vector2 v = to - from;
			return (float)Math.Atan2(v.Y, Math.Abs(v.X));
		}

		private static int AimFrameFor(float elevation) {
			int k = (int)Math.Round((MathHelper.ToDegrees(elevation) - R.AimMinDegrees) / R.AimStepDegrees);
			return Math.Clamp(k, 0, R.AimFrames - 1);
		}

		private Vector2 Shoulder => NPC.Bottom + new Vector2(R.ShoulderX * -NPC.direction, R.ShoulderY);

		/// <summary>Where the ray leaves his fist in aim frame <paramref name="k"/> (world).</summary>
		private Vector2 Muzzle(int k) {
			k = Math.Clamp(k, 0, R.AimFrames - 1);
			return NPC.Bottom + new Vector2(R.MuzzleX[k] * -NPC.direction, R.MuzzleY[k]);
		}

		private Vector2 Aim(float elevation) => new(NPC.direction * (float)Math.Cos(elevation), (float)Math.Sin(elevation));

		private bool CanShoot(Player target) {
			return Vector2.DistanceSquared(target.Center, NPC.Center) < RayRange * RayRange
				&& Collision.CanHitLine(Shoulder, 1, 1, target.position, target.width, target.height);
		}

		protected override void UpdateState() {
			if (CurrentPhase == Phase.Walk) {
				Retarget();                                 // he keeps his mark through a charge
			}
			Player target = Target;
			RecordMark(target);
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.Charge: {
					NPC.velocity.X *= 0.8f;
					if (target != null) {
						NPC.direction = NPC.spriteDirection = dir;   // he turns to keep his mark in front
					}
					Vector2 mark = target != null ? DelayedMark(target) : NPC.Center;
					int want = target != null ? AimFrameFor(Elevation(Shoulder, mark)) : HangingAim;
					if (Timer % AimSweepTicks == 0f && (int)ArmFrame != want) {
						ArmFrame += Math.Sign(want - (int)ArmFrame);
					}
					if (IsAuthority) {
						if (target == null) {
							ChangeState((int)Phase.Recover);
						}
						else if (Timer >= TrackTicks) {
							LockedAim = Elevation(Muzzle(want), mark);
							ChangeState((int)Phase.Lock);
						}
					}
					break;
				}
				case Phase.Lock:
					NPC.velocity.X *= 0.8f;
					ArmFrame = AimFrameFor(LockedAim);
					if (IsAuthority && Timer >= LockTicks) {
						Fire();
						ChangeState((int)Phase.Fire);
					}
					break;
				case Phase.Fire:
					NPC.velocity.X *= 0.8f;
					ArmFrame = AimFrameFor(LockedAim);
					if (IsAuthority && Timer >= FireTicks) {
						ChangeState((int)Phase.Recover);
					}
					break;
				case Phase.Recover:
					NPC.velocity.X *= 0.85f;
					if (Timer % 2f == 0f && ArmFrame < HangingAim) {
						ArmFrame++;                             // the arm comes down through the aim frames
					}
					if (IsAuthority && Timer >= RecoverTicks) {
						ChangeState((int)Phase.Walk);
					}
					break;
				default:
					ArmFrame = HangingAim;
					Walked++;
					Run(target != null ? dir : 0, WalkSpeed, WalkAccel, JumpSpeed);
					FaceMotion(dir);
					if (IsAuthority && target != null && Walked >= WalkTicks && Grounded && CanShoot(target)) {
						Walked = 0f;
						NPC.direction = NPC.spriteDirection = dir;
						ChangeState((int)Phase.Charge);
					}
					break;
			}
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Server: the ray along the locked line, from the fist of the frame it points with.</summary>
		private void Fire() {
			Vector2 from = Muzzle(AimFrameFor(LockedAim));
			Vector2 dir = Aim(LockedAim);
			if (!MathSafety.IsFinite(from) || !MathSafety.IsFinite(dir)) {
				return;
			}
			float length = JadeRay.RayLength(from, dir, RayRange);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, Vector2.Zero, ModContent.ProjectileType<JadeRay>(),
				ExpertStats.HostileProjectile(NPC, RayDamage), 5f, out _, Main.myPlayer, (float)Math.Atan2(dir.Y, dir.X), length);
		}

		private void Effects() {
			if (CurrentPhase == Phase.Charge && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Item8 with { Pitch = -0.7f, Volume = 0.9f }, NPC.Center);   // the charge gathering
			}
			if (CurrentPhase == Phase.Lock && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = -0.4f, Volume = 0.9f }, NPC.Center);   // locked: move now
			}
			if (CurrentPhase != Phase.Charge && CurrentPhase != Phase.Lock) {
				return;
			}
			Vector2 fist = Muzzle((int)ArmFrame);
			Lighting.AddLight(fist, 0.1f, 0.55f, 0.35f);
			if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()) {
				Vector2 from = fist + Main.rand.NextVector2CircularEdge(18f, 18f);
				if (SafeSpawn.TryNewDust(from - new Vector2(2f), 4, 4, DustID.GreenTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = (fist - from) * 0.12f;      // drawn into the fist
					d.scale = 1.1f;
				}
			}
		}

		protected override int PickFrame() {
			if (CurrentPhase != Phase.Walk) {
				if (CurrentPhase == Phase.Recover && ArmFrame >= HangingAim) {
					return R.Idle;
				}
				return R.Aim + Math.Clamp((int)ArmFrame, 0, R.AimFrames - 1);
			}
			if (!Grounded) {
				return R.Walk + 1;
			}
			if (Math.Abs(NPC.velocity.X) > 0.1f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= R.WalkStep * R.WalkFrames) {
					NPC.frameCounter -= R.WalkStep * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / R.WalkStep) % R.WalkFrames;
			}
			return R.Idle + (int)(Timer / 15f) % R.IdleFrames;     // a slow breath: 4 frames, 1 s
		}

		/// <summary>The charge in his fist, and while he charges the dotted line he aims along (faint while it follows, blinking
		/// once locked); the shot's flash fades from his fist while the ray burns.</summary>
		protected override void DrawExtras(SpriteBatch spriteBatch, Vector2 anchor, Color light, bool flip, float scale, bool dummy) {
			if (dummy || CurrentPhase == Phase.Walk || CurrentPhase == Phase.Recover || orb?.IsLoaded != true || node?.IsLoaded != true) {
				return;
			}
			Texture2D orbTex = orb.Value, nodeTex = node.Value;
			if (orbTex.Height < OrbFrames * OrbSize || nodeTex.Height < NodeSize) {
				return;
			}
			int k = Math.Clamp((int)ArmFrame, 0, R.AimFrames - 1);
			Vector2 fist = anchor + new Vector2(flip ? -R.MuzzleX[k] : R.MuzzleX[k], R.MuzzleY[k]);
			Vector2 fistWorld = Muzzle(k);
			if (CurrentPhase != Phase.Fire) {
				Player target = Target;
				Vector2 dir = CurrentPhase == Phase.Lock ? Aim(LockedAim) : target != null ? Aim(Elevation(fistWorld, DelayedMark(target))) : Vector2.Zero;
				float alpha = CurrentPhase == Phase.Lock ? (Timer % 6f < 3f ? 0.75f : 0.3f) : 0.22f;
				if (dir != Vector2.Zero) {
					float length = JadeRay.RayLength(fistWorld, dir, RayRange);
					Rectangle dot = new(0, 0, NodeSize, NodeSize);
					for (float d = AimDotSpacing; d < length; d += AimDotSpacing) {   // at most 57 dots (800 / 14)
						Vector2 at = fist + dir * d - new Vector2(NodeSize * 0.5f);
						spriteBatch.Draw(nodeTex, at.Floor(), dot, Color.White * alpha, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
					}
				}
			}
			float charge = CurrentPhase == Phase.Charge ? Timer / ChargeTicks : CurrentPhase == Phase.Lock ? (TrackTicks + Timer) / ChargeTicks : 1f;
			int frame = Math.Clamp((int)(charge * OrbFrames), 0, OrbFrames - 1);
			float fade = CurrentPhase == Phase.Fire ? 1f - Timer / FireTicks : 1f;
			Rectangle source = new(0, frame * (OrbSize + Gap), OrbSize, OrbSize);
			spriteBatch.Draw(orbTex, (fist - new Vector2(OrbSize * 0.5f)).Floor(), source, Color.White * fade, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 18;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 4 == 0 ? DustID.GreenTorch : DustID.GemEmerald, out _);
			}
			if (NPC.life > 0) {
				return;
			}
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center, NPC.velocity * 0.4f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
				}
			}
		}
	}
}
