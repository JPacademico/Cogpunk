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
	/// <item><b>a jade golem</b> (Coghaven's, floating): stands guard beside its owner on the target's side, its arm raised and
	/// following the target (the arm sheets, 5 degrees apart: never rotated), and shoots a jade bolt from its palm
	/// (<see cref="JadeSpiritBolt"/>);</item>
	/// <item><b>a jade loong</b> (new art, art/research/make_jade_coin_art.py: user, "like default terraria cloud hard mode loong,
	/// but smaller and jade colored"): a serpent of <see cref="LoongSegments"/> segments that weaves through its target and
	/// coils over its owner when idle; head and body both bite (one projectile, so one local cooldown per enemy).</item>
	/// </list>
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
		/// <summary>Per form (index = <see cref="Form"/>): hit damage over the coin's (10: 10, 22, 30, 34) and the ticks between
		/// hits on one enemy. The eff DPS a slot: 15.6 (bat), 15.3 (beetle), 15.6 (golem), 15.6 (loong): the Imp Staff's 15.6.</summary>
		public static readonly float[] FormDamage = { 0f, 1f, 2.2f, 3f, 3.4f };
		public static readonly int[] FormCooldown = { 20, 40, 45, 40, 34 };
		public static readonly int[] FormWidth = { 24, 28, 52, 44, 28 }, FormHeight = { 24, 24, 32, 96, 28 };

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
		public const float GolemGuard = 96f, GolemHeight = -40f;           // beside its owner, clear of them (its art is wide)
		// the loong
		public const int LoongSegments = 8;
		public const float LoongSpacing = 16f, LoongSpeed = 13f, LoongIdleSpeed = 8f, LoongTurn = 0.14f, LoongIdleTurn = 0.08f;
		public const float LoongBite = 12f;                       // a body segment's bite radius
		public const int LoongHeadings = 32, LoongCell = 60, LoongStride = 62;
		// idling round the owner
		public const float IdleBack = 48f, IdleGap = 40f, IdleHeight = -56f;
		private const float MaxParallax = 2f;

		private static Asset<Texture2D> bat, batGlow, beetleFar, beetle, beetleNear, beetleGlow, golemFar, golem, golemNear,
			golemGlow, golemArm, golemArmGlow, loong, loongGlow;

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
				golemFar = DepthLayers.RequestOptional(haven + "JadeGolem_Far");
				golem = DepthLayers.RequestOptional(haven + "JadeGolem");
				golemNear = DepthLayers.RequestOptional(haven + "JadeGolem_Near");
				golemGlow = DepthLayers.RequestOptional(haven + "JadeGolem_Glow");
				golemArm = DepthLayers.RequestOptional(haven + "JadeGolem_Arm");
				golemArmGlow = DepthLayers.RequestOptional(haven + "JadeGolem_ArmGlow");
				loong = DepthLayers.RequestOptional("Cogpunk/Content/Research/Summons/JadeLoong");
				loongGlow = DepthLayers.RequestOptional("Cogpunk/Content/Research/Summons/JadeLoong_Glow");
			}
		}

		public override void Unload() {
			bat = batGlow = beetleFar = beetle = beetleNear = beetleGlow = golemFar = golem = golemNear = golemGlow = golemArm =
				golemArmGlow = loong = loongGlow = null;
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

		public override bool MinionContactDamage() => CurrentForm != Form.Golem;

		public override bool? CanDamage() => CurrentForm == Form.Golem ? false : null;

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
			if (Main.dedServ) {
				return;
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

		/// <summary>The golem: floats beside its owner (on the target's side when it has one), its arm easing onto the target,
		/// a bolt from its palm every <see cref="GolemCycle"/> ticks once the arm is on it.</summary>
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

		/// <summary>The golem's anchor (the ground point under its hips: the bottom of its hitbox).</summary>
		private Vector2 Anchor => Projectile.Bottom;

		private Vector2 Shoulder() => Anchor + new Vector2(Golem.ShoulderX * -Projectile.spriteDirection, Golem.ShoulderY);

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
			return false;
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

		/// <summary>The jade golem: its planes in a breathing idle frame, or, with a target, its aiming body with the raised arm
		/// (the arm sheet's frame nearest its aim) between the middle and near planes; its runes glowing.</summary>
		private void DrawGolem(Color light) {
			if (golem?.IsLoaded != true) {
				return;
			}
			SpriteBatch sb = Main.spriteBatch;
			Vector2 anchor = Snapped(Anchor - Main.screenPosition);
			bool flip = Projectile.spriteDirection == 1;          // the art faces left
			bool aiming = TargetIndex >= 0 && aim < MathHelper.PiOver2 - 0.05f;
			int frame = aiming ? Golem.AimBody : Golem.Idle + (int)(Main.GameUpdateCount / 15 % Golem.IdleFrames);
			Vector2 farShift = new(DepthLayers.Shift(anchor, DepthLayers.Far, MaxParallax).X, 0f);
			Vector2 nearShift = new(DepthLayers.Shift(anchor, DepthLayers.Near, MaxParallax).X, 0f);
			if (golemFar?.IsLoaded == true) {
				DepthLayers.DrawCell(sb, golemFar.Value, frame, Golem.Columns, Golem.CellWidth, Golem.CellHeight, 2, Golem.OriginX,
					Golem.OriginY, anchor + farShift, 0, DepthLayers.Tint(light, DepthLayers.Far), flip);
			}
			DepthLayers.DrawCell(sb, golem.Value, frame, Golem.Columns, Golem.CellWidth, Golem.CellHeight, 2, Golem.OriginX,
				Golem.OriginY, anchor, 0, light, flip);
			int arm = Math.Clamp((int)Math.Round((MathHelper.ToDegrees(aim) - Golem.ArmMinDegrees) / Golem.ArmStepDegrees), 0, Golem.ArmFrames - 1);
			if (aiming && golemArm?.IsLoaded == true) {
				DepthLayers.DrawCell(sb, golemArm.Value, arm, Golem.ArmColumns, Golem.ArmCellWidth, Golem.ArmCellHeight, 2,
					Golem.ArmOriginX, Golem.ArmOriginY, anchor + nearShift, 0, light, flip);
			}
			if (golemNear?.IsLoaded == true) {
				DepthLayers.DrawCell(sb, golemNear.Value, frame, Golem.Columns, Golem.CellWidth, Golem.CellHeight, 2, Golem.OriginX,
					Golem.OriginY, anchor + nearShift, 0, light, flip);
			}
			if (golemGlow?.IsLoaded == true) {
				DepthLayers.DrawCell(sb, golemGlow.Value, frame, Golem.Columns, Golem.CellWidth, Golem.CellHeight, 2, Golem.OriginX,
					Golem.OriginY, anchor, 0, Color.White * 0.8f, flip);
			}
			if (aiming && golemArmGlow?.IsLoaded == true) {
				DepthLayers.DrawCell(sb, golemArmGlow.Value, arm, Golem.ArmColumns, Golem.ArmCellWidth, Golem.ArmCellHeight, 2,
					Golem.ArmOriginX, Golem.ArmOriginY, anchor + nearShift, 0, Color.White * 0.8f, flip);
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
