using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The Metal Wrench's clash (user-set 2026-10-30: "a metal clash sound and effect"): a starburst of brass and white
	/// (<see cref="Frames"/> frames of <see cref="FrameTicks"/> ticks), the clang (Assets/Sounds/Weapons/MetalClash.wav) and
	/// sparks, by mode (<c>ai[0]</c>):
	/// <list type="bullet">
	/// <item><see cref="ParryMode"/>: a blow turned aside by the guard.</item>
	/// <item><see cref="HitMode"/>: the riposte landing on an ordinary enemy (smaller).</item>
	/// <item><see cref="BossMode"/>: the riposte landing on a boss or a mini-boss: the clang an octave down, a heavier camera
	/// punch, and <see cref="SlowMotion"/> for every entity (<see cref="MetalWrench.SlowMotionTicks"/> ticks at
	/// <see cref="MetalWrench.SlowMotionSpeed"/>). It starts on each side as this projectile first updates there: the owner at
	/// once, the server and the other clients when vanilla's projectile sync brings it (D2, no packet of its own).</item>
	/// </list>
	/// It keeps full speed through the slow motion it starts (<see cref="CogpunkSets.IgnoresSlowMotion"/>), deals no damage
	/// and lives <see cref="Lifetime"/> ticks. D1: effects client-side and throttled by the effect density.
	/// </summary>
	public class MetalClash : CogpunkProjectile
	{
		public const float HitMode = 0f, ParryMode = 1f, BossMode = 2f;
		public const int Frames = 6, FrameTicks = 3;
		public const int Lifetime = Frames * FrameTicks;
		private const int FrameSize = 64, FrameStride = 66;

		public static readonly SoundStyle Clang = new("Cogpunk/Assets/Sounds/Weapons/MetalClash") {
			Volume = 0.8f,
			PitchVariance = 0.1f,
			MaxInstances = 4,
		};

		private ref float Mode => ref Projectile.ai[0];
		private ref float Started => ref Projectile.localAI[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
			CogpunkSets.IgnoresSlowMotion[Type] = true;
		}

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage() => false;

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (Started == 0f) {
				Started = 1f;
				if (Mode == BossMode) {
					SlowMotion.Start(MetalWrench.SlowMotionTicks, MetalWrench.SlowMotionSpeed);
				}
				if (!Main.dedServ) {
					Burst();
				}
			}
			Projectile.frame = Math.Clamp((Lifetime - Projectile.timeLeft) / FrameTicks, 0, Frames - 1);
			if (!Main.dedServ) {
				float glow = 1f - Projectile.frame / (float)Frames;
				Lighting.AddLight(Projectile.Center, 0.9f * glow, 0.75f * glow, 0.4f * glow);
			}
		}

		private void Burst() {
			bool boss = Mode == BossMode;
			bool parry = Mode == ParryMode;
			SoundEngine.PlaySound(Clang with { Pitch = boss ? -0.45f : (parry ? 0.15f : -0.1f), Volume = Mode == HitMode ? 0.55f : 0.8f }, Projectile.Center);
			if (boss) {
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f, Volume = 0.45f }, Projectile.Center);
			}
			if (CogpunkClientConfig.Instance?.ScreenShake ?? true) {
				float strength = boss ? 7f : (parry ? 3f : 2f);
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(Projectile.Center, Main.rand.NextVector2Unit(), strength, 12f, boss ? 20 : 10, 1000f, "Cogpunk:MetalClash"));
			}
			int sparks = boss ? 22 : (parry ? 12 : 8);
			for (int i = 0; i < sparks; i++) {
				if (i > 4 && !CogpunkClientConfig.RollEffect()) {
					continue;
				}
				int type = i % 3 == 0 ? DustID.GoldFlame : (i % 3 == 1 ? DustID.Enchanted_Gold : DustID.Iron);
				Vector2 v = Main.rand.NextVector2CircularEdge(1f, 1f) * Main.rand.NextFloat(3f, boss ? 9f : 6f);
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, type, out Dust d, v.X, v.Y, 0, default, boss ? 1.4f : 1.1f)) {
					d.noGravity = type != DustID.Iron;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameSize, FrameSize);
			Vector2 position = (Projectile.Center - Main.screenPosition - new Vector2(FrameSize * 0.5f)).Floor();
			float strength = Mode == HitMode ? 0.75f : 1f;
			if (CogpunkClientConfig.Instance?.ReduceFlashing ?? false) {
				strength *= 0.5f;
			}
			Main.EntitySpriteDraw(texture, position, source, Color.White * strength, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
