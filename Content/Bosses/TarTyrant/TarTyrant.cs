using System;
using System.IO;
using Cogpunk.Content.Bosses.TarTyrant.Items;
using Cogpunk.Content.Junkyard;
using Cogpunk.Content.Junkyard.NPCs;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Chat;
using Terraria.DataStructures;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.TarTyrant.TarTyrantRigData;

namespace Cogpunk.Content.Bosses.TarTyrant
{
	/// <summary>
	/// Tar Tyrant, the Junkyard tar pool's boss, fished out of the tar with a <see cref="Summon.Scrapworm"/> (the way the
	/// Truffle Worm calls Duke Fishron). Reworked 2026-10-29 (user): a mass of tar with the bones of a dinosaur sticking
	/// out of it (a Tyrannosaurus skull for a head, a ridge of spines, ribs, a femur in its back, a bone claw), T3 (after
	/// Skeletron, anchor Deerclops), three planes, every animation tweened from key poses. (A redraw from the user's
	/// reference painting replaced this look for a few hours the same day; the user asked for this one back, on the
	/// redraw's animation; on 2026-10-30 the user asked for a fusion: this design's colours and bones on the redraw's
	/// hunched, less round build, with its horns on the skull.)
	/// <para><b>Loop:</b> <see cref="DowntimeTicks"/> (3 s; <see cref="EnragedDowntimeTicks"/> enraged) of oozing after its
	/// target between attacks, then one attack: too far (<see cref="FarRange"/>, or out of reach for
	/// <see cref="OutOfReachTicks"/>, King Slime's rule) it <b>melts</b> into the ground and rises where the target will
	/// be in a second; otherwise, at random and never twice in a row, it <b>burps</b> three bubbles that grow and burst
	/// into Living Tar, <b>spits</b> a fan of three globs that leave tar on the ground, or raises its claw and
	/// <b>summons</b> a screen-wide row of bone spikes out of the ground. All fight long, on its own, its back heaves and
	/// <b>flings bones</b> every 3.5 s (<see cref="VentInterval"/>: three bones that bounce once). Every telegraph is 30
	/// ticks or more (D3, T0-T4), and every hit it lands gives <see cref="PlagueTicks"/> of Tar Plague (the user's "tar
	/// poisoning").</para>
	/// <para><b>Shedding tar:</b> every 2% of its life lost a Living Tar splashes off it (<see cref="SpawnLostTar"/>, at
	/// most <see cref="MaxSlimes"/> alive) and it shrinks by 1% (<see cref="Size"/>: half its size at the end, like vanilla's
	/// King Slime; the sprite is drawn scaled, the hitboxes and the AI points follow).</para>
	/// <para><b>Enrage</b> at a third of its life, with its own attack (<see cref="Phase.Rage"/>): it growls, melts away,
	/// and a tar claw comes up out of the ground under its target five times (a "!" and a boiling patch 8 tiles wide, 1.5 s
	/// to get out), then it rises on the other side of the target, roars, and attacks every 1.5 s from then on.</para>
	/// <para><b>Focus</b> (the rule for every boss since 2026-11-09, <see cref="BossNPC"/>): it hunts the player who does the
	/// most damage, switching to the top damage dealer among the others every 5 s; with no damage yet, the closest player
	/// (in the Junkyard first: <see cref="TargetTieBreak"/>). It glides on the ground, so it is not a floaty boss.</para>
	/// <para>Boss-fight rules (user, 2026-10-26): rises with a title card under a camera lock; dies in a camera-locked
	/// cinematic (the tar lets go of the bones and runs back into its puddle) with the "Defeated" card
	/// (<see cref="BossNPC"/>); no natural spawns around it; melts away when nobody has been in the Junkyard for
	/// <see cref="LeaveGraceTicks"/>; hitboxes follow the art (<see cref="R.Hit"/> strips, scaled with it).</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/bosses.csv; anchor Deerclops, Expert 11900 life / 10 defense / 40
	/// contact / 52 ice spikes / 72 debris): <see cref="ExpertLife"/> life (+35% per extra player), <see cref="BaseDefense"/>
	/// defense, <see cref="ExpertContactDamage"/> contact; glob <see cref="GlobDamage"/>, bone spike <see cref="SpikeDamage"/>,
	/// flung bone <see cref="BackBoneDamage"/> (the user's "small damage"), claw <see cref="ClawDamage"/> (user-set).
	/// Loot (<see cref="TarTyrantLoot"/>): Bones, Tar Drops, at least one piece of the Tyrant armor; the Serene Tear in the
	/// bag.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer (<see cref="StateMachineNPC"/>), <c>ai[2]</c> spare, <c>ai[3]</c>
	/// the enraged flag; the melt's and the rage's destination and the bone volley's count in <see cref="SendExtraAI"/>. The
	/// server decides, targets and spawns; the ooze, the surface following, the size (from the synced life), the volley's
	/// count and the pose run on every side.</para>
	/// </summary>
	[AutoloadBossHead]
	public partial class TarTyrant : BossNPC
	{
		public enum Phase { Emerge, Idle, Burp, Spit, Melt, Summon, Rage, Retreat, Dying }

		// --- stats (Expert, docs/balance/bosses.csv) -------------------------------------------------------------------
		// 2026-11-18 (user: every boss 10-35% over its tier's vanilla boss, by difficulty): Deerclops's 11900 + 20% (it was 11000)
		public const int ExpertLife = 14300;
		public const float LifePerExtraPlayer = 0.35f;
		public const int BaseDefense = 12;
		public const int ExpertContactDamage = 50;
		public const int GlobDamage = 50, SpikeDamage = 55, BackBoneDamage = 30, ClawDamage = 125;
		/// <summary>Tar Plague from every hit (user, 2026-10-29: "tar poisoning for 1 second").</summary>
		public const int PlagueTicks = 60;
		public const float EnrageLifeFraction = 0.33f;

		// --- shedding tar: a Living Tar and 1% of its size every 2% of its life (user, 2026-10-29) ------------------------
		public const int SizeSteps = 50;
		public const float ShrinkPerStep = 0.01f;
		public const int MaxSlimes = 12;
		public const int MaxSlimesPerTick = 2;

		// --- size, pacing, targeting -----------------------------------------------------------------------------------
		public const int HitboxWidth = R.BodyRight - R.BodyLeft;
		public const int HitboxHeight = -R.BodyTop;
		public const int RigShiftX = (R.BodyLeft + R.BodyRight) / 2;
		public const int DowntimeTicks = 180, EnragedDowntimeTicks = 90;   // user-set: 3 s, 1.5 s enraged
		public const float OozeSpeed = 1.6f, EnragedOozeSpeed = 2.2f;
		public const float OozeAccel = 0.06f;
		public const float HoldDistance = 9f * 16f;        // it stops oozing this close to its target
		public const float FarRange = 45f * 16f;           // farther than this: it melts and rises at the target
		public const int OutOfReachTicks = 180;            // far, out of sight, or 12+ tiles above or below this long: the same,
		public const int MinDowntimeTicks = 30;            // even before the downtime ends (but not right after an attack)
		public const float ReachHeight = 12f * 16f;
		public const int ResyncInterval = 60;
		public const float DespawnRange = 300f * 16f;
		public const int LeaveGraceTicks = 60;
		public const int JunkyardCheckInterval = 10;

		// --- intro, retreat, death -----------------------------------------------------------------------------------------
		public const int RiseTicks = 120, RoarTicks = 60;
		public const int EmergeTicks = RiseTicks + RoarTicks;
		public const int TitleTick = 70;
		public const int TitleHoldTicks = EmergeTicks - TitleTick + 45;
		public const int CameraEaseTicks = 30;
		public const float CameraLockRange = 150f * 16f;
		public const int RetreatTicks = 60;
		public const int DeathTicks = 300;
		public const int DeathCardTick = 262;
		public const int DeathSinkTick = 290;

		private static LocalizedText epithet;
		private static readonly Phase[] RandomPool = { Phase.Burp, Phase.Spit, Phase.Summon };

		private Phase CurrentPhase => (Phase)State;
		public bool Enraged => NPC.ai[3] == 1f;

		private ref float TitleShown => ref NPC.localAI[0];
		private ref float LastEffectKey => ref NPC.localAI[1];

		/// <summary>Where the melt (or the rage) brings it back up: synced in <see cref="SendExtraAI"/>.</summary>
		private Vector2 destination;

		private bool playerScaled;
		private int outsideTicks;
		private int outOfReach;
		private int lastAttack = -1;
		private int shedSteps;
		private int sizeStep = -1;
		private int rageSide = 1;
		private float rageDistance = 24f * 16f;

		protected override int DyingState => (int)Phase.Dying;
		protected override int DeathAnimationTicks => DeathTicks;
		protected override int DefeatCardTick => DeathCardTick;

		public bool IsEmerging => CurrentPhase == Phase.Emerge;

		/// <summary>2% steps of life lost (0..49), from the synced life.</summary>
		public int LostSteps => NPC.lifeMax <= 0 ? 0 : Math.Clamp((int)((long)(NPC.lifeMax - Math.Max(0, NPC.life)) * SizeSteps / NPC.lifeMax), 0, SizeSteps - 1);

		/// <summary>1 at full life, 1% smaller every 2% of life lost (0.51 at the end).</summary>
		public float Size => 1f - ShrinkPerStep * LostSteps;

		/// <summary>The rig origin (the ground point under the mass) in the world.</summary>
		public Vector2 RigOrigin => NPC.Bottom + new Vector2(RigShiftX * Size * NPC.spriteDirection, 0f);

		public Vector2 CameraFocus => RigOrigin - new Vector2(0f, 110f * Size);

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 1;
			NPCID.Sets.MPAllowedEnemies[Type] = true;
			NPCID.Sets.BossBestiaryPriority.Add(Type);
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;      // tar
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Oiled] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][ModContent.BuffType<TarPlague>()] = true;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() {
				Scale = 0.4f,
				PortraitScale = 0.55f,
				PortraitPositionYOverride = 40f,
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
			NPC.damage = ExpertStats.Base(ExpertContactDamage);
			NPC.knockBackResist = 0f;
			NPC.HitSound = SoundID.NPCHit1 with { Pitch = -0.6f };
			NPC.DeathSound = SoundID.NPCDeath1 with { Pitch = -0.6f };
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.boss = true;
			NPC.npcSlots = 10f;
			NPC.aiStyle = -1;
			NPC.value = Item.buyPrice(gold: 5);           // Deerclops' 5 gold (terraria.wiki.gg)
			NPC.SpawnWithHigherTime(30);
			if (!Main.dedServ) {
				Music = MusicID.Boss3;                       // vanilla's "Boss 3" until his own track (user, 2026-11-26)
			}
		}

		/// <summary>Expert and Master: Expert lands exactly on <see cref="ExpertLife"/> and <see cref="ExpertContactDamage"/>;
		/// Master keeps vanilla's boss adjustment; +35% life per extra player (as Trash-Tr0m).</summary>
		public override void ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment) {
			NPC.lifeMax = (int)Math.Round(ExpertStats.Snap(NPC.lifeMax, ExpertLife) * bossAdjustment * PlayerFactor(numPlayers));
			NPC.damage = ExpertStats.Snap(NPC.damage, ExpertContactDamage);
			playerScaled = true;
		}

		public static float PlayerFactor(int players) => 1f + LifePerExtraPlayer * Math.Max(0, players - 1);

		/// <summary>Server or singleplayer: Classic player scaling, and the "has awoken" announcement (vanilla's
		/// <c>NPC.SpawnOnPlayer</c> makes it, but a fished-out NPC comes through <c>NPC.NewNPC</c>, decompiled
		/// <c>Player.ItemCheck_CheckFishingBobber_PullBobber</c> / message 130).</summary>
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
			FaceTarget();
			Color purple = new(175, 75, 255);
			if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey("Announcement.HasAwoken", NPC.GetTypeNetName()), purple);
			}
			else {
				Main.NewText(Language.GetTextValue("Announcement.HasAwoken", NPC.TypeName), purple);
			}
			NPC.netUpdate = true;
		}

		public override void SendExtraAI(BinaryWriter writer) {
			writer.Write(NPC.lifeMax);
			writer.Write(NPC.life >= NPC.lifeMax);
			writer.Write(destination.X);
			writer.Write(destination.Y);
			writer.Write((short)ventTimer);
		}

		public override void ReceiveExtraAI(BinaryReader reader) {
			int lifeMax = reader.ReadInt32();
			bool full = reader.ReadBoolean();
			float x = reader.ReadSingle();
			float y = reader.ReadSingle();
			int vent = reader.ReadInt16();
			if (lifeMax > 0 && lifeMax != NPC.lifeMax) {
				NPC.lifeMax = lifeMax;
				if (full) {
					NPC.life = lifeMax;
				}
			}
			destination = float.IsFinite(x) && float.IsFinite(y) ? new Vector2(x, y) : Vector2.Zero;
			ventTimer = Math.Clamp(vent, 0, VentInterval);         // the server's count: the telegraph lines up with the volley
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				ModContent.GetInstance<JunkyardBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		/// <summary>A bag per player in Expert/Master (vanilla <c>ItemDropRule.BossBag</c>), its contents in Classic
		/// (<see cref="TarTyrantLoot"/>).</summary>
		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.BossBag(ModContent.ItemType<TarTyrantBag>()));
			npcLoot.Add(Manuals.ManualDrop.Of<Manuals.Items.StickyPages>());   // 2026-11-17: one per player, first defeat
			LeadingConditionRule classic = new(new Conditions.NotExpert());
			TarTyrantLoot.AddClassic(classic);
			npcLoot.Add(classic);
		}

		public override void BossLoot(ref int potionType) {
			potionType = ItemID.HealingPotion;             // Deerclops' (T3)
		}

		public override bool CanHitPlayer(Player target, ref int cooldownSlot) {
			cooldownSlot = ImmunityCooldownID.Bosses;
			return !Harmless;
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			target.AddBuff(ModContent.BuffType<TarPlague>(), PlagueTicks);
		}

		// ------------------------------------------------------------------------------------------------------------
		// State machine (every side; only the server changes state)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>Under the tar: nothing can touch it and it touches nothing.</summary>
		public bool Submerged {
			get {
				int t = (int)Timer;
				return CurrentPhase switch {
					Phase.Emerge => t < EmergeSolidTick,
					Phase.Melt => t >= MeltGoneTick && t < MeltUnderTick + MeltUnderTicks + RiseSolidTick,
					Phase.Rage => t >= RageGrowlTicks + MeltGoneTick && t < RageRiseTick + RiseSolidTick,
					Phase.Retreat => t >= MeltGoneTick,
					_ => false,
				};
			}
		}

		/// <summary>Can't be hurt: the intro, transitions, the death and anything under the tar.</summary>
		private bool Untouchable => Submerged || CurrentPhase == Phase.Emerge || CurrentPhase == Phase.Rage || CurrentPhase == Phase.Retreat
			|| CurrentPhase == Phase.Dying;

		/// <summary>Hurts nothing: as <see cref="Untouchable"/> (the rise out of a melt does hurt, once its bones are out).</summary>
		private bool Harmless => Submerged || CurrentPhase == Phase.Emerge || CurrentPhase == Phase.Rage || CurrentPhase == Phase.Retreat
			|| CurrentPhase == Phase.Dying;

		protected override void UpdateBoss() {
			TarTyrantSystem.Track(NPC.whoAmI);
			if (!Main.dedServ) {
				ResetEffectKeys();
			}
			UpdateSize();
			NPC.dontTakeDamage = Untouchable;
			switch (CurrentPhase) {
				case Phase.Emerge:
					NPC.velocity.X = 0f;
					if (Timer >= EmergeTicks && Retarget()) {
						StartIdle();
					}
					break;
				case Phase.Idle:
					DoIdle();
					break;
				case Phase.Burp:
					Brake();
					DoBurp();
					break;
				case Phase.Spit:
					Brake();
					DoSpit();
					break;
				case Phase.Melt:
					NPC.velocity.X = 0f;
					DoMelt();
					break;
				case Phase.Summon:
					Brake();
					DoSummon();
					break;
				case Phase.Rage:
					NPC.velocity.X = 0f;
					DoRage();
					break;
				case Phase.Retreat:
					NPC.velocity.X = 0f;
					if (Timer >= RetreatTicks && IsAuthority) {
						NPC.active = false;
						if (Main.netMode == NetmodeID.Server) {
							NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
						}
					}
					break;
				case Phase.Dying:
					NPC.velocity.X *= 0.9f;
					UpdateDeath();
					break;
				default:
					StartIdle();                               // an unknown state from a newer version (D0)
					break;
			}
			UpdateVent();
			if (CurrentPhase != Phase.Dying && CurrentPhase != Phase.Retreat) {
				if (IsAuthority) {
					SpawnLostTar();
					if (CurrentPhase != Phase.Emerge && CurrentPhase != Phase.Rage && CurrentPhase != Phase.Melt) {
						TrackReach(TargetPlayer);
					}
				}
				CheckJunkyard();
			}
			FollowSurface();
			KeepInWorld();
			if (!Main.dedServ) {
				StateEffects();
			}
		}

		/// <summary>Every side, when the 2% step changes: the NPC rectangle follows <see cref="Size"/>, bottom kept.</summary>
		private void UpdateSize() {
			int step = LostSteps;
			if (step == sizeStep) {
				return;
			}
			sizeStep = step;
			Vector2 bottom = NPC.Bottom;
			NPC.scale = Size;
			NPC.width = Math.Max(16, (int)(HitboxWidth * Size));
			NPC.height = Math.Max(16, (int)(HitboxHeight * Size));
			NPC.Bottom = bottom;
		}

		private void StartIdle() {
			if (!IsAuthority) {
				return;
			}
			ChangeState((int)Phase.Idle);
		}

		private void Brake() {
			NPC.velocity.X *= 0.85f;
		}

		/// <summary>The downtime between attacks: it oozes after its target, then picks the next attack.</summary>
		private void DoIdle() {
			Player target = TargetPlayer;
			float speed = Enraged ? EnragedOozeSpeed : OozeSpeed;
			float want = 0f;
			if (target != null) {
				float dx = target.Center.X - NPC.Center.X;
				if (Math.Abs(dx) > HoldDistance * Size + NPC.width * 0.5f) {
					want = Math.Sign(dx) * speed;
				}
				if (Math.Abs(dx) > 16f) {
					NPC.direction = NPC.spriteDirection = Math.Sign(dx);
				}
			}
			NPC.velocity.X += MathHelper.Clamp(want - NPC.velocity.X, -OozeAccel, OozeAccel);
			if (!IsAuthority) {
				return;
			}
			if ((int)Timer % ResyncInterval == 0) {
				NPC.netUpdate = true;
			}
			if (!Enraged && NPC.life <= NPC.lifeMax * EnrageLifeFraction) {
				StartRage();
				return;
			}
			bool rest = Timer >= (Enraged ? EnragedDowntimeTicks : DowntimeTicks);
			bool chase = outOfReach >= OutOfReachTicks && Timer >= MinDowntimeTicks;
			if ((rest || chase) && Retarget()) {
				PickAttack();
			}
		}

		/// <summary>Server, every tick it is up and fighting (attacks included): counts how long the target has been out of
		/// its reach (farther than <see cref="FarRange"/>, far above or below it, or out of sight), King Slime's rule.</summary>
		private void TrackReach(Player target) {
			bool away = target != null && (Math.Abs(target.Center.X - RigOrigin.X) > FarRange || Math.Abs(target.Center.Y - NPC.Center.Y) > ReachHeight
				|| !Collision.CanHitLine(NPC.Center, 0, 0, target.Center, 0, 0));
			outOfReach = away ? outOfReach + 1 : 0;
		}

		/// <summary>Server: the next attack. Far (or out of reach): the melt; otherwise burp, spit or summon at random, never
		/// the same twice in a row.</summary>
		private void PickAttack() {
			FaceTarget();
			Player target = TargetPlayer;
			float dx = target != null ? Math.Abs(target.Center.X - RigOrigin.X) : 0f;
			Phase next;
			if (target != null && (dx > FarRange || outOfReach >= OutOfReachTicks)) {
				next = Phase.Melt;
			}
			else {
				int pick = Main.rand.Next(RandomPool.Length);
				if ((int)RandomPool[pick] == lastAttack) {
					pick = (pick + 1 + Main.rand.Next(RandomPool.Length - 1)) % RandomPool.Length;
				}
				next = RandomPool[pick];
			}
			lastAttack = (int)next;
			outOfReach = 0;
			destination = Vector2.Zero;                    // a new melt picks its own spot (synced with the state change)
			ChangeState((int)next);
		}

		private void EndAttack() {
			if (Retarget()) {
				StartIdle();
			}
		}

		private Player TargetPlayer => NPC.target >= 0 && NPC.target < Main.maxPlayers && Main.player[NPC.target].active && !Main.player[NPC.target].dead
			? Main.player[NPC.target] : null;

		/// <summary>A rig point (art px, left-facing) of <paramref name="frame"/> in the world, scaled with <see cref="Size"/>.</summary>
		public Vector2 RigPoint(short[] points, int frame) {
			int i = frame * 2;
			if (i < 0 || i + 1 >= points.Length) {
				return NPC.Center;
			}
			float x = NPC.spriteDirection == 1 ? -points[i] : points[i];   // the art faces left: mirror when facing right
			return RigOrigin + new Vector2(x, points[i + 1]) * Size;
		}

		protected override void OnDeathStarted() {
			destination = Vector2.Zero;
			NPC.netUpdate = true;
		}

		// --- targeting: whoever hurts it most ----------------------------------------------------------------------------

		/// <summary>Server: a living player within <see cref="DespawnRange"/> can be its target.</summary>
		protected override bool CanTarget(Player player) {
			return player != null && player.active && !player.dead
				&& Vector2.DistanceSquared(player.Center, NPC.Center) <= DespawnRange * DespawnRange;
		}

		/// <summary>Among equal damage (no one has hurt it yet): the closest, players in the Junkyard first.</summary>
		protected override float TargetTieBreak(Player player) {
			float d = Vector2.DistanceSquared(player.Center, NPC.Center);
			return !JunkyardSystem.Exists || JunkyardSystem.Contains(player.Center) ? d : d * 4f;
		}

		/// <summary>Server: keeps a target (the shared rule picks and switches it, <see cref="BossNPC"/>); melts away if there
		/// is nobody. True while fighting.</summary>
		private bool Retarget() {
			if (!IsAuthority) {
				return true;
			}
			if (EnsureTarget()) {
				return true;
			}
			ChangeState((int)Phase.Retreat);
			return false;
		}

		private void FaceTarget() {
			Player target = TargetPlayer;
			if (target != null) {
				NPC.direction = NPC.spriteDirection = target.Center.X >= NPC.Center.X ? 1 : -1;
			}
		}

		// --- shedding tar ------------------------------------------------------------------------------------------------

		/// <summary>Server: a Living Tar splashes off the mass for every 2% step of life lost (at most
		/// <see cref="MaxSlimesPerTick"/> a tick: a big hit pays the rest next tick). Past <see cref="MaxSlimes"/> alive a step
		/// passes without one (D0: bounded).</summary>
		private void SpawnLostTar() {
			int steps = LostSteps;
			if (shedSteps >= steps || Submerged) {
				return;
			}
			int type = ModContent.NPCType<LivingTar>();
			int alive = 0;
			foreach (NPC other in Main.ActiveNPCs) {
				if (other.type == type) {
					alive++;
				}
			}
			for (int k = 0; k < MaxSlimesPerTick && shedSteps < steps; k++) {
				shedSteps++;
				if (alive >= MaxSlimes) {
					continue;
				}
				Vector2 at = RigPoint(R.Core, ResolveFrame(false));
				if (SafeSpawn.TryNewNPC(NPC.GetSource_FromAI(), (int)at.X, (int)at.Y, type, out NPC slime)) {
					alive++;
					if (slime.ModNPC is LivingTar tar) {
						tar.FromBoss = true;
					}
					slime.velocity = new Vector2(Main.rand.NextFloat(1.5f, 4f) * (Main.rand.NextBool() ? 1 : -1), -Main.rand.NextFloat(4f, 7f));
					slime.target = NPC.target;
					slime.netUpdate = true;
				}
			}
		}

		// --- the enrage ----------------------------------------------------------------------------------------------------

		/// <summary>Server: a third of its life gone: enraged for good, and the rage attack starts. It will come back on the
		/// other side of its target, as far away as it is now (clamped).</summary>
		private void StartRage() {
			NPC.ai[3] = 1f;
			Player target = TargetPlayer;
			if (target != null) {
				float dx = RigOrigin.X - target.Center.X;
				rageSide = dx >= 0f ? 1 : -1;
				rageDistance = MathHelper.Clamp(Math.Abs(dx), RageMinDistance, RageMaxDistance);
			}
			destination = Vector2.Zero;
			ChangeState((int)Phase.Rage);
		}

		/// <summary>Server: sinks away when no living player has been in the Junkyard for <see cref="LeaveGraceTicks"/>
		/// (checked every <see cref="JunkyardCheckInterval"/> ticks). Worlds without a Junkyard skip the rule.</summary>
		private void CheckJunkyard() {
			if (!IsAuthority || !JunkyardSystem.Exists || CurrentPhase == Phase.Emerge || Hidden || (int)Timer % JunkyardCheckInterval != 0) {
				return;
			}
			bool anyone = false;
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && JunkyardSystem.Contains(player.Center)) {
					anyone = true;
					break;
				}
			}
			outsideTicks = anyone ? 0 : outsideTicks + JunkyardCheckInterval;
			if (outsideTicks >= LeaveGraceTicks) {
				outsideTicks = 0;
				ChangeState((int)Phase.Retreat);
			}
		}

		private void KeepInWorld() {
			float min = 60f * 16f;
			float max = (Main.maxTilesX - 60) * 16f;
			if (NPC.Center.X + NPC.velocity.X < min || NPC.Center.X + NPC.velocity.X > max) {
				NPC.velocity.X = 0f;
			}
		}

		/// <summary>Moves it so its rig origin stands on <paramref name="spot"/> (a ground point); the server syncs it.</summary>
		private void MoveTo(Vector2 spot) {
			NPC.Bottom = new Vector2(spot.X - RigShiftX * Size * NPC.spriteDirection, spot.Y);
			NPC.velocity = Vector2.Zero;
			if (IsAuthority) {
				NPC.netUpdate = true;
			}
		}

		// --- surface following: it glides on ground and on liquid (every side; tiles and liquids are synced) --------------

		public const int ClimbRows = 8, DropRows = 24;
		public const float ClimbSpeed = 3f, FallAcceleration = 0.4f, MaxFallSpeed = 12f;
		private const float SurfaceSampleOffset = 5f * 16f;

		private void FollowSurface() {
			if (Hidden) {
				NPC.velocity.Y = 0f;                             // under the surface
				return;
			}
			float bottom = NPC.Bottom.Y;
			float best = float.MaxValue;
			for (int s = -1; s <= 1; s++) {
				float y = FindSurface(NPC.Center.X + NPC.velocity.X + s * SurfaceSampleOffset * Size, bottom, out _);
				if (y < best) {
					best = y;
				}
			}
			if (best == float.MaxValue && Holds((int)(NPC.Center.X / 16f), (int)((bottom - 8f) / 16f), out bool wet) && !wet) {
				NPC.velocity.Y = -ClimbSpeed;                    // inside a wall taller than the window: climb out of it
				NPC.velocity.X = 0f;
				return;
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

		/// <summary>Top of the first solid tile or liquid surface in the column under <paramref name="worldX"/>, from
		/// <see cref="ClimbRows"/> above <paramref name="bottom"/> to <see cref="DropRows"/> below; float.MaxValue if none.
		/// At most ClimbRows + DropRows + 1 bounds-checked reads (D0).</summary>
		public static float FindSurface(float worldX, float bottom, out bool liquid) {
			return FindSurface(worldX, bottom, ClimbRows, DropRows, out liquid);
		}

		/// <summary>The same with its own window: <paramref name="up"/> rows above to <paramref name="down"/> rows below
		/// (each at most 64, D0).</summary>
		public static float FindSurface(float worldX, float bottom, int up, int down, out bool liquid) {
			up = Math.Clamp(up, 0, 64);
			down = Math.Clamp(down, 0, 64);
			int x = (int)(worldX / 16f);
			int row = (int)(bottom / 16f);
			int top = row - up;
			bool airAbove = !Holds(x, top - 1, out _);
			for (int y = top; y <= row + down; y++) {
				bool holds = Holds(x, y, out liquid);
				if (holds && airAbove) {
					return y * 16f + (liquid ? 16f - LiquidPixels(x, y) : 0f);
				}
				airAbove = !holds;
			}
			liquid = false;
			return float.MaxValue;
		}

		private static bool Holds(int x, int y, out bool liquid) {
			liquid = false;
			if (!TileSafety.TryGetTile(x, y, out Tile tile, 1)) {
				return false;
			}
			if (tile.HasTile && !tile.IsActuated && (Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType])) {
				return true;
			}
			if (tile.LiquidAmount > 64) {
				liquid = true;
				return true;
			}
			return false;
		}

		private static float LiquidPixels(int x, int y) {
			return TileSafety.TryGetTile(x, y, out Tile tile, 1) ? tile.LiquidAmount / 16f : 16f;
		}

		/// <summary>A ground point at <paramref name="worldX"/> near the height <paramref name="nearY"/> (a wide window); false if
		/// the column has nothing to stand on there.</summary>
		public static bool TryGround(float worldX, float nearY, out Vector2 ground) {
			float y = FindSurface(worldX, nearY, 14, 30, out _);
			ground = new Vector2(worldX, y);
			return y != float.MaxValue;
		}

		public override void OnKill() {
			NPC.SetEventFlagCleared(ref TarTyrantSystem.DownedFlag, -1);
		}

		public override void BossHeadSlot(ref int index) {
			if (Submerged || Hidden) {
				index = -1;                                    // under the tar: no map icon
			}
		}
	}
}
