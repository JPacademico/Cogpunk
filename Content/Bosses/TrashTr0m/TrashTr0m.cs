using System;
using System.IO;
using Cogpunk.Content.Bosses.TrashTr0m.Items;
using Cogpunk.Content.Junkyard;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Chat;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	/// <summary>
	/// Trash-Tr0m, the Junkyard's guardian and Cogpunk's first boss (T0): the torn-off upper half of a Devastator-style
	/// construction titan, 7x the player's height, seen in a three-quarter side view.
	/// <para><b>Loop</b> (user-set 2026-10-26): it crawls towards the closest player in the Junkyard for
	/// <see cref="CrawlTicks"/> (2.5 s, hand over hand, moving only while a planted hand drags), then attacks, then crawls
	/// again:</para>
	/// <list type="bullet">
	/// <item><b>Suck</b> (<see cref="Phase.Suck"/>) when any player is within its suction range: it opens its jaw for
	/// <see cref="SuckTicks"/> (5 s) and inhales. Players are dragged towards the mouth (<see cref="TrashTr0mPlayer"/>: a
	/// conveyor pull a player can only outrun at Hermes Boots speed) and friendly projectiles are swallowed. A player who
	/// reaches the mouth is swallowed, chewed and spat high into the air and out behind it (user-set 2026-10-27) (<see cref="Phase.SwallowPlayer"/>,
	/// <see cref="Phase.SpitPlayer"/>). Otherwise it gulps and spits the swallowed projectiles back as chewed scrap
	/// (<see cref="Phase.SpitScrap"/>), or, if it caught nothing, one big ball of scrap (<see cref="Phase.SpitBall"/>).</item>
	/// <item><b>Slam</b> (<see cref="Phase.SlamWindup"/>) when nobody is in range: it raises its near fist and smashes it
	/// down; a fast ground shockwave runs away from the fist along the terrain (<see cref="Projectiles.TrashTr0mShockwave"/>),
	/// jumped over at the right moment.</item>
	/// </list>
	/// <para><b>Cog volley</b> (user-set 2026-10-27), on its own all fight long: every <see cref="CogInterval"/> ticks
	/// (1.5 s; <see cref="CogIntervalHalfLife"/>, 0.75 s, at half life) the exhaust stacks on its back cough a loose rusted
	/// cog high into the air towards a player (<see cref="Projectiles.TrashTr0mCog"/>, 25 damage, bounces twice),
	/// after a <see cref="CogTelegraphTicks"/>-tick rattle.</para>
	/// <para><b>Enraged</b> below <see cref="EnrageLifeFraction"/> of its life: the suction reaches twice as far, and the
	/// slam comes twice, the near fist and then the far claw, each with its own shockwave. The 2.5 s crawl between
	/// attacks stays.</para>
	/// <para>It only fights in the Junkyard: when no living player has been inside it for <see cref="LeaveGraceTicks"/>,
	/// it burrows back into the ground and despawns (<see cref="Phase.Retreat"/>).</para>
	/// <para>Spawn: it bursts out from under the Junkyard's central heap when the locked cache is touched, or out of the
	/// ground in front of a player who uses <see cref="Junkyard.Items.Junkbait"/> (<see cref="TrashTr0mSummon"/>). Death:
	/// a scripted breakdown with the camera locked (<see cref="Phase.Dying"/>, <see cref="BossNPC"/>); the first kill drops
	/// the <see cref="LostKey"/> that opens the cache, which stays shut (no longer wakes it) from then on. Loot:
	/// <see cref="TrashTr0mLoot"/>.</para>
	/// <para>Stats (user-set 2026-10-26, docs/balance/bosses.csv), <b>Expert</b> values like every Cogpunk number
	/// (user directive 2026-10-27, <see cref="ExpertStats"/>): 5000 life, +35% of that per extra player; contact 50, slam
	/// 120, spat scrap 50, scrap ball 100, cog 25. Classic gets half, Master 1.5x (life: 6375, vanilla's 0.85 boss
	/// adjustment). A spat player falls far enough for up to 200 fall damage (absolute, every mode).</para>
	/// <para>Hitboxes (TrashTr0m.Hitboxes.cs): contact damage and hits use silhouette strips measured from the sprites,
	/// not the whole NPC rectangle.</para>
	/// <para>D2: <see cref="StateMachineNPC"/> keeps state and timer in <c>ai[0]</c>/<c>ai[1]</c>; <c>ai[2]</c> is the
	/// state's argument (heap burst flag, which arm slams, eaten count, swallowed player, scrap left to spit) and
	/// <c>ai[3]</c> the enraged flag; only the server changes them. Movement is root motion from the synced timer plus
	/// terrain following, so every side computes the same path; the server resyncs once per crawl cycle. Player effects
	/// are applied by the owning client from the synced state (<see cref="TrashTr0mPlayer"/>).</para>
	/// </summary>
	[AutoloadBossHead]
	public partial class TrashTr0m : BossNPC
	{
		public enum Phase
		{
			Emerge,
			Crawl,
			SlamWindup,
			SlamRecover,
			SuckWindup,
			Suck,
			SwallowPlayer,
			SpitPlayer,
			Gulp,
			SpitScrap,
			SpitBall,
			Recover,                                       // kept for old saves/packets: hands straight over to the crawl
			Retreat,
			Dying,
		}

		// --- stats (docs/balance/bosses.csv): Expert values (ExpertStats: Classic half, Master 1.5x) ---------------------
		public const int ExpertLife = 5000;                // single player; Classic 2500, Master 6375
		public const float LifePerExtraPlayer = 0.35f;     // +35% of the mode's base life per additional player
		public const int BaseDefense = 12;
		public const int ExpertContactDamage = 50;         // Classic 25, Master 75
		// Damage a player takes in Expert (ExpertStats.HostileProjectile halves the field: hostile hits are x2).
		public const int SlamDamage = 120;
		public const int ChewedScrapDamage = 50;
		public const int ScrapBallDamage = 100;
		public const int MaxSpitFallTiles = 45;            // vanilla fall damage = (tiles - 25 - extraFall) x 10 -> 200 max
		public const float EnrageLifeFraction = 0.33f;

		// --- size and pacing ----------------------------------------------------------------------------------------------
		/// <summary>The NPC rectangle: the idle body's box measured from the sprite (TrashTr0mRigData.Body*), used as the
		/// broad phase; the silhouette strips decide what actually touches (TrashTr0m.Hitboxes.cs).</summary>
		public const int HitboxWidth = TrashTr0mRigData.BodyRight - TrashTr0mRigData.BodyLeft;
		public const int HitboxHeight = -TrashTr0mRigData.BodyTop;
		/// <summary>The rig origin sits this far behind the rectangle's centre (left-facing), so the rectangle is centred on
		/// the body it measures.</summary>
		public const int RigShiftX = (TrashTr0mRigData.BodyLeft + TrashTr0mRigData.BodyRight) / 2;
		public const int CrawlTicks = 150;                 // 2.5 s of crawling between attacks (user-set)
		public const int CrawlCycleTicks = 75;             // 12 frames in 75 ticks: two cycles fill the crawl exactly
		public const float DespawnRange = 300f * 16f;
		public const int LeaveGraceTicks = 60;             // a knockback over the border doesn't despawn it
		public const int JunkyardCheckInterval = 10;

		// --- intro -----------------------------------------------------------------------------------------------------------
		public const int RumbleTicks = 45;
		public const int BurstTick = RumbleTicks;          // the heap blows apart
		public const int BurstTicks = 4;                   // the tiles are cleared over this many ticks (D1: spread the work)
		public const int RiseTicks = 135;
		public const int RoarTicks = 60;
		public const int EmergeTicks = RumbleTicks + RiseTicks + RoarTicks;   // 240 ticks = 4 s
		public const int TitleTick = RumbleTicks + 90;
		public const int TitleHoldTicks = EmergeTicks - TitleTick + 45;
		public const int CameraEaseTicks = 30;
		public const float CameraLockRange = 150f * 16f;
		public const int RetreatTicks = 90;

		// --- death -----------------------------------------------------------------------------------------------------------
		public const int DeathTicks = 240;
		public const int DeathSagTick = 40, DeathSlumpTick = 110, DeathDownTick = 150, DeathBlastTick = 200;

		private static LocalizedText epithet;

		private Phase CurrentPhase => (Phase)State;

		/// <summary>The state's argument (synced): heap-burst flag, slamming arm, eaten projectiles, swallowed player, scrap left.</summary>
		private ref float Arg => ref NPC.ai[2];

		/// <summary>Below a third of its life (synced, set once by the server).</summary>
		public bool Enraged => NPC.ai[3] == 1f;

		// localAI (never synced): [0] title card shown, [1] last one-shot effect key, [2] gores thrown, [3] enrage effect played.
		private ref float TitleShown => ref NPC.localAI[0];

		private bool playerScaled;                          // life already scaled for players (Expert/Master hook ran)
		private int outsideTicks;                           // server: how long no player has been in the Junkyard

		public bool IsEmerging => CurrentPhase == Phase.Emerge;

		public bool FromHeap => IsEmerging && Arg == 1f;

		protected override int DyingState => (int)Phase.Dying;

		protected override int DeathAnimationTicks => DeathTicks;

		protected override int DefeatCardTick => DeathBlastTick;

		/// <summary>The rig origin (the ground point under the body pivot) in the world: every sprite and rig point hangs from it.</summary>
		public Vector2 RigOrigin => NPC.Bottom + new Vector2(RigShiftX * NPC.spriteDirection, 0f);

		/// <summary>Where the camera looks during the intro and the death: the middle of the risen boss.</summary>
		public Vector2 CameraFocus => RigOrigin - new Vector2(-NPC.spriteDirection * 40f, 150f);

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 1;
			NPCID.Sets.MPAllowedEnemies[Type] = true;
			NPCID.Sets.BossBestiaryPriority.Add(Type);
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() {
				Scale = 0.36f,
				PortraitScale = 0.5f,
				Position = new Vector2(10f, 30f),
				PortraitPositionYOverride = 40f,
			});
			CogpunkSets.Mechanical[Type] = true;
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
			NPC.lifeMax = ExpertStats.Base(ExpertLife);    // Classic; vanilla x2 / x3 in Expert / Master, snapped below
			NPC.defense = BaseDefense;
			NPC.damage = ExpertStats.Base(ExpertContactDamage);
			NPC.knockBackResist = 0f;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.boss = true;
			NPC.npcSlots = 10f;
			NPC.aiStyle = -1;
			NPC.value = Item.buyPrice(gold: 3);
			NPC.SpawnWithHigherTime(30);
			if (!Main.dedServ) {
				Music = MusicID.Boss1;
			}
		}

		/// <summary>
		/// Expert and Master (vanilla only calls this hook there; decompiled <c>NPC.ScaleStats</c>): by now life and contact
		/// damage are the <c>SetDefaults</c> values x2 (Expert) or x3 (Master). Expert lands exactly on
		/// <see cref="ExpertLife"/> and <see cref="ExpertContactDamage"/>; Master keeps vanilla's 0.85 boss adjustment
		/// (7500 x 0.85 = 6375); then +35% per extra player instead of vanilla's balance curve.
		/// </summary>
		public override void ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment) {
			NPC.lifeMax = (int)Math.Round(ExpertStats.Snap(NPC.lifeMax, ExpertLife) * bossAdjustment * PlayerFactor(numPlayers));
			NPC.damage = ExpertStats.Snap(NPC.damage, ExpertContactDamage);
			playerScaled = true;
		}

		/// <summary>Classic has no player scaling hook, so the server scales life when the boss spawns and sends the
		/// result with the NPC (<see cref="SendExtraAI"/>).</summary>
		public override void OnSpawn(Terraria.DataStructures.IEntitySource source) {
			if (!playerScaled && Main.netMode != NetmodeID.MultiplayerClient) {
				int players = Math.Max(1, NPC.GetActivePlayerCount());
				NPC.lifeMax = (int)Math.Round(NPC.lifeMax * PlayerFactor(players));
				NPC.life = NPC.lifeMax;
				playerScaled = true;
			}
		}

		public static float PlayerFactor(int players) => 1f + LifePerExtraPlayer * Math.Max(0, players - 1);

		public override void SendExtraAI(BinaryWriter writer) {
			writer.Write(NPC.lifeMax);
			writer.Write(NPC.life >= NPC.lifeMax);
			writer.Write((short)cogTimer);
		}

		public override void ReceiveExtraAI(BinaryReader reader) {
			int lifeMax = reader.ReadInt32();
			bool full = reader.ReadBoolean();
			cogTimer = Math.Clamp((int)reader.ReadInt16(), 0, CogInterval);   // the server's count: the telegraph lines up
			if (lifeMax > 0 && lifeMax != NPC.lifeMax) {
				NPC.lifeMax = lifeMax;                     // a client computes its own lifeMax; the server's is the truth
				if (full) {
					NPC.life = lifeMax;
				}
			}
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				ModContent.GetInstance<JunkyardBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		/// <summary>The Lost Key on the first kill only, a bag per player in Expert/Master, the bag's contents in Classic
		/// (<see cref="TrashTr0mLoot"/>).</summary>
		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.ByCondition(new FirstKillCondition(), ModContent.ItemType<LostKey>()));
			npcLoot.Add(ItemDropRule.BossBag(ModContent.ItemType<TrashTr0mBag>()));
			LeadingConditionRule classic = new(new Conditions.NotExpert());
			classic.OnSuccess(ItemDropRule.OneFromOptionsNotScalingWithLuck(1, TrashTr0mLoot.WeaponPool()));
			classic.OnSuccess(ItemDropRule.Common(ModContent.ItemType<RustedScrap>(), 1, TrashTr0mLoot.MinScrap, TrashTr0mLoot.MaxScrap));
			npcLoot.Add(classic);
		}

		public override bool CanHitPlayer(Player target, ref int cooldownSlot) {
			cooldownSlot = ImmunityCooldownID.Bosses;
			switch (CurrentPhase) {
				case Phase.Crawl:
				case Phase.SlamWindup:
				case Phase.SlamRecover:
				case Phase.Gulp:
				case Phase.SpitScrap:
				case Phase.SpitBall:
					return true;
				default:
					return false;                          // intro, suck (it must not knock its meal away), swallow, death
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// State machine (every side; only the server changes state)
		// ------------------------------------------------------------------------------------------------------------

		protected override void UpdateBoss() {
			TrashTr0mSystem.Track(NPC.whoAmI);
			if (!Main.dedServ) {
				ResetEffectKeys();
			}
			NPC.velocity.X = 0f;
			NPC.dontTakeDamage = CurrentPhase == Phase.Emerge || CurrentPhase == Phase.Retreat || CurrentPhase == Phase.Dying;
			switch (CurrentPhase) {
				case Phase.Emerge:
					NPC.velocity.Y = 0f;
					DoEmerge();
					return;
				case Phase.Retreat:
					NPC.velocity.Y = 0f;
					DoRetreat();
					return;
				case Phase.Dying:
					DoDying();
					break;
				case Phase.Crawl:
					DoCrawl();
					break;
				case Phase.SlamWindup:
					DoSlamWindup();
					break;
				case Phase.SlamRecover:
					if (Timer >= SlamRecoverTicks) {
						EndAttack();
					}
					break;
				case Phase.SuckWindup:
					DoSuckWindup();
					break;
				case Phase.Suck:
					DoSuck();
					break;
				case Phase.SwallowPlayer:
					DoSwallowPlayer();
					break;
				case Phase.SpitPlayer:
					DoSpitPlayer();
					break;
				case Phase.Gulp:
					DoGulp();
					break;
				case Phase.SpitScrap:
					DoSpitScrap();
					break;
				case Phase.SpitBall:
					DoSpitBall();
					break;
				default:
					EndAttack();                           // Recover, or an unknown state from a newer version (D0)
					break;
			}
			if (CurrentPhase != Phase.Dying) {
				UpdateCogs();
				CheckEnrage();
				CheckJunkyard();
			}
			FollowGround();
			if (!Main.dedServ) {
				StateEffects();
			}
		}

		private void DoEmerge() {
			if (!Main.dedServ) {
				EmergeEffects();
			}
			if (FromHeap && Timer >= BurstTick && Timer < BurstTick + BurstTicks && IsAuthority) {
				TrashTr0mSummon.ClearHeapRows(NPC.Bottom, (int)Timer - BurstTick, BurstTicks);
			}
			FaceTarget();
			if (Timer >= EmergeTicks && RetargetOrRetreat()) {
				StartCrawl();
			}
		}

		private void DoRetreat() {
			if (!Main.dedServ && Timer % 3 == 0) {
				GroundDebris(2);
			}
			if (Timer >= RetreatTicks && IsAuthority) {
				NPC.active = false;
				if (Main.netMode == NetmodeID.Server) {
					NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
				}
			}
		}

		private void DoDying() {
			if (!Main.dedServ) {
				DeathEffects();
			}
			UpdateDeath();
		}

		protected override void OnDeathStarted() {
			Arg = 0f;                                      // let go of anything it held (a swallowed player is released)
			NPC.netUpdate = true;
		}

		/// <summary>Server: below a third of its life it enrages, once (synced in ai[3]).</summary>
		private void CheckEnrage() {
			if (IsAuthority && !Enraged && NPC.life <= NPC.lifeMax * EnrageLifeFraction) {
				NPC.ai[3] = 1f;
				NPC.netUpdate = true;
			}
		}

		/// <summary>Server: burrow away when no living player has been in the Junkyard for <see cref="LeaveGraceTicks"/>.
		/// Checked every <see cref="JunkyardCheckInterval"/> ticks (a loop over the players, D1). Worlds without a Junkyard
		/// skip the rule.</summary>
		private void CheckJunkyard() {
			if (!IsAuthority || !JunkyardSystem.Exists || (int)Timer % JunkyardCheckInterval != 0) {
				return;
			}
			outsideTicks = AnyPlayerInJunkyard() ? 0 : outsideTicks + JunkyardCheckInterval;
			if (outsideTicks >= LeaveGraceTicks) {
				outsideTicks = 0;
				ChangeState((int)Phase.Retreat);
			}
		}

		private static bool AnyPlayerInJunkyard() {
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && JunkyardSystem.Contains(player.Center)) {
					return true;
				}
			}
			return false;
		}

		/// <summary>Every attack ends here: straight back to crawling (the 2.5 s between attacks), or away if nobody is left.</summary>
		private void EndAttack() {
			if (RetargetOrRetreat()) {
				StartCrawl();
			}
		}

		// --- crawl --------------------------------------------------------------------------------------------------------

		/// <summary>Server: start crawling from the rest pose.</summary>
		private void StartCrawl() {
			if (!IsAuthority) {
				return;
			}
			ChangeState((int)Phase.Crawl);
			Arg = 0f;
		}

		/// <summary>Crawl steps taken by tick <paramref name="t"/>: 12 frames per <see cref="CrawlCycleTicks"/>, exact integers.</summary>
		private static int CrawlStep(int t) => t * TrashTr0mRigData.CrawlFrames / CrawlCycleTicks;

		/// <summary>Crawl frame for the current tick: the cycle starts and ends on the rest pose (both hands planted).</summary>
		public int CrawlFrame => (TrashTr0mRigData.RestFrame + CrawlStep((int)Timer)) % TrashTr0mRigData.CrawlFrames;

		private void DoCrawl() {
			int t = (int)Timer;
			int step = CrawlStep(t);
			if (t > 0 && step != CrawlStep(t - 1)) {
				// Root motion: on a frame change, the body moves exactly as far as the planted hands slide back.
				int previous = (TrashTr0mRigData.RestFrame + step - 1) % TrashTr0mRigData.CrawlFrames;
				if (TrashTr0mRigData.CrawlDrag[previous] != 0) {
					NPC.velocity.X = NPC.spriteDirection * TrashTr0mRigData.CrawlStep;
					if (!Main.dedServ) {
						DragEffects();
					}
				}
				if (step % TrashTr0mRigData.CrawlFrames == 0) {
					// Back on the rest pose (both hands planted): retarget the closest player, turn, resync, maybe attack.
					if (!RetargetOrRetreat()) {
						return;
					}
					FaceTarget();
					if (IsAuthority) {
						NPC.netUpdate = true;              // once per cycle: correct any drift on clients
						if (t >= CrawlTicks) {
							PickAttack();
						}
					}
				}
			}
			KeepInWorld();
		}

		/// <summary>Server: suck if any player is within suction range of the mouth, slam otherwise.</summary>
		private void PickAttack() {
			FaceTarget();
			bool suck = AnyPlayerInSuckRange();
			ChangeState((int)(suck ? Phase.SuckWindup : Phase.SlamWindup));
			Arg = 0f;                                      // the slam starts with the near arm
		}

		/// <summary>Server: targets the closest living player, preferring players inside the Junkyard; burrows away only
		/// if nobody is alive within <see cref="DespawnRange"/>. (Players all leaving the Junkyard is handled with a grace
		/// period by <see cref="CheckJunkyard"/>.) True while fighting.</summary>
		private bool RetargetOrRetreat() {
			if (!IsAuthority) {
				return true;
			}
			int inside = -1, anywhere = -1;
			float insideDistance = DespawnRange * DespawnRange, anyDistance = insideDistance;
			bool hasJunkyard = JunkyardSystem.Exists;
			foreach (Player player in Main.ActivePlayers) {
				if (player.dead) {
					continue;
				}
				float d = Vector2.DistanceSquared(player.Center, NPC.Center);
				if (d < anyDistance) {
					anyDistance = d;
					anywhere = player.whoAmI;
				}
				if (hasJunkyard && d < insideDistance && JunkyardSystem.Contains(player.Center)) {
					insideDistance = d;
					inside = player.whoAmI;
				}
			}
			int best = inside >= 0 ? inside : anywhere;
			if (best < 0) {
				ChangeState((int)Phase.Retreat);
				return false;
			}
			if (best != NPC.target) {
				NPC.target = best;
				NPC.netUpdate = true;
			}
			return true;
		}

		private void FaceTarget() {
			if (NPC.target < 0 || NPC.target >= Main.maxPlayers || !Main.player[NPC.target].active) {
				return;
			}
			int dir = Main.player[NPC.target].Center.X >= NPC.Center.X ? 1 : -1;
			NPC.direction = NPC.spriteDirection = dir;
		}

		private void KeepInWorld() {
			float min = 60f * 16f;
			float max = (Main.maxTilesX - 60) * 16f;
			if (NPC.Center.X + NPC.velocity.X < min || NPC.Center.X + NPC.velocity.X > max) {
				NPC.velocity.X = 0f;
			}
		}

		// --- terrain following (every side; tiles are synced, so every side finds the same ground) ---------------------

		public const int ClimbRows = 10;                   // how far above its bottom it looks for ground (it climbs ledges)
		public const int DropRows = 24;
		public const float ClimbSpeed = 3f;
		public const float FallAcceleration = 0.4f;
		public const float MaxFallSpeed = 12f;
		private const float GroundSampleOffset = 8f * 16f;  // samples under the near hand, the body and the waist

		private void FollowGround() {
			float bottom = NPC.Bottom.Y;
			float best = float.MaxValue;
			bool walled = false;
			for (int s = -1; s <= 1; s++) {
				float x = NPC.Center.X + NPC.velocity.X + s * GroundSampleOffset;
				float y = FindGround(x, bottom, out bool solidAbove);
				walled |= solidAbove;
				if (y < best) {
					best = y;
				}
			}
			if (best == float.MaxValue) {
				best = walled ? bottom - ClimbRows * 16f : float.MaxValue;   // a wall taller than the window: keep climbing
			}
			float diff = best == float.MaxValue ? MaxFallSpeed : best - bottom;
			if (diff < -0.5f) {
				NPC.velocity.Y = Math.Max(diff, -ClimbSpeed);
			}
			else if (diff > 0.5f) {
				NPC.velocity.Y = Math.Min(Math.Min(Math.Max(NPC.velocity.Y, 0f) + FallAcceleration, MaxFallSpeed), diff);
			}
			else {
				NPC.velocity.Y = diff;
			}
		}

		/// <summary>Top of the first solid surface in the column under <paramref name="worldX"/>, searched from
		/// <see cref="ClimbRows"/> above <paramref name="bottom"/> to <see cref="DropRows"/> below; float.MaxValue if none.
		/// At most ClimbRows + DropRows bounds-checked reads (D0).</summary>
		private static float FindGround(float worldX, float bottom, out bool solidAtTop) {
			int x = (int)(worldX / 16f);
			int row = (int)(bottom / 16f);
			int top = row - ClimbRows;
			solidAtTop = IsGround(x, top) && IsGround(x, top - 1);
			bool airAbove = !IsGround(x, top - 1);
			for (int y = top; y <= row + DropRows; y++) {
				bool ground = IsGround(x, y);
				if (ground && airAbove) {
					return y * 16f;
				}
				airAbove = !ground;
			}
			return float.MaxValue;
		}

		private static bool IsGround(int x, int y) {
			if (!TileSafety.TryGetTile(x, y, out Tile tile, 1) || !tile.HasTile || tile.IsActuated) {
				return false;
			}
			return Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType];
		}

		public override void OnKill() {
			bool firstKill = !TrashTr0mSystem.Downed;                     // the Lost Key only drops on the first kill
			NPC.SetEventFlagCleared(ref TrashTr0mSystem.DownedFlag, -1);   // vanilla sends WorldData after a boss kill
			if (!firstKill) {
				return;
			}
			Color keyColor = new(223, 185, 78);                          // Brass 4, the cache's glow
			if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey(this.GetLocalizationKey("KeyDropped")), keyColor);
			}
			else if (Main.netMode == NetmodeID.SinglePlayer) {
				Main.NewText(this.GetLocalization("KeyDropped").Value, keyColor);
			}
		}

		public override void BossHeadSlot(ref int index) {
			if ((IsEmerging && Timer < BurstTick) || (CurrentPhase == Phase.Retreat && Timer > RetreatTicks / 2)) {
				index = -1;                                // under the ground: no map icon
			}
		}
	}
}
