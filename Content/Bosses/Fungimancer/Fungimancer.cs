using System;
using System.IO;
using Cogpunk.Content.Bosses.Fungimancer.Items;
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
	/// The Fungimancer, the glowing mushroom biome's secret boss (user-set 2026-11-19: "a magic dumb frog like creature. to spawn
	/// it add a very rare chance for a rainbow mushroom ... if the player breaks the rainbow mushroom (does not drop) it should
	/// spawn the Fungimancer. allthough it can be spawned pre hardmode the fungimancer is a hardmode intended fight (just like
	/// duke fishroom ...) ... (floaty boss). add a "fungi manual" for the fungimancer to drop"). A fat frog-mage sitting on a
	/// floating glowing mushroom (art/bosses/fungimancer/make_fungimancer_art.py, after the user's reference).
	/// <para>The fight (the attacks, numbers and cadence are my calls):
	/// <list type="bullet">
	/// <item>Floaty (BossNPC rules): it drifts beside and above its target with a lag and a slow figure of eight, comes into a
	/// blade's reach of a melee fighter, and never hurts by touch.</item>
	/// <item>An attack every <see cref="AttackInterval"/> ticks (<see cref="AttackIntervalEnraged"/> under half its life), never
	/// the same twice running: <b>Cast</b> (a fan of homing <see cref="SporeBolt"/>s from its raised hand; one cast in
	/// <see cref="FizzleOneIn"/> goes wrong instead: a puff of smoke and a dumb look, a breather: <b>Fizzle</b>), <b>Croak</b>
	/// (its throat swells and glowing mushrooms burst out of the ground under and beside its target, each shown first by
	/// spores on the ground: <see cref="ShroomSpike"/>) and <b>Tongue</b> (it gapes, an aim line shows, and its tongue lashes
	/// out <see cref="FungimancerTongue.Range"/> px: <see cref="FungimancerTongue"/>).</item>
	/// <item>It despawns if no player stays in the glowing mushroom biome near it for <see cref="LeaveGrace"/> ticks.</item>
	/// </list></para>
	/// <para>Boss rules: an intro with a camera lock and a title card (its name and epithet); a death cinematic under a camera
	/// lock (it bloats, mushrooms sprout all over it, it bursts into spores) with the "Defeated" card (<see cref="BossNPC"/>);
	/// no natural spawns near it; DPS targeting; its hitbox is its seat, body and head from the art (<see cref="R.BodyTop"/>);
	/// its summon (<see cref="RainbowMushroom"/>) is sold by the Friendo-bot once it has been defeated.</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/bosses.csv): Duke Fishron's tier (terraria.wiki.gg 1.4.4 Expert: 78000 life,
	/// 50 defense), +10% (the user's 10-35% band; its bottom, as it has no contact damage): <see cref="ExpertLife"/>, +35% per
	/// extra player. D2: ai[0]/ai[1] state and timer; the clock, the last attack, the aim and the drift in <see cref="SendExtraAI"/>;
	/// the server decides and spawns. D0: spawns through <see cref="SafeSpawn"/>, scans bounded. D1: no allocation per tick.</para>
	/// </summary>
	[AutoloadBossHead]
	public class Fungimancer : BossNPC
	{
		public enum Phase { Intro, Idle, Cast, Croak, Tongue, Fizzle, Leave, Dying }

		// --- stats (Expert) ------------------------------------------------------------------------------------------------
		public const int ExpertLife = 85800;                              // Duke Fishron's Expert 78000 + 10%
		public const float LifePerExtraPlayer = 0.35f;
		public const int BaseDefense = 50;                                // Duke Fishron's
		public const int BoltDamage = 90, SpikeDamage = 120, TongueDamage = 140;   // Expert (Duke Fishron: 100 bubble, 140 contact)

		// --- the cadence ---------------------------------------------------------------------------------------------------
		public const int AttackInterval = 90, AttackIntervalEnraged = 66, MinIdle = 18;
		public const float EnrageAt = 0.5f;
		public const int FizzleOneIn = 5;                                 // "dumb": one cast in five fizzles

		// --- the attacks ---------------------------------------------------------------------------------------------------
		public const int CastTicks = 48, CastRelease = 24, Bolts = 3, BoltsEnraged = 5;
		public const float BoltSpread = 0.32f, BoltSpeed = 7f;
		public const int CroakTicks = 70, CroakRelease = 30, Spikes = 3, SpikesEnraged = 5, SpikeGap = 6 * 16, SpikeScanDown = 30;
		public const int TongueAim = 36, TongueTicks = TongueAim + FungimancerTongue.Life + 8;
		public const int FizzleTicks = 60;

		// --- the float -----------------------------------------------------------------------------------------------------
		public const float HoverX = 12f * 16f, HoverY = 6f * 16f;
		public const float SwayX = 3f * 16f, BobY = 20f, MeleeSwayX = 12f, MeleeBobY = 8f;
		public const float HoverSpeed = 6f, AttackSpeed = 2.5f, HoverAccel = 0.08f, HoverApproach = 0.06f;
		public const float MeleeGap = 14f, MeleeLift = 6f, MeleeSpeed = 9f;

		// --- intro, leaving, death -----------------------------------------------------------------------------------------
		public const int IntroTicks = 150, TitleTick = 50, TitleHoldTicks = 140;
		public const int LeaveTicks = 50;
		public const int DeathTicks = 200, BurstTick = 172;
		public const int CameraEaseTicks = 30;
		public const float CameraLockRange = 120f * 16f, FightRange = 150f * 16f;
		public const int CheckInterval = 30, LeaveGrace = 120;
		public const float MaxParallax = 2f;

		private static LocalizedText epithet;
		private static Asset<Texture2D> farSheet, nearSheet, glowSheet;

		public Phase CurrentPhase => (Phase)State;

		// synced (SendExtraAI)
		private int attackClock;
		private byte lastAttack = 255;
		private Vector2 aim;
		// the server's own
		private int absentTicks;
		private bool playerScaled;
		// clients' own
		private int lastOnce = -1;
		private bool titleShown, burst;

		protected override int DyingState => (int)Phase.Dying;
		protected override int DeathAnimationTicks => DeathTicks;
		protected override int DefeatCardTick => BurstTick + 8;
		public override bool Floaty => true;

		public bool Enraged => NPC.life < NPC.lifeMax * EnrageAt;

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
			}
		}

		public override void Unload() {
			epithet = null;
			farSheet = nearSheet = glowSheet = null;
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
			NPC.DeathSound = null;                            // the burst is its death sound
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
			writer.Write((short)Math.Clamp(attackClock, short.MinValue, short.MaxValue));
			writer.Write(lastAttack);
			writer.Write(aim.X);
			writer.Write(aim.Y);
			WriteDrift(writer);
		}

		public override void ReceiveExtraAI(BinaryReader reader) {
			int lifeMax = reader.ReadInt32();
			bool full = reader.ReadBoolean();
			attackClock = reader.ReadInt16();
			lastAttack = reader.ReadByte();
			float x = reader.ReadSingle(), y = reader.ReadSingle();
			aim = float.IsFinite(x) && float.IsFinite(y) ? new Vector2(x, y) : Vector2.Zero;
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

		public override bool CanHitPlayer(Player target, ref int cooldownSlot) => false;

		public override void OnKill() {
			NPC.SetEventFlagCleared(ref FungimancerSystem.DownedFlag, -1);
		}

		public override void BossHeadSlot(ref int index) {
			if (burst || CurrentPhase == Phase.Leave) {
				index = -1;
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

		private Vector2 HandWorld => RigPoint(R.NearX[Math.Clamp(BodyFrame(), 0, R.Frames - 1)], R.NearY[Math.Clamp(BodyFrame(), 0, R.Frames - 1)]);

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
							attackClock = AttackInterval - 30;
							ChangeState((int)Phase.Idle);
						}
						else {
							ChangeState((int)Phase.Leave);
						}
					}
					break;
				case Phase.Idle:
					Float(HoverSpeed);
					if (IsAuthority && attackClock >= (Enraged ? AttackIntervalEnraged : AttackInterval) && t >= MinIdle) {
						StartAttack();
					}
					break;
				case Phase.Cast:
					Float(AttackSpeed);
					if (IsAuthority && t == CastRelease) {
						CastBolts();
					}
					if (IsAuthority && t >= CastTicks) {
						ChangeState((int)Phase.Idle);
					}
					break;
				case Phase.Croak:
					Float(AttackSpeed * 0.5f);
					if (IsAuthority && t == CroakRelease) {
						Bloom();
					}
					if (IsAuthority && t >= CroakTicks) {
						ChangeState((int)Phase.Idle);
					}
					break;
				case Phase.Tongue:
					NPC.velocity *= 0.85f;                          // it plants itself to lash
					if (t < TongueAim - 6) {
						FaceTarget();
						if (IsAuthority && CurrentTarget is Player target) {
							aim = target.Center + target.velocity * 8f;   // where it will be (my call: a short lead)
							if (t % 10 == 0) {
								NPC.netUpdate = true;
							}
						}
					}
					if (IsAuthority && t == TongueAim) {
						Lash();
					}
					if (IsAuthority && t >= TongueTicks) {
						ChangeState((int)Phase.Idle);
					}
					break;
				case Phase.Fizzle:
					NPC.velocity *= 0.9f;
					if (IsAuthority && t >= FizzleTicks) {
						ChangeState((int)Phase.Idle);
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
					UpdateDeath();
					break;
				default:
					if (IsAuthority) {
						ChangeState((int)Phase.Idle);
					}
					break;
			}
			if (CurrentPhase != Phase.Intro && CurrentPhase != Phase.Leave && CurrentPhase != Phase.Dying) {
				if (CurrentPhase == Phase.Idle) {
					attackClock++;
				}
				CheckFight();
				TickDrift();
			}
			if (!Main.dedServ) {
				StateEffects(t);
			}
		}

		protected override void OnDeathStarted() {
			aim = Vector2.Zero;
			NPC.netUpdate = true;
		}

		private void StartAttack() {
			if (!EnsureTarget()) {
				return;
			}
			Span<byte> options = stackalloc byte[3] { (byte)Phase.Cast, (byte)Phase.Croak, (byte)Phase.Tongue };
			int count = 3;
			for (int k = 0; k < count; k++) {
				if (options[k] == lastAttack) {
					options[k] = options[count - 1];
					count--;
					break;
				}
			}
			byte pick = options[Main.rand.Next(Math.Max(1, count))];
			lastAttack = pick;
			attackClock = 0;
			aim = Vector2.Zero;
			if (pick == (byte)Phase.Cast && Main.rand.NextBool(FizzleOneIn)) {
				pick = (byte)Phase.Fizzle;                          // the spell goes wrong (it is not very bright)
			}
			ChangeState(pick);
		}

		/// <summary>Server: the spore bolts, fanned at the target from the raised hand.</summary>
		private void CastBolts() {
			if (CurrentTarget is not Player target) {
				return;
			}
			Vector2 from = HandWorld;
			Vector2 dir = (target.Center - from).SafeNormalize(Vector2.UnitX * NPC.spriteDirection);
			int n = Enraged ? BoltsEnraged : Bolts;
			int damage = ExpertStats.HostileProjectile(NPC, BoltDamage);
			for (int k = 0; k < n; k++) {
				float turn = (k - (n - 1) * 0.5f) * BoltSpread;
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, dir.RotatedBy(turn) * BoltSpeed, ModContent.ProjectileType<SporeBolt>(),
					damage, 0f, out _, ai0: target.whoAmI);
			}
		}

		/// <summary>Server: mushrooms to burst out of the ground under the target and either side of it (each finds the ground
		/// below its column, at most <see cref="SpikeScanDown"/> tiles down; none where there is none).</summary>
		private void Bloom() {
			if (CurrentTarget is not Player target) {
				return;
			}
			int n = Enraged ? SpikesEnraged : Spikes;
			int damage = ExpertStats.HostileProjectile(NPC, SpikeDamage);
			for (int k = 0; k < n; k++) {
				int side = k == 0 ? 0 : (k % 2 == 1 ? 1 : -1) * ((k + 1) / 2);
				float x = target.Center.X + side * SpikeGap;
				if (FindGround(x, target.Center.Y - 32f, out Vector2 ground)) {
					SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), ground - new Vector2(0f, ShroomSpike.Height * 0.5f), Vector2.Zero,
						ModContent.ProjectileType<ShroomSpike>(), damage, 0f, out _);
				}
			}
		}

		/// <summary>The first solid top below (<paramref name="x"/>, <paramref name="y"/>), at most <see cref="SpikeScanDown"/>
		/// tiles down (bounded, D0): the point on its surface.</summary>
		private static bool FindGround(float x, float y, out Vector2 ground) {
			ground = Vector2.Zero;
			int tx = (int)(x / 16f), ty = (int)(y / 16f);
			for (int k = 0; k < SpikeScanDown; k++) {
				int j = ty + k;
				if (!TileSafety.TryGetTile(tx, j, out Tile tile)) {
					return false;
				}
				if (tile.HasTile && !tile.IsActuated && (Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType])) {
					ground = new Vector2(tx * 16f + 8f, j * 16f);
					return true;
				}
			}
			return false;
		}

		/// <summary>Server: the tongue lashes from the mouth at the aim.</summary>
		private void Lash() {
			Vector2 from = MouthWorld;
			Vector2 to = aim == Vector2.Zero && CurrentTarget is Player p ? p.Center : aim;
			Vector2 dir = (to - from).SafeNormalize(Vector2.UnitX * NPC.spriteDirection);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, Vector2.Zero, ModContent.ProjectileType<FungimancerTongue>(),
				ExpertStats.HostileProjectile(NPC, TongueDamage), 0f, out _, ai0: NPC.whoAmI, ai2: dir.ToRotation());
		}

		// --- the float -----------------------------------------------------------------------------------------------------

		private void FaceTarget() {
			Player target = CurrentTarget;
			if (target != null && Math.Abs(target.Center.X - NPC.Center.X) > 8f) {
				NPC.direction = NPC.spriteDirection = target.Center.X > NPC.Center.X ? 1 : -1;
			}
		}

		/// <summary>Every side: it eases to its spot beside and above its target (at a melee fighter's side, close in), round a
		/// point that follows the target with a lag and sways (BossNPC's floaty rules).</summary>
		private void Float(float speed) {
			Player target = CurrentTarget;
			FaceTarget();
			if (target == null) {
				NPC.velocity *= 0.92f;
				return;
			}
			Vector2 focus = FloatFocus(target);
			float side = NPC.Center.X < focus.X ? -1f : 1f;
			bool melee = MeleeFocus.Of(target);
			Vector2 spot = melee
				? new Vector2(focus.X + side * (target.width * 0.5f + MeleeGap + NPC.width * 0.5f + DriftSway * MeleeSwayX),
					focus.Y + target.height * 0.5f - MeleeLift - NPC.height * 0.5f + DriftBob * MeleeBobY)
				: focus + new Vector2(side * HoverX + DriftSway * SwayX, -HoverY + DriftBob * BobY);
			float max = melee ? Math.Max(speed, MeleeSpeed) : speed;
			Vector2 to = spot - NPC.Center;
			float distance = to.Length();
			Vector2 want = distance > 1f ? to / distance * Math.Min(max, distance * HoverApproach) : Vector2.Zero;
			NPC.velocity += (want - NPC.velocity) * HoverAccel;
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

		/// <summary>The body frame for the synced state and timer.</summary>
		public int BodyFrame() {
			int t = (int)Timer;
			switch (CurrentPhase) {
				case Phase.Cast:
					return R.Cast + (t < 12 ? 0 : t < CastRelease ? 1 : t < 34 ? 2 : 3);
				case Phase.Croak:
					return R.Croak + (t < 12 ? 0 : t < CroakRelease ? 1 : t < 44 ? 2 : 3);
				case Phase.Tongue:
					return R.Tongue + (t < TongueAim ? 0 : t < TongueTicks - 8 ? 1 : 2);
				case Phase.Fizzle:
					return R.Fizzle + (t < 20 ? 0 : 1);
				case Phase.Intro:
					return R.Intro + (t < 90 ? 0 : 1);
				case Phase.Dying:
					return R.Death + Math.Clamp(t * R.DeathFrames / BurstTick, 0, R.DeathFrames - 1);
				default:
					int clock = (int)(Main.GameUpdateCount + NPC.whoAmI * 37);
					if (clock % 200 < 8) {
						return R.Idle + 3;                          // a blink
					}
					int k = clock / 12 % 4;
					return R.Idle + (k == 3 ? 1 : k);               // breathing: 0 1 2 1
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
				case Phase.Cast:
					if (Once(10)) {
						SoundEngine.PlaySound(SoundID.Item8 with { Pitch = 0.2f }, NPC.Center);
					}
					if (t > 10 && t < CastRelease && CogpunkClientConfig.RollEffect()
						&& SafeSpawn.TryNewDust(HandWorld - new Vector2(4f), 8, 8, DustID.PurpleTorch, out Dust d)) {
						d.noGravity = true;
						d.velocity = Main.rand.NextVector2Circular(1.5f, 1.5f);
					}
					if (Once(CastRelease)) {
						SoundEngine.PlaySound(SoundID.Item20 with { Pitch = 0.3f }, HandWorld);
					}
					break;
				case Phase.Croak:
					if (Once(12)) {
						SoundEngine.PlaySound(SoundID.Zombie13 with { Pitch = -0.3f, Volume = 0.9f }, NPC.Center);   // the swell
					}
					if (Once(CroakRelease)) {
						SoundEngine.PlaySound(SoundID.Zombie13 with { Pitch = -0.8f, Volume = 1f }, NPC.Center);     // the croak
						Punch(NPC.Center, 2.5f, 14);
					}
					break;
				case Phase.Tongue:
					if (Once(2)) {
						SoundEngine.PlaySound(SoundID.Item95 with { Pitch = -0.4f, Volume = 0.6f }, MouthWorld);
					}
					if (Once(TongueAim)) {
						SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.6f }, MouthWorld);
					}
					break;
				case Phase.Fizzle:
					if (Once(4)) {
						SoundEngine.PlaySound(SoundID.Item16 with { Pitch = 0.4f, Volume = 0.7f }, HandWorld);      // pfft
						for (int i = 0; i < 14; i++) {
							if (SafeSpawn.TryNewDust(HandWorld - new Vector2(8f), 16, 16, DustID.Smoke, out Dust smoke)) {
								smoke.velocity = Main.rand.NextVector2Circular(2f, 2f) - Vector2.UnitY;
								smoke.scale = 1.4f;
							}
						}
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
			if (t < BurstTick && t % 24 == 6) {
				SoundEngine.PlaySound(SoundID.Item2 with { Pitch = -0.6f + t * 0.004f, Volume = 0.7f }, NPC.Center);   // it swells
				Spores(NPC.Center + Main.rand.NextVector2Circular(30f, 40f), 3, 1.5f);
			}
			if (Once(BurstTick)) {
				SoundEngine.PlaySound(SoundID.NPCDeath1 with { Pitch = -0.5f, Volume = 1f }, NPC.Center);
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = 0.3f, Volume = 0.8f }, NPC.Center);
				Punch(NPC.Center, 6f, 30);
				Burst();
			}
		}

		/// <summary>It bursts: head, body and seat gores and a cloud of glowing spores.</summary>
		private void Burst() {
			if (burst) {
				return;
			}
			burst = true;
			string[] gores = { "Fungimancer_GoreHead", "Fungimancer_GoreBody", "Fungimancer_GoreSeat" };
			for (int k = 0; k < gores.Length; k++) {
				if (Mod.TryFind(gores[k], out ModGore gore)) {
					Vector2 at = Origin + new Vector2(-30f, -110f + k * 40f);
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), at, new Vector2(Main.rand.NextFloat(-3f, 3f), Main.rand.NextFloat(-5f, -2f)), gore.Type, out _);
				}
			}
			Spores(NPC.Center, CogpunkClientConfig.RollEffect() ? 80 : 24, 7f);
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

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			if (burst) {
				return false;
			}
			bool dummy = NPC.IsABestiaryIconDummy;
			Texture2D middle = TextureAssets.Npc[Type].Value;
			Vector2 anchor = (dummy ? NPC.Bottom : Origin) - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;                  // the art faces left
			Color light = NPC.GetAlpha(drawColor);
			int body = dummy ? R.Idle : BodyFrame();
			float shift = dummy ? 0f : MaxParallax;
			Vector2 farShift = new(DepthLayers.Shift(anchor, DepthLayers.Far, shift).X, 0f);
			Vector2 nearShift = new(DepthLayers.Shift(anchor, DepthLayers.Near, shift).X, 0f);
			if (farSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, farSheet.Value, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor + farShift, 0, DepthLayers.Tint(light, DepthLayers.Far), flip);
			}
			DepthLayers.DrawCell(spriteBatch, middle, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY, anchor, 0, light, flip);
			if (nearSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, nearSheet.Value, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor + nearShift, 0, light, flip);
			}
			if (glowSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, glowSheet.Value, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor, 0, Color.White * NPC.Opacity, flip);
			}
			if (!dummy && CurrentPhase == Phase.Tongue && Timer < TongueAim && aim != Vector2.Zero) {
				DrawAim(MouthWorld, aim, 0.4f + 0.6f * Timer / TongueAim);
			}
			return false;
		}

		/// <summary>The tongue's telegraph: 2 px violet dots every 12 px from the mouth towards the aim, out to the tongue's
		/// reach, added onto the scene.</summary>
		private static void DrawAim(Vector2 from, Vector2 to, float strength) {
			Texture2D dot = TextureAssets.MagicPixel.Value;
			Vector2 dir = (to - from).SafeNormalize(Vector2.Zero);
			int count = (int)(FungimancerTongue.Range / 12f);
			Color c = new Color(198, 189, 255, 0) * strength;
			for (int i = 1; i <= count; i++) {
				Vector2 p = from + dir * (i * 12f) - Main.screenPosition;
				Main.spriteBatch.Draw(dot, new Rectangle((int)DepthLayers.Snap(p.X), (int)DepthLayers.Snap(p.Y), 2, 2), c);
			}
		}
	}
}
