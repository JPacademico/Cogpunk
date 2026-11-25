using System;
using System.IO;
using Cogpunk.Content.Bosses.Fungimancer.Items;
using Cogpunk.Content.Bosses.Fungimancer.NPCs;
using Cogpunk.Content.Bosses.Fungimancer.Projectiles;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.UI;
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
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.Fungimancer.FungimancerRigData;

namespace Cogpunk.Content.Bosses.Fungimancer
{
	/// <summary>
	/// The Fungimancer, the glowing mushroom biome's secret boss (user, 2026-11-19: a magic dumb frog summoned by breaking a rare
	/// Rainbow Mushroom; a floaty boss; Hardmode-intended, Duke Fishron's tier; drops the Fungi Manual). Drawn from the v4 model in
	/// three parallax planes (art/bosses/fungimancer/make_fungimancer_art.py), every pose that model's own parts moved.
	/// <para><b>The fight</b> (user, 2026-11-25, his eight mechanics; the numbers are mine unless quoted):
	/// <list type="number">
	/// <item>Idle, all fight long: a <see cref="FloatyMushroom"/> every <see cref="RainInterval"/> (1 s) drifting down over a
	/// player (never inside blocks); its touch and its 4 x 4 spore cloud confuse.</item>
	/// <item>A burp (<see cref="BurpCooldown"/>, 10 s; over any other attack, an overlay of his throat and mouth): a pink
	/// <see cref="PolymorphBolt"/> that speeds up and homes softly; its hit turns the player into a toadstool for 2.5 s.</item>
	/// <item>Five spores: the hand raised quickly and shaken, five <see cref="RainbowSpore"/>s hang for 1.2 s, then fire one by one
	/// at the target (heavy, confusing).</item>
	/// <item>Idle, all fight long: a <see cref="RainbowLaser"/> every <see cref="LaserInterval"/> (2 s): a diagonal line through a
	/// player, 0.6 s of warning, then the beam.</item>
	/// <item>Six <see cref="OrbitMushroom"/>s circling him for 6 s, then hatching into 1-2 Toadstools each; not again while any
	/// remain.</item>
	/// <item>The channel: he stops, raises both arms (his eyes a spinning rainbow), takes half damage, and a
	/// <see cref="ChannelMushroom"/> grows over his hands for 5 s: destroyed, it stuns him (<see cref="StunTicks"/>); still
	/// standing, it blows up (<see cref="ChannelBlast"/>: the whole screen, a white flash, ringing ears, players stunned 1.5 s).</item>
	/// <item>A fan: the hand shaken, six spores hang for 1.5 s, then burst out in a fan at the target.</item>
	/// <item>A missile: the hand shaken, a <see cref="MushroomMissile"/> hangs for 1.3 s turning to its target, then shoots and
	/// bounces off up to 3 blocks (heavy).</item>
	/// </list>
	/// Between attacks he rests <see cref="Downtime"/> (2 s; 1.5 s under half his life), counted from the moment an attack's last
	/// spell has left (a delayed spell's wait is part of the attack), never the same attack twice running, the channel no more
	/// than once in three. Floaty (BossNPC rules): a lagged drifting hover, into a blade's reach of a melee fighter slowly, no touch
	/// damage.</para>
	/// <para><b>Defeat</b> (user: "he should croack and puff transform into a default terraria frog critter"): dazed, he croaks
	/// (his throat swells), a puff of magic smoke swells over him and, as it clears, a Frog (<c>NPCID.Frog</c>, vanilla's critter)
	/// sits where he was; the camera is held as in his intro, the "Defeated" card shows (BossNPC).</para>
	/// <para><b>Stats</b> (Expert, D3 rule 0; docs/balance/bosses.csv; user, 2026-11-25: "make sure that he is a very strong boss
	/// since its suposed duke fishroom tier"): Duke Fishron (terraria.wiki.gg 1.4.4 Expert: 78000 life, 50 defense; 100 bubble,
	/// 140 contact) + 35% life (the top of the user's 10-35% band: the most mechanics of any Cogpunk boss) = <see cref="ExpertLife"/>,
	/// +35% per extra player; his hits at Fishron's level and above (the heavy and massive ones).</para>
	/// <para>D2: the server decides (attacks, targets, spawns); state and timer in ai[0]/ai[1], the rest in ExtraAI (clocks, the
	/// burp, the downtime, the channel mushroom, the drift); every side counts the clocks between syncs. D0: spawns through
	/// SafeSpawn, scans bounded, indices checked. D1: no allocation per tick.</para>
	/// </summary>
	[AutoloadBossHead]
	public class Fungimancer : BossNPC
	{
		public enum Phase { Intro, Idle, Spores, Orbit, Channel, Fan, Missile, Stunned, Leave, Dying }

		// --- stats (Expert) ------------------------------------------------------------------------------------------------
		public const int ExpertLife = 105300;                             // Duke Fishron's Expert 78000 + 35%
		public const float LifePerExtraPlayer = 0.35f;
		public const int BaseDefense = 50;                                // Duke Fishron's
		public const int RainDamage = 50, CloudDamage = 40, LaserDamage = 110, BurpDamage = 70, SporeDamage = 140, FanDamage = 120,
			MissileDamage = 180, BlastDamage = 360;

		// --- the idle mechanics (user-set intervals) ----------------------------------------------------------------------------
		public const int RainInterval = 60, MaxRain = 10, RainTries = 6;
		public const int LaserInterval = 120;
		public const int BurpCooldown = 600, BurpTicks = 30, BurpRelease = 16;

		// --- the attacks ---------------------------------------------------------------------------------------------------
		public const int Downtime = 120, DowntimeEnraged = 90;            // user-set: 2 s, 1.5 s under half life
		public const float EnrageAt = 0.5f;
		public const int ConjureTick = 30;                                // the hand raised (6) and shaken (24): the spell appears
		public const int SporeCount = 5, SporeHover = 72, SporeGap = 5;   // user-set: 5, 1.2 s
		public const int FanCount = 6, FanDelay = 90;                     // user-set: 6, 1.5 s
		public const float FanSpread = 0.7f;
		public const int MissileDelay = 78;                               // user-set: 1.3 s
		public const int OrbitCount = 6, OrbitTicks = 48, OrbitRelease = 24;
		public const int ChannelRaise = 12, ChannelTicks = 300, ChannelLower = 8;   // user-set: 5 s
		public const float ChannelReduction = 0.5f;                       // user-set: 50% less damage
		public const int StunTicks = 120;

		// --- the float -----------------------------------------------------------------------------------------------------
		public const float HoverX = 12f * 16f, HoverY = 6f * 16f;
		public const float SwayX = 3f * 16f, BobY = 20f, MeleeSwayX = 12f, MeleeBobY = 8f;
		public const float HoverSpeed = 6f, AttackSpeed = 2.5f, HoverAccel = 0.08f, HoverApproach = 0.06f;
		public const float MeleeGap = 14f, MeleeLift = 6f;

		// --- intro, leaving, death -----------------------------------------------------------------------------------------
		public const int IntroTicks = 150, TitleTick = 50, TitleHoldTicks = 140;
		public const int LeaveTicks = 50;
		public const int DeathTicks = 170, CroakStart = 40, PuffTick = 100, PuffFrameTicks = 6, HideTick = PuffTick + 12;
		public const int CameraEaseTicks = 30;
		public const float CameraLockRange = 120f * 16f, FightRange = 150f * 16f;
		public const int CheckInterval = 30, LeaveGrace = 120;
		public const float MaxParallax = 4f;
		private static readonly byte[] IdleCycle = { 0, 1, 2, 3, 4, 1 };

		private static LocalizedText epithet;
		private static Asset<Texture2D> farSheet, nearSheet, glowSheet, burpSheet, eyeSheet, puffSheet;

		public Phase CurrentPhase => (Phase)State;

		// synced (SendExtraAI)
		private byte lastAttack = 255;
		private byte attacksSinceChannel = 9;
		private int rainClock, laserClock, burpClock, downtime;
		private int burpTick = -1;
		private int channelNpc = -1;
		private byte rainTurn, laserTurn;
		// the server's own
		private int absentTicks;
		private bool playerScaled;
		// clients' own
		private int lastOnce = -1;
		private bool titleShown, frogged;

		protected override int DyingState => (int)Phase.Dying;
		protected override int DeathAnimationTicks => DeathTicks;
		protected override int DefeatCardTick => HideTick + 10;
		public override bool Floaty => true;

		public bool Enraged => NPC.life < NPC.lifeMax * EnrageAt;

		/// <summary>He is holding his rainbow mushroom up (its life ends with this).</summary>
		public bool Channeling => CurrentPhase == Phase.Channel && Timer < ChannelRaise + ChannelTicks;

		/// <summary>Where the channel's mushroom stands: between his raised hands, over his head.</summary>
		public Vector2 ChannelPoint {
			get {
				int f = Math.Clamp(BodyFrame(), 0, R.Frames - 1);
				Vector2 a = RigPoint(R.NearX[f], R.NearY[f]), b = RigPoint(R.Near2X[f], R.Near2Y[f]);
				return new Vector2((a.X + b.X) * 0.5f, Math.Min(a.Y, b.Y) - 4f);
			}
		}

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 1;
			NPCID.Sets.MPAllowedEnemies[Type] = true;
			NPCID.Sets.BossBestiaryPriority.Add(Type);
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() {
				Scale = 0.6f,
				PortraitScale = 0.7f,
				PortraitPositionYOverride = 12f,
			});
			epithet = this.GetLocalization("Epithet");
			if (!Main.dedServ) {
				string path = "Cogpunk/Content/Bosses/Fungimancer/Fungimancer";
				farSheet = DepthLayers.RequestOptional(path + "_Far");
				nearSheet = DepthLayers.RequestOptional(path + "_Near");
				glowSheet = DepthLayers.RequestOptional(path + "_Glow");
				burpSheet = DepthLayers.RequestOptional(path + "_Burp");
				eyeSheet = DepthLayers.RequestOptional(path + "_Eyes");
				puffSheet = DepthLayers.RequestOptional(path + "_Puff");
			}
		}

		public override void Unload() {
			epithet = null;
			farSheet = nearSheet = glowSheet = burpSheet = eyeSheet = puffSheet = null;
		}

		public const int HitboxWidth = R.BodyRight - R.BodyLeft, HitboxHeight = -R.BodyTop;

		public override void SetDefaults() {
			NPC.width = HitboxWidth;
			NPC.height = HitboxHeight;
			NPC.lifeMax = ExpertStats.Base(ExpertLife);
			NPC.defense = BaseDefense;
			NPC.damage = 0;                                   // floaty: no contact damage (BossNPC rule)
			NPC.knockBackResist = 0f;
			NPC.HitSound = SoundID.NPCHit13;
			NPC.DeathSound = null;                            // the croak and the puff are his death
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.boss = true;
			NPC.npcSlots = 10f;
			NPC.aiStyle = -1;
			NPC.value = Item.buyPrice(gold: 15);
			NPC.SpawnWithHigherTime(30);
			if (!Main.dedServ) {
				Music = MusicID.Boss3;
			}
		}

		public override void ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment) {
			NPC.lifeMax = (int)Math.Round(ExpertStats.Snap(NPC.lifeMax, ExpertLife) * bossAdjustment * PlayerFactor(numPlayers));
			NPC.damage = 0;
			playerScaled = true;
		}

		public static float PlayerFactor(int players) => 1f + LifePerExtraPlayer * Math.Max(0, players - 1);

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
			NPC.velocity = Vector2.Zero;
			FaceTarget();
			NPC.netUpdate = true;
		}

		public override void SendExtraAI(BinaryWriter writer) {
			writer.Write(NPC.lifeMax);
			writer.Write(NPC.life >= NPC.lifeMax);
			writer.Write(lastAttack);
			writer.Write(attacksSinceChannel);
			writer.Write((short)Math.Clamp(rainClock, 0, short.MaxValue));
			writer.Write((short)Math.Clamp(laserClock, 0, short.MaxValue));
			writer.Write((short)Math.Clamp(burpClock, 0, short.MaxValue));
			writer.Write((short)Math.Clamp(burpTick, -1, short.MaxValue));
			writer.Write((short)Math.Clamp(downtime, 0, short.MaxValue));
			writer.Write((short)Math.Clamp(channelNpc, -1, Main.maxNPCs));
			WriteDrift(writer);
		}

		public override void ReceiveExtraAI(BinaryReader reader) {
			int lifeMax = reader.ReadInt32();
			bool full = reader.ReadBoolean();
			lastAttack = reader.ReadByte();
			attacksSinceChannel = reader.ReadByte();
			rainClock = reader.ReadInt16();
			laserClock = reader.ReadInt16();
			burpClock = reader.ReadInt16();
			burpTick = reader.ReadInt16();
			downtime = reader.ReadInt16();
			channelNpc = reader.ReadInt16();
			ReadDrift(reader);
			if (lifeMax > 0 && lifeMax != NPC.lifeMax) {
				NPC.lifeMax = lifeMax;
				if (full) {
					NPC.life = lifeMax;
				}
			}
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.UndergroundMushroom,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		/// <summary>A bag per player in Expert/Master (vanilla <c>ItemDropRule.BossBag</c>), its contents in Classic; the Fungi
		/// Manual once per player on the first defeat (<see cref="Manuals.ManualDrop"/>).</summary>
		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.BossBag(ModContent.ItemType<FungimancerBag>()));
			npcLoot.Add(Manuals.ManualDrop.Of<Manuals.Items.FungiManual>());
			LeadingConditionRule classic = new(new Conditions.NotExpert());
			FungimancerBag.AddContents(classic);
			npcLoot.Add(classic);
		}

		public override void BossLoot(ref int potionType) {
			potionType = ItemID.GreaterHealingPotion;        // a Hardmode fight (Duke Fishron's tier)
		}

		public override void OnKill() {
			NPC.SetEventFlagCleared(ref FungimancerSystem.DownedFlag, -1);
		}

		public override void BossHeadSlot(ref int index) {
			if (frogged || CurrentPhase == Phase.Leave || (CurrentPhase == Phase.Dying && Timer >= HideTick)) {
				index = -1;
			}
		}

		/// <summary>The channel: his damage is halved while he holds the mushroom up (user-set).</summary>
		public override void ModifyIncomingHit(ref NPC.HitModifiers modifiers) {
			if (Channeling) {
				modifiers.FinalDamage *= 1f - ChannelReduction;
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// The state machine (every side; only the server changes state)
		// ------------------------------------------------------------------------------------------------------------

		private bool Untouchable => CurrentPhase == Phase.Intro || CurrentPhase == Phase.Leave || CurrentPhase == Phase.Dying;

		/// <summary>The rig's origin in the world: under the seat's stalk.</summary>
		public Vector2 Origin => NPC.Bottom;

		private Vector2 RigPoint(int x, int y) => Origin + new Vector2(NPC.spriteDirection == 1 ? -x : x, y);

		public Vector2 MouthWorld => RigPoint(R.MouthX, R.MouthY);

		private Vector2 HandWorld {
			get {
				int f = Math.Clamp(BodyFrame(), 0, R.Frames - 1);
				return RigPoint(R.NearX[f], R.NearY[f]);
			}
		}

		protected override void UpdateBoss() {
			FungimancerSystem.Track(NPC.whoAmI);
			NPC.dontTakeDamage = Untouchable;
			int t = (int)Timer;
			switch (CurrentPhase) {
				case Phase.Intro:
					NPC.velocity *= 0.9f;
					NPC.velocity.Y -= t < 60 ? 0.05f : 0f;       // it rises out of the spores
					FaceTarget();
					if (IsAuthority && t >= IntroTicks) {
						if (EnsureTarget()) {
							downtime = 60;
							ChangeState((int)Phase.Idle);
						}
						else {
							ChangeState((int)Phase.Leave);
						}
					}
					break;
				case Phase.Idle:
					Float(HoverSpeed);
					if (IsAuthority) {
						if (downtime > 0) {
							downtime--;
						}
						else {
							StartAttack();
						}
					}
					break;
				case Phase.Spores:
				case Phase.Fan:
				case Phase.Missile:
					Float(AttackSpeed);
					if (IsAuthority && t == ConjureTick) {
						Conjure(CurrentPhase);
					}
					if (IsAuthority && t >= SpellEnd(CurrentPhase)) {
						EndAttack();
					}
					break;
				case Phase.Orbit:
					Float(AttackSpeed);
					if (IsAuthority && t == OrbitRelease) {
						SummonOrbit();
					}
					if (IsAuthority && t >= OrbitTicks) {
						EndAttack();
					}
					break;
				case Phase.Channel:
					NPC.velocity *= 0.85f;                         // "he stops"
					FaceTarget();
					if (IsAuthority && t == ChannelRaise) {
						GrowMushroom();
					}
					if (IsAuthority && t == ChannelRaise + ChannelTicks) {
						Detonate();
					}
					if (IsAuthority && t >= ChannelRaise + ChannelTicks + ChannelLower) {
						EndAttack();
					}
					break;
				case Phase.Stunned:
					NPC.velocity *= 0.9f;
					NPC.velocity.Y += 0.02f;
					if (IsAuthority && t >= StunTicks) {
						EndAttack();
					}
					break;
				case Phase.Leave:
					NPC.velocity *= 0.9f;
					NPC.velocity.Y += 0.04f;                       // it sinks back into the spores
					NPC.alpha = Math.Min(255, (int)(t * 255f / LeaveTicks));
					if (IsAuthority && t >= LeaveTicks) {
						NPC.active = false;
						if (Main.netMode == NetmodeID.Server) {
							NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
						}
					}
					break;
				case Phase.Dying:
					NPC.velocity *= 0.85f;
					if (IsAuthority && t == HideTick) {
						SafeSpawn.TryNewNPC(NPC.GetSource_FromAI(), (int)NPC.Center.X, (int)NPC.Center.Y + 20, NPCID.Frog, out _);
					}
					UpdateDeath();
					break;
				default:
					if (IsAuthority) {
						ChangeState((int)Phase.Idle);
					}
					break;
			}
			if (CurrentPhase != Phase.Intro && CurrentPhase != Phase.Leave && CurrentPhase != Phase.Dying) {
				IdleMechanics();
				CheckFight();
				TickDrift();
			}
			if (!Main.dedServ) {
				StateEffects(t);
			}
		}

		protected override void OnDeathStarted() {
			burpTick = -1;
			NPC.netUpdate = true;
		}

		// --- the idle mechanics: the mushroom rain, the lasers, the burp ---------------------------------------------------------

		private void IdleMechanics() {
			rainClock++;
			laserClock++;
			if (IsAuthority && rainClock >= RainInterval) {
				rainClock = 0;
				Rain();
			}
			if (IsAuthority && laserClock >= LaserInterval) {
				laserClock = 0;
				Laser();
			}
			if (burpTick >= 0) {
				burpTick++;
				if (IsAuthority && burpTick == BurpRelease) {
					Burp();
				}
				if (burpTick >= BurpTicks) {
					burpTick = -1;
				}
			}
			else {
				burpClock++;
				if (IsAuthority && burpClock >= BurpCooldown && CurrentPhase != Phase.Stunned && CurrentTarget != null) {
					burpClock = 0;
					burpTick = 0;                                  // over whatever he is doing (user: "can be performed on the midle of other attacks")
					NPC.netUpdate = true;
				}
			}
		}

		/// <summary>Server: the next fighter in turn (every player near the fight gets the rain and the lasers in turn: co-op adds
		/// pressure, never focus); the target when alone.</summary>
		private Player NextFighter(ref byte turn) {
			int count = 0;
			foreach (Player p in Main.ActivePlayers) {
				if (!p.dead && Vector2.DistanceSquared(p.Center, NPC.Center) <= FightRange * FightRange) {
					count++;
				}
			}
			if (count == 0) {
				return CurrentTarget;
			}
			int pick = turn++ % count;
			foreach (Player p in Main.ActivePlayers) {
				if (!p.dead && Vector2.DistanceSquared(p.Center, NPC.Center) <= FightRange * FightRange && pick-- == 0) {
					return p;
				}
			}
			return CurrentTarget;
		}

		/// <summary>Server: a falling mushroom over a fighter, at a spot with no block round it (tried <see cref="RainTries"/>
		/// times), at most <see cref="MaxRain"/> of his at once.</summary>
		private void Rain() {
			Player p = NextFighter(ref rainTurn);
			if (p == null) {
				return;
			}
			int type = ModContent.NPCType<FloatyMushroom>(), mine = 0;
			foreach (NPC n in Main.ActiveNPCs) {
				if (n.type == type && (int)n.ai[0] == NPC.whoAmI) {
					mine++;
				}
			}
			if (mine >= MaxRain) {
				return;
			}
			for (int k = 0; k < RainTries; k++) {
				float x = p.Center.X + Main.rand.NextFloat(-18f, 18f) * 16f;
				float y = p.Center.Y - Main.rand.NextFloat(15f, 22f) * 16f;
				int tx = (int)(x / 16f), ty = (int)(y / 16f);
				if (!Core.Safety.TileSafety.InWorld(tx - 2, ty - 2) || !Core.Safety.TileSafety.InWorld(tx + 2, ty + 2)
					|| Collision.SolidCollision(new Vector2(x - 24f, y - 24f), 48, 48)) {
					continue;                                      // never inside a block ("instantaneously burst")
				}
				SafeSpawn.TryNewNPC(NPC.GetSource_FromAI(), (int)x, (int)y + 10, type, out _, ai0: NPC.whoAmI,
					ai1: Main.rand.NextFloat(MathHelper.TwoPi));
				return;
			}
		}

		/// <summary>Server: a diagonal line through a fighter (30-60 degrees from level, either way).</summary>
		private void Laser() {
			Player p = NextFighter(ref laserTurn);
			if (p == null) {
				return;
			}
			float angle = Main.rand.NextFloat(MathHelper.Pi / 6f, MathHelper.Pi / 3f) * (Main.rand.NextBool() ? 1f : -1f);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), p.Center, Vector2.Zero, ModContent.ProjectileType<RainbowLaser>(),
				ExpertStats.HostileProjectile(NPC, LaserDamage), 0f, out _, ai0: angle);
		}

		/// <summary>Server: the burp's bolt from his mouth, off towards the target.</summary>
		private void Burp() {
			Player p = CurrentTarget;
			if (p == null) {
				return;
			}
			Vector2 dir = (p.Center - MouthWorld).SafeNormalize(Vector2.UnitX * NPC.spriteDirection);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), MouthWorld, dir * PolymorphBolt.StartSpeed, ModContent.ProjectileType<PolymorphBolt>(),
				ExpertStats.HostileProjectile(NPC, BurpDamage), 0f, out _, ai0: p.whoAmI);
		}

		// --- the attacks ------------------------------------------------------------------------------------------------

		private void StartAttack() {
			if (!EnsureTarget()) {
				return;
			}
			bool orbitsUp = false;
			int orbit = ModContent.NPCType<OrbitMushroom>();
			foreach (NPC n in Main.ActiveNPCs) {
				if (n.type == orbit && (int)n.ai[0] == NPC.whoAmI) {
					orbitsUp = true;                               // "he cant cast it again if theres still mushrooms arround"
					break;
				}
			}
			Span<byte> options = stackalloc byte[5];
			int count = 0;
			if (lastAttack != (byte)Phase.Spores) {
				options[count++] = (byte)Phase.Spores;
			}
			if (lastAttack != (byte)Phase.Fan) {
				options[count++] = (byte)Phase.Fan;
			}
			if (lastAttack != (byte)Phase.Missile) {
				options[count++] = (byte)Phase.Missile;
			}
			if (!orbitsUp && lastAttack != (byte)Phase.Orbit) {
				options[count++] = (byte)Phase.Orbit;
			}
			if (attacksSinceChannel >= 2 && lastAttack != (byte)Phase.Channel) {
				options[count++] = (byte)Phase.Channel;
			}
			if (count == 0) {
				options[count++] = (byte)Phase.Spores;
			}
			byte pick = options[Main.rand.Next(count)];
			lastAttack = pick;
			attacksSinceChannel = pick == (byte)Phase.Channel ? (byte)0 : (byte)Math.Min(255, attacksSinceChannel + 1);
			ChangeState(pick);
		}

		private void EndAttack() {
			downtime = Enraged ? DowntimeEnraged : Downtime;
			channelNpc = -1;
			ChangeState((int)Phase.Idle);
		}

		/// <summary>The tick a delayed spell's attack ends: its last spell has left the hand.</summary>
		private static int SpellEnd(Phase phase) => phase switch {
			Phase.Spores => ConjureTick + SporeHover + (SporeCount - 1) * SporeGap + 6,
			Phase.Fan => ConjureTick + FanDelay + 6,
			_ => ConjureTick + MissileDelay + 6,
		};

		/// <summary>Server: the delayed spell appears at the shaken hand (it fires itself later: the projectiles count their own age).</summary>
		private void Conjure(Phase phase) {
			Player target = CurrentTarget;
			if (target == null) {
				return;
			}
			Vector2 hand = HandWorld;
			var source = NPC.GetSource_FromAI();
			switch (phase) {
				case Phase.Spores: {
					int damage = ExpertStats.HostileProjectile(NPC, SporeDamage);
					for (int i = 0; i < SporeCount; i++) {
						float a = -MathHelper.PiOver2 + (i - (SporeCount - 1) * 0.5f) * 0.42f;
						Vector2 at = hand + a.ToRotationVector2() * 44f;
						SafeSpawn.TryNewProjectile(source, at, a.ToRotationVector2() * 2f, ModContent.ProjectileType<RainbowSpore>(), damage, 0f, out _,
							ai0: SporeHover + i * SporeGap, ai1: target.whoAmI);
					}
					break;
				}
				case Phase.Fan: {
					int damage = ExpertStats.HostileProjectile(NPC, FanDamage);
					for (int i = 0; i < FanCount; i++) {
						float a = i * MathHelper.TwoPi / FanCount;
						float spread = (i - (FanCount - 1) * 0.5f) * (FanSpread / (FanCount - 1)) * 2f;
						SafeSpawn.TryNewProjectile(source, hand + a.ToRotationVector2() * 14f, Vector2.Zero, ModContent.ProjectileType<RainbowSpore>(),
							damage, 0f, out _, ai0: FanDelay, ai1: target.whoAmI, ai2: spread);
					}
					break;
				}
				default:
					SafeSpawn.TryNewProjectile(source, hand, Vector2.Zero, ModContent.ProjectileType<MushroomMissile>(),
						ExpertStats.HostileProjectile(NPC, MissileDamage), 0f, out _, ai0: MissileDelay, ai1: target.whoAmI);
					break;
			}
		}

		/// <summary>Server: six toadstool caps round him, a sixth of a turn apart.</summary>
		private void SummonOrbit() {
			int type = ModContent.NPCType<OrbitMushroom>();
			for (int i = 0; i < OrbitCount; i++) {
				float a = i * MathHelper.TwoPi / OrbitCount;
				Vector2 at = NPC.Center + a.ToRotationVector2() * OrbitMushroom.Radius;
				SafeSpawn.TryNewNPC(NPC.GetSource_FromAI(), (int)at.X, (int)at.Y + 14, type, out _, ai0: NPC.whoAmI, ai1: a);
			}
		}

		/// <summary>Server: the channel's mushroom over his raised hands.</summary>
		private void GrowMushroom() {
			Vector2 at = ChannelPoint;
			if (SafeSpawn.TryNewNPC(NPC.GetSource_FromAI(), (int)at.X, (int)at.Y, ModContent.NPCType<ChannelMushroom>(), out NPC m, ai0: NPC.whoAmI)) {
				channelNpc = m.whoAmI;
				NPC.netUpdate = true;
			}
		}

		private NPC ChannelMushroomNpc => channelNpc >= 0 && channelNpc < Main.maxNPCs && Main.npc[channelNpc].active
			&& Main.npc[channelNpc].ModNPC is ChannelMushroom ? Main.npc[channelNpc] : null;

		/// <summary>Server: the channel ran out with the mushroom standing: it blows up (and is gone).</summary>
		private void Detonate() {
			NPC m = ChannelMushroomNpc;
			if (m == null) {
				return;
			}
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), m.Center, Vector2.Zero, ModContent.ProjectileType<ChannelBlast>(),
				ExpertStats.HostileProjectile(NPC, BlastDamage), 0f, out _, critical: true);
			m.life = 0;
			m.active = false;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: m.whoAmI);
			}
			channelNpc = -1;
		}

		/// <summary>The server, from the channel mushroom's death: the players destroyed it in time; he is stunned.</summary>
		public void MushroomDestroyed() {
			if (!IsAuthority || CurrentPhase != Phase.Channel) {
				return;
			}
			channelNpc = -1;
			ChangeState((int)Phase.Stunned);
		}

		// --- the float -----------------------------------------------------------------------------------------------------

		private void FaceTarget() {
			Player target = CurrentTarget;
			if (target != null && Math.Abs(target.Center.X - NPC.Center.X) > 8f) {
				NPC.direction = NPC.spriteDirection = target.Center.X > NPC.Center.X ? 1 : -1;
			}
		}

		/// <summary>Every side: it eases to its spot beside and above its target (at a melee fighter's side, close in), round a
		/// point that follows the target with a lag and sways (BossNPC's floaty rules); into the melee hover it slides over 1.5 s
		/// and tracks slowly (BossNPC's melee approach, user 2026-11-25).</summary>
		private void Float(float speed) {
			Player target = CurrentTarget;
			FaceTarget();
			if (target == null) {
				NPC.velocity *= 0.92f;
				return;
			}
			TickMeleeBlend(MeleeFocus.Of(target));
			Vector2 focus = FloatFocus(target);
			float side = NPC.Center.X < focus.X ? -1f : 1f;
			Vector2 near = new(focus.X + side * (target.width * 0.5f + MeleeGap + NPC.width * 0.5f + DriftSway * MeleeSwayX),
				focus.Y + target.height * 0.5f - MeleeLift - NPC.height * 0.5f + DriftBob * MeleeBobY);
			Vector2 far = focus + new Vector2(side * HoverX + DriftSway * SwayX, -HoverY + DriftBob * BobY);
			FloatSteer(Vector2.Lerp(far, near, MeleeAmount), speed, HoverApproach, HoverAccel);
			if (IsAuthority && (int)Timer % 45 == 0) {
				NPC.netUpdate = true;
			}
		}

		protected override bool CanTarget(Player player) {
			return player != null && player.active && !player.dead && Vector2.DistanceSquared(player.Center, NPC.Center) <= FightRange * FightRange;
		}

		/// <summary>Server, every <see cref="CheckInterval"/> ticks: no living player in the glowing mushroom biome near it for
		/// <see cref="LeaveGrace"/> ticks (BossNPC rule: bosses leave when their biome is left) and it sinks back into the spores.</summary>
		private void CheckFight() {
			if (!IsAuthority || (int)Timer % CheckInterval != 0) {
				return;
			}
			bool anyIn = false;
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && player.ZoneGlowshroom && Vector2.DistanceSquared(player.Center, NPC.Center) <= FightRange * FightRange) {
					anyIn = true;
					break;
				}
			}
			absentTicks = anyIn ? 0 : absentTicks + CheckInterval;
			if (absentTicks >= LeaveGrace || (!anyIn && !EnsureTarget())) {
				absentTicks = 0;
				ChangeState((int)Phase.Leave);
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Looks (clients)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>The delayed spells' hand: up in 6 ticks, shaken for 24 (a frame every 3), let go, lowered, then resting.</summary>
		private int CastFrame(int t) {
			if (t < 3) {
				return R.Raise;
			}
			if (t < 6) {
				return R.Raise + 1;
			}
			if (t < ConjureTick) {
				return R.Shake + (t - 6) / 3 % R.ShakeFrames;
			}
			if (t < ConjureTick + 4) {
				return R.Release;
			}
			if (t < ConjureTick + 10) {
				return R.Lower;
			}
			return IdleFrame();
		}

		private int IdleFrame() {
			int clock = (int)(Main.GameUpdateCount + NPC.whoAmI * 37);
			if (clock % 200 < 8) {
				return R.Idle + 5;                                  // a blink
			}
			return R.Idle + IdleCycle[clock / 10 % IdleCycle.Length];
		}

		/// <summary>The body frame for the synced state and timer.</summary>
		public int BodyFrame() {
			int t = (int)Timer;
			switch (CurrentPhase) {
				case Phase.Spores:
				case Phase.Fan:
				case Phase.Missile:
					return CastFrame(t);
				case Phase.Orbit:                                   // the summoning gesture: wind-up, raise, gather | fling, follow-through
					return R.Cast + (t < 6 ? 0 : t < 14 ? 1 : t < OrbitRelease ? 2 : t < 30 ? 3 : t < 38 ? 4 : 5);
				case Phase.Channel:
					if (t < 4) {
						return R.ArmsUp;
					}
					if (t < 8) {
						return R.ArmsUp + 1;
					}
					if (t < ChannelRaise) {
						return R.ArmsUp + 2;
					}
					if (t < ChannelRaise + ChannelTicks) {
						return R.Hold + t / 6 % R.HoldFrames;              // the strain: a pixel's tremble
					}
					return R.ArmsDown + Math.Min(R.ArmsDownFrames - 1, (t - ChannelRaise - ChannelTicks) / 4);
				case Phase.Stunned:
					return R.Fizzle + t / 10 % R.FizzleFrames;
				case Phase.Intro:
					return R.Intro + (t < 90 ? 0 : 1);
				case Phase.Dying:
					if (t < CroakStart) {
						return R.Fizzle + t / 8 % R.FizzleFrames;        // dazed
					}
					return R.Croak + Math.Clamp((t - CroakStart) * 3 / Math.Max(1, PuffTick - CroakStart), 0, 2);   // the throat swells to a croak
				default:
					return IdleFrame();
			}
		}

		private bool Once(int tick) {
			int key = State * 10000 + tick;
			if ((int)Timer != tick || lastOnce == key) {
				return false;
			}
			lastOnce = key;
			return true;
		}

		private float CameraLock(Player viewer) {
			if (viewer == null || !viewer.active || Vector2.DistanceSquared(viewer.Center, NPC.Center) > CameraLockRange * CameraLockRange) {
				return 0f;
			}
			if (CurrentPhase == Phase.Intro) {
				return CinematicCamera.Envelope(Timer, IntroTicks, CameraEaseTicks, CameraEaseTicks);
			}
			if (CurrentPhase == Phase.Dying) {
				return CinematicCamera.Envelope(Timer, DeathTicks, CameraEaseTicks, 30f);
			}
			return 0f;
		}

		private void StateEffects(int t) {
			Lighting.AddLight(Origin + new Vector2(0f, -20f), 0.15f, 0.3f, 0.7f);
			if (burpTick == 2) {
				SoundEngine.PlaySound(SoundID.Zombie13 with { Pitch = 0.2f, Volume = 0.6f }, MouthWorld);     // the swell
			}
			if (burpTick == BurpRelease) {
				SoundEngine.PlaySound(SoundID.Item111 with { Pitch = -0.6f, Volume = 0.8f }, MouthWorld);     // *burp*
				Spores(MouthWorld, 8, 2.5f);
			}
			switch (CurrentPhase) {
				case Phase.Intro:
					float lockAmount = CameraLock(Main.LocalPlayer);
					if (lockAmount > 0f) {
						CinematicCamera.Request(NPC.Center, lockAmount);
					}
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.Item8 with { Pitch = -0.5f }, NPC.Center);
						Spores(NPC.Center, 30, 6f);
					}
					if (t < 70 && t % 3 == 0) {
						Spores(Origin + new Vector2(Main.rand.NextFloat(-40f, 40f), -10f), 1, 2f);
					}
					if (!titleShown && t >= TitleTick && lockAmount > 0f) {
						titleShown = true;
						BossTitleSystem.Show(DisplayName, epithet, TitleHoldTicks);
					}
					if (Once(90)) {
						SoundEngine.PlaySound(SoundID.Zombie13 with { Pitch = -0.6f, Volume = 0.8f }, NPC.Center);   // a croak
					}
					break;
				case Phase.Spores:
				case Phase.Fan:
				case Phase.Missile:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.Item8 with { Pitch = 0.3f }, HandWorld);
					}
					if (t >= 6 && t < ConjureTick && t % 3 == 0) {
						SoundEngine.PlaySound(SoundID.Item35 with { Pitch = 0.5f + (t % 6) * 0.05f, Volume = 0.25f, MaxInstances = 3 }, HandWorld);  // the shaken spell
						if (CogpunkClientConfig.RollEffect() && SafeSpawn.TryNewDust(HandWorld - new Vector2(6f), 12, 12, DustID.RainbowMk2, out Dust d, 0f, 0f, 0,
							Spectrum.At(t / 3), 1f)) {
							d.noGravity = true;
							d.velocity = Main.rand.NextVector2Circular(2f, 2f);
						}
					}
					if (Once(ConjureTick)) {
						SoundEngine.PlaySound(SoundID.Item29 with { Pitch = 0.4f, Volume = 0.6f }, HandWorld);
					}
					break;
				case Phase.Orbit:
					if (Once(10)) {
						SoundEngine.PlaySound(SoundID.Item8 with { Pitch = 0.2f }, NPC.Center);
					}
					if (Once(OrbitRelease)) {
						SoundEngine.PlaySound(SoundID.Item44 with { Pitch = -0.2f }, NPC.Center);
						Spores(NPC.Center, 20, 5f);
					}
					break;
				case Phase.Channel:
					if (Once(ChannelRaise)) {
						SoundEngine.PlaySound(SoundID.Item4 with { Pitch = -0.4f, Volume = 0.8f }, NPC.Center);
					}
					if (t > ChannelRaise && t < ChannelRaise + ChannelTicks && t % 30 == 0) {
						float pitch = -0.6f + 1.2f * (t - ChannelRaise) / ChannelTicks;    // a hum rising as it grows
						SoundEngine.PlaySound(SoundID.Item15 with { Pitch = pitch, Volume = 0.45f, MaxInstances = 2 }, NPC.Center);
					}
					break;
				case Phase.Stunned:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.Zombie13 with { Pitch = 0.5f, Volume = 0.8f }, NPC.Center);   // a dazed croak
						Punch(NPC.Center, 3f, 16);
					}
					if (t % 5 == 0 && SafeSpawn.TryNewDust(MouthWorld + new Vector2(MathF.Cos(t * 0.2f) * 30f, -36f + MathF.Sin(t * 0.2f) * 6f), 2, 2,
						DustID.YellowStarDust, out Dust star)) {
						star.noGravity = true;
						star.velocity = Vector2.Zero;
					}
					break;
				case Phase.Leave:
					Spores(NPC.Center, 2, 2f);
					break;
				case Phase.Dying:
					DeathEffects(t);
					break;
			}
		}

		private void DeathEffects(int t) {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(NPC.Center, lockAmount);
			}
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.Zombie13 with { Pitch = 0.4f }, NPC.Center);     // a last, confused croak
			}
			if (Once(CroakStart + 20)) {
				SoundEngine.PlaySound(SoundID.Zombie13 with { Pitch = -0.7f, Volume = 1f }, NPC.Center);   // the big croak
			}
			if (Once(PuffTick)) {
				SoundEngine.PlaySound(SoundID.Item6 with { Pitch = 0.2f, Volume = 1f }, NPC.Center);       // poof
				SoundEngine.PlaySound(SoundID.Item16 with { Pitch = -0.2f, Volume = 0.8f }, NPC.Center);
				Punch(NPC.Center, 4f, 20);
			}
			if (Once(HideTick)) {
				frogged = true;
				Spores(NPC.Center, CogpunkClientConfig.RollEffect() ? 50 : 16, 6f);
			}
		}

		private static void Spores(Vector2 at, int count, float speed) {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(10f), 20, 20, i % 3 == 0 ? DustID.PurpleTorch : DustID.GlowingMushroom, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(speed, speed) - Vector2.UnitY * 0.5f;
					d.scale = 1.1f;
				}
			}
		}

		private static void Punch(Vector2 at, float strength, int frames) {
			if (CogpunkClientConfig.Instance?.ScreenShake == false) {
				return;
			}
			Main.instance.CameraModifiers.Add(new PunchCameraModifier(at, Vector2.UnitY, strength, 6f, frames, 1000f, "Cogpunk:Fungimancer"));
		}

		protected override void BossHitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 3; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.GlowingMushroom, out _);
			}
		}

		/// <summary>The burp overlay's frame (swell, swell, full, open, closing) while burping, else -1.</summary>
		private int BurpFrame => burpTick < 0 ? -1 : burpTick < 5 ? 0 : burpTick < 10 ? 1 : burpTick < BurpRelease ? 2 : burpTick < 22 ? 3 : 4;

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			bool dummy = NPC.IsABestiaryIconDummy;
			Vector2 anchor = (dummy ? NPC.Bottom : Origin) - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;                  // the art faces left
			int t = (int)Timer;
			bool dying = !dummy && CurrentPhase == Phase.Dying;
			if (!(dying && t >= HideTick) && !frogged) {
				DrawBody(spriteBatch, anchor, flip, dummy, NPC.GetAlpha(drawColor));
			}
			if (dying && t >= PuffTick && puffSheet?.IsLoaded == true) {
				int f = (t - PuffTick) / PuffFrameTicks;
				if (f < R.PuffFrames) {
					DepthLayers.DrawCell(spriteBatch, puffSheet.Value, f, 1, R.PuffCellW, R.PuffCellH, 2, R.PuffOriginX, R.PuffOriginY, anchor, 0,
						Color.White * NPC.Opacity, false);
				}
			}
			return false;
		}

		private void DrawBody(SpriteBatch spriteBatch, Vector2 anchor, bool flip, bool dummy, Color light) {
			Texture2D middle = TextureAssets.Npc[Type].Value;
			int body = dummy ? R.Idle : BodyFrame();
			int lift = R.Lift[Math.Clamp(body, 0, R.Frames - 1)];
			float shift = dummy ? 0f : MaxParallax;
			Vector2 farShift = new(DepthLayers.Shift(anchor, DepthLayers.Far, shift).X, 0f);
			Vector2 nearShift = new(DepthLayers.Shift(anchor, DepthLayers.Near, shift).X, 0f);
			if (farSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, farSheet.Value, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor + farShift, 0, DepthLayers.Tint(light, DepthLayers.Far), flip);
			}
			DepthLayers.DrawCell(spriteBatch, middle, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY, anchor, 0, light, flip);
			int burp = dummy ? -1 : BurpFrame;
			if (burp >= 0 && burpSheet?.IsLoaded == true) {               // the burp over any pose: its throat and mouth
				DepthLayers.DrawCell(spriteBatch, burpSheet.Value, lift * R.BurpFrames + burp, R.BurpFrames, R.BurpCellW, R.BurpCellH, 2,
					R.BurpOriginX, R.BurpOriginY, anchor, 0, light, flip);
			}
			if (glowSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, glowSheet.Value, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor, 0, Color.White * NPC.Opacity, flip);
			}
			if (!dummy && CurrentPhase == Phase.Channel && Timer >= 8 && Timer < ChannelRaise + ChannelTicks && eyeSheet?.IsLoaded == true) {
				int e = (int)(Main.GameUpdateCount / 4 % (uint)R.EyeFrames);   // the hypnotic eyes, spinning
				DepthLayers.DrawCell(spriteBatch, eyeSheet.Value, lift * R.EyeFrames + e, R.EyeFrames, R.EyeCellW, R.EyeCellH, 2,
					R.EyeOriginX, R.EyeOriginY, anchor, 0, Color.White * NPC.Opacity, flip);
			}
			if (nearSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, nearSheet.Value, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor + nearShift, 0, light, flip);
			}
		}
	}
}
