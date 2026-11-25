using System;
using System.IO;
using Cogpunk.Content.Bosses.Jadey.Items;
using Cogpunk.Content.Coghaven;
using Cogpunk.Content.Coghaven.Generation;
using Cogpunk.Content.Gems.Buffs;
using Cogpunk.Core.Combat;
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
using R = Cogpunk.Content.Bosses.Jadey.JadeyRigData;

namespace Cogpunk.Content.Bosses.Jadey
{
	/// <summary>
	/// Jadey, a Molda-Jade, Coghaven's boss (user-set 2026-11-16): "a panda jademancer" who guards the Jade Vault in the middle of
	/// the hall under the Main Hall; touching the sealed vault wakes her (<see cref="JadeySummon"/>), and it opens only once she
	/// is dead (<see cref="JadeySystem.Downed"/>). A panda in a jade qipao sitting cross-legged on a floating crimson cushion,
	/// a rope dart of jade in her paw, a jade gem on her brow (art/bosses/jadey/make_jadey_art.py).
	/// <para>The fight (user-set; every number below the user's unless marked):
	/// <list type="bullet">
	/// <item>"she should float and dont cause contact damage depending on its attacks or minions to deal damage": she drifts to
	/// a spot beside and above her target inside the vault (<see cref="HoverX"/>, <see cref="HoverY"/>, my calls), through
	/// blocks, and never hurts by touch (<see cref="CanHitPlayer"/>).</item>
	/// <item>"Jadey should quickly throw a jade coin every 4 seconds during the fight" (<see cref="CoinInterval"/>): flicked from
	/// her far paw, it lands and 0.5 s later becomes a Jade Golem, two Jade Bats or a Jade Beetle, at random
	/// (<see cref="Projectiles.JadeCoin"/>, <see cref="JadeyMinion"/>). My call: no coin while she has
	/// <see cref="MaxMinions"/> minions.</item>
	/// <item>"Jadey should do one of her other attacks every 2 seconds" (<see cref="AttackInterval"/>, from the start of one to
	/// the next; my call: never the same one twice running when another is possible):
	/// <list type="number">
	/// <item><b>Whip</b>: she spins her rope dart for 0.4 s (<see cref="SpinTicks"/>; my call: an aim line shows where it will
	/// fly) and throws it fast at where her target will be (<see cref="Lead"/>), "high damage" (<see cref="DartDamage"/>), on
	/// until it bites a wall or floor, which curses the three tiles for 8 s (<see cref="Projectiles.JadeyRopeDart"/>,
	/// <see cref="Projectiles.JadeCursedGround"/>).</item>
	/// <item><b>Zone</b>: a 12-tile band of glyphs under her target; 1.2 s later everyone on it is turned to jade
	/// (<see cref="Projectiles.JadePetrifyZone"/>).</item>
	/// <item><b>Channel</b> (only with 3+ of her minions up; my call: not again for <see cref="HealCooldown"/> ticks): 1.2 s with
	/// her eyes glowing green, then she consumes her minions and heals 15% of her life (<see cref="HealFraction"/>). My call:
	/// minions killed during the channel aren't eaten; with none left, no heal.</item>
	/// <item><b>Lasers</b>: she aims (<see cref="LaserAim"/>, my call; an aim line) and fires three jade lasers from her brow gem
	/// 0.3 s apart (<see cref="LaserGap"/>), small damage (<see cref="LaserDamage"/>) and a stack each; each may land (a short
	/// immunity after one, <see cref="Gems.JadeCursePlayer.ShortImmunity"/>).</item>
	/// </list></item>
	/// <item>"All attacks of jadey should apply a stack of jade curse to the player hit and she should be immune to jade curse".</item>
	/// <item>"she should despawn if the players leave coghaven" (<see cref="CheckFight"/>): no living player in Coghaven for
	/// <see cref="LeaveGrace"/> ticks and she bows out in a swirl of jade (<see cref="Phase.Leave"/>).</item>
	/// </list></para>
	/// <para>Boss rules (2026-10-26 / 11-09): an intro with a camera lock and a title card (her name and her epithet, "a
	/// Molda-Jade"); a death cinematic under a camera lock: the jade creeps up her from the cushion, she is a statue, it cracks
	/// and bursts (<see cref="BossNPC"/>: the "Defeated" card); no natural spawns near her; DPS targeting with a switch every
	/// 5 s; she is floaty (<see cref="Floaty"/>): a target that fights in melee gets her close, within the Blade of Grass's
	/// reach. Her hitbox is her cushion, body and head from the art (<see cref="R.BodyTop"/>).</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/bosses.csv; Coghaven is T4: anchor the Wall of Flesh, terraria.wiki.gg Expert
	/// 11200 life, 12 defense): <see cref="ExpertLife"/> life (+35% per extra player, as every Cogpunk boss) because her adds
	/// and heals add to it, <see cref="BaseDefense"/> defense, no contact damage. Loot (<see cref="JadeyLoot"/>).</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer; <c>ai[2]</c>/<c>ai[3]</c> the vault's top-left tile (her home: the
	/// arena is reckoned from it); the clocks, the last attack, the heal cooldown and the locked aim in <see cref="SendExtraAI"/>.
	/// The server decides, targets and spawns; the float, the frames and the telegraphs follow the synced state everywhere.
	/// D0: every spawn through <see cref="Core.Safety.SafeSpawn"/>, minions capped, scans bounded and bounds-checked. D1: no
	/// allocation per tick.</para>
	/// </summary>
	[AutoloadBossHead]
	public partial class Jadey : BossNPC
	{
		public enum Phase { Intro, Idle, Whip, Zone, Channel, Laser, Leave, Dying, Statue }

		// --- stats (Expert, docs/balance/bosses.csv) -------------------------------------------------------------------
		// 2026-11-18 (user: every boss 10-35% over its tier's vanilla boss, by difficulty): the Wall of Flesh's 11200 + 10%, the
		// band's bottom because her heals and her invulnerable statue phases lengthen the fight already (it was 7000)
		public const int ExpertLife = 12300;
		public const float LifePerExtraPlayer = 0.35f;
		public const int BaseDefense = 14;
		public const int DartDamage = 90, LaserDamage = 30;                 // "high damage", "small damage" (Expert)

		// --- the cadence -----------------------------------------------------------------------------------------------
		public const int AttackInterval = 120;                              // user-set: an attack every 2 s
		public const int MinIdle = 16;
		public const int CoinInterval = 240;                                // user-set: a coin every 4 s
		public const int MaxMinions = 6;                                    // my call
		public const int FlickTicks = 18;                                   // the far paw's flick (6 frames x 3)

		// --- the attacks -----------------------------------------------------------------------------------------------
		public const int SpinTicks = 24;                                    // user-set: 0.4 s
		public const int WhipTicks = 90;
		public const float LeadMax = 12f * 16f;                             // the most it leads a running target
		public const int ZoneTicks = Projectiles.JadePetrifyZone.SnapTick + 18;
		public const int ZoneGroundScan = 24;
		public const int ChannelTicks = 72, ChannelRecover = 18;            // user-set: 1.2 s
		public const int MinMinionsToChannel = 3;                           // user-set
		public const float HealFraction = 0.15f;                            // user-set
		public const int HealCooldown = 900;                                // my call: 15 s
		public const int LaserAim = 30, LaserGap = 18, LaserShots = 3;      // the gap and the count user-set (0.3 s)
		public const int LaserTicks = LaserAim + LaserGap * (LaserShots - 1) + 18;

		// --- the float -------------------------------------------------------------------------------------------------
		public const float HoverX = 9f * 16f, HoverY = 5f * 16f;
		// the drift (BossNPC's floaty rule, user 2026-11-17): px either way of her hover spot, at range and in her melee hover
		public const float SwayX = 3f * 16f, BobY = 20f, MeleeSwayX = 12f, MeleeBobY = 8f;
		public const float HoverSpeed = 5f, AttackSpeed = 2f, HoverAccel = 0.08f, HoverApproach = 0.06f;
		// the Blade of Grass's reach (BossNPC rule); she eases in over BossNPC.MeleeBlendTicks and tracks at BossNPC.MeleeTrackSpeed
		public const float MeleeGap = 14f, MeleeLift = 6f;
		public const float ArenaMarginX = 3f * 16f, ArenaMarginTop = 2f * 16f, ArenaMarginBottom = 1f * 16f;
		// my calls: with less than this share of HoverX between her target and the wall on her side (and more on the other),
		// she crosses to the other side instead of hanging over a cornered target's head
		public const float WallRoomShare = 0.5f, SideSwitchMargin = 16f;

		// --- intro, leaving, death -------------------------------------------------------------------------------------
		public const int IntroTicks = 150, TitleTick = 50, TitleHoldTicks = 140;
		public const int LeaveTicks = 50;
		public const int DeathTicks = 240, ShatterTick = 196;
		public const int CameraEaseTicks = 30;
		public const float CameraLockRange = 120f * 16f;
		public const int CheckInterval = 30, LeaveGrace = 60;
		// the statue (user-set 2026-11-17: "every 20% health lost she should stop to perform a special attack throwing 3 jade
		// coins that spawn 1-2 random jade minions each and becoming petrified in jade and immune to damage for 8 seconds (or until
		// every minion is killed), if there's still minions alive by the end of the duration she should drain them restoring life")
		public const float StatueStep = 0.2f;                               // user-set: every 20%
		public const int StatueCount = 4;                                   // at 80, 60, 40 and 20% of her life
		public const int StatueCoins = 3, StatueCoinGap = 12;               // user-set: 3 coins (a flick each, 0.2 s apart)
		public const int PetrifyAt = 42, PetrifyTurnTicks = 20;            // she turns to jade once the third coin is away
		public const int StatueTicks = 480;                                 // user-set: 8 s
		public const int StatueMinionGrace = 110;                           // the coins land and hatch before "every minion is killed" counts
		public const int StatueCrackWarn = 30;                              // cracks show for the last 0.5 s of a statue that times out
		public const int StatueMinionCap = 12;                              // her minions at most, statue coins included (D0)
		public const float FightRange = 150f * 16f;

		private static LocalizedText epithet;

		public Phase CurrentPhase => (Phase)State;
		private int HomeX => (int)NPC.ai[2];
		private int HomeY => (int)NPC.ai[3];
		public bool HasHome => HomeX > 0 && HomeY > 0;

		// synced (SendExtraAI)
		private int attackClock, coinClock = CoinInterval - 60, healCooldown, flickTick = -1;
		private byte lastAttack = 255, nextKind, statuesDone;
		private Vector2 aim;
		// the server's own
		private int absentTicks;
		private bool playerScaled;

		protected override int DyingState => (int)Phase.Dying;
		protected override int DeathAnimationTicks => DeathTicks;
		protected override int DefeatCardTick => ShatterTick + 8;
		public override bool Floaty => true;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 1;
			NPCID.Sets.MPAllowedEnemies[Type] = true;
			NPCID.Sets.BossBestiaryPriority.Add(Type);
			NPCID.Sets.SpecificDebuffImmunity[Type][ModContent.BuffType<JadeCurse>()] = true;   // user-set: immune to the jade curse
			NPCID.Sets.SpecificDebuffImmunity[Type][ModContent.BuffType<JadePetrified>()] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][ModContent.BuffType<JadeWard>()] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() {
				Scale = 0.8f,
				PortraitScale = 0.9f,
				PortraitPositionYOverride = 8f,
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
			NPC.damage = 0;                                   // no contact damage (user-set)
			NPC.knockBackResist = 0f;
			NPC.HitSound = SoundID.NPCHit5;
			NPC.DeathSound = null;                            // the statue's burst is her death sound (Visuals)
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.boss = true;
			NPC.npcSlots = 10f;
			NPC.aiStyle = -1;
			NPC.value = Item.buyPrice(gold: 6);
			NPC.SpawnWithHigherTime(30);
			if (!Main.dedServ) {
				Music = MusicID.Boss2;
			}
		}

		/// <summary>Her hitbox: the cushion, the body and the head (the art's box, a little inside the cushion's tassels).</summary>
		public const int HitboxWidth = R.BodyRight - R.BodyLeft, HitboxHeight = -R.BodyTop - 2;   // her body and cushion (2026-11-18:
		                                                                                          // the arms out at her sides)

		/// <summary>Expert lands exactly on <see cref="ExpertLife"/>; Master keeps vanilla's boss adjustment; +35% per extra player.</summary>
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
			writer.Write((short)Math.Clamp(coinClock, short.MinValue, short.MaxValue));
			writer.Write((short)Math.Clamp(healCooldown, 0, short.MaxValue));
			writer.Write((short)Math.Clamp(flickTick, -1, short.MaxValue));
			writer.Write(lastAttack);
			writer.Write(nextKind);
			writer.Write(aim.X);
			writer.Write(aim.Y);
			writer.Write(statuesDone);
			WriteDrift(writer);
		}

		public override void ReceiveExtraAI(BinaryReader reader) {
			int lifeMax = reader.ReadInt32();
			bool full = reader.ReadBoolean();
			attackClock = reader.ReadInt16();
			coinClock = reader.ReadInt16();
			healCooldown = reader.ReadInt16();
			flickTick = reader.ReadInt16();
			lastAttack = reader.ReadByte();
			nextKind = reader.ReadByte();
			float x = reader.ReadSingle(), y = reader.ReadSingle();
			aim = float.IsFinite(x) && float.IsFinite(y) ? new Vector2(x, y) : Vector2.Zero;
			statuesDone = reader.ReadByte();
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
				ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		/// <summary>A bag per player in Expert/Master (vanilla <c>ItemDropRule.BossBag</c>), its contents in Classic.</summary>
		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.BossBag(ModContent.ItemType<JadeyBag>()));
			npcLoot.Add(Manuals.ManualDrop.Of<Manuals.Items.JadeShaperManual>());   // 2026-11-17: one per player, first defeat
			LeadingConditionRule classic = new(new Conditions.NotExpert());
			JadeyLoot.AddClassic(classic);
			npcLoot.Add(classic);
		}

		public override void BossLoot(ref int potionType) {
			potionType = ItemID.HealingPotion;             // Coghaven's tier: before the Wall of Flesh
		}

		/// <summary>She never touches anyone (user-set: "dont cause contact damage").</summary>
		public override bool CanHitPlayer(Player target, ref int cooldownSlot) => false;

		/// <summary>The vault unseals: the world flag (sent with the world data) and a line in the chat.</summary>
		public override void OnKill() {
			NPC.SetEventFlagCleared(ref JadeySystem.DownedFlag, -1);
			if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey("Mods.Cogpunk.NPCs.Jadey.VaultOpens"), new Color(140, 201, 176));
			}
			else if (Main.netMode == NetmodeID.SinglePlayer) {
				Main.NewText(Language.GetTextValue("Mods.Cogpunk.NPCs.Jadey.VaultOpens"), 140, 201, 176);
			}
		}

		public override void BossHeadSlot(ref int index) {
			if (Shattered || CurrentPhase == Phase.Leave) {
				index = -1;
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// The state machine (every side; only the server changes state)
		// ------------------------------------------------------------------------------------------------------------

		private bool Untouchable => CurrentPhase == Phase.Intro || CurrentPhase == Phase.Leave || CurrentPhase == Phase.Dying
			|| (CurrentPhase == Phase.Statue && Timer >= PetrifyAt);

		/// <summary>Turned to jade (the statue's hold): she takes no damage and doesn't move.</summary>
		public bool Petrified => CurrentPhase == Phase.Statue && Timer >= PetrifyAt;

		protected override void UpdateBoss() {
			JadeySystem.Track(NPC.whoAmI);
			NPC.dontTakeDamage = Untouchable;
			if (flickTick >= 0 && ++flickTick > FlickTicks) {
				flickTick = -1;
			}
			switch (CurrentPhase) {
				case Phase.Intro:
					NPC.velocity *= 0.9f;
					FaceTarget();
					if (IsAuthority && Timer >= IntroTicks) {
						if (EnsureTarget()) {
							attackClock = AttackInterval - 40;    // her first attack soon after the intro
							ChangeState((int)Phase.Idle);
						}
						else {
							ChangeState((int)Phase.Leave);
						}
					}
					break;
				case Phase.Idle:
					Float(HoverSpeed);
					if (IsAuthority && StatueDue()) {
						StartStatue();                            // between attacks: a 20% of her life has gone
					}
					else if (IsAuthority && attackClock >= AttackInterval && Timer >= MinIdle) {
						StartAttack();
					}
					break;
				case Phase.Statue:
					NPC.velocity *= Petrified ? 0.8f : 0.9f;
					if (!Petrified) {
						FaceTarget();
					}
					DoStatue();
					break;
				case Phase.Whip:
					Float(AttackSpeed);
					DoWhip();
					break;
				case Phase.Zone:
					Float(AttackSpeed);
					DoZone();
					break;
				case Phase.Channel:
					NPC.velocity *= 0.9f;
					FaceTarget();
					DoChannel();
					break;
				case Phase.Laser:
					Float(AttackSpeed);
					DoLaser();
					break;
				case Phase.Leave:
					NPC.velocity *= 0.9f;
					NPC.velocity.Y -= 0.06f;
					NPC.alpha = Math.Min(255, (int)(Timer * 255f / LeaveTicks));
					if (IsAuthority && Timer >= LeaveTicks) {
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
						ChangeState((int)Phase.Idle);      // an unknown state from a newer version (D0)
					}
					break;
			}
			if (CurrentPhase != Phase.Intro && CurrentPhase != Phase.Leave && CurrentPhase != Phase.Dying) {
				if (CurrentPhase != Phase.Statue) {
					attackClock++;
					UpdateCoin();                                // the coin and the attacks wait while she is a statue
				}
				if (healCooldown > 0) {
					healCooldown--;
				}
				CheckFight();
				TickDrift();
			}
			KeepInArena();
			if (!Main.dedServ) {
				StateEffects();
			}
		}

		protected override void OnDeathStarted() {
			aim = Vector2.Zero;
			flickTick = -1;
			NPC.netUpdate = true;
		}

		// --- the float ---------------------------------------------------------------------------------------------------

		private void FaceTarget() {
			Player target = CurrentTarget;
			if (target != null && Math.Abs(target.Center.X - NPC.Center.X) > 8f) {
				NPC.direction = NPC.spriteDirection = target.Center.X > NPC.Center.X ? 1 : -1;
			}
		}

		/// <summary>Every side: she eases to her spot beside and above her target (close in, at a melee fighter's side), inside the
		/// vault; slower while attacking. The spot hangs round a point that follows her target with a lag and sways side to side and
		/// up and down (BossNPC's drift, user rule 2026-11-17: never a perfect lock-on), a little in her melee hover so she stays in
		/// a blade's reach. She slides into the melee hover over 1.5 s and tracks a melee fighter slowly (BossNPC's melee
		/// approach, user 2026-11-25: "slowly float into melee range and keep traking slowly").</summary>
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
			Vector2 far = focus + new Vector2(RoomySide(side, focus.X) * HoverX + DriftSway * SwayX, -HoverY + DriftBob * BobY);
			Vector2 spot = ClampToArena(Vector2.Lerp(far, near, MeleeAmount));
			FloatSteer(spot, speed, HoverApproach, HoverAccel);
			if (IsAuthority && (int)Timer % 45 == 0) {
				NPC.netUpdate = true;                             // a gentle correction for clients' drift
			}
		}

		/// <summary>The vault's hall in world px (the inside of the shell), reckoned from her home (the vault's top-left tile)
		/// and the blueprint's numbers; empty without a home.</summary>
		public Rectangle Arena => HasHome ? ArenaFor(HomeX, HomeY) : Rectangle.Empty;

		/// <summary>The hall of the vault whose chest's top-left tile is (<paramref name="homeX"/>, <paramref name="homeY"/>), in world
		/// px (the inside of the shell), from the blueprint's numbers (also the Jade Incense's test, <see cref="JadeySummon"/>).</summary>
		public static Rectangle ArenaFor(int homeX, int homeY) {
			int mid = (CoghavenBlueprints.VaultLeft + 1 + CoghavenBlueprints.VaultRight - 1) / 2;
			int chestTop = CoghavenBlueprints.VaultFloor - 2;
			int left = homeX - (mid - (CoghavenBlueprints.VaultLeft + 1));
			int right = homeX + (CoghavenBlueprints.VaultRight - 1 - mid);
			int top = homeY - (chestTop - (CoghavenBlueprints.VaultTop + 1));
			int bottom = homeY + (CoghavenBlueprints.VaultFloor - 1 - chestTop);
			return new Rectangle(left * 16, top * 16, (right - left + 1) * 16, (bottom - top + 1) * 16);
		}

		/// <summary>Her side of the focus, or the other one when the hall's wall leaves less than <see cref="WallRoomShare"/> of
		/// <see cref="HoverX"/> on hers and the other side has <see cref="SideSwitchMargin"/> px more room (no flip-flop in a narrow
		/// hall: the side is read from where she is, so once she has crossed, the roomier side is hers).</summary>
		private float RoomySide(float side, float focusX) {
			Rectangle a = Arena;
			if (a.IsEmpty) {
				return side;
			}
			float x0 = a.Left + ArenaMarginX + NPC.width * 0.5f, x1 = a.Right - ArenaMarginX - NPC.width * 0.5f;
			float room = side < 0f ? focusX - x0 : x1 - focusX;
			float other = side < 0f ? x1 - focusX : focusX - x0;
			return room < HoverX * WallRoomShare && other > room + SideSwitchMargin ? -side : side;
		}

		private Vector2 ClampToArena(Vector2 spot) {
			Rectangle a = Arena;
			if (a.IsEmpty) {
				return spot;
			}
			float x0 = a.Left + ArenaMarginX + NPC.width * 0.5f, x1 = a.Right - ArenaMarginX - NPC.width * 0.5f;
			float y0 = a.Top + ArenaMarginTop + NPC.height * 0.5f, y1 = a.Bottom - ArenaMarginBottom - NPC.height * 0.5f;
			return new Vector2(x0 < x1 ? MathHelper.Clamp(spot.X, x0, x1) : a.Center.X, y0 < y1 ? MathHelper.Clamp(spot.Y, y0, y1) : a.Center.Y);
		}

		/// <summary>She stays in the vault's hall (she floats through blocks: nothing else would keep her in).</summary>
		private void KeepInArena() {
			Rectangle a = Arena;
			if (a.IsEmpty || CurrentPhase == Phase.Leave) {
				return;
			}
			Vector2 next = NPC.Center + NPC.velocity;
			Vector2 inside = new(MathHelper.Clamp(next.X, a.Left + NPC.width * 0.5f, a.Right - NPC.width * 0.5f),
				MathHelper.Clamp(next.Y, a.Top + NPC.height * 0.5f, a.Bottom - NPC.height * 0.5f));
			if (inside != next) {
				NPC.velocity = inside - NPC.Center;
			}
		}

		// --- the fight's bounds ------------------------------------------------------------------------------------------

		/// <summary>Only a living player within <see cref="FightRange"/> may be her target.</summary>
		protected override bool CanTarget(Player player) {
			return player != null && player.active && !player.dead && Vector2.DistanceSquared(player.Center, NPC.Center) <= FightRange * FightRange;
		}

		/// <summary>Server, every <see cref="CheckInterval"/> ticks: no living player inside Coghaven (user: "she should despawn if
		/// the players leave coghaven"; a world without Coghaven: none near) for <see cref="LeaveGrace"/> ticks, she leaves.</summary>
		private void CheckFight() {
			if (!IsAuthority || (int)Timer % CheckInterval != 0) {
				return;
			}
			bool anyIn = false;
			foreach (Player player in Main.ActivePlayers) {
				if (player.dead || Vector2.DistanceSquared(player.Center, NPC.Center) > FightRange * FightRange) {
					continue;
				}
				if (!CoghavenSystem.Exists || CoghavenSystem.Contains(player.Center)) {
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
	}
}
