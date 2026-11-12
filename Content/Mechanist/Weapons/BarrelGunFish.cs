using System;
using Cogpunk.Content.Mechanist.Buffs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// The Barrel Gun's fish (user-set 2026-11-11b: "shoot fish ... with a chance to stun enemies (only stun basic enemies,
	/// not bosses or mini bosses); it can't crit and gains 50% more damage and homing when it's raining or underwater"). A
	/// bass, a trout or a snapper (<c>ai[1]</c>, the owner's pick) flopping through the air: it flies in a shallow arc
	/// (<see cref="Gravity"/> after <see cref="GravityDelay"/> ticks) and bursts in a splash on the first enemy or wall. A hit
	/// stuns the enemy <see cref="StunChance"/> of the time for <see cref="StunTicks"/> (my calls; basic enemies only,
	/// <see cref="StunnedNPC.CanStun"/>) and never crits. Empowered (<c>ai[0]</c> = 1: rain or water round the wielder as it
	/// fired, <see cref="BarrelGun.Empowered"/>; the +50% is already in its damage) it swims straight through the air and
	/// homes in on the nearest enemy in sight within <see cref="HomingRange"/>, trailing water.
	/// <para>D2: the owner's projectile: its hits and stun rolls are the owner's (the stun is a buff vanilla syncs); every
	/// side runs the same flight, the homing's target picked from the synced positions every <see cref="RetargetTicks"/>
	/// ticks, the owner re-syncing it when the target changes. D0/D1: finite <see cref="Lifetime"/>, one NPC walk every
	/// <see cref="RetargetTicks"/> ticks, no allocation; dust, light and sound on clients.</para>
	/// </summary>
	public class BarrelGunFish : CogpunkProjectile
	{
		public const int Kinds = 3, FlopFrames = 2, FrameTicks = 6;
		public const int FrameWidth = 24, FrameHeight = 16, FrameStride = FrameHeight + 2;
		public const float StunChance = 0.12f;                     // my call: "a chance to stun"
		public const int StunTicks = 60;                           // my call: 1 s
		public const int Lifetime = 150;
		public const int GravityDelay = 10;
		public const float Gravity = 0.18f, MaxFall = 12f;
		public const float HomingRange = 30f * 16f, HomingSpeed = 11f, HomingLerp = 0.1f;
		public const int RetargetTicks = 10;

		private bool Empowered => Projectile.ai[0] >= 1f;
		private int Kind => Math.Clamp((int)Projectile.ai[1], 0, Kinds - 1);
		private ref float Age => ref Projectile.localAI[0];
		private ref float TargetSlot => ref Projectile.localAI[1];     // the homing's target + 1 (0: none)

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 12;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = ModContent.GetInstance<MechanistDamage>();
			Projectile.penetrate = 1;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;                             // a fish is at home in water
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			Age++;
			MathSafety.Sanitize(ref Projectile.velocity);
			if (Empowered) {
				Home();
			}
			else if (Age > GravityDelay) {
				Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFall);
			}
			Projectile.rotation = Projectile.velocity.ToRotation();
			if (Main.dedServ) {
				return;
			}
			if (Empowered) {
				Lighting.AddLight(Projectile.Center, 0.1f, 0.25f, 0.45f);
				if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Water, out Dust d)) {
					d.velocity = -Projectile.velocity * 0.15f;
					d.scale = 1.1f;
				}
			}
		}

		/// <summary>Every side: steers towards the nearest enemy in sight within <see cref="HomingRange"/> (picked every
		/// <see cref="RetargetTicks"/> ticks), at <see cref="HomingSpeed"/>.</summary>
		private void Home() {
			if (Age % RetargetTicks == 1f) {
				int pick = FindTarget();
				if (pick + 1 != (int)TargetSlot) {
					TargetSlot = pick + 1;
					if (Projectile.owner == Main.myPlayer) {
						Projectile.netUpdate = true;
					}
				}
			}
			int slot = (int)TargetSlot - 1;
			Vector2 dir = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			Vector2 want = dir * HomingSpeed;
			if (slot >= 0 && slot < Main.maxNPCs && Main.npc[slot].active && Main.npc[slot].CanBeChasedBy(Projectile)) {
				want = (Main.npc[slot].Center - Projectile.Center).SafeNormalize(dir) * HomingSpeed;
			}
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, want, HomingLerp);
		}

		private int FindTarget() {
			int best = -1;
			float bestDist = HomingRange * HomingRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}
				float d = Vector2.DistanceSquared(npc.Center, Projectile.Center);
				if (d < bestDist) {
					bestDist = d;
					best = npc.whoAmI;
				}
			}
			if (best >= 0 && !Collision.CanHitLine(Projectile.position, Projectile.width, Projectile.height, Main.npc[best].position,
				Main.npc[best].width, Main.npc[best].height)) {
				best = -1;                                             // not through walls
			}
			return best;
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			modifiers.DisableCrit();                                   // user-set: it can't crit
		}

		/// <summary>The owner's client (vanilla works out a player projectile's hits there): the stun's roll.</summary>
		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (Main.rand.NextFloat() < StunChance) {
				StunnedNPC.TryStun(target, StunTicks);
			}
		}

		/// <summary>Every client: a splash of water where it burst.</summary>
		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.SplashWeak with { Volume = 0.7f, Pitch = 0.2f, MaxInstances = 4 }, Projectile.Center);
			for (int k = 0; k < 8 && CogpunkClientConfig.RollEffect(); k++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Water, out Dust d)) {
					d.velocity = Main.rand.NextVector2Circular(2.5f, 2.5f) - Vector2.UnitY;
					d.scale = 1.2f;
				}
			}
		}

		/// <summary>Its kind's frame for the flop, pointing along its flight, belly down whichever way it flies.</summary>
		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			int frame = Kind * FlopFrames + (int)(Age / FrameTicks) % FlopFrames;
			Rectangle source = new(0, frame * FrameStride, FrameWidth, FrameHeight);
			if (source.Bottom > tex.Height) {
				return false;
			}
			SpriteEffects flip = Projectile.velocity.X < 0f ? SpriteEffects.FlipVertically : SpriteEffects.None;
			Color colour = Empowered ? Color.Lerp(lightColor, Color.White, 0.35f) : lightColor;
			Main.EntitySpriteDraw(tex, Projectile.Center - Main.screenPosition, source, colour, Projectile.rotation,
				new Vector2(FrameWidth / 2f, FrameHeight / 2f), 1f, flip);
			return false;
		}
	}
}
