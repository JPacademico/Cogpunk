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
using Terraria.GameContent;
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
	/// charges for <see cref="ChargeTicks"/> (1.5 s, the telegraph, D3): his near arm swings up, palm out, and follows the
	/// player, the charge gathers in his open palm, his eyes, heart and runes brighten, and a faint dotted line shows exactly
	/// where he aims. He tracks an afterimage: where his mark was <see cref="AimDelayTicks"/> ticks ago (user, 2026-11-10b:
	/// "it should smoothly follow the player with a 0.5 seconds delay on the movement (like it is tracking an after image
	/// of the player), verify applicability and ensure no abrupt change of positions"; 0.75 s since 2026-11-09), marked by
	/// a jade reticle, so a player who keeps moving stays ahead of the arm. The arm's angle is continuous: it closes
	/// <see cref="AimFollow"/> of the gap to that afterimage each tick, never turning more than <see cref="AimMaxTurn"/> a
	/// tick, so neither the arm nor the line ever jumps (a mark that teleports is swept to, not snapped to); the arm is
	/// drawn from 37 frames 5 degrees apart (the arm sheets, D4 rule 14: never rotated at runtime) and the line, the charge
	/// and the ray all leave the palm at <see cref="JadeGolemRigData.PalmReach"/> along that angle. For the last
	/// <see cref="LockTicks"/> ticks the aim locks (the line blinks: the moment to move), then the <see cref="JadeRay"/>
	/// fires from the palm along the arm. He recovers (<see cref="RecoverTicks"/>, the arm lowered at
	/// <see cref="RecoverTurn"/> a tick) and walks on. His hands are open palms (user, 2026-11-10b: "the hands of the jade
	/// golem should be an open palm hand and the jade laser has to come out from the hand"; they were fists). Drops 1-2 <see cref="Gems.Items.Jade"/> 1 time in <see cref="JadeOdds"/> (user-set 2026-11-09: 25%).
	/// Every hit he lands, by touch or by ray, lays a stack of the jade curse on the player (user, 2026-11-10:
	/// <see cref="Gems.JadeCursePlayer"/>: slower attacks, turned to jade at 3 stacks).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; Coghaven is a T4 area: the anchor is the Bone Serpent's head,
	/// decompiled 1.4.4 NPC 39: 300 life / 12 defense / 36 contact in Classic = 600 / 12 / 72 in Expert; the ray against the
	/// Demon's scythe, 21 x 2 = 42 a hit in every mode): <see cref="Life"/> life, <see cref="Defense"/> defense,
	/// <see cref="ContactDamage"/> contact ("heavy"), immune to knockback ("tanky"), the ray <see cref="RayDamage"/>
	/// ("great"). Spawns only in Coghaven (<see cref="CoghavenSpawnRules.SpawnWeight"/>).</para>
	/// <para>D2: ai[0]/ai[1] state and timer, ai[2] the ticks walked, ai[3] the locked aim (radians below forward), all
	/// synced; the server decides, locks and spawns the ray (its angle and length go with it). Every side keeps its own
	/// trail of where the mark has been (<see cref="RecordMark"/>) and follows it with the same rule (the arm is visual
	/// there); only the server's aim decides the lock, and a client's arm eases onto the synced lock (<see cref="LockBlend"/>)
	/// instead of snapping. D1: the trail is a fixed array made per golem in <see cref="SetDefaults"/>, no allocation per
	/// tick; the aim line's raycast runs on clients only while he charges and is capped. D0: every angle is clamped to the
	/// arm's range and checked finite. Art: art/coghaven/make_jade_golem_art.py (the arm sheets: _Arm, _ArmGlow).</para>
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
		public const int AimDelayTicks = 30;                                 // user-set 2026-11-10b: the afterimage 0.5 s behind (0.75 s before)
		public const float AimFollow = 0.16f;                                // of the gap to the afterimage closed each tick (my call)
		public const float AimMaxTurn = 0.06f;                               // radians a tick at most: 3.4 degrees (my call)
		public const float LockBlend = 0.3f;                                 // a client's arm easing onto the server's lock, a tick
		public const float RecoverTurn = 0.06f;                              // the arm lowered after the shot, radians a tick (no faster than it tracks)
		public const int JadeOdds = 4, JadeMin = 1, JadeMax = 2;             // user-set 2026-11-09: 1-2 Jade, 25%
		public const float SpawnWeight = 1f;                                 // Coghaven's only enemy since 2026-11-11 (the Imperial Defender removed)
		public const float Value = 1200f;                                    // the Bone Serpent's (decompiled NPC 39: value 1200)
		private const float Hanging = MathHelper.PiOver2;                    // the arm at rest: straight down
		private const float AimMin = R.ArmMinDegrees * MathHelper.Pi / 180f;
		private const float AimMax = (R.ArmMinDegrees + (R.ArmFrames - 1) * R.ArmStepDegrees) * MathHelper.Pi / 180f;
		private const int NodeSize = 16, OrbSize = 24, OrbFrames = 5, Gap = 2;
		private const float AimDotSpacing = 14f;
		private const float ReticleRadius = 12f;

		private static Asset<Texture2D> far, near, glow, node, orb, armSheet, armGlow;
		private static readonly string[] GoreNames = { "JadeGolem_GoreHead", "JadeGolem_GoreHand", "JadeGolem_GoreHeart", "JadeGolem_GoreCrystal" };

		private Phase CurrentPhase => (Phase)State;
		private ref float Walked => ref NPC.ai[2];
		private ref float LockedAim => ref NPC.ai[3];

		/// <summary>The near arm's angle, radians below forward (continuous; every side follows the same rule).</summary>
		private float aim = Hanging;

		/// <summary>The arm is raised (the aim sheets draw it): charging, locked, firing, or not yet lowered after.</summary>
		private bool Aiming => CurrentPhase == Phase.Charge || CurrentPhase == Phase.Lock || CurrentPhase == Phase.Fire
			|| (CurrentPhase == Phase.Recover && aim < Hanging - 0.001f);

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
			armSheet = DepthLayers.RequestOptional(Texture + "_Arm");
			armGlow = DepthLayers.RequestOptional(Texture + "_ArmGlow");
		}

		public override void Unload() {
			far = near = glow = node = orb = armSheet = armGlow = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // stone
		}

		public override void SetDefaults() {
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = 34;                                 // 0.4.0 (user, 2026-11-27: 25% smaller): 46 x 104 -> 34 x 78
			NPC.height = 78;
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

		/// <summary>His touch lays the jade curse (user, 2026-11-10; on the hit player's own client, see
		/// <see cref="Gems.JadeCursePlayer"/>).</summary>
		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			Gems.JadeCursePlayer.Hit(target);
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

		/// <summary>The afterimage he aims at: where the mark was <see cref="AimDelayTicks"/> ticks ago (or as far back as the
		/// trail goes).</summary>
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

		/// <summary>The arm sheet's frame nearest <paramref name="elevation"/> (5 degrees apart).</summary>
		private static int ArmFrameFor(float elevation) {
			int k = (int)Math.Round((MathHelper.ToDegrees(elevation) - R.ArmMinDegrees) / R.ArmStepDegrees);
			return Math.Clamp(k, 0, R.ArmFrames - 1);
		}

		private Vector2 Shoulder => NPC.Bottom + new Vector2(R.ShoulderX * -NPC.direction, R.ShoulderY);

		/// <summary>Where the ray leaves his open palm with the arm at <paramref name="elevation"/> (world): on the arm's line,
		/// <see cref="JadeGolemRigData.PalmReach"/> from the shoulder, at any angle.</summary>
		private Vector2 Palm(float elevation) => Shoulder + Aim(elevation) * R.PalmReach;

		private Vector2 Aim(float elevation) => new(NPC.direction * (float)Math.Cos(elevation), (float)Math.Sin(elevation));

		/// <summary><paramref name="from"/> eased towards <paramref name="to"/>: <see cref="AimFollow"/> of the gap, at most
		/// <see cref="AimMaxTurn"/>, inside the arm's range; a non-finite goal is ignored.</summary>
		private static float Follow(float from, float to) {
			if (!float.IsFinite(to)) {
				return from;
			}
			float step = MathHelper.Clamp((to - from) * AimFollow, -AimMaxTurn, AimMaxTurn);
			return MathHelper.Clamp(from + step, AimMin, AimMax);
		}

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
						aim = Follow(aim, Elevation(Shoulder, DelayedMark(target)));   // after the afterimage, smoothly
					}
					if (IsAuthority) {
						if (target == null) {
							ChangeState((int)Phase.Recover);
						}
						else if (Timer >= TrackTicks) {
							LockedAim = aim;                    // the arm's own line: the ray leaves the palm along it
							ChangeState((int)Phase.Lock);
						}
					}
					break;
				}
				case Phase.Lock:
				case Phase.Fire:
					NPC.velocity.X *= 0.8f;
					if (float.IsFinite(LockedAim)) {
						aim = MathHelper.Clamp(aim + (LockedAim - aim) * LockBlend, AimMin, AimMax);   // a client eases onto the lock
					}
					if (IsAuthority) {
						if (CurrentPhase == Phase.Lock && Timer >= LockTicks) {
							aim = LockedAim;
							Fire();
							ChangeState((int)Phase.Fire);
						}
						else if (CurrentPhase == Phase.Fire && Timer >= FireTicks) {
							ChangeState((int)Phase.Recover);
						}
					}
					break;
				case Phase.Recover:
					NPC.velocity.X *= 0.85f;
					aim = Math.Min(Hanging, aim + RecoverTurn);   // the arm comes down
					if (IsAuthority && Timer >= RecoverTicks) {
						ChangeState((int)Phase.Walk);
					}
					break;
				default:
					aim = Hanging;
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

		/// <summary>Server: the ray along the locked line, out of the open palm.</summary>
		private void Fire() {
			Vector2 from = Palm(LockedAim);
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
			Vector2 palm = Palm(aim);
			Lighting.AddLight(palm, 0.12f, 0.6f, 0.22f);          // the emerald glow (v3, 2026-11-26b)
			if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()) {
				Vector2 from = palm + Main.rand.NextVector2CircularEdge(18f, 18f);
				if (SafeSpawn.TryNewDust(from - new Vector2(2f), 4, 4, DustID.GreenTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = (palm - from) * 0.12f;      // drawn into the palm
					d.scale = 1.1f;
				}
			}
		}

		protected override int PickFrame() {
			if (CurrentPhase != Phase.Walk) {
				return Aiming ? R.AimBody : R.Idle;            // the raised arm comes from the arm sheets (PreDraw)
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

		/// <summary>While he aims: the planes with the raised arm between the middle plane and the near one (the arm sheet's
		/// frame nearest <see cref="aim"/>, its runes and palm on the arm glow sheet), then the charge. Otherwise as every
		/// walker draws.</summary>
		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			if (NPC.IsABestiaryIconDummy || !Aiming) {
				return base.PreDraw(spriteBatch, screenPos, drawColor);
			}
			Vector2 anchor = DrawAnchor - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;                  // the art faces left
			Color light = NPC.GetAlpha(drawColor);
			int frame = R.AimBody;
			Vector2 farShift = new(DepthLayers.Shift(anchor, DepthLayers.Far, MaxParallax).X, 0f);
			Vector2 nearShift = new(DepthLayers.Shift(anchor, DepthLayers.Near, MaxParallax).X, 0f);
			int arm = ArmFrameFor(aim);
			if (far?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, far.Value, frame, Columns, CellWidth, CellHeight, CellPadding, OriginX, OriginY,
					anchor + farShift, 0, DepthLayers.Tint(light, DepthLayers.Far), flip);
			}
			DepthLayers.DrawCell(spriteBatch, TextureAssets.Npc[Type].Value, frame, Columns, CellWidth, CellHeight, CellPadding, OriginX,
				OriginY, anchor, 0, light, flip);
			if (armSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, armSheet.Value, arm, R.ArmColumns, R.ArmCellWidth, R.ArmCellHeight, CellPadding,
					R.ArmOriginX, R.ArmOriginY, anchor + nearShift, 0, light, flip);
			}
			if (near?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, near.Value, frame, Columns, CellWidth, CellHeight, CellPadding, OriginX, OriginY,
					anchor + nearShift, 0, light, flip);
			}
			float strength = GlowStrength;
			if (glow?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, glow.Value, frame, Columns, CellWidth, CellHeight, CellPadding, OriginX, OriginY, anchor,
					0, Color.White * strength * NPC.Opacity, flip);
			}
			if (armGlow?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, armGlow.Value, arm, R.ArmColumns, R.ArmCellWidth, R.ArmCellHeight, CellPadding,
					R.ArmOriginX, R.ArmOriginY, anchor + nearShift, 0, Color.White * strength * NPC.Opacity, flip);
			}
			DrawCharge(spriteBatch, anchor + nearShift, flip);
			return false;
		}

		/// <summary>The palm on screen: the rig's shoulder plus the arm's reach along <see cref="aim"/> (left-facing art,
		/// mirrored when <paramref name="flip"/>).</summary>
		private Vector2 PalmOnScreen(Vector2 anchor, bool flip) {
			float x = R.ShoulderX - R.PalmReach * MathF.Cos(aim);
			float y = R.ShoulderY + R.PalmReach * MathF.Sin(aim);
			return anchor + new Vector2(flip ? -x : x, y);
		}

		/// <summary>The charge in his palm; while he charges, the jade reticle on the afterimage he tracks and the dotted line
		/// he aims along (faint while it follows, blinking once locked); the shot's flash fades from his palm while the ray
		/// burns.</summary>
		private void DrawCharge(SpriteBatch spriteBatch, Vector2 anchor, bool flip) {
			if (CurrentPhase == Phase.Walk || CurrentPhase == Phase.Recover || orb?.IsLoaded != true || node?.IsLoaded != true) {
				return;
			}
			Texture2D orbTex = orb.Value, nodeTex = node.Value;
			if (orbTex.Height < OrbFrames * OrbSize || nodeTex.Height < NodeSize) {
				return;
			}
			Vector2 palm = PalmOnScreen(anchor, flip);
			Vector2 palmWorld = Palm(aim);
			Rectangle dot = new(0, 0, NodeSize, NodeSize);
			if (CurrentPhase != Phase.Fire && MathSafety.IsFinite(palmWorld)) {
				Vector2 dir = Aim(CurrentPhase == Phase.Lock ? LockedAim : aim);
				float alpha = CurrentPhase == Phase.Lock ? (Timer % 6f < 3f ? 0.75f : 0.3f) : 0.22f;
				float length = JadeRay.RayLength(palmWorld, dir, RayRange);
				for (float d = AimDotSpacing; d < length; d += AimDotSpacing) {   // at most 57 dots (800 / 14)
					Vector2 at = palm + dir * d - new Vector2(NodeSize * 0.5f);
					spriteBatch.Draw(nodeTex, at.Floor(), dot, Color.White * alpha, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
				}
				Player target = Target;
				if (CurrentPhase == Phase.Charge && target != null) {   // the afterimage he follows: four nodes round it
					Vector2 ghost = DelayedMark(target) - Main.screenPosition;
					float r = ReticleRadius + (Timer % 20f < 10f ? 0f : 2f);
					for (int i = 0; i < 4; i++) {
						Vector2 off = new(i == 0 ? r : i == 1 ? -r : 0f, i == 2 ? r : i == 3 ? -r : 0f);
						Vector2 at = ghost + off - new Vector2(NodeSize * 0.5f);
						spriteBatch.Draw(nodeTex, at.Floor(), dot, Color.White * 0.45f, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
					}
				}
			}
			float charge = CurrentPhase == Phase.Charge ? Timer / ChargeTicks : CurrentPhase == Phase.Lock ? (TrackTicks + Timer) / ChargeTicks : 1f;
			int frame = Math.Clamp((int)(charge * OrbFrames), 0, OrbFrames - 1);
			float fade = CurrentPhase == Phase.Fire ? 1f - Timer / FireTicks : 1f;
			Rectangle source = new(0, frame * (OrbSize + Gap), OrbSize, OrbSize);
			spriteBatch.Draw(orbTex, (palm - new Vector2(OrbSize * 0.5f)).Floor(), source, Color.White * fade, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
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
