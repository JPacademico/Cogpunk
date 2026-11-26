using System;
using Cogpunk.Core.Configs;
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
using Terraria.ID;
using Terraria.ModLoader;
using Bat = Cogpunk.Content.Bosses.Jadey.JadeyRigData;
using Beetle = Cogpunk.Content.Jungle.NPCs.RhinoBeetleRigData;
using Golem = Cogpunk.Content.Coghaven.NPCs.JadeGolemRigData;

namespace Cogpunk.Content.Research.Summons
{
	/// <summary>
	/// A jade spirit of the <see cref="JadeCoin"/>: the visible minion (no slot of its own, as vanilla's Abigail), whose form
	/// grows with its owner's <see cref="JadeCoinCounter"/>s: spirit <c>ai[0]</c> = k shows counters 4k+1 .. 4k+4 as
	/// <list type="number">
	/// <item><b>a jade bat</b> (Jadey's, <c>JadeBat.png</c>): flits beside its target and darts through it, a bite a pass;</item>
	/// <item><b>a jade beetle</b> (Jadey's, the Rhino Beetle's rig in jade, its flight frames): backs off on the target's side
	/// and rams straight through it, wings buzzing;</item>
	/// <item><b>a jade golem's arm</b> (Coghaven's golem's own arm sheet; user, 2026-11-26: "instead off a full jade golem the
	/// jade coin should summon a jade golem arm that floats next to the player and shoots jade bolts"; the whole golem until
	/// then): it floats beside its owner on the target's side, hanging when idle, raised and following the target with a
	/// target (the arm sheet's frames, 5 degrees apart: never rotated), and shoots a jade bolt from its palm
	/// (<see cref="JadeSpiritBolt"/>);</item>
	/// <item><b>a jade loong</b> (new art, art/research/make_jade_coin_art.py: user, "like default terraria cloud hard mode loong,
	/// but smaller and jade colored"): a serpent of <see cref="LoongSegments"/> segments that weaves through its target and
	/// coils over its owner when idle; head and body both bite (one projectile, so one local cooldown per enemy).</item>
	/// </list>
	/// <para>Between fights each spirit is a <b>jade coin</b> (user, 2026-11-26: "the jade coin summons should be a floaty jade coin
	/// above the player while theres no enemies to target, and transform (smooth quick tranform animation) when theres enemies in
	/// range"): the coins float in a row over their owner's head, turning slowly. When a spirit has a target, its coin spins up
	/// and bursts into its creature (<see cref="TransformTicks"/>: a jade burst covers the change, <c>JadeSpirit_Burst.png</c>);
	/// <see cref="CoinGrace"/> ticks after its last target is gone it bursts back into its coin and floats home. Only a whole
	/// creature attacks.</para>
	/// Each form is stronger than the one before (per hit, and worth its slots: <see cref="FormDamage"/> x the coin's damage,
	/// one hit per <see cref="FormCooldown"/> ticks), and changing form plays a burst of jade and a chime on every client.
	/// <para>Targeting as ExampleMod 1.4.4's <c>ExampleSimpleMinion</c>: the owner's whip or right-click target first, else the
	/// closest chaseable enemy within <see cref="TargetRange"/> of the owner (the golem needs a clear shot), re-chosen every
	/// <see cref="RetargetInterval"/> ticks.</para>
	/// <para>D2: <c>ai[0]</c> its number, <c>ai[1]</c> its target (+1), <c>ai[2]</c> the attack cycle's tick, set by the owner
	/// (synced on a change and as each dash starts); the form is derived on every client from the owner's counters
	/// (<c>ownedProjectileCounts</c>, kept by vanilla for every player). The golem's bolts are the owner's. D0: NaN guarded, a
	/// teleport home past <see cref="TeleportDistance"/>, a spirit whose number is taken twice keeps only the older, every
	/// sheet and frame checked before drawing (missing art draws nothing). D1: the loong's segments are one array per spirit
	/// (made once); textures cached on clients; one pass over the NPCs when retargeting.</para>
	/// </summary>
	public class JadeSpirit : CogpunkProjectile
	{
		public enum Form { None = 0, Bat = 1, Beetle = 2, Golem = 3, Loong = 4 }

		public const int StagesPerSpirit = 4, MaxSpirits = 10;
		/// <summary>Per form (index = <see cref="Form"/>): hit damage over the coin's (15: 15, 22, 30, 34) and the ticks between
		/// hits on one enemy. The eff DPS a slot: 23.4 (bat, 2026-11-26: the user's buff; 15.6 before), 15.3 (beetle), 15.6 (the
		/// arm), 15.6 (the loong): the Imp Staff's 15.6, each form still more in all than the one before.</summary>
		public static readonly float[] FormDamage = { 0f, 1f, 22f / 15f, 30f / 15f, 34f / 15f };
		public static readonly int[] FormCooldown = { 20, 40, 45, 40, 34 };
		public static readonly int[] FormWidth = { 24, 28, 52, 32, 28 }, FormHeight = { 24, 24, 32, 32, 28 };   // the arm: its shoulder

		public const float TargetRange = 900f, TeleportDistance = 2000f;
		public const int RetargetInterval = 10, DuplicateCheck = 30;
		// the bat: hovers BatHover px beside its target, darts at BatDashSpeed for the last BatDash ticks of each cycle
		public const int BatCycle = 40, BatDash = 18, BatFrameTicks = 4;
		public const float BatHover = 90f, BatDashSpeed = 13f, BatSpeed = 11f;
		// the beetle: backs off BeetleBack px, rams for the last BeetleRam ticks of each cycle
		public const int BeetleCycle = 45, BeetleRam = 18, BeetleFlap = 3, BeetleRamFlap = 2;
		public const float BeetleBack = 150f, BeetleRamSpeed = 15f, BeetleSpeed = 9f;
		// the golem: a bolt every GolemCycle ticks once its arm is on the target
		public const int GolemCycle = 40;
		public const float GolemTurn = 0.12f, GolemFollow = 0.2f, GolemAimError = 0.2f, BoltSpeed = 12f, GolemSpeed = 9f;
		public const float GolemGuard = 52f, GolemHeight = -30f;           // the arm's shoulder: beside its owner's shoulder, clear of them
		// the loong
		public const int LoongSegments = 8;
		public const float LoongSpacing = 16f, LoongSpeed = 13f, LoongIdleSpeed = 8f, LoongTurn = 0.14f, LoongIdleTurn = 0.08f;
		public const float LoongBite = 12f;                       // a body segment's bite radius
		public const int LoongHeadings = 32, LoongCell = 60, LoongStride = 62;
		// idling round the owner
		public const float IdleBack = 48f, IdleGap = 40f, IdleHeight = -56f;
		/// <summary>The coin (2026-11-26): ticks from coin to creature (0.23 s: "smooth quick"; the creature shows from the middle,
		/// under the burst), ticks without a target before it turns back, its spot over its owner's head (game px above the top of
		/// the head, and between coins), its turn (ticks a frame of <see cref="CoinFrames"/>), the burst's length.</summary>
		public const int TransformTicks = 14, CoinGrace = 45, CoinFrames = 8, CoinTurnTicks = 6, BurstTicks = 10, BurstFrames = 5;
		public const float CoinHeight = 30f, CoinGap = 30f, CoinSpeed = 10f;
		public const int CoinCell = 32, BurstCell = 48;
		private const float MaxParallax = 2f;

		private static Asset<Texture2D> bat, batGlow, beetleFar, beetle, beetleNear, beetleGlow, golemArm, golemArmGlow, loong,
			loongGlow, coin, burst;

		private Vector2[] segments;
		private bool segmentsReady;
		private int retargetTimer, duplicateTimer;
		private float aim = MathHelper.PiOver2;                  // the golem's arm: radians below forward (hanging)

		public override string Texture => "Cogpunk/Content/Bosses/Jadey/NPCs/JadeBat";

		public int Index => (int)Projectile.ai[0];

		private int TargetIndex {
			get => (int)Projectile.ai[1] - 1;
			set => Projectile.ai[1] = value + 1;
		}

		private ref float Cycle => ref Projectile.ai[2];

		/// <summary>The form last shown on this client (each plays its own change).</summary>
		private Form Shown {
			get => (Form)(int)Projectile.localAI[0];
			set => Projectile.localAI[0] = (float)value;
		}

		/// <summary>Coin (0) to creature (<see cref="TransformTicks"/>), every side from the synced target: a creature only
		/// fights at the top. Local, as its timers.</summary>
		private ref float Morph => ref Projectile.localAI[1];

		/// <summary>Ticks since its last target (every side, from the synced target).</summary>
		private ref float Idle => ref Projectile.localAI[2];

		private bool creatureShown;                              // the drawn half of the change (flips under the burst)
		private int burstLeft;                                    // the burst's ticks left (clients)

		/// <summary>A whole creature (it fights).</summary>
		private bool Awake => Morph >= TransformTicks;

		public static Form FormOf(int counters, int index) => (Form)Math.Clamp(counters - index * StagesPerSpirit, 0, StagesPerSpirit);

		public override void SetStaticDefaults() {
			Main.projPet[Type] = true;
			ProjectileID.Sets.MinionTargettingFeature[Type] = true;
			ProjectileID.Sets.CultistIsResistantTo[Type] = true;
			ProjectileID.Sets.DrawScreenCheckFluff[Type] = 600;   // the loong's tail trails behind its head
			CogpunkSets.RollsOwnCrit[Type] = true;
			if (!Main.dedServ) {
				const string jadey = "Cogpunk/Content/Bosses/Jadey/NPCs/", haven = "Cogpunk/Content/Coghaven/NPCs/";
				bat = DepthLayers.RequestOptional(jadey + "JadeBat");
				batGlow = DepthLayers.RequestOptional(jadey + "JadeBat_Glow");
				beetleFar = DepthLayers.RequestOptional(jadey + "JadeBeetle_Far");
				beetle = DepthLayers.RequestOptional(jadey + "JadeBeetle");
				beetleNear = DepthLayers.RequestOptional(jadey + "JadeBeetle_Near");
				beetleGlow = DepthLayers.RequestOptional(jadey + "JadeBeetle_Glow");
				coin = DepthLayers.RequestOptional("Cogpunk/Content/Research/Summons/JadeSpirit_Coin");
				burst = DepthLayers.RequestOptional("Cogpunk/Content/Research/Summons/JadeSpirit_Burst");
				golemArm = DepthLayers.RequestOptional(haven + "JadeGolem_Arm");
				golemArmGlow = DepthLayers.RequestOptional(haven + "JadeGolem_ArmGlow");
				loong = DepthLayers.RequestOptional("Cogpunk/Content/Research/Summons/JadeLoong");
				loongGlow = DepthLayers.RequestOptional("Cogpunk/Content/Research/Summons/JadeLoong_Glow");
			}
		}

		public override void Unload() {
			bat = batGlow = beetleFar = beetle = beetleNear = beetleGlow = golemArm =
				golemArmGlow = loong = loongGlow = coin = burst = null;
		}

		public override void SetDefaults() {
			Projectile.width = FormWidth[1];
			Projectile.height = FormHeight[1];
			Projectile.friendly = true;
			Projectile.minion = true;
			Projectile.minionSlots = 0f;                         // the counters hold the slots
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = FormCooldown[1];
			segments = new Vector2[LoongSegments];
		}

		/// <summary>The owner's client: the spirits that <paramref name="counters"/> counters need (spirit k for counters past
		/// 4k), the missing ones made; <paramref name="baseDamage"/> (when 0 or more) is the coin's damage they start from.</summary>
		public static void EnsureSpirits(Player player, IEntitySource source, int counters, int baseDamage) {
			if (player.whoAmI != Main.myPlayer) {
				return;
			}
			int type = ModContent.ProjectileType<JadeSpirit>();
			int needed = Math.Min(MaxSpirits, (counters + StagesPerSpirit - 1) / StagesPerSpirit);
			int have = 0;
			foreach (Projectile p in Main.ActiveProjectiles) {
				int k = (int)p.ai[0];
				if (p.owner == player.whoAmI && p.type == type && k >= 0 && k < MaxSpirits) {
					have |= 1 << k;
				}
			}
			int damage = baseDamage > 0 ? baseDamage : JadeCoin.Damage;
			for (int k = 0; k < needed; k++) {
				if ((have & (1 << k)) == 0 && SafeSpawn.TryNewProjectile(source, player.Center, Vector2.Zero, type, damage, 2f,
					out Projectile spirit, player.whoAmI, k)) {
					spirit.originalDamage = damage;
				}
			}
		}

		public override bool? CanCutTiles() => false;

		public override bool MinionContactDamage() => CurrentForm != Form.Golem && Awake;

		public override bool? CanDamage() => CurrentForm == Form.Golem || !Awake ? false : null;

		private Form CurrentForm => Shown;

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers || Index < 0 || Index >= MaxSpirits) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			int buff = ModContent.BuffType<JadeCoinBuff>();
			if (!owner.active || owner.dead) {
				owner.ClearBuff(buff);
				Projectile.Kill();
				return;
			}
			if (owner.HasBuff(buff)) {
				Projectile.timeLeft = 2;
			}
			Form form = FormOf(owner.ownedProjectileCounts[ModContent.ProjectileType<JadeCoinCounter>()], Index);
			if (form == Form.None) {
				Projectile.Kill();
				return;
			}
			bool isOwner = Projectile.owner == Main.myPlayer;
			if (isOwner && ++duplicateTimer >= DuplicateCheck) {
				duplicateTimer = 0;
				if (Duplicated()) {
					Projectile.Kill();
					return;
				}
			}
			if (form != Shown) {
				ChangeForm(Shown, form);
			}
			int i = (int)form;
			Projectile.originalDamage = (int)Math.Round(owner.GetModPlayer<JadeCoinPlayer>().CounterDamage * FormDamage[i]);
			Projectile.localNPCHitCooldown = FormCooldown[i];

			if (isOwner && Vector2.DistanceSquared(owner.Center, Projectile.Center) > TeleportDistance * TeleportDistance) {
				Projectile.Center = owner.Center;
				Projectile.velocity = Vector2.Zero;
				segmentsReady = false;
				Projectile.netUpdate = true;
			}
			NPC target = AcquireTarget(owner, isOwner, form);
			if (!UpdateCoin(owner, target)) {
				MathSafety.Sanitize(ref Projectile.velocity);
				return;                                          // a coin, or changing: no fighting
			}
			switch (form) {
				case Form.Bat:
					UpdateDarter(owner, target, isOwner, BatCycle, BatDash, BatHover, -60f, BatSpeed, BatDashSpeed);
					break;
				case Form.Beetle:
					UpdateDarter(owner, target, isOwner, BeetleCycle, BeetleRam, BeetleBack, -10f, BeetleSpeed, BeetleRamSpeed);
					break;
				case Form.Golem:
					UpdateGolem(owner, target, isOwner);
					break;
				default:
					UpdateLoong(owner, target);
					break;
			}
			MathSafety.Sanitize(ref Projectile.velocity);
			if (!MathSafety.IsFinite(Projectile.position)) {
				Projectile.Center = owner.Center;
				segmentsReady = false;
			}
			if (!Main.dedServ) {
				Vector3 light = form == Form.Loong ? new Vector3(0.10f, 0.32f, 0.22f) : new Vector3(0.06f, 0.20f, 0.14f);
				Lighting.AddLight(Projectile.Center, light);
			}
		}

		/// <summary>The coin (2026-11-26): <see cref="Morph"/> climbs while it has a target and falls <see cref="CoinGrace"/> ticks
		/// after its last one; below the top it floats as a coin over its owner's head (spinning up as it changes) and doesn't
		/// fight. True: a whole creature, which fights as before. The change's burst and chime play as the drawn half flips.</summary>
		private bool UpdateCoin(Player owner, NPC target) {
			Idle = target != null ? 0f : Math.Min(Idle + 1f, 10000f);
			bool wanted = target != null || (Morph > 0f && Idle < CoinGrace);
			Morph = Math.Clamp(Morph + (wanted ? 1f : -1f), 0f, TransformTicks);
			bool shown = Morph >= TransformTicks * 0.5f;
			if (shown != creatureShown) {
				creatureShown = shown;
				Changed(shown);
			}
			if (Awake) {
				return true;
			}
			Projectile.friendly = false;
			Cycle = 0f;
			if (!creatureShown) {
				segmentsReady = false;                           // a loong lays itself out afresh as it appears
			}
			else if (!segmentsReady && CurrentForm == Form.Loong) {
				LayOutSegments();                                // shown under the burst, still
			}
			aim = MathHelper.PiOver2;
			int spirits = Math.Max(1, (owner.ownedProjectileCounts[ModContent.ProjectileType<JadeCoinCounter>()] + StagesPerSpirit - 1) / StagesPerSpirit);
			float bob = MathF.Sin(Main.GlobalTimeWrappedHourly * 2.4f + Index * 0.9f) * 3f;
			Vector2 spot = owner.Top + new Vector2((Index - (spirits - 1) * 0.5f) * CoinGap, -CoinHeight + bob);
			if (Morph <= 0f) {
				MoveTo(spot, CoinSpeed, 0.12f);                  // home over the head
			}
			else {
				Projectile.velocity *= 0.85f;                    // changing: it holds still under the burst
			}
			Projectile.spriteDirection = owner.direction;
			return false;
		}

		/// <summary>The drawn half of the change flipped (to the creature, or back to the coin): the burst, a chime and jade dust.</summary>
		private void Changed(bool toCreature) {
			if (Main.dedServ) {
				return;
			}
			burstLeft = BurstTicks;
			SoundEngine.PlaySound((toCreature ? SoundID.Item29 : SoundID.Item4) with { Pitch = toCreature ? 0.35f : 0.6f, Volume = 0.45f,
				MaxInstances = 3 }, Projectile.Center);
			for (int k = 0; k < 10 && CogpunkClientConfig.RollEffect(); k++) {
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(8f), 16, 16, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(3f, 3f);
					d.scale = 1.1f;
				}
			}
		}

		/// <summary>Another spirit of this owner already has this number (an older one): this one goes.</summary>
		private bool Duplicated() {
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.whoAmI < Projectile.whoAmI && p.owner == Projectile.owner && p.type == Projectile.type && (int)p.ai[0] == Index) {
					return true;
				}
			}
			return false;
		}

		/// <summary>A new form: the hitbox resized about its centre, the loong laid out behind its head, a burst of jade and a
		/// chime (clients).</summary>
		private void ChangeForm(Form from, Form to) {
			Shown = to;
			Projectile.Resize(FormWidth[(int)to], FormHeight[(int)to]);
			Cycle = 0f;
			segmentsReady = false;
			aim = MathHelper.PiOver2;
			if (Main.dedServ || !Awake) {
				return;                                          // a coin takes its new form quietly: it shows when it next wakes
			}
			SoundEngine.PlaySound(SoundID.Item4 with { Pitch = -0.2f + 0.15f * (int)to, Volume = 0.6f }, Projectile.Center);
			if (from != Form.None) {
				SoundEngine.PlaySound(SoundID.Item29 with { Pitch = 0.1f * (int)to, Volume = 0.5f }, Projectile.Center);
			}
			for (int k = 0; k < 24 && CogpunkClientConfig.RollEffect(); k++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(4f, 4f);
					d.scale = 1.2f;
				}
			}
		}

		// --- targeting ------------------------------------------------------------------------------------------------------

		private NPC AcquireTarget(Player owner, bool isOwner, Form form) {
			int index = TargetIndex;
			if (isOwner && (--retargetTimer <= 0 || !IsValidTarget(index, owner, form))) {
				retargetTimer = RetargetInterval;
				int found = SearchTarget(owner, form);
				if (found != index) {
					TargetIndex = found;
					Cycle = 0f;
					Projectile.netUpdate = true;
				}
				index = found;
			}
			return index >= 0 && index < Main.maxNPCs && Main.npc[index].active ? Main.npc[index] : null;
		}

		private bool IsValidTarget(int index, Player owner, Form form) {
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC npc = Main.npc[index];
			return npc.CanBeChasedBy(Projectile) && Vector2.DistanceSquared(npc.Center, owner.Center) < TargetRange * TargetRange
				&& (form != Form.Golem || Collision.CanHitLine(Projectile.Center, 1, 1, npc.position, npc.width, npc.height));
		}

		private int SearchTarget(Player owner, Form form) {
			int forced = owner.MinionAttackTargetNPC;
			if (IsValidTarget(forced, owner, form)) {
				return forced;
			}
			int best = -1;
			float bestSq = TargetRange * TargetRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}
				float distanceSq = Vector2.DistanceSquared(npc.Center, owner.Center);
				if (distanceSq < bestSq && (form != Form.Golem || Collision.CanHitLine(Projectile.Center, 1, 1, npc.position, npc.width, npc.height))) {
					best = npc.whoAmI;
					bestSq = distanceSq;
				}
			}
			return best;
		}

		// --- movement -------------------------------------------------------------------------------------------------------

		private void MoveTo(Vector2 spot, float maxSpeed, float inertia) {
			Vector2 to = spot - Projectile.Center;
			float distance = to.Length();
			if (distance < 6f) {
				Projectile.velocity *= 0.85f;
				return;
			}
			Vector2 wanted = to / distance * Math.Min(maxSpeed, distance / 6f);
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, wanted, inertia);
		}

		/// <summary>Its place round the owner: behind them, staggered by its number, bobbing.</summary>
		private Vector2 IdleSpot(Player owner, float extraBack, float height) {
			float bob = MathF.Sin(Main.GlobalTimeWrappedHourly * 2.2f + Index) * 4f;
			return owner.Center + new Vector2(-owner.direction * (IdleBack + extraBack + Index * IdleGap), height + bob);
		}

		/// <summary>The bat and the beetle: hover <paramref name="hover"/> px beside the target, then for the last
		/// <paramref name="dash"/> ticks of each <paramref name="cycle"/> dart straight through it; idle behind the owner.</summary>
		private void UpdateDarter(Player owner, NPC target, bool isOwner, int cycle, int dash, float hover, float lift, float speed, float dashSpeed) {
			if (target == null) {
				Projectile.friendly = false;
				Cycle = 0f;
				MoveTo(IdleSpot(owner, 0f, IdleHeight), speed * 0.8f, 0.08f);
				Face(Projectile.velocity.X, owner.Center.X - Projectile.Center.X);
				return;
			}
			Cycle = (Cycle + 1f) % cycle;
			int t = (int)Cycle;
			if (t < cycle - dash) {
				Projectile.friendly = false;
				float side = Projectile.Center.X < target.Center.X ? -1f : 1f;
				MoveTo(target.Center + new Vector2(side * hover, lift), speed, 0.14f);
				Face(0f, target.Center.X - Projectile.Center.X);
				return;
			}
			if (t == cycle - dash) {
				Projectile.velocity = (target.Center - Projectile.Center).SafeNormalize(Vector2.UnitX) * dashSpeed;
				if (isOwner) {
					Projectile.netUpdate = true;
				}
			}
			Projectile.friendly = true;
			Face(Projectile.velocity.X, 0f);
		}

		/// <summary>spriteDirection from a horizontal speed (or, when still, from where it looks).</summary>
		private void Face(float vx, float look) {
			float x = Math.Abs(vx) > 0.4f ? vx : look;
			if (x != 0f) {
				Projectile.spriteDirection = x > 0f ? 1 : -1;
			}
		}

		/// <summary>The golem's arm: floats beside its owner (on the target's side when it has one), easing onto the target, a bolt
		/// from its palm every <see cref="GolemCycle"/> ticks once it is on it; hanging when it has nothing to aim at.</summary>
		private void UpdateGolem(Player owner, NPC target, bool isOwner) {
			Projectile.friendly = false;
			float side = target != null ? Math.Sign(target.Center.X - owner.Center.X) : -owner.direction;
			if (side == 0f) {
				side = -owner.direction;
			}
			float bob = MathF.Sin(Main.GlobalTimeWrappedHourly * 1.6f + Index) * 4f;
			Vector2 spot = owner.Center + new Vector2(side * (GolemGuard + Index * IdleGap), GolemHeight + bob);
			MoveTo(spot, GolemSpeed, 0.1f);
			if (target == null) {
				Face(0f, owner.direction);
				aim = Math.Min(MathHelper.PiOver2, aim + GolemTurn * 0.5f);   // the arm comes down
				Cycle = 0f;
				return;
			}
			Face(0f, target.Center.X - Projectile.Center.X);
			Vector2 shoulder = Shoulder();
			Vector2 v = target.Center - shoulder;
			float goal = MathHelper.Clamp((float)Math.Atan2(v.Y, Math.Abs(v.X)), MathHelper.ToRadians(Golem.ArmMinDegrees),
				MathHelper.ToRadians(Golem.ArmMinDegrees + (Golem.ArmFrames - 1) * Golem.ArmStepDegrees));
			if (float.IsFinite(goal)) {
				aim += MathHelper.Clamp((goal - aim) * GolemFollow, -GolemTurn, GolemTurn);
			}
			Cycle = Math.Min(Cycle + 1f, GolemCycle);
			if (isOwner && Cycle >= GolemCycle && Math.Abs(goal - aim) < GolemAimError) {
				Cycle = 0f;
				Vector2 palm = shoulder + Aim() * Golem.PalmReach;
				Vector2 velocity = (target.Center - palm).SafeNormalize(Aim()) * BoltSpeed;
				SafeSpawn.TryNewProjectile(Projectile.GetSource_FromThis(), palm, velocity, ModContent.ProjectileType<JadeSpiritBolt>(),
					Projectile.damage, Projectile.knockBack, out _, Projectile.owner);
				SoundEngine.PlaySound(SoundID.Item8 with { Pitch = -0.3f, Volume = 0.6f }, palm);
				Projectile.netUpdate = true;
			}
		}

		/// <summary>The arm's shoulder: the spirit's centre (it floats there).</summary>
		private Vector2 Shoulder() => Projectile.Center;

		/// <summary>Where the arm sheet's cell origin goes (the golem's hip point, which the sheet is drawn from) so that its
		/// shoulder lands on <see cref="Shoulder"/>.</summary>
		private Vector2 Anchor => Shoulder() - new Vector2(Golem.ShoulderX * -Projectile.spriteDirection, Golem.ShoulderY);

		private Vector2 Aim() => new(Projectile.spriteDirection * MathF.Cos(aim), MathF.Sin(aim));

		/// <summary>The loong: its head turns at most <see cref="LoongTurn"/> a tick towards its target (so it overshoots and
		/// loops back through it, weaving) or, idle, towards a point circling over its owner; its segments follow the head
		/// <see cref="LoongSpacing"/> px apart (each pulled after the one before, as vanilla's worms).</summary>
		private void UpdateLoong(Player owner, NPC target) {
			Projectile.friendly = target != null;
			if (!segmentsReady) {
				LayOutSegments();
			}
			float t = Main.GlobalTimeWrappedHourly;
			Vector2 goal = target != null ? target.Center
				: owner.Center + new Vector2(MathF.Cos(t * 1.8f + Index * 2f) * 140f, -110f + MathF.Sin(t * 3.6f + Index) * 30f);
			float speed = target != null ? LoongSpeed : LoongIdleSpeed;
			float turn = target != null ? LoongTurn : LoongIdleTurn;
			Vector2 heading = Projectile.velocity.SafeNormalize(new Vector2(owner.direction, 0f));
			Vector2 wanted = (goal - Projectile.Center).SafeNormalize(heading);
			float current = heading.ToRotation();
			float delta = MathHelper.WrapAngle(wanted.ToRotation() - current);
			float angle = current + MathHelper.Clamp(delta, -turn, turn);
			float pace = MathHelper.Lerp(Projectile.velocity.Length(), speed, 0.08f);
			Projectile.velocity = angle.ToRotationVector2() * Math.Max(pace, 2f);
			Projectile.spriteDirection = Projectile.velocity.X >= 0f ? 1 : -1;
			FollowSegments(Projectile.Center + Projectile.velocity);
		}

		private void LayOutSegments() {
			Vector2 back = -Projectile.velocity.SafeNormalize(Vector2.UnitX);
			for (int k = 0; k < LoongSegments; k++) {
				segments[k] = Projectile.Center + back * LoongSpacing * k;
			}
			segmentsReady = true;
		}

		/// <summary>Segment 0 is the head (where the projectile will be after this tick's move); each after it keeps
		/// <see cref="LoongSpacing"/> from the one in front.</summary>
		private void FollowSegments(Vector2 head) {
			segments[0] = head;
			for (int k = 1; k < LoongSegments; k++) {
				Vector2 d = segments[k] - segments[k - 1];
				float length = d.Length();
				segments[k] = length > 0.01f ? segments[k - 1] + d / length * LoongSpacing : segments[k - 1] - Vector2.UnitX * LoongSpacing;
				if (!MathSafety.IsFinite(segments[k])) {
					segmentsReady = false;
					return;
				}
			}
		}

		/// <summary>The loong bites with its whole body: the head's hitbox or any segment within <see cref="LoongBite"/>.</summary>
		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (CurrentForm != Form.Loong || !segmentsReady) {
				return null;
			}
			if (projHitbox.Intersects(targetHitbox)) {
				return true;
			}
			for (int k = 1; k < LoongSegments; k++) {
				Vector2 nearest = Vector2.Clamp(segments[k], targetHitbox.TopLeft(), targetHitbox.BottomRight());
				if (Vector2.DistanceSquared(nearest, segments[k]) < LoongBite * LoongBite) {
					return true;
				}
			}
			return false;
		}

		/// <summary>Summon damage skips vanilla's crit roll: rolled here on the owner's client (D3 rule 9), as the Mice-bot.</summary>
		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (Main.rand.Next(100) < Projectile.CritChance) {
				modifiers.SetCrit();
			}
		}

		// --- drawing --------------------------------------------------------------------------------------------------------

		public override bool PreDraw(ref Color lightColor) {
			if (burstLeft > 0) {
				burstLeft--;
			}
			if (!creatureShown) {
				DrawCoin(lightColor);
				DrawBurst();
				return false;
			}
			switch (CurrentForm) {
				case Form.Bat:
					DrawBat(lightColor);
					break;
				case Form.Beetle:
					DrawBeetle(lightColor);
					break;
				case Form.Golem:
					DrawGolem(lightColor);
					break;
				case Form.Loong:
					DrawLoong();
					break;
			}
			DrawBurst();
			return false;
		}

		/// <summary>The coin turning (its turn quickens as it spins up to change), lit where it is with a little of its own light.</summary>
		private void DrawCoin(Color light) {
			if (coin?.IsLoaded != true) {
				return;
			}
			int turn = Morph > 0f ? Math.Max(1, CoinTurnTicks - (int)Morph) : CoinTurnTicks;
			int frame = (int)((Main.GameUpdateCount / (uint)turn + (uint)(Index * 3)) % CoinFrames);
			Rectangle source = new(0, frame * (CoinCell + 2), CoinCell, CoinCell);
			if (source.Bottom > coin.Value.Height) {
				return;
			}
			Vector2 at = Snapped(Projectile.Center - Main.screenPosition - new Vector2(CoinCell / 2f));
			Main.EntitySpriteDraw(coin.Value, at, source, Color.Lerp(light, Color.White, 0.35f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
		}

		/// <summary>The change's burst over whatever shows (full-bright), its five frames over <see cref="BurstTicks"/>.</summary>
		private void DrawBurst() {
			if (burstLeft <= 0 || burst?.IsLoaded != true) {
				return;
			}
			int frame = Math.Clamp((BurstTicks - burstLeft) * BurstFrames / BurstTicks, 0, BurstFrames - 1);
			Rectangle source = new(0, frame * (BurstCell + 2), BurstCell, BurstCell);
			if (source.Bottom > burst.Value.Height) {
				return;
			}
			Vector2 at = Snapped(Projectile.Center - Main.screenPosition - new Vector2(BurstCell / 2f));
			Main.EntitySpriteDraw(burst.Value, at, source, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
		}

		private static Vector2 Snapped(Vector2 v) => new(DepthLayers.Snap(v.X), DepthLayers.Snap(v.Y));

		/// <summary>Jadey's bat (left-facing art, mirrored when it faces right), its eyes' glow on top.</summary>
		private void DrawBat(Color light) {
			if (bat?.IsLoaded != true) {
				return;
			}
			int frame = (int)((Main.GameUpdateCount / BatFrameTicks + (uint)Projectile.whoAmI) % Bat.BatFrames);
			Rectangle source = new(0, frame * (Bat.BatHeight + 2), Bat.BatWidth, Bat.BatHeight);
			if (source.Bottom > bat.Value.Height) {
				return;
			}
			Vector2 at = Snapped(Projectile.Center - Main.screenPosition - new Vector2(Bat.BatWidth / 2f, Bat.BatHeight / 2f));
			SpriteEffects fx = Projectile.spriteDirection == 1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Main.EntitySpriteDraw(bat.Value, at, source, light, 0f, Vector2.Zero, 1f, fx);
			if (batGlow?.IsLoaded == true && source.Bottom <= batGlow.Value.Height) {
				Main.EntitySpriteDraw(batGlow.Value, at, source, new Color(255, 255, 255, 0), 0f, Vector2.Zero, 1f, fx);
			}
		}

		/// <summary>The jade beetle's three planes in a flight frame (faster wing beats while it rams), its rune glowing.</summary>
		private void DrawBeetle(Color light) {
			if (beetle?.IsLoaded != true) {
				return;
			}
			int flap = Projectile.friendly ? BeetleRamFlap : BeetleFlap;
			int frame = Beetle.Fly + (int)((Main.GameUpdateCount / (uint)flap + (uint)Projectile.whoAmI) % Beetle.FlyFrames);
			Vector2 anchor = Snapped(Projectile.Bottom - Main.screenPosition);
			bool flip = Projectile.spriteDirection == 1;          // the art faces left
			DepthLayers.DrawWalker(Main.spriteBatch, beetleFar?.Value, beetle.Value, beetleNear?.Value, frame, Beetle.CellWidth,
				Beetle.CellHeight, 2, Beetle.OriginX, Beetle.OriginY, anchor, light, flip, MaxParallax);
			if (beetleGlow?.IsLoaded == true) {
				DepthLayers.DrawCell(Main.spriteBatch, beetleGlow.Value, frame, 1, Beetle.CellWidth, Beetle.CellHeight, 2,
					Beetle.OriginX, Beetle.OriginY, anchor, 0, Color.White * (Projectile.friendly ? 1f : 0.65f), flip);
			}
		}

		/// <summary>The golem's arm alone (2026-11-26): the arm sheet's frame nearest its aim (hanging when idle), its runes
		/// glowing, and a soft jade light at the shoulder it floats from.</summary>
		private void DrawGolem(Color light) {
			if (golemArm?.IsLoaded != true) {
				return;
			}
			SpriteBatch sb = Main.spriteBatch;
			Vector2 anchor = Snapped(Anchor - Main.screenPosition);
			bool flip = Projectile.spriteDirection == 1;          // the art faces left
			int arm = Math.Clamp((int)Math.Round((MathHelper.ToDegrees(aim) - Golem.ArmMinDegrees) / Golem.ArmStepDegrees), 0, Golem.ArmFrames - 1);
			DepthLayers.DrawCell(sb, golemArm.Value, arm, Golem.ArmColumns, Golem.ArmCellWidth, Golem.ArmCellHeight, 2,
				Golem.ArmOriginX, Golem.ArmOriginY, anchor, 0, Color.Lerp(light, Color.White, 0.2f), flip);
			if (golemArmGlow?.IsLoaded == true) {
				DepthLayers.DrawCell(sb, golemArmGlow.Value, arm, Golem.ArmColumns, Golem.ArmCellWidth, Golem.ArmCellHeight, 2,
					Golem.ArmOriginX, Golem.ArmOriginY, anchor, 0, Color.White * 0.8f, flip);
			}
		}

		/// <summary>The loong, tail first: each segment's own heading frame (32 headings, generator-rendered), lit where it
		/// is; the head's eye glows.</summary>
		private void DrawLoong() {
			if (loong?.IsLoaded != true || !segmentsReady) {
				return;
			}
			Texture2D sheet = loong.Value;
			for (int k = LoongSegments - 1; k >= 0; k--) {
				Vector2 at = segments[k];
				Vector2 forward = k == 0 ? Projectile.velocity : segments[k - 1] - segments[k];
				int heading = (int)Math.Round(forward.ToRotation() / MathHelper.TwoPi * LoongHeadings);
				heading = ((heading % LoongHeadings) + LoongHeadings) % LoongHeadings;
				int kind = k == 0 ? 0 : k == LoongSegments - 1 ? 3 : (k == 2 || k == 5) ? 2 : 1;
				Rectangle source = new(heading * LoongStride, kind * LoongStride, LoongCell, LoongCell);
				if (source.Right > sheet.Width || source.Bottom > sheet.Height) {
					continue;
				}
				Point tile = at.ToTileCoordinates();
				Color light = TileSafety.InWorld(tile.X, tile.Y, 0) ? Lighting.GetColor(tile.X, tile.Y) : Color.White;
				Vector2 draw = Snapped(at - Main.screenPosition - new Vector2(LoongCell / 2f));
				Main.EntitySpriteDraw(sheet, draw, source, light, 0f, Vector2.Zero, 1f, SpriteEffects.None);
				if (k == 0 && loongGlow?.IsLoaded == true && source.Bottom <= loongGlow.Value.Height) {
					Main.EntitySpriteDraw(loongGlow.Value, draw, source, new Color(255, 255, 255, 0), 0f, Vector2.Zero, 1f, SpriteEffects.None);
				}
			}
		}
	}

	/// <summary>
	/// The jade golem's bolt: a jade spark (the Jade Staff's own art) flying straight from its palm, through one enemy,
	/// breaking on blocks; full-bright, lighting its way, a trail of jade dust (clients). Summon damage (it crits on its own
	/// roll, D3 rule 9). D0: a finite life; D2: the owner's.
	/// </summary>
	public class JadeSpiritBolt : CogpunkProjectile
	{
		public override string Texture => "Cogpunk/Content/Gems/Projectiles/JadeBolt";

		public override void SetStaticDefaults() {
			CogpunkSets.RollsOwnCrit[Type] = true;
			ProjectileID.Sets.MinionShot[Type] = true;
		}

		public override void SetDefaults() {
			Projectile.width = 10;
			Projectile.height = 10;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 75;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
		}

		public override void AI() {
			if (Main.dedServ) {
				return;
			}
			Lighting.AddLight(Projectile.Center, 0.08f, 0.3f, 0.18f);
			if (Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.GemEmerald, out Dust d)) {
				d.noGravity = true;
				d.velocity = Projectile.velocity * 0.15f;
				d.scale = 0.9f;
			}
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (Main.rand.Next(100) < Projectile.CritChance) {
				modifiers.SetCrit();
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			for (int k = 0; k < 6 && CogpunkClientConfig.RollEffect(); k++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(2.5f, 2.5f);
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = Terraria.GameContent.TextureAssets.Projectile[Type].Value;
			Vector2 at = Projectile.Center - Main.screenPosition - new Vector2(texture.Width / 2, texture.Height / 2);
			Main.EntitySpriteDraw(texture, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), null, Color.White, 0f, Vector2.Zero, 1f,
				SpriteEffects.None);
			return false;
		}
	}
}
