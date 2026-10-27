using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// Tr0mhead: a small copy of Trash-Tr0m's head on a scrap tripod (sentry, <see cref="Tr0mheadStaff"/>). When an enemy
	/// comes within <see cref="SuckRange"/> (and in line of sight) it turns to it, drops its jaw and inhales like the boss's
	/// suction, without the spitting: enemies in range are dragged towards its mouth and chewed for the staff's damage once
	/// per second each (<see cref="HitCooldown"/>: 15 summon damage per second). It sucks for at most
	/// <see cref="SuckTicks"/> (5 s), or until nothing has been in range for <see cref="NoTargetGrace"/> ticks, then shuts
	/// its jaw and vents steam for <see cref="RestTicks"/> (2.5 s) before it can suck again.
	/// <para>The pull is a steer of the enemy's velocity towards the mouth, scaled by its knockback resistance, so bosses and
	/// anything that ignores knockback don't move (walkers are only pulled sideways, fliers in both axes). Fliers
	/// (<c>noGravity</c>) are pulled harder (user-set 2026-10-27): <see cref="FlyerPullScale"/>x the speed and
	/// <see cref="FlyerSteerScale"/>x the steer.</para>
	/// <para>D2: <c>ai[0]</c> state, <c>ai[1]</c> timer, <c>ai[2]</c> facing; every side counts the timer, only the owner
	/// changes state or facing and syncs then. The pull runs on every side from that synced state, the way vanilla applies
	/// knockback on every side; the server's copy is authoritative and its NPC syncs correct any drift. Damage is the
	/// owner's, as for every player projectile. D1: one pass over the active NPCs per tick, a line-of-sight check only for
	/// those already in range, no allocation; effects client-only.</para>
	/// </summary>
	public class Tr0mheadSentry : CogpunkProjectile
	{
		public enum SentryState { Idle, Open, Suck, Close, Rest }

		public const int HitboxWidth = 36;
		public const int HitboxHeight = 44;
		public const float SuckRange = 18f * 16f;
		public const float FullPullRange = 8f * 16f;     // full strength inside this, fading to nothing at SuckRange
		public const int SuckTicks = 300;
		public const int RestTicks = 150;
		public const int OpenTicks = 12;
		public const int CloseTicks = 12;
		public const int RampTicks = 20;
		public const int NoTargetGrace = 45;
		public const int HitCooldown = 60;               // one bite per enemy per second
		public const float PullSpeed = 5f;
		public const float PullSteer = 0.14f;
		public const float FlyerPullScale = 1.8f;          // fliers: faster...
		public const float FlyerSteerScale = 1.6f;         // ...and steered harder
		public const float MouthStop = 18f;              // no pull this close to the mouth (no jitter)
		public const int FrameWidth = 56, FrameHeight = 60, FrameStride = 62;
		public const int FrameCount = 10;
		public const int IdleFrame = 0, OpenFrame = 2, SuckFrame = 4, RestFrame = 8;
		/// <summary>Mouth point relative to the hitbox centre, art facing left (mirrored when facing right). From the generator.</summary>
		public static readonly Vector2 MouthOffset = new(-8f, -1f);

		private static Asset<Texture2D> glow;

		private SentryState State {
			get => (SentryState)(int)Projectile.ai[0];
			set => Projectile.ai[0] = (int)value;
		}

		private ref float Timer => ref Projectile.ai[1];
		private ref float Facing => ref Projectile.ai[2];
		private ref float Spawned => ref Projectile.localAI[0];
		private ref float SinceTarget => ref Projectile.localAI[1];

		public Vector2 Mouth => Projectile.Center + new Vector2(MouthOffset.X * -FacingSign, MouthOffset.Y);

		private int FacingSign => Facing >= 0f ? 1 : -1;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = FrameCount;
			ProjectileID.Sets.MinionTargettingFeature[Type] = true;
			if (!Main.dedServ) {
				glow = TetanusProjectile.TryRequest("Cogpunk/Content/Bosses/TrashTr0m/Weapons/Tr0mheadSentry_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = HitboxWidth;
			Projectile.height = HitboxHeight;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.sentry = true;
			Projectile.timeLeft = Projectile.SentryLifeTime;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;              // synced to players who join later
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = HitCooldown;
			Projectile.aiStyle = -1;
		}

		public override bool TileCollideStyle(ref int width, ref int height, ref bool fallThrough, ref Vector2 hitboxCenterFrac) {
			fallThrough = false;                         // stands on platforms too
			return true;
		}

		public override bool OnTileCollide(Vector2 oldVelocity) => false;

		public override void AI() {
			Projectile.velocity.X = 0f;
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + 0.3f, 12f);
			if (Spawned == 0f) {
				Spawned = 1f;
				if (Facing == 0f) {
					Facing = -1f;                            // the art faces left
				}
				if (!Main.dedServ) {
					SpawnEffects();
				}
			}
			Timer++;
			bool owner = Projectile.owner == Main.myPlayer;
			NPC target = owner && (State == SentryState.Idle || State == SentryState.Suck) ? FindTarget() : null;   // only these use it (D1)
			switch (State) {
				case SentryState.Idle:
					if (owner && target != null) {
						Face(target);
						Switch(SentryState.Open);
					}
					break;
				case SentryState.Open:
					if (owner && Timer >= OpenTicks) {
						Switch(SentryState.Suck);
					}
					break;
				case SentryState.Suck:
					SinceTarget = target != null || !owner ? 0f : SinceTarget + 1f;
					if (owner && target != null) {
						Face(target);
					}
					if (owner && (Timer >= SuckTicks || SinceTarget >= NoTargetGrace)) {
						Switch(SentryState.Close);
					}
					else {
						Pull();
					}
					break;
				case SentryState.Close:
					if (owner && Timer >= CloseTicks) {
						Switch(SentryState.Rest);
					}
					break;
				case SentryState.Rest:
					if (owner && Timer >= RestTicks) {
						Switch(SentryState.Idle);
					}
					break;
				default:
					if (owner) {
						Switch(SentryState.Idle);                // unknown state from a newer version (D0)
					}
					break;
			}
			Projectile.frame = ResolveFrame();
			Projectile.spriteDirection = FacingSign;
			if (!Main.dedServ) {
				StateEffects();
			}
		}

		private void Switch(SentryState next) {
			State = next;
			Timer = 0f;
			SinceTarget = 0f;
			Projectile.netUpdate = true;
		}

		private void Face(NPC target) {
			float dir = target.Center.X >= Projectile.Center.X ? 1f : -1f;
			if (dir != Facing) {
				Facing = dir;
				Projectile.netUpdate = true;
			}
		}

		private bool InReach(NPC npc, Vector2 mouth) {
			return npc.CanBeChasedBy(Projectile) && Vector2.DistanceSquared(npc.Center, mouth) <= SuckRange * SuckRange
				&& Collision.CanHitLine(mouth, 1, 1, npc.position, npc.width, npc.height);
		}

		/// <summary>The whip-tagged target if it is in reach, else the closest enemy in reach (owner only).</summary>
		private NPC FindTarget() {
			Vector2 mouth = Mouth;
			NPC tagged = Projectile.OwnerMinionAttackTargetNPC;
			if (tagged != null && InReach(tagged, mouth)) {
				return tagged;
			}
			NPC best = null;
			float bestDistance = SuckRange * SuckRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				float d = Vector2.DistanceSquared(npc.Center, mouth);
				if (d < bestDistance && InReach(npc, mouth)) {
					bestDistance = d;
					best = npc;
				}
			}
			return best;
		}

		/// <summary>Every side: steers enemies in reach towards the mouth (ramps up, fades with distance, scaled by knockback
		/// resistance; bosses never move).</summary>
		private void Pull() {
			float strength = MathHelper.Clamp(Timer / RampTicks, 0f, 1f);
			Vector2 mouth = Mouth;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.boss || npc.knockBackResist <= 0f || !npc.CanBeChasedBy(Projectile)) {
					continue;
				}
				Vector2 d = mouth - npc.Center;
				float dist2 = d.LengthSquared();
				if (dist2 > SuckRange * SuckRange || dist2 < MouthStop * MouthStop
					|| !Collision.CanHitLine(mouth, 1, 1, npc.position, npc.width, npc.height)) {
					continue;
				}
				float dist = MathF.Sqrt(dist2);
				float falloff = dist < FullPullRange ? 1f : 1f - (dist - FullPullRange) / (SuckRange - FullPullRange);
				bool flyer = npc.noGravity;
				float steer = PullSteer * strength * falloff * Math.Min(1f, npc.knockBackResist) * (flyer ? FlyerSteerScale : 1f);
				Vector2 want = d / dist * (PullSpeed * (flyer ? FlyerPullScale : 1f));
				npc.velocity.X = MathHelper.Lerp(npc.velocity.X, want.X, steer);
				if (flyer) {
					npc.velocity.Y = MathHelper.Lerp(npc.velocity.Y, want.Y, steer);
				}
			}
		}

		public override bool? CanDamage() => State == SentryState.Suck ? null : false;

		/// <summary>Bites anything in reach of the mouth (circle around it), not only what touches the head.</summary>
		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 mouth = Mouth;
			Vector2 nearest = Vector2.Clamp(mouth, targetHitbox.TopLeft(), targetHitbox.BottomRight());
			return Vector2.DistanceSquared(nearest, mouth) <= SuckRange * SuckRange;
		}

		public override bool? CanHitNPC(NPC target) {
			return Collision.CanHitLine(Mouth, 1, 1, target.position, target.width, target.height) ? null : false;
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			modifiers.DisableKnockback();                 // the pull does the moving
			if (Main.rand.Next(100) < Projectile.CritChance) {
				modifiers.SetCrit();                      // summon damage skips vanilla's crit roll (see MiceBotMinion)
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (!Main.dedServ) {
				Vector2 at = Vector2.Lerp(target.Center, Mouth, 0.5f);
				for (int i = 0; i < 4; i++) {
					SafeSpawn.TryNewDust(at - new Vector2(4f), 8, 8, i % 2 == 0 ? DustID.Iron : DustID.Enchanted_Gold, out _);
				}
			}
		}

		private int ResolveFrame() {
			int t = (int)Timer;
			switch (State) {
				case SentryState.Open:
					return t < OpenTicks / 2 ? OpenFrame : OpenFrame + 1;
				case SentryState.Suck:
					return SuckFrame + (t / 3) % 4;
				case SentryState.Close:
					return t < CloseTicks / 2 ? OpenFrame + 1 : OpenFrame;
				case SentryState.Rest:
					return RestFrame + (t / 15) % 2;
				default:
					return IdleFrame + (t / 20) % 2;
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Effects (clients)
		// ------------------------------------------------------------------------------------------------------------

		private void SpawnEffects() {
			for (int i = 0; i < 16; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 2 == 0 ? DustID.Iron : DustID.Smoke, out Dust d,
					0f, -1.5f, 80, default, 1.2f)) {
					d.velocity *= 1.5f;
				}
			}
		}

		private void StateEffects() {
			int t = (int)Timer;
			switch (State) {
				case SentryState.Open:
					if (t == 1) {
						SoundEngine.PlaySound(SoundID.DD2_BetsyWindAttack with { Pitch = 0.4f, Volume = 0.45f, MaxInstances = 2 }, Projectile.Center);
					}
					break;
				case SentryState.Suck:
					if (t % 30 == 1) {
						SoundEngine.PlaySound(SoundID.DD2_BookStaffTwisterLoop with { Pitch = 0.3f, Volume = 0.35f, MaxInstances = 2 }, Projectile.Center);
					}
					SuckStreaks();
					break;
				case SentryState.Close:
					if (t == 1) {
						SoundEngine.PlaySound(SoundID.Item2 with { Pitch = 0.2f, Volume = 0.6f }, Projectile.Center);   // gulp
					}
					break;
				case SentryState.Rest:
					if (t == 1) {
						SoundEngine.PlaySound(SoundID.Item34 with { Pitch = 0.6f, Volume = 0.35f }, Projectile.Center);   // the steam vents
					}
					if (t % 10 == 0 && CogpunkClientConfig.RollEffect()) {
						Vector2 stack = Projectile.Center + new Vector2(-12f * FacingSign, -32f);   // the exhaust (art: behind the head)
						if (SafeSpawn.TryNewDust(stack - new Vector2(3f), 6, 6, DustID.Smoke, out Dust s, 0f, -1.5f, 100, new Color(195, 200, 205), 1.1f)) {
							s.noGravity = true;
						}
					}
					break;
			}
		}

		/// <summary>Air streaks (steam, aether) rushing into the mouth from the edge of its reach.</summary>
		private void SuckStreaks() {
			if (!CogpunkClientConfig.RollEffect() || !Main.rand.NextBool(2)) {
				return;
			}
			Vector2 mouth = Mouth;
			float strength = MathHelper.Clamp(Timer / RampTicks, 0f, 1f);
			float angle = (FacingSign == 1 ? 0f : MathHelper.Pi) + Main.rand.NextFloat(-1.1f, 1.1f);
			Vector2 at = mouth + angle.ToRotationVector2() * Main.rand.NextFloat(60f, SuckRange);
			bool aether = Main.rand.NextBool(3);
			if (SafeSpawn.TryNewDust(at, 4, 4, aether ? DustID.PurpleTorch : DustID.Smoke, out Dust d, 0f, 0f, aether ? 0 : 120,
				aether ? default : new Color(238, 241, 243), aether ? 1f : 0.8f)) {
				d.noGravity = true;
				d.velocity = (mouth - at).SafeNormalize(Vector2.Zero) * (4f + 5f * strength);
				d.fadeIn = 0.5f;
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameWidth, FrameHeight);
			Vector2 bottom = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY + 2f);
			Vector2 position = new((int)(bottom.X - FrameWidth * 0.5f), (int)(bottom.Y - FrameHeight));
			SpriteEffects effects = FacingSign == 1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;   // the art faces left
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), 0f, Vector2.Zero, 1f, effects);
			if (glow?.IsLoaded == true) {
				float pulse = State == SentryState.Rest ? 0.35f : (State == SentryState.Suck ? 1f : 0.8f + 0.2f * MathF.Sin(Main.GlobalTimeWrappedHourly * 3f));
				Main.EntitySpriteDraw(glow.Value, position, source, Color.White * pulse, 0f, Vector2.Zero, 1f, effects);
			}
			return false;
		}
	}
}
