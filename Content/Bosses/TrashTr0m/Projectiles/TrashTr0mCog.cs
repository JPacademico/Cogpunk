using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;

namespace Cogpunk.Content.Bosses.TrashTr0m.Projectiles
{
	/// <summary>
	/// A loose, rusted cog that Trash-Tr0m's exhaust stacks cough up on their own all fight long (user-set 2026-10-27,
	/// <see cref="TrashTr0m.CogInterval"/>): fired high into the air towards a player, never straight at them
	/// (<see cref="TrashTr0m.CogVelocity"/>), it comes down on them under <see cref="Gravity"/> and bounces up to
	/// <see cref="MaxBounces"/> times, losing speed, before the next tile breaks it. 25 damage in Expert (Classic half, Master 1.5x).
	/// Pre-rendered spin (4 frames, ring teeth; D4: no runtime rotation), an ember spark trail (hostile colours, D3).
	/// <para>D2: spawned by the server; the bounce count is <c>ai[0]</c> and tile collision runs on every side from the
	/// same synced start.</para>
	/// </summary>
	public class TrashTr0mCog : CogpunkProjectile
	{
		public const float Gravity = 0.24f;
		public const int MaxBounces = 2;
		public const float BounceKeep = 0.7f;
		public const int Frames = 4;
		public const int TicksPerFrame = 4;
		private const int FrameSize = 24, FrameStride = 26;

		private ref float Bounces => ref Projectile.ai[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 18;                         // the 20 px cog in its 24 px frame, teeth tips trimmed
			Projectile.height = 18;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 360;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 14f);
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				int step = Projectile.velocity.X >= 0f ? 1 : Frames - 1;      // spins the way it flies
				Projectile.frame = (Projectile.frame + step) % Frames;
			}
			if (!Main.dedServ && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Torch, out Dust d, 0f, 0f, 0, default, 0.9f)) {
				d.velocity *= 0.3f;
				d.noGravity = true;
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Bounces >= MaxBounces) {
				return true;                               // the third tile breaks it
			}
			Bounces++;
			if (Math.Abs(Projectile.velocity.X - oldVelocity.X) > 0.01f) {
				Projectile.velocity.X = -oldVelocity.X * BounceKeep;
			}
			if (Math.Abs(Projectile.velocity.Y - oldVelocity.Y) > 0.01f) {
				Projectile.velocity.Y = -oldVelocity.Y * BounceKeep;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item52 with { Pitch = 0.3f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);
				for (int i = 0; i < 4; i++) {
					SafeSpawn.TryNewDust(Projectile.BottomLeft - new Vector2(0f, 4f), Projectile.width, 6, i % 2 == 0 ? DustID.Torch : DustID.Copper, out _, 0f, -1.5f);
				}
			}
			return false;
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.2f, Volume = 0.6f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 2 == 0 ? DustID.Copper : DustID.Iron, out _,
					Main.rand.NextFloat(-2.5f, 2.5f), -Main.rand.NextFloat(1f, 3.5f));
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameSize, FrameSize);
			Vector2 centre = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Vector2 position = new((int)(centre.X - FrameSize * 0.5f), (int)(centre.Y - FrameSize * 0.5f));
			Main.EntitySpriteDraw(texture, position, source, Color.Lerp(lightColor, Color.White, 0.2f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
