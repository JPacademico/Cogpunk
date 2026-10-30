using System;
using Cogpunk.Content.Junkyard.Tar;
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
using R = Cogpunk.Content.Bosses.TarTyrant.TarTyrantRigData;

namespace Cogpunk.Content.Bosses.TarTyrant.Projectiles
{
	/// <summary>
	/// One bone of Tar Tyrant's summoned row (user-set 2026-10-29: a wave of bones out of the ground across the whole
	/// screen, 5 tiles apart, with tar on the ground showing where each will come out). It stands still on the ground: first
	/// the boiling tar patch for <c>ai[0]</c> ticks (the warning, <see cref="MinWarnTicks"/> or more), then the bone bursts
	/// up (<see cref="RiseTicks"/>), stands <see cref="HoldTicks"/> and sinks. It hurts (<see cref="TarTyrant.SpikeDamage"/>
	/// in Expert, and the Tar Plague) only while it is up, and only where it is: the hitbox grows with the drawn bone.
	/// <para>D2: spawned by the server with its delay in <c>ai[0]</c>; <c>ai[1]</c> counts its ticks on every side, so
	/// every client shows the same warning and the same eruption. D0: the delay is clamped and the lifetime is finite.</para>
	/// </summary>
	public class TarTyrantBoneSpike : CogpunkProjectile
	{
		public const int HitboxWidth = 16, HitboxHeight = 72;
		public const int MinWarnTicks = 30, MaxWarnTicks = 200;
		public const int WarnFrameTicks = 6, RiseFrameTicks = 3, HoldFrameTicks = 8, SinkFrameTicks = 3;
		public const int RiseTicks = R.SpikeRiseFrames * RiseFrameTicks;
		public const int HoldTicks = 36;
		public const int SinkTicks = R.SpikeSinkFrames * SinkFrameTicks;
		private static readonly float[] RiseReach = { 0.32f, 0.78f, 1f, 1f };

		private ref float Delay => ref Projectile.ai[0];
		private ref float Age => ref Projectile.ai[1];

		public override void SetDefaults() {
			Projectile.width = HitboxWidth;
			Projectile.height = HitboxHeight;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = MaxWarnTicks + RiseTicks + HoldTicks + SinkTicks;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		/// <summary>Ticks since the bone broke the surface (negative while the patch is still boiling).</summary>
		private int Out => (int)(Age - Delay);

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (Age == 0f) {
				Delay = Math.Clamp(Delay, MinWarnTicks, MaxWarnTicks);
				Projectile.timeLeft = (int)Delay + RiseTicks + HoldTicks + SinkTicks;
			}
			Age++;
			if (Main.dedServ) {
				return;
			}
			int e = Out;
			Vector2 ground = Projectile.Bottom;
			if (e < 0) {
				Lighting.AddLight(ground - new Vector2(0f, 6f), 0.22f, 0.1f, 0.03f);
				if ((int)Age % 10 == 0 && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(ground - new Vector2(10f, 6f), 20, 6, ModContent.DustType<TarSplash>(), out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-0.6f, 0.6f), -Main.rand.NextFloat(1f, 2.4f));
				}
			}
			else if (e == 0) {
				SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = -0.2f, Volume = 0.6f, MaxInstances = 6, PitchVariance = 0.25f }, ground);
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 6; i++) {
						if (SafeSpawn.TryNewDust(ground - new Vector2(12f, 8f), 24, 8, i % 2 == 0 ? DustID.Bone : ModContent.DustType<TarSplash>(), out Dust d)) {
							d.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), -Main.rand.NextFloat(2f, 5f));
						}
					}
				}
			}
		}

		/// <summary>How much of the bone is out of the ground (0..1), from the drawn frames.</summary>
		private float Reach() {
			int e = Out;
			if (e < 0) {
				return 0f;
			}
			if (e < RiseTicks) {
				return RiseReach[Math.Clamp(e / RiseFrameTicks, 0, RiseReach.Length - 1)];
			}
			return e < RiseTicks + HoldTicks ? 1f : 0f;
		}

		public override bool CanHitPlayer(Player target) {
			int e = Out;
			return e >= RiseFrameTicks && e < RiseTicks + HoldTicks;
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			int h = (int)(HitboxHeight * Reach());
			if (h <= 0) {
				return false;
			}
			return new Rectangle(projHitbox.X, projHitbox.Bottom - h, projHitbox.Width, h).Intersects(targetHitbox);
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(ModContent.BuffType<TarPlague>(), TarTyrant.PlagueTicks);
		}

		private int Frame() {
			int e = Out;
			if (e < 0) {
				return R.SpikeWarn0 + (int)(Age / WarnFrameTicks) % R.SpikeWarnFrames;
			}
			if (e < RiseTicks) {
				return R.SpikeRise0 + Math.Min(R.SpikeRiseFrames - 1, e / RiseFrameTicks);
			}
			if (e < RiseTicks + HoldTicks) {
				return R.SpikeHold0 + (e - RiseTicks) / HoldFrameTicks % R.SpikeHoldFrames;
			}
			return R.SpikeSink0 + Math.Min(R.SpikeSinkFrames - 1, (e - RiseTicks - HoldTicks) / SinkFrameTicks);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Frame() * (R.SpikeHeight + 2), R.SpikeWidth, R.SpikeHeight);
			if (source.Bottom > texture.Height) {
				return false;
			}
			Vector2 bottom = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY + 2f);
			Vector2 position = new((int)(bottom.X - R.SpikeWidth * 0.5f), (int)(bottom.Y - R.SpikeHeight));
			Main.EntitySpriteDraw(texture, position, source, lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
