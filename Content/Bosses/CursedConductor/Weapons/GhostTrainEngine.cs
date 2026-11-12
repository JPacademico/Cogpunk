using System;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using Train = Cogpunk.Content.Bosses.CursedConductor.Projectiles.GhostTrain;

namespace Cogpunk.Content.Bosses.CursedConductor.Weapons
{
	/// <summary>
	/// The head of the <see cref="CursedTrainWhistle"/>'s ghost train (one minion slot): a little ghost engine, smaller than
	/// the Conductor's and, since 2026-11-10, in his train's ghostly verdigris (user: "more ghostly blue, like the boss one";
	/// it was aether-blue with brass fittings), only its lamp a warm brass light where his has an ember eye. It floats round
	/// its owner (an ellipse over their head, <see cref="OrbitRadius"/>) and, with an enemy in
	/// reach, attacks in runs (<see cref="Mode"/>): it charges from its owner at <see cref="ChargeSpeed"/> (turning at most
	/// <see cref="ChargeTurn"/> radians a tick), holds its line once inside <see cref="PassThrough"/> px so it runs straight
	/// through, keeps going until its last wagon is <see cref="PassExit"/> px past the enemy, then flies home and only
	/// charges again once back within <see cref="HomeRadius"/> of its owner (user, 2026-11-09: "nerf the train summon so it
	/// attacks a bit slower: it should go back to the player before attacking again"; it used to turn back and pass again).
	/// It hurts only while charging, and within one run every segment that hits the same enemy deals
	/// <see cref="FalloffPerHit"/> times the one before (user-set: "each subsequent hit from the wagons on the same enemy on
	/// the same attack causes 12% less damage than the previous wagon": the engine 100%, the next 88%, then 77.4%...).
	/// <para>The wagons (<see cref="GhostTrainWagon"/>, one per further blow of the whistle) are placed by the engine every
	/// tick, in hitching order, along the path it has run (a ring of points <see cref="TrailStep"/> px apart, walked once by
	/// arc length), so they follow its every turn as the Conductor's train does and never lag a tick behind it.</para>
	/// <para>Targeting as ExampleMod 1.4.4's <c>ExampleSimpleMinion</c> and vanilla's Stardust Dragon (decompiled
	/// <c>AI_121</c>, 1000 px): the owner's whip or right-click target first, else the closest chaseable enemy within
	/// <see cref="TargetRange"/> of the owner (a ghost: no line of sight needed), re-chosen every
	/// <see cref="RetargetInterval"/> ticks.</para>
	/// <para>D2: <c>ai[0]</c> the target (+1, 0 for none), <c>ai[1]</c> the next wagon's ticket and <c>ai[2]</c> the run's
	/// <see cref="Mode"/>, set by the owner and synced on change, plus a sync every <see cref="SyncInterval"/> ticks (as
	/// vanilla's dragon); every client steers the same way from them and lays its own path, so every client places the same
	/// wagons. The damage falloff is the owner's (it deals the hits): a run number and, per enemy, the run it was last hit
	/// in and how many segments hit it then (two arrays made per engine). Hits are the owner's (vanilla's friendly
	/// projectile rule). D0: NaN guarded, a teleport home past <see cref="TeleportDistance"/> (the path is laid straight
	/// behind it again), at most <see cref="MaxWagons"/> wagons (more are dismissed), every index checked. D1: the path and
	/// the wagon list are fixed arrays made per engine in <see cref="SetDefaults"/>; one pass over the projectiles a tick.</para>
	/// </summary>
	public class GhostTrainEngine : CogpunkProjectile
	{
		public const float MinionSlots = 1f;
		public const int MaxWagons = 24;
		// shape, game px (art/bosses/cursedconductor/make_train_whistle_art.py): the engine and a car along their heading
		public const float EngineLength = 56f, CarLength = 42f, Gap = 4f;
		public const float FirstSpacing = EngineLength * 0.5f + Gap + CarLength * 0.5f, Spacing = CarLength + Gap;
		public const float EngineRadius = 12f, CarRadius = 10f;      // the hit capsules' half thickness
		// flight
		public const float IdleSpeed = 6.5f, ChargeSpeed = 16f, Accel = 0.45f;
		public const float IdleTurn = 0.07f, ChargeTurn = 0.16f;           // a 100 px turn at full speed
		public const float PassThrough = 64f;
		public const float OrbitRadius = 110f, OrbitHeight = 70f, OrbitFlatten = 0.35f, OrbitRate = 0.025f;
		public const float TargetRange = 1000f, TeleportDistance = 2000f;
		public const int RetargetInterval = 10, SyncInterval = 120;
		public const int HitCooldown = 20;
		// the runs (2026-11-09 nerf): home within HomeRadius of the orbit's centre before each charge; out PassExit px past
		// the enemy behind the last wagon; a charge that hasn't reached its enemy in ChargeTimeout ticks turns home
		public const float HomeRadius = 160f, PassExit = 96f, ReturnSpeed = 18f;
		public const int ChargeTimeout = 150;
		public const float FalloffPerHit = 0.88f;                 // user-set: 12% less than the segment before, same enemy, same run
		public const int PassTicks = 62;                          // a run (engine alone) on a still 32x48 target 20 tiles out (the sim; was 40)
		// the path
		public const float TrailStep = 4f;
		public const int TrailPoints = 400;                       // 1600 px: the longest train is 53 + 23 x 46 = 1111 px
		public const float Opacity = 0.85f;

		private static Asset<Texture2D> glow;

		private Vector2[] trail;
		private int trailHead, trailCount;
		private int[] wagons;
		private int retargetTimer;
		private Vector2[] samples;                                // the path's points at each wagon's distances (ahead, at, behind)
		// owner: the run under way and the damage falloff (per enemy: the run it was last hit in, segments that hit it then)
		private int run, chargeTicks;
		private float pastTarget;
		private int[] hitRun;
		private byte[] hitCount;

		/// <summary>The attack cycle, <c>ai[2]</c> (synced): orbiting, charging, holding the line through the enemy, flying
		/// home.</summary>
		public enum Mode { Idle = 0, Charge = 1, Through = 2, Return = 3 }

		public Mode CurrentMode {
			get => (Mode)(int)Projectile.ai[2];
			private set => Projectile.ai[2] = (float)value;
		}

		/// <summary>Only a run hurts (not the way home): read by the wagons too.</summary>
		public bool Hurting => CurrentMode == Mode.Charge || CurrentMode == Mode.Through;

		/// <summary>Wagons hitched now (counted every tick).</summary>
		public int WagonCount { get; private set; }

		private int TargetIndex {
			get => (int)Projectile.ai[0] - 1;
			set => Projectile.ai[0] = value + 1;
		}

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = 1;
			Main.projPet[Type] = true;                            // vanilla frees slots for a summon whose minion is a "pet"
			ProjectileID.Sets.MinionTargettingFeature[Type] = true;
			ProjectileID.Sets.MinionSacrificable[Type] = true;    // ... and only then (Player.FreeUpPetsAndMinions)
			ProjectileID.Sets.MinionCannotBeFreed[Type] = true;   // but never frees the engine itself
			ProjectileID.Sets.CultistIsResistantTo[Type] = true;
			ProjectileID.Sets.DrawScreenCheckFluff[Type] = 1200;
			CogpunkSets.RollsOwnCrit[Type] = true;
			if (!Main.dedServ) {
				glow = DepthLayers.RequestOptional(Texture + "_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 28;
			Projectile.height = 28;
			Projectile.friendly = true;
			Projectile.minion = true;
			Projectile.minionSlots = MinionSlots;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = HitCooldown;
			trail = new Vector2[TrailPoints];
			wagons = new int[MaxWagons];
			samples = new Vector2[MaxWagons * 3];
			hitRun = new int[Main.maxNPCs];
			hitCount = new byte[Main.maxNPCs];
		}

		public override bool? CanDamage() => Hurting ? null : false;

		/// <summary>Owner, as a segment strikes <paramref name="npc"/>: this hit's share (1 for the first segment of the run to
		/// hit it, then <see cref="FalloffPerHit"/> times the one before).</summary>
		public float NextHitScale(int npc) {
			if (hitRun == null || npc < 0 || npc >= hitRun.Length) {
				return 1f;
			}
			if (hitRun[npc] != run) {
				hitRun[npc] = run;
				hitCount[npc] = 0;
			}
			float scale = MathF.Pow(FalloffPerHit, hitCount[npc]);
			if (hitCount[npc] < byte.MaxValue) {
				hitCount[npc]++;
			}
			return scale;
		}

		public override bool? CanCutTiles() => false;

		public override bool MinionContactDamage() => true;

		/// <summary>The owner's engine, or null (owner side: the whistle's <c>Shoot</c>).</summary>
		public static Projectile FindOwned(Player owner) {
			int type = ModContent.ProjectileType<GhostTrainEngine>();
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == type && p.owner == owner.whoAmI) {
					return p;
				}
			}
			return null;
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			int buff = ModContent.BuffType<GhostTrainBuff>();
			if (!owner.active || owner.dead) {
				owner.ClearBuff(buff);
				return;
			}
			if (owner.HasBuff(buff)) {
				Projectile.timeLeft = 2;
			}
			bool isOwner = Projectile.owner == Main.myPlayer;
			if (isOwner) {
				if (Vector2.DistanceSquared(owner.Center, Projectile.Center) > TeleportDistance * TeleportDistance) {
					Projectile.Center = owner.Center + new Vector2(0f, -OrbitHeight);
					trailCount = 0;                               // the path starts again behind it
					Projectile.netUpdate = true;
				}
				if (--retargetTimer <= 0) {
					retargetTimer = RetargetInterval;
					int target = SearchTarget(owner);
					if (target != TargetIndex) {
						TargetIndex = target;
						Projectile.netUpdate = true;
					}
				}
				if (Main.GameUpdateCount % SyncInterval == 0) {
					Projectile.netUpdate = true;
				}
				UpdateRun(owner);
			}
			Steer(owner);
			MathSafety.Sanitize(ref Projectile.velocity);
			Record(Projectile.Center + Projectile.velocity);      // where vanilla moves it this tick
			PlaceWagons(owner, Projectile.Center + Projectile.velocity);
			if (!Main.dedServ) {
				Effects();
			}
		}

		private bool IsValidTarget(int index, Player owner) {
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC npc = Main.npc[index];
			return npc.CanBeChasedBy(Projectile) && Vector2.DistanceSquared(npc.Center, owner.Center) < TargetRange * TargetRange;
		}

		private int SearchTarget(Player owner) {
			int forced = owner.MinionAttackTargetNPC;
			if (IsValidTarget(forced, owner)) {
				return forced;
			}
			int best = -1;
			float bestSq = TargetRange * TargetRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}
				float sq = Vector2.DistanceSquared(npc.Center, owner.Center);
				if (sq < bestSq) {
					best = npc.whoAmI;
					bestSq = sq;
				}
			}
			return best;
		}

		private Vector2 Home(Player owner) => owner.Center + new Vector2(0f, -OrbitHeight);

		/// <summary>The train's length from the engine's middle to its last wagon's (what must clear the enemy).</summary>
		private float TrainLength => WagonCount <= 0 ? 0f : FirstSpacing + (WagonCount - 1) * Spacing;

		/// <summary>Owner: the run's mode changes (each synced): home with an enemy in reach starts a charge (a new run for the
		/// falloff); inside <see cref="PassThrough"/> it holds its line; once the last wagon is <see cref="PassExit"/> past the
		/// enemy, or the enemy is gone, or the charge ran <see cref="ChargeTimeout"/> ticks, it flies home; home again, it
		/// charges or idles.</summary>
		private void UpdateRun(Player owner) {
			int target = TargetIndex;
			bool valid = IsValidTarget(target, owner);
			Mode mode = CurrentMode;
			Mode next = mode;
			switch (mode) {
				case Mode.Charge:
					chargeTicks++;
					if (!valid || chargeTicks > ChargeTimeout) {
						next = Mode.Return;
					}
					else if (Vector2.DistanceSquared(Main.npc[target].Center, Projectile.Center) < PassThrough * PassThrough) {
						next = Mode.Through;
						pastTarget = 0f;
					}
					break;
				case Mode.Through:
					pastTarget += Projectile.velocity.Length();
					if (pastTarget >= PassThrough + PassExit + TrainLength) {
						next = Mode.Return;
					}
					break;
				case Mode.Return:
					if (Vector2.DistanceSquared(Home(owner), Projectile.Center) < HomeRadius * HomeRadius) {
						next = valid ? Mode.Charge : Mode.Idle;
					}
					break;
				default:
					if (valid && Vector2.DistanceSquared(Home(owner), Projectile.Center) < HomeRadius * HomeRadius) {
						next = Mode.Charge;
					}
					else if (valid) {
						next = Mode.Return;                       // too far out: home first
					}
					break;
			}
			if (next != mode) {
				if (next == Mode.Charge) {
					run++;
					chargeTicks = 0;
				}
				CurrentMode = next;
				Projectile.netUpdate = true;
			}
		}

		/// <summary>Every side, by the synced mode: at the target, straight through it, home, or round the owner; the heading
		/// turns at most a set rate a tick and the speed eases towards its goal, so the path is a smooth curve the wagons can
		/// follow.</summary>
		private void Steer(Player owner) {
			Vector2 velocity = Projectile.velocity;
			float speed = velocity.Length();
			float angle = speed > 0.01f ? MathF.Atan2(velocity.Y, velocity.X) : (owner.direction >= 0 ? 0f : MathHelper.Pi);
			int target = TargetIndex;
			Mode mode = CurrentMode;
			Vector2 goal;
			float wantSpeed, turn;
			if (mode == Mode.Charge && IsValidTarget(target, owner)) {
				goal = Main.npc[target].Center;
				wantSpeed = ChargeSpeed;
				turn = ChargeTurn;
			}
			else if (mode == Mode.Through) {
				goal = Projectile.Center + Projectile.velocity;   // hold the line: straight through and out the far side
				wantSpeed = ChargeSpeed;
				turn = 0f;
			}
			else if (mode == Mode.Return) {
				goal = Home(owner);
				wantSpeed = ReturnSpeed;
				turn = ChargeTurn;
			}
			else {
				float t = Main.GameUpdateCount * OrbitRate + Projectile.whoAmI;
				goal = owner.Center + new Vector2(MathF.Cos(t) * OrbitRadius, -OrbitHeight + MathF.Sin(t) * OrbitRadius * OrbitFlatten);
				float far = Vector2.Distance(goal, Projectile.Center);
				wantSpeed = MathHelper.Clamp(far * 0.06f, IdleSpeed, ChargeSpeed);
				turn = IdleTurn;
			}
			Vector2 to = goal - Projectile.Center;
			if (to.LengthSquared() > 1f && turn > 0f) {
				float diff = MathHelper.WrapAngle(MathF.Atan2(to.Y, to.X) - angle);
				angle += MathHelper.Clamp(diff, -turn, turn);
			}
			speed += MathHelper.Clamp(wantSpeed - speed, -Accel, Accel);
			Projectile.velocity = new Vector2(MathF.Cos(angle), MathF.Sin(angle)) * Math.Max(1f, speed);
		}

		private void Record(Vector2 at) {
			if (!MathSafety.IsFinite(at)) {
				return;
			}
			if (trailCount == 0) {
				trailHead = 0;
				trail[0] = at;
				trailCount = 1;
				return;
			}
			if (Vector2.DistanceSquared(at, trail[trailHead]) < TrailStep * TrailStep) {
				return;
			}
			trailHead = (trailHead + 1) % TrailPoints;
			trail[trailHead] = at;
			if (trailCount < TrailPoints) {
				trailCount++;
			}
		}

		/// <summary>Every side: the owner's wagons hitched to this engine, in ticket order, each set on the path at its
		/// distance behind the engine with the path's heading there; wagons past <see cref="MaxWagons"/> are dismissed by the
		/// owner.</summary>
		private void PlaceWagons(Player owner, Vector2 head) {
			int wagonType = ModContent.ProjectileType<GhostTrainWagon>();
			int count = 0;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type != wagonType || p.owner != Projectile.owner || (int)p.ai[1] != Projectile.projUUID) {
					continue;
				}
				if (count >= MaxWagons) {
					if (Projectile.owner == Main.myPlayer) {
						p.Kill();
					}
					continue;
				}
				int k = count++;                                  // insertion sort by ticket (ai[0]); at most MaxWagons
				while (k > 0 && Main.projectile[wagons[k - 1]].ai[0] > p.ai[0]) {
					wagons[k] = wagons[k - 1];
					k--;
				}
				wagons[k] = p.whoAmI;
			}
			WagonCount = count;
			if (count == 0) {
				return;
			}
			SampleTrail(head, count);
			for (int k = 0; k < count; k++) {
				Projectile wagon = Main.projectile[wagons[k]];
				Vector2 ahead = samples[k * 3], at = samples[k * 3 + 1], behind = samples[k * 3 + 2];
				Vector2 heading = (ahead - behind).SafeNormalize(Projectile.velocity.SafeNormalize(Vector2.UnitX));
				if (!MathSafety.IsFinite(at)) {
					continue;
				}
				wagon.Center = at;
				wagon.velocity = Vector2.Zero;
				wagon.rotation = MathF.Atan2(heading.Y, heading.X);
				if (wagon.ModProjectile is GhostTrainWagon w) {
					w.Rank = k + 1;
					w.PlacedTick = Main.GameUpdateCount;
				}
			}
		}

		/// <summary>One walk back along the path from <paramref name="head"/> filling <see cref="samples"/>: for wagon k, the
		/// points at its distance - 10, at it and + 10 px (all increasing, as the spacing is over 20). Past the path's end the
		/// points go on in a straight line.</summary>
		private void SampleTrail(Vector2 head, int count) {
			int total = count * 3;
			int next = 0;
			float acc = 0f;
			Vector2 prev = head;
			Vector2 dir = -Projectile.velocity.SafeNormalize(Vector2.UnitX);
			int idx = trailHead;
			for (int i = 0; i < trailCount && next < total; i++) {
				Vector2 p = trail[idx];
				float seg = Vector2.Distance(prev, p);
				if (seg > 0.001f) {
					dir = (p - prev) / seg;
					while (next < total) {
						float want = Distance(next);
						if (want > acc + seg) {
							break;
						}
						samples[next++] = prev + dir * (want - acc);
					}
					acc += seg;
					prev = p;
				}
				idx = idx == 0 ? TrailPoints - 1 : idx - 1;
			}
			while (next < total) {
				samples[next] = prev + dir * (Distance(next) - acc);
				next++;
			}
		}

		private const float HeadingLook = 10f;                    // a wagon's heading is read over +-10 px of path

		private static float Distance(int sample) {
			int k = sample / 3, which = sample % 3;
			return Math.Max(0f, FirstSpacing + k * Spacing + (which - 1) * HeadingLook);
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 u = Projectile.velocity.SafeNormalize(Vector2.UnitX) * (EngineLength * 0.5f - EngineRadius);
			return SwingPose.CapsuleHitsRect(Projectile.Center - u, Projectile.Center + u, EngineRadius, targetHitbox);
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			// summon damage skips vanilla's crit roll; tModLoader keeps CritChance current for minions (the owner's roll, D2)
			if (Main.rand.Next(100) < Projectile.CritChance) {
				modifiers.SetCrit();
			}
			modifiers.SourceDamage *= NextHitScale(target.whoAmI);   // the first of the run to hit it: 100%
		}

		/// <summary>His train's ghost light and stack steam (since 2026-11-10 the summon wears the boss train's colours, user:
		/// "more ghostly blue, like the boss one"; GhostTrain.Effects).</summary>
		private void Effects() {
			Lighting.AddLight(Projectile.Center, 0.2f, 0.55f, 0.45f);
			if (!Main.rand.NextBool(4) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			Vector2 heading = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			Vector2 stack = Projectile.Center + heading * 10f + new Vector2(heading.Y, -heading.X) * Math.Sign(heading.X == 0f ? 1f : heading.X) * 14f;
			if (SafeSpawn.TryNewDust(stack - new Vector2(4f), 8, 8, DustID.CursedTorch, out Dust d)) {
				d.noGravity = true;
				d.velocity = -Projectile.velocity * 0.1f + new Vector2(0f, -0.8f);
				d.scale = 0.9f;
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			DrawSegment(TextureAssets.Projectile[Type].Value, glow?.IsLoaded == true ? glow.Value : null, GhostTrainArt.EngineCell, Projectile.Center,
				Projectile.velocity);
			return false;
		}

		/// <summary>A segment at its pre-drawn heading (mirrored for the left half, never rotated: D4), translucent, its lit
		/// windows and lamp solid from the glow sheet, at whole pixels.</summary>
		public static void DrawSegment(Texture2D sheet, Texture2D lit, int cell, Vector2 center, Vector2 heading) {
			int frame = Train.HeadingFrame(heading.SafeNormalize(Vector2.UnitX), out bool flip);
			Rectangle source = new(0, frame * (cell + 2), cell, cell);
			Vector2 at = center - Main.screenPosition;
			at = new Vector2(MathF.Round(at.X), MathF.Round(at.Y));
			Vector2 origin = new(cell * 0.5f);
			SpriteEffects effects = flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			if (sheet != null && source.Bottom <= sheet.Height) {
				Main.EntitySpriteDraw(sheet, at, source, Color.White * Opacity, 0f, origin, 1f, effects);
			}
			if (lit != null && source.Bottom <= lit.Height) {
				Main.EntitySpriteDraw(lit, at, source, Color.White, 0f, origin, 1f, effects);
			}
		}
	}

	/// <summary>The mini train's sheet cells (game px; art/bosses/cursedconductor/make_train_whistle_art.py).</summary>
	public static class GhostTrainArt
	{
		public const int EngineCell = 68, CarCell = 56;
	}
}
