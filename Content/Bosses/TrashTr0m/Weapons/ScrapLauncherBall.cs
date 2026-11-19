using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// The Scrap Launcher's right-click shot: Trash-Tr0m's big scrap ball (<see cref="Projectiles.TrashTr0mScrapBall"/>:
	/// same size, gravity and spin), friendly-coloured. Unlike the chunk it falls under gravity (user-set 2026-10-27). It
	/// bounces off the ground or a wall <see cref="MaxBounces"/> time, losing some speed, and breaks on the next tile or on
	/// the first enemy it hits (<c>penetrate = 1</c>) in a big <see cref="ScrapImpact"/> burst.
	/// <para>D2: the bounce count is <c>ai[0]</c>; tile collision runs on every side with the same synced start, and the
	/// owner's copy is authoritative for hits.</para>
	/// </summary>
	public class ScrapLauncherBall : CogpunkProjectile
	{
		public const float Gravity = Projectiles.TrashTr0mScrapBall.Gravity;
		public const int MaxBounces = 1;
		public const float BounceKeep = 0.6f;            // fraction of the speed kept by a bounce
		public const int Frames = 4;
		public const int TicksPerFrame = 5;
		private const int FrameSize = 60, FrameStride = 62;

		private ref float Bounces => ref Projectile.ai[0];

		private ref float Launched => ref Projectile.localAI[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 44;                         // a little inside the 50 px ball, so it doesn't snag on every ledge
			Projectile.height = 44;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = ModContent.GetInstance<Mechanist.MechanistDamage>();
			Projectile.tileCollide = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 240;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			if (Launched == 0f) {
				Launched = 1f;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item62 with { Pitch = -0.3f, MaxInstances = 2 }, Projectile.Center);
					ScrapLauncherChunk.LaunchPuff(Projectile.Center, Projectile.velocity, 12);
					if (Projectile.owner == Main.myPlayer && (CogpunkClientConfig.Instance?.ScreenShake ?? true)) {
						Main.instance.CameraModifiers.Add(new PunchCameraModifier(Projectile.Center, -Projectile.velocity.SafeNormalize(Vector2.UnitX), 3f, 8f, 8, 600f, "Cogpunk:ScrapLauncher"));
					}
				}
			}
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 16f);
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + (Projectile.velocity.X >= 0f ? 1 : Frames - 1)) % Frames;
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect() && Main.rand.NextBool(2)
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Smoke, out Dust d, 0f, 0f, 120, new Color(127, 135, 148), 1.2f)) {
				d.velocity *= 0.2f;
				d.noGravity = true;
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Bounces >= MaxBounces) {
				return true;                               // the second tile breaks it
			}
			Bounces++;
			if (Math.Abs(Projectile.velocity.X - oldVelocity.X) > 0.01f) {
				Projectile.velocity.X = -oldVelocity.X * BounceKeep;
			}
			if (Math.Abs(Projectile.velocity.Y - oldVelocity.Y) > 0.01f) {
				Projectile.velocity.Y = -oldVelocity.Y * BounceKeep;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.7f, MaxInstances = 2 }, Projectile.Center);
				for (int i = 0; i < 8; i++) {
					SafeSpawn.TryNewDust(Projectile.BottomLeft - new Vector2(0f, 6f), Projectile.width, 8, i % 2 == 0 ? DustID.Iron : DustID.Smoke, out _, 0f, -2f);
				}
			}
			return false;
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			ScrapImpact.Burst(Projectile.Center, Projectile.velocity, big: true);
			if (Projectile.owner == Main.myPlayer && (CogpunkClientConfig.Instance?.ScreenShake ?? true)) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(Projectile.Center, Vector2.UnitY, 2.5f, 8f, 8, 600f, "Cogpunk:ScrapLauncherHit"));
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			ScrapLauncherChunk.DrawCentredFrame(Projectile, TextureAssets.Projectile[Type].Value, FrameSize, FrameSize, FrameStride, lightColor);
			return false;
		}
	}
}
