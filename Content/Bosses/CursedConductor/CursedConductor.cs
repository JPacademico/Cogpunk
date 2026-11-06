using System;
using System.IO;
using Cogpunk.Content.Bosses.CursedConductor.Items;
using Cogpunk.Content.Bosses.CursedConductor.NPCs;
using Cogpunk.Content.Bosses.CursedConductor.Projectiles;
using Cogpunk.Content.OldBrassTown;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.CursedConductor.CursedConductorRigData;

namespace Cogpunk.Content.Bosses.CursedConductor
{
	/// <summary>
	/// The Cursed Conductor, Old Brass Town's boss (user-set 2026-11-04: "a train conductor robot that calls a spirit of a
	/// big flying ghost train to attack the player in different patterns", T5 "same tier as the Wall of Flesh"), called with
	/// the <see cref="CursedWhistle"/> inside the town. A robot conductor who floats on a turbine pumping smoke (user,
	/// 2026-11-05b: "a turbine that pumps smoke on the bottom instead of the ghost floaty bottom"; it was a tail of ghost mist);
	/// he never fights hand to hand (no contact damage, user 2026-11-05). The fight (user-set 2026-11-05):
	/// <list type="bullet">
	/// <item><b>Passive trains</b>: every <see cref="PassiveInterval"/> ticks (3 s; <see cref="EnragedPassiveInterval"/> below
	/// half his life), with no gesture of his, a ghost train runs across the screen of the fighter farthest from him, after a
	/// <see cref="PassiveTelegraph"/>-tick warning (1 s; 0.7 s below half): an <b>Express</b> along the player's row, coming in
	/// from the screen edge away from him and vanishing at the edge towards him, or a <b>Dive</b> down (or up: 50%) the
	/// player's column, from one screen edge to the other (vanilla's 1920x1080 screen, <see cref="ScreenHalfWidth"/>).</item>
	/// <item><b>Lantern</b> (his main attack): every <see cref="LanternInterval"/> ticks (1.5 s) he swings his lantern
	/// (<see cref="ThrowWindup"/> ticks of warning) and flings a fan of <see cref="Bolts"/> (<see cref="EnragedBolts"/> below
	/// half) straight cursed bolts, <see cref="BoltSpread"/> apart, at the closest fighter not trapped in the loop. A bolt
	/// that hits curses for 6 s (<see cref="Buffs.ConductorCurse"/>: +25% from the train and the ghosts); one that strikes a
	/// block opens a rift and a ghost rises from it <see cref="RiftDelay"/> ticks later (<see cref="ConductorGhost"/>, at most
	/// <see cref="MaxGhosts"/>).</item>
	/// <item><b>Loop</b> (rare: every <see cref="LoopIntervalMin"/>-<see cref="LoopIntervalMax"/> ticks): a random fighter is
	/// circled by the train for 3 laps (<see cref="GhostTrain.LoopLaps"/>) after a ring of ghost lights; two ghosts rise on
	/// opposite sides inside the ring every lap; no passive train runs and the lantern never aims at the trapped
	/// player meanwhile.</item>
	/// <item><b>Whistle</b>: at 70%, 40% and 10% of his life he stops, blows his whistle and can't be hurt for
	/// <see cref="WhistleTicks"/> ticks (7 s): the train runs a wave across the screen, left to right and then right to left
	/// (6.5 s for the two), while ghosts rise out of the ground near the fighters, one a second.</item>
	/// </list>
	/// <b>Fury</b> (user, 2026-11-05: "enrage outside of the brass town area so players do not run from him"): while no
	/// fighter is inside Old Brass Town his attacks hit <see cref="FuryDamage"/>x, the passive train comes every
	/// <see cref="FuryPassiveInterval"/> ticks after <see cref="FuryPassiveTelegraph"/> of warning and he throws every
	/// <see cref="FuryLanternInterval"/>. He leaves only when no living player is within <see cref="DespawnRange"/>.
	/// Every telegraph is 30 ticks or more (D3, the Wall of Flesh's tier).
	/// <para>Fighters (<see cref="IsFighter"/>): alive for <see cref="RespawnGraceTicks"/>, within <see cref="FightRange"/> of
	/// him (a player elsewhere or just respawned is left alone).</para>
	/// <para>Boss-fight rules (user, 2026-10-26): he materializes and tips his cap under a camera lock with a title card;
	/// dies in a camera-locked cinematic (he slumps, his lantern and eyes go out, and the last ghost train comes for him and
	/// blows him to bits: user 2026-11-05, "explode in tiny bits when hit by the train") with the "Defeated" card
	/// (<see cref="BossNPC"/>); no natural spawns around him; his hitbox is his coat, head and cap from the art, and since
	/// 2026-11-05b the turbine under them (solid machinery, down to <see cref="CursedConductorRigData.BodyBottom"/>).</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/bosses.csv; anchor the Wall of Flesh, terraria.wiki.gg Expert: 11200
	/// life, 12 defense, 150 contact, eye lasers 44-60, the Hungry 60-120): <see cref="ExpertLife"/> life (+35% per extra
	/// player), <see cref="BaseDefense"/> defense, no contact; the train <see cref="TrainDamage"/> head on (half from a wagon),
	/// a bolt <see cref="BoltDamage"/>, a ghost <see cref="ConductorGhost.ExpertDamage"/>. Loot (<see cref="CursedConductorLoot"/>).</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the side he floats on, <c>ai[3]</c> flags (enraged,
	/// furious, the whistles blown); the passive train's and the throw's progress, the loop's centre and target and the wave's
	/// point and phase in <see cref="SendExtraAI"/>. The server decides, targets and spawns; the float, the frames and the
	/// telegraphs follow the synced state on every side. D1: no allocation per tick (fighters are counted in place).</para>
	/// </summary>
	[AutoloadBossHead]
	public partial class CursedConductor : BossNPC
	{
		public enum Phase { Intro, Hover, Loop, Whistle, Dying, Leaving }

		// --- stats (Expert, docs/balance/bosses.csv) -------------------------------------------------------------------
		public const int ExpertLife = 11000;
		public const float LifePerExtraPlayer = 0.35f;
		public const int BaseDefense = 14;
		public const int TrainDamage = 150, BoltDamage = 60;        // the train head on; a wagon GhostTrain.CarDamageScale
		public const float EnrageLifeFraction = 0.5f;
		public const float FuryDamage = 1.5f;
		public const float Whistle1 = 0.7f, Whistle2 = 0.4f, Whistle3 = 0.1f;   // user-set: every 30% of his life gone

		// --- the float and the fight ------------------------------------------------------------------------------------
		public const int HitboxWidth = R.BodyRight - R.BodyLeft;
		public const int HitboxHeight = R.BodyBottom - R.BodyTop;      // the coat, head and cap, and the turbine under them
		public const int RigShiftX = (R.BodyLeft + R.BodyRight) / 2;   // the hitbox's middle from the rig origin (facing left)
		public const float HoverOffsetX = 16f * 16f, HoverOffsetY = -9f * 16f;
		public const float HoverSpeed = 7f, EnragedHoverSpeed = 9f, AttackDrift = 2.5f;
		public const float HoverAccel = 0.08f;
		public const float FightRange = 125f * 16f;
		public const int RespawnGraceTicks = 90;
		public const int ResyncInterval = 60;
		public const float DespawnRange = 250f * 16f;
		public const int LeaveGraceTicks = 180;
		public const int CheckInterval = 10;

		// --- the passive trains ----------------------------------------------------------------------------------------
		public const int PassiveInterval = 180, EnragedPassiveInterval = 120, FuryPassiveInterval = 90;   // user-set: 3 s, 2 s
		public const int PassiveTelegraph = 60, EnragedPassiveTelegraph = 42, FuryPassiveTelegraph = 36;   // user-set: 1 s, 0.7 s
		public const float PassiveSpeed = 24f;
		public const float ScreenHalfWidth = 960f, ScreenHalfHeight = 540f;   // vanilla's 1920x1080 (NPC.sWidth, NPC.sHeight)
		public const byte KindExpress = 0, KindDive = 1;

		// --- the lantern -----------------------------------------------------------------------------------------------
		public const int LanternInterval = 90, FuryLanternInterval = 60;     // user-set: every 1.5 s
		public const int ThrowWindup = 30, ThrowRelease = 10, ThrowRecover = 10;
		public const int ThrowTicks = ThrowWindup + ThrowRelease + ThrowRecover;
		public const int Bolts = 3, EnragedBolts = 5;
		public const float BoltSpread = 0.38f, BoltSpeed = 8.5f;               // 22 degrees apart (it was 11: "too tight")

		// --- the loop --------------------------------------------------------------------------------------------------
		public const int LoopFirstTicks = 600, LoopIntervalMin = 1080, LoopIntervalMax = 1440;
		public const int LoopTelegraph = 60;
		public const float LoopRadius = 22f * 16f, LoopSpeed = 21f, LoopApproach = 60f * 16f;   // 21: "a bit faster" (was 18)
		public const int LoopEnter = (int)(LoopApproach / LoopSpeed);
		public const int LapTicks = (int)(MathHelper.TwoPi * LoopRadius / LoopSpeed);
		public const int LoopRun = (int)(GhostTrain.LoopLaps * LapTicks);
		public const int LoopTicks = LoopTelegraph + LoopEnter + LoopRun + (int)(GhostTrain.Length / LoopSpeed) + 10;
		public const float LoopGhostRadius = LoopRadius * 0.6f;
		public const int LoopGhostDelay = 40;

		// --- the whistle -----------------------------------------------------------------------------------------------
		public const int WhistleTicks = 420;                                 // user-set: immune for 7 s
		public const int WavePass1 = 30, WavePass2 = 225, WaveTelegraph = 45;  // the two waves fill 6.5 s (user-set)
		public const float WaveSpeed = 17f;
		public const int GroundGhostInterval = 60, GroundGhostDelay = 45;      // user-set: a ghost a second
		public const float GroundGhostReach = 25f * 16f;

		// --- the ghosts ------------------------------------------------------------------------------------------------
		public const int MaxGhosts = 8;
		public const int RiftDelay = 90;                                     // user-set: 1.5 s after a bolt lands

		// --- intro, leaving, death ------------------------------------------------------------------------------------
		public const int IntroTicks = 180, FadeTicks = 60;
		public const int TitleTick = 70, TitleHoldTicks = IntroTicks - TitleTick + 45;
		public const int TipStart = 72, TipRaise = 90, TipBow = 118, TipEnd = 146;
		public const int LeaveTicks = 60;
		public const int DeathTicks = 240;
		public const int FarewellTick = 96;                  // the last train is sent for him...
		public const float FarewellReach = 40f * 16f, FarewellSpeed = 16f;
		public const int PickupTick = FarewellTick + (int)(FarewellReach / FarewellSpeed);   // ...and blows him to bits here
		public const int CameraEaseTicks = 30;
		public const float CameraLockRange = 150f * 16f;

		private const int FlagEnraged = 0, FlagFury = 1, FlagWhistle1 = 2;

		private static LocalizedText epithet;

		private Phase CurrentPhase => (Phase)State;
		public bool Enraged => Flag(FlagEnraged);
		public bool Furious => Flag(FlagFury);
		private ref float Side => ref NPC.ai[2];

		// synced (SendExtraAI)
		private Vector2 locked;                              // the loop's centre, or the wave pass's point
		private int passiveTick = -1;
		private byte passiveKind, passiveLength;
		private sbyte passiveDir = 1;
		private Vector2 passivePoint;
		private int throwTick = -1;
		private byte throwTarget = 255, loopTarget = 255;
		private float wavePhase;
		// the server's own clocks
		private int passiveClock, lanternClock, loopClock, nextLoop = LoopFirstTicks, absentTicks;
		private bool playerScaled;

		protected override int DyingState => (int)Phase.Dying;
		protected override int DeathAnimationTicks => DeathTicks;

		/// <summary>The rig origin (under his turbine's exhaust bell) in the world.</summary>
		public Vector2 RigOrigin => new(NPC.Center.X + RigShiftX * NPC.spriteDirection, NPC.Bottom.Y - R.BodyBottom);

		/// <summary>An art point (game px from the origin, facing left) in the world.</summary>
		public Vector2 RigPoint(int x, int y) => RigOrigin + new Vector2(NPC.spriteDirection == 1 ? -x : x, y);

		public Vector2 CameraFocus => NPC.Center;

		/// <summary>Gone from sight: blown to bits by the last train.</summary>
		public bool Hidden => CurrentPhase == Phase.Dying && Timer >= PickupTick;

		private bool Flag(int bit) => ((int)NPC.ai[3] & (1 << bit)) != 0;

		private void SetFlag(int bit, bool on) {
			int f = (int)NPC.ai[3];
			int g = on ? f | (1 << bit) : f & ~(1 << bit);
			if (g != f) {
				NPC.ai[3] = g;
				NPC.netUpdate = true;
			}
		}

		private float DamageScale => Furious ? FuryDamage : 1f;
		private int PassiveIntervalNow => Furious ? FuryPassiveInterval : Enraged ? EnragedPassiveInterval : PassiveInterval;
		private int PassiveTelegraphNow => Furious ? FuryPassiveTelegraph : Enraged ? EnragedPassiveTelegraph : PassiveTelegraph;
		private int LanternIntervalNow => Furious ? FuryLanternInterval : LanternInterval;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 1;
			NPCID.Sets.MPAllowedEnemies[Type] = true;
			NPCID.Sets.BossBestiaryPriority.Add(Type);
			CogpunkSets.Mechanical[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;    // a machine, and a ghost
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Venom] = true;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() {
				Scale = 0.65f,
				PortraitScale = 0.75f,
				PortraitPositionYOverride = 16f,
			});
			epithet = this.GetLocalization("Epithet");
			LoadVisuals();
		}

		public override void Unload() {
			epithet = null;
			UnloadVisuals();
		}

		public override void SetDefaults() {
			NPC.width = HitboxWidth;
			NPC.height = HitboxHeight;
			NPC.lifeMax = ExpertStats.Base(ExpertLife);
			NPC.defense = BaseDefense;
			NPC.damage = 0;                                   // no contact damage (user-set 2026-11-05)
			NPC.knockBackResist = 0f;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath6;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.boss = true;
			NPC.npcSlots = 10f;
			NPC.aiStyle = -1;
			NPC.value = Item.buyPrice(gold: 8);               // the Wall of Flesh's 8 gold (terraria.wiki.gg)
			NPC.SpawnWithHigherTime(30);
			if (!Main.dedServ) {
				Music = MusicID.Boss3;
			}
		}

		/// <summary>Expert lands exactly on <see cref="ExpertLife"/>; Master keeps vanilla's boss adjustment; +35% life per
		/// extra player (as the other Cogpunk bosses). No contact damage to scale.</summary>
		public override void ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment) {
			NPC.lifeMax = (int)Math.Round(ExpertStats.Snap(NPC.lifeMax, ExpertLife) * bossAdjustment * PlayerFactor(numPlayers));
			NPC.damage = 0;
			playerScaled = true;
		}

		public static float PlayerFactor(int players) => 1f + LifePerExtraPlayer * Math.Max(0, players - 1);

		/// <summary>Server or singleplayer: Classic player scaling, and he materializes beside the player who blew the whistle
		/// (vanilla's <c>NPC.SpawnOnPlayer</c> puts a boss off screen and announces it, decompiled <c>NPC.SpawnBoss</c>).</summary>
		public override void OnSpawn(IEntitySource source) {
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}
			if (!playerScaled) {
				int players = Math.Max(1, NPC.GetActivePlayerCount());
				NPC.lifeMax = (int)Math.Round(NPC.lifeMax * PlayerFactor(players));
				NPC.life = NPC.lifeMax;
				playerScaled = true;
			}
			NPC.TargetClosest(false);
			Player target = TargetPlayer;
			Side = target != null && Main.rand.NextBool() ? -1f : 1f;
			if (target != null) {
				NPC.Center = target.Center + new Vector2(Side * HoverOffsetX, HoverOffsetY);
			}
			FaceTarget();
			NPC.velocity = Vector2.Zero;
			NPC.netUpdate = true;
		}

		public override void SendExtraAI(BinaryWriter writer) {
			writer.Write(NPC.lifeMax);
			writer.Write(NPC.life >= NPC.lifeMax);
			writer.Write(locked.X);
			writer.Write(locked.Y);
			writer.Write((short)Math.Clamp(passiveTick, -1, short.MaxValue));
			writer.Write(passiveKind);
			writer.Write(passiveLength);
			writer.Write(passiveDir);
			writer.Write(passivePoint.X);
			writer.Write(passivePoint.Y);
			writer.Write((short)Math.Clamp(throwTick, -1, short.MaxValue));
			writer.Write(throwTarget);
			writer.Write(loopTarget);
			writer.Write(wavePhase);
		}

		public override void ReceiveExtraAI(BinaryReader reader) {
			int lifeMax = reader.ReadInt32();
			bool full = reader.ReadBoolean();
			float x = reader.ReadSingle();
			float y = reader.ReadSingle();
			passiveTick = reader.ReadInt16();
			passiveKind = reader.ReadByte();
			passiveLength = reader.ReadByte();
			passiveDir = reader.ReadSByte();
			float px = reader.ReadSingle();
			float py = reader.ReadSingle();
			throwTick = reader.ReadInt16();
			throwTarget = reader.ReadByte();
			loopTarget = reader.ReadByte();
			wavePhase = reader.ReadSingle();
			if (lifeMax > 0 && lifeMax != NPC.lifeMax) {
				NPC.lifeMax = lifeMax;
				if (full) {
					NPC.life = lifeMax;
				}
			}
			locked = float.IsFinite(x) && float.IsFinite(y) ? new Vector2(x, y) : Vector2.Zero;
			passivePoint = float.IsFinite(px) && float.IsFinite(py) ? new Vector2(px, py) : Vector2.Zero;
			if (!float.IsFinite(wavePhase)) {
				wavePhase = 0f;
			}
			if (passiveDir == 0) {
				passiveDir = 1;
			}
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				ModContent.GetInstance<OldBrassTownBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		/// <summary>A bag per player in Expert/Master (vanilla <c>ItemDropRule.BossBag</c>), its contents in Classic
		/// (<see cref="CursedConductorLoot"/>).</summary>
		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.BossBag(ModContent.ItemType<CursedConductorBag>()));
			LeadingConditionRule classic = new(new Conditions.NotExpert());
			CursedConductorLoot.AddClassic(classic);
			npcLoot.Add(classic);
		}

		public override void BossLoot(ref int potionType) {
			potionType = ItemID.HealingPotion;             // the Wall of Flesh's tier
		}

		/// <summary>He never touches anyone (user-set 2026-11-05: "should not cause contact damage").</summary>
		public override bool CanHitPlayer(Player target, ref int cooldownSlot) => false;

		public override void OnKill() {
			NPC.SetEventFlagCleared(ref CursedConductorSystem.DownedFlag, -1);
		}

		public override void BossHeadSlot(ref int index) {
			if (Hidden) {
				index = -1;
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// State machine (every side; only the server changes state)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>Can't be hurt: materializing, blowing the whistle (user-set: immune 7 s), fading away, dying.</summary>
		private bool Untouchable => CurrentPhase == Phase.Intro || CurrentPhase == Phase.Whistle || CurrentPhase == Phase.Leaving
			|| CurrentPhase == Phase.Dying;

		protected override void UpdateBoss() {
			if (!Main.dedServ) {
				ResetEffectKeys();
			}
			NPC.dontTakeDamage = Untouchable;
			if (throwTick >= 0) {
				throwTick++;
			}
			if (passiveTick >= 0) {
				passiveTick++;
			}
			switch (CurrentPhase) {
				case Phase.Intro:
					NPC.velocity *= 0.9f;
					FaceTarget();
					if (Timer >= IntroTicks && IsAuthority && Retarget()) {
						StartHover();
					}
					break;
				case Phase.Hover:
					DoHover();
					break;
				case Phase.Loop:
					Drift(throwTick >= 0 ? AttackDrift : HoverSpeed);
					DoLoop();
					break;
				case Phase.Whistle:
					NPC.velocity *= 0.85f;
					FaceTarget();
					DoWhistle();
					break;
				case Phase.Leaving:
					NPC.velocity *= 0.9f;
					if (Timer >= LeaveTicks && IsAuthority) {
						NPC.active = false;
						if (Main.netMode == NetmodeID.Server) {
							NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
						}
					}
					break;
				case Phase.Dying:
					NPC.velocity *= 0.85f;
					DoDeath();
					UpdateDeath();
					break;
				default:
					StartHover();                              // an unknown state from a newer version (D0)
					break;
			}
			if (CurrentPhase == Phase.Hover || CurrentPhase == Phase.Loop) {
				UpdateThrow();
			}
			if (CurrentPhase == Phase.Hover) {
				UpdatePassive();
			}
			else if (passiveTick > PassiveTelegraphMax + 12) {
				passiveTick = -1;
			}
			if (CurrentPhase != Phase.Dying && CurrentPhase != Phase.Leaving && (CurrentPhase != Phase.Intro || Timer >= IntroTicks)) {
				CheckFight();
			}
			KeepInWorld();
			if (!Main.dedServ) {
				StateEffects();
			}
		}

		private const int PassiveTelegraphMax = PassiveTelegraph;

		private void StartHover() {
			if (IsAuthority) {
				ChangeState((int)Phase.Hover);
			}
		}

		/// <summary>He floats to his spot beside and above his target; the server keeps the clocks and starts the loop and
		/// the whistle.</summary>
		private void DoHover() {
			Drift(throwTick >= 0 ? AttackDrift : (Enraged ? EnragedHoverSpeed : HoverSpeed));
			if (!IsAuthority) {
				return;
			}
			if ((int)Timer % ResyncInterval == 0) {
				NPC.netUpdate = true;
				Retarget();
			}
			if (!Enraged && NPC.life <= NPC.lifeMax * EnrageLifeFraction) {
				SetFlag(FlagEnraged, true);                     // the whistle shrieks (StateEffects) and he speeds up for good
			}
			if (WhistleDue()) {
				StartWhistle();
				return;
			}
			loopClock++;
			if (loopClock >= nextLoop && passiveTick < 0 && throwTick < 0) {
				StartLoop();
			}
		}

		private Vector2 HoverSpot(Player target) => target.Center + new Vector2((Side == 0f ? 1f : Side) * HoverOffsetX, HoverOffsetY);

		private void Drift(float speed) {
			Player target = TargetPlayer;
			FaceTarget();
			if (target != null) {
				MoveToward(HoverSpot(target), speed);
			}
			else {
				NPC.velocity *= 0.9f;
			}
		}

		private void MoveToward(Vector2 spot, float maxSpeed) {
			Vector2 to = spot - NPC.Center;
			float distance = to.Length();
			Vector2 want = distance > 1f ? to / distance * Math.Min(maxSpeed, distance * 0.06f) : Vector2.Zero;
			NPC.velocity += (want - NPC.velocity) * HoverAccel;
		}

		// --- the lantern: his main attack, every 1.5 s (a sub-action: it runs over the hover and the loop) ------------------

		private void UpdateThrow() {
			if (throwTick < 0) {
				if (!IsAuthority) {
					return;
				}
				lanternClock++;
				if (lanternClock < LanternIntervalNow) {
					return;
				}
				Player target = ClosestFighter(true);
				if (target == null) {
					lanternClock = LanternIntervalNow - 15;    // nobody to throw at (only the trapped player): look again soon
					return;
				}
				throwTarget = (byte)target.whoAmI;
				throwTick = 0;
				lanternClock = 0;
				NPC.netUpdate = true;
				return;
			}
			if (IsAuthority && throwTick == ThrowWindup) {
				ThrowBolts();
			}
			if (throwTick >= ThrowTicks) {
				throwTick = -1;
			}
		}

		/// <summary>Server: a fan of straight cursed bolts from the lantern overhead at the throw's target (never the player in
		/// the loop).</summary>
		private void ThrowBolts() {
			Player target = throwTarget < Main.maxPlayers && IsFighter(Main.player[throwTarget]) && throwTarget != loopTarget
				? Main.player[throwTarget] : ClosestFighter(true);
			if (target == null) {
				return;
			}
			Vector2 from = RigPoint(R.ThrowX, R.ThrowY);
			Vector2 aim = (target.Center - from).SafeNormalize(Vector2.UnitY) * BoltSpeed;
			int count = Enraged || Furious ? EnragedBolts : Bolts;
			int damage = ExpertStats.HostileProjectile(NPC, BoltDamage * DamageScale);
			int type = ModContent.ProjectileType<ConductorFlame>();
			for (int k = 0; k < count; k++) {
				float turn = (k - (count - 1) * 0.5f) * BoltSpread;
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, aim.RotatedBy(turn), type, damage, 0f, out _, ai0: Furious ? 1f : 0f);
			}
		}

		// --- the passive trains: every 3 s at the farthest fighter, with no gesture ---------------------------------------

		private void UpdatePassive() {
			if (passiveTick < 0) {
				if (!IsAuthority) {
					return;
				}
				passiveClock++;
				if (passiveClock >= PassiveIntervalNow - PassiveTelegraphNow) {
					StartPassive();
				}
				return;
			}
			if (IsAuthority && passiveTick == passiveLength) {
				LaunchPassive();
			}
			if (passiveTick > passiveLength + 12) {
				passiveTick = -1;
			}
		}

		/// <summary>Server: the warning starts: the farthest fighter's row (an Express towards him) or column (a Dive, down or
		/// up), locked now.</summary>
		private void StartPassive() {
			Player target = FarthestFighter();
			if (target == null) {
				passiveClock = 0;
				return;
			}
			passivePoint = target.Center;
			passiveLength = (byte)PassiveTelegraphNow;
			if (Main.rand.NextBool()) {
				passiveKind = KindExpress;
				float dx = NPC.Center.X - target.Center.X;
				passiveDir = (sbyte)(Math.Abs(dx) < 1f ? (Main.rand.NextBool() ? 1 : -1) : Math.Sign(dx));   // towards him
			}
			else {
				passiveKind = KindDive;
				passiveDir = (sbyte)(Main.rand.NextBool() ? 1 : -1);                                       // down or up
			}
			passiveTick = 0;
			NPC.netUpdate = true;
		}

		/// <summary>Server: the train, from the screen edge away from him (an Express) or from the top or the bottom (a
		/// Dive), across that player's screen.</summary>
		private void LaunchPassive() {
			Vector2 p = passivePoint;
			if (passiveKind == KindExpress) {
				SendTrain(new Vector2(p.X - passiveDir * ScreenHalfWidth, p.Y), new Vector2(passiveDir * PassiveSpeed, 0f), GhostTrain.Route.Express,
					2f * ScreenHalfWidth);
			}
			else {
				SendTrain(new Vector2(p.X, p.Y - passiveDir * ScreenHalfHeight), new Vector2(0f, passiveDir * PassiveSpeed), GhostTrain.Route.Dive,
					2f * ScreenHalfHeight);
			}
			passiveClock = 0;
		}

		/// <summary>The passive train's entry and exit (world px) and how strong its warning is now (0 when none).</summary>
		public bool PassiveTelegraphNowFor(out Vector2 entry, out Vector2 exit, out bool express, out float strength) {
			express = passiveKind == KindExpress;
			Vector2 p = passivePoint;
			entry = express ? new Vector2(p.X - passiveDir * ScreenHalfWidth, p.Y) : new Vector2(p.X, p.Y - passiveDir * ScreenHalfHeight);
			exit = express ? new Vector2(p.X + passiveDir * ScreenHalfWidth, p.Y) : new Vector2(p.X, p.Y + passiveDir * ScreenHalfHeight);
			strength = passiveTick < 0 || passivePoint == Vector2.Zero ? 0f : TelegraphStrength(passiveTick, Math.Max(1, (int)passiveLength));
			return strength > 0f;
		}

		// --- the loop: a random fighter circled for 3 laps, two ghosts a lap ---------------------------------------------

		private void StartLoop() {
			Player target = RandomFighter();
			loopClock = 0;
			nextLoop = Main.rand.Next(LoopIntervalMin, LoopIntervalMax + 1);
			if (target == null) {
				return;
			}
			loopTarget = (byte)target.whoAmI;
			locked = target.Center;
			passiveTick = -1;                                  // the train can't run an express or a dive while it loops
			ChangeState((int)Phase.Loop);
			NPC.netUpdate = true;
		}

		private void DoLoop() {
			int t = (int)Timer;
			if (!IsAuthority) {
				return;
			}
			if (t == LoopTelegraph && locked != Vector2.Zero) {
				// in along the ring's top tangent from his side, LoopApproach away
				float side = Side >= 0f ? 1f : -1f;
				Vector2 top = locked - new Vector2(0f, LoopRadius);
				SendTrain(top + new Vector2(side * LoopApproach, 0f), new Vector2(-side * LoopSpeed, 0f), GhostTrain.Route.Loop, 0f, locked);
			}
			for (int lap = 0; lap < (int)GhostTrain.LoopLaps; lap++) {
				if (t == LoopTelegraph + LoopEnter + lap * LapTicks + 4) {
					float a = Main.rand.NextFloat(MathHelper.TwoPi);
					Vector2 off = new Vector2(MathF.Cos(a), MathF.Sin(a)) * LoopGhostRadius;
					OpenRift(NPC.GetSource_FromAI(), locked + off, LoopGhostDelay, Furious);
					OpenRift(NPC.GetSource_FromAI(), locked - off, LoopGhostDelay, Furious);   // the opposite side
				}
			}
			if (t >= LoopTicks) {
				loopTarget = 255;
				locked = Vector2.Zero;
				passiveClock = 0;
				if (Main.rand.NextBool(3)) {
					Side = Side >= 0f ? -1f : 1f;
				}
				StartHover();
				NPC.netUpdate = true;
			}
		}

		// --- the whistle: at 70%, 40% and 10% of his life, immune for 7 s, two waves, ghosts out of the ground --------------

		private bool WhistleDue() {
			float life = NPC.life / (float)Math.Max(1, NPC.lifeMax);
			return (life <= Whistle1 && !Flag(FlagWhistle1)) || (life <= Whistle2 && !Flag(FlagWhistle1 + 1))
				|| (life <= Whistle3 && !Flag(FlagWhistle1 + 2));
		}

		private void StartWhistle() {
			float life = NPC.life / (float)Math.Max(1, NPC.lifeMax);
			if (life <= Whistle1) {
				SetFlag(FlagWhistle1, true);
			}
			if (life <= Whistle2) {
				SetFlag(FlagWhistle1 + 1, true);               // a burst past two marks blows the whistle once
			}
			if (life <= Whistle3) {
				SetFlag(FlagWhistle1 + 2, true);
			}
			throwTick = -1;
			passiveTick = -1;
			loopTarget = 255;
			locked = Vector2.Zero;
			ChangeState((int)Phase.Whistle);
			NPC.netUpdate = true;
		}

		/// <summary>The wave pass in progress (0 / 1), and its ticks from its start; false outside both.</summary>
		public static bool WavePass(int t, out int pass, out int local) {
			pass = t >= WavePass2 ? 1 : 0;
			local = t - (pass == 0 ? WavePass1 : WavePass2);
			return t >= WavePass1 && local >= 0 && local < WavePass2 - WavePass1;
		}

		private void DoWhistle() {
			int t = (int)Timer;
			if (!IsAuthority) {
				return;
			}
			if (t == WavePass1 || t == WavePass2) {
				Player target = RandomFighter();
				if (target != null) {
					locked = target.Center;
					wavePhase = Main.rand.NextFloat(MathHelper.TwoPi);
					NPC.netUpdate = true;
				}
			}
			if ((t == WavePass1 + WaveTelegraph || t == WavePass2 + WaveTelegraph) && locked != Vector2.Zero) {
				float dir = t < WavePass2 ? 1f : -1f;          // left to right, then right to left (user-set)
				Vector2 from = new(locked.X - dir * ScreenHalfWidth, locked.Y + GhostTrain.WaveAmplitude * MathF.Sin(wavePhase));
				SendTrain(from, new Vector2(dir * WaveSpeed, 0f), GhostTrain.Route.Wave, 2f * ScreenHalfWidth, new Vector2(0f, wavePhase));
			}
			if (t >= WavePass1 && t < WhistleTicks - 30 && (t - WavePass1) % GroundGhostInterval == 0) {
				GroundGhost();
			}
			if (t >= WhistleTicks) {
				locked = Vector2.Zero;
				passiveClock = 0;
				lanternClock = 0;
				StartHover();
				NPC.netUpdate = true;
			}
		}

		/// <summary>Server: a rift on the ground near a random fighter (the surface found by a bounded scan down from above
		/// them, D0: <see cref="TileSafety"/>).</summary>
		private void GroundGhost() {
			Player target = RandomFighter();
			if (target == null) {
				return;
			}
			float x = target.Center.X + Main.rand.NextFloat(-GroundGhostReach, GroundGhostReach);
			int tx = (int)(x / 16f);
			int ty0 = (int)(target.Center.Y / 16f) - 12;
			Vector2 at = new(x, target.Center.Y + 4f * 16f);
			for (int ty = ty0; ty < ty0 + 40; ty++) {
				if (TileSafety.TryGetTile(tx, ty, out Tile tile) && tile.HasTile && Main.tileSolid[tile.TileType]
					&& TileSafety.TryGetTile(tx, ty - 1, out Tile above) && !(above.HasTile && Main.tileSolid[above.TileType])) {
					at = new Vector2(tx * 16f + 8f, ty * 16f - 10f);
					break;
				}
			}
			OpenRift(NPC.GetSource_FromAI(), at, GroundGhostDelay, Furious);
		}

		// --- trains, rifts and ghosts -------------------------------------------------------------------------------------

		/// <summary>Server: one ghost train (D0: through <see cref="SafeSpawn"/>, refused rather than overwriting).
		/// <paramref name="extra"/>: the loop's centre, or (0, phase) for a wave.</summary>
		private void SendTrain(Vector2 from, Vector2 velocity, GhostTrain.Route route, float distance, Vector2 extra = default) {
			int damage = route == GhostTrain.Route.Farewell ? 0 : ExpertStats.HostileProjectile(NPC, TrainDamage * DamageScale);
			float ai1 = route == GhostTrain.Route.Loop ? extra.X : distance;
			float ai2 = route == GhostTrain.Route.Loop ? extra.Y : route == GhostTrain.Route.Wave ? extra.Y : 0f;
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, velocity, ModContent.ProjectileType<GhostTrain>(), damage, 0f, out _,
				ai0: (float)route, ai1: ai1, ai2: ai2);
		}

		/// <summary>Server: a ghost rift (a ghost rises from it after <paramref name="delay"/> ticks), while the ghosts are under
		/// their cap.</summary>
		public static void OpenRift(IEntitySource source, Vector2 at, int delay, bool furious) {
			if (Main.netMode == NetmodeID.MultiplayerClient || !MathSafety.IsFinite(at) || GhostRoom(-1) <= 0) {
				return;
			}
			SafeSpawn.TryNewProjectile(source, at, Vector2.Zero, ModContent.ProjectileType<GhostRift>(), 0, 0f, out _, ai0: delay,
				ai1: furious ? 1f : 0f);
		}

		/// <summary>How many more ghosts may come (<see cref="MaxGhosts"/> less those alive and those still rising), not
		/// counting the rift <paramref name="exceptRift"/>.</summary>
		public static int GhostRoom(int exceptRift) {
			int count = 0;
			int ghost = ModContent.NPCType<ConductorGhost>();
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.type == ghost) {
					count++;
				}
			}
			int rift = ModContent.ProjectileType<GhostRift>();
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == rift && p.whoAmI != exceptRift) {
					count++;
				}
			}
			return MaxGhosts - count;
		}

		// --- the death: the last train comes for him ------------------------------------------------------------------

		protected override void OnDeathStarted() {
			locked = Vector2.Zero;
			throwTick = -1;
			passiveTick = -1;
			loopTarget = 255;
			NPC.netUpdate = true;
		}

		private void DoDeath() {
			if (!IsAuthority || (int)Timer != FarewellTick) {
				return;
			}
			float side = Side >= 0f ? 1f : -1f;
			SendTrain(new Vector2(NPC.Center.X + side * FarewellReach, NPC.Center.Y), new Vector2(-side * FarewellSpeed, 0f), GhostTrain.Route.Farewell,
				FarewellReach);
		}

		// --- fighters and targeting -----------------------------------------------------------------------------------

		private Player TargetPlayer => NPC.target >= 0 && NPC.target < Main.maxPlayers && Main.player[NPC.target].active && !Main.player[NPC.target].dead
			? Main.player[NPC.target] : null;

		/// <summary>In the fight: alive for <see cref="RespawnGraceTicks"/> and within <see cref="FightRange"/> of him.</summary>
		public bool IsFighter(Player player) => player != null && player.active && !player.dead
			&& player.GetModPlayer<ConductorFightPlayer>().AliveTicks >= RespawnGraceTicks
			&& Vector2.DistanceSquared(player.Center, NPC.Center) <= FightRange * FightRange;

		/// <summary>The closest fighter (those in the town first); with <paramref name="notLooped"/>, never the player the
		/// loop has trapped.</summary>
		private Player ClosestFighter(bool notLooped) {
			Player best = null;
			float bestScore = float.MaxValue;
			foreach (Player player in Main.ActivePlayers) {
				if (!IsFighter(player) || (notLooped && player.whoAmI == loopTarget)) {
					continue;
				}
				float d = Vector2.DistanceSquared(player.Center, NPC.Center);
				float score = !OldBrassTownSystem.Exists || OldBrassTownSystem.Contains(player.Center) ? d : d * 4f;
				if (score < bestScore) {
					bestScore = score;
					best = player;
				}
			}
			return best;
		}

		private Player FarthestFighter() {
			Player best = null;
			float bestD = -1f;
			foreach (Player player in Main.ActivePlayers) {
				if (!IsFighter(player)) {
					continue;
				}
				float d = Vector2.DistanceSquared(player.Center, NPC.Center);
				if (d > bestD) {
					bestD = d;
					best = player;
				}
			}
			return best;
		}

		private Player RandomFighter() {
			int count = 0;
			foreach (Player player in Main.ActivePlayers) {
				if (IsFighter(player)) {
					count++;
				}
			}
			if (count == 0) {
				return null;
			}
			int pick = Main.rand.Next(count);
			foreach (Player player in Main.ActivePlayers) {
				if (IsFighter(player) && pick-- == 0) {
					return player;
				}
			}
			return null;
		}

		/// <summary>Server: the closest fighter becomes the one he floats beside. False when there is none.</summary>
		private bool Retarget() {
			if (!IsAuthority) {
				return true;
			}
			Player best = ClosestFighter(false);
			if (best == null) {
				return false;
			}
			if (best.whoAmI != NPC.target) {
				NPC.target = best.whoAmI;
				NPC.netUpdate = true;
			}
			return true;
		}

		private void FaceTarget() {
			Player target = TargetPlayer;
			if (target != null && Math.Abs(target.Center.X - NPC.Center.X) > 8f) {
				NPC.direction = NPC.spriteDirection = target.Center.X > NPC.Center.X ? 1 : -1;
			}
		}

		/// <summary>Server, every <see cref="CheckInterval"/> ticks: the fury (no fighter inside Old Brass Town: user-set, so
		/// running away doesn't cheese him), and leaving (no living player within <see cref="DespawnRange"/> for
		/// <see cref="LeaveGraceTicks"/>). A world without the town (an old world) never makes him furious.</summary>
		private void CheckFight() {
			if (!IsAuthority || (int)Timer % CheckInterval != 0) {
				return;
			}
			bool anyFighter = false, anyInTown = false, anyNear = false;
			foreach (Player player in Main.ActivePlayers) {
				if (player.dead) {
					continue;
				}
				if (Vector2.DistanceSquared(player.Center, NPC.Center) <= DespawnRange * DespawnRange) {
					anyNear = true;
				}
				if (IsFighter(player)) {
					anyFighter = true;
					if (OldBrassTownSystem.Contains(player.Center)) {
						anyInTown = true;
					}
				}
			}
			SetFlag(FlagFury, OldBrassTownSystem.Exists && anyFighter && !anyInTown);
			absentTicks = anyNear ? 0 : absentTicks + CheckInterval;
			if (absentTicks >= LeaveGraceTicks) {
				absentTicks = 0;
				ChangeState((int)Phase.Leaving);
				NPC.netUpdate = true;
			}
			else if (anyFighter && TargetPlayer == null) {
				Retarget();
			}
		}

		private void KeepInWorld() {
			float min = 60f * 16f, max = (Main.maxTilesX - 60) * 16f;
			float top = 60f * 16f, bottom = (Main.maxTilesY - 60) * 16f;
			Vector2 next = NPC.Center + NPC.velocity;
			if (next.X < min || next.X > max) {
				NPC.velocity.X = 0f;
			}
			if (next.Y < top || next.Y > bottom) {
				NPC.velocity.Y = 0f;
			}
		}
	}
}
