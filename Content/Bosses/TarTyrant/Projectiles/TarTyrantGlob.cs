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

namespace Cogpunk.Content.Bosses.TarTyrant.Projectiles
{
	/// <summary>
	/// A glob of tar from Tar Tyrant's spit (a fan of three, user-set 2026-10-29): a lob under <see cref="Gravity"/> that
	/// lands on its spot (<see cref="LobVelocity"/>), splats on the first tile and leaves 3 tiles of tar there for 3 s
	/// (<see cref="TarTyrantPuddle"/>). <see cref="TarTyrant.GlobDamage"/> in Expert, and the Tar Plague for
	/// <see cref="TarTyrant.PlagueTicks"/> on a hit.
	/// <para>D2: spawned by the server; the puddle is spawned where it lands by the server too (synced). D0: the puddle
	/// goes through SafeSpawn, and only if fewer than <see cref="TarTyrantPuddle.MaxAlive"/> are out.</para>
	/// </summary>
	public class TarTyrantGlob : CogpunkProjectile
	{
		public const float Gravity = 0.3f;
		public const float MaxFall = 14f;
		public const int Frames = 3;
		public const int TicksPerFrame = 5;
		private const int FrameSize = 28, FrameStride = 30;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 20;
			Projectile.height = 20;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 300;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		/// <summary>The launch velocity that lands on <paramref name="to"/> after about <paramref name="ticks"/> under
		/// <see cref="Gravity"/> (x straight, y solved for the flight time). Always finite (D0).</summary>
		public static Vector2 LobVelocity(Vector2 from, Vector2 to, float ticks) {
			ticks = Math.Max(10f, ticks);
			float vx = (to.X - from.X) / ticks;
			float vy = (to.Y - from.Y - 0.5f * Gravity * ticks * ticks) / ticks;
			Vector2 v = new(MathHelper.Clamp(vx, -14f, 14f), MathHelper.Clamp(vy, -16f, 8f));
			return MathSafety.IsFinite(v) ? v : new Vector2(0f, -6f);
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFall);
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (!Main.dedServ && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out _);
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(ModContent.BuffType<TarPlague>(), TarTyrant.PlagueTicks);
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Main.netMode != NetmodeID.MultiplayerClient && oldVelocity.Y > 0f && TarTyrantPuddle.CanSpawnMore()) {
				Vector2 at = new(Projectile.Center.X, Projectile.Bottom.Y);
				SafeSpawn.TryNewProjectile(Projectile.GetSource_FromThis(), at - new Vector2(0f, TarTyrantPuddle.HitboxHeight * 0.5f), Vector2.Zero,
					ModContent.ProjectileType<TarTyrantPuddle>(), 0, 0f, out _);
			}
			return true;
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCDeath13 with { Pitch = 0.2f, Volume = 0.5f, MaxInstances = 5 }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust d);
				if (d != null) {
					d.velocity = new Vector2(Main.rand.NextFloat(-2.5f, 2.5f), -Main.rand.NextFloat(1f, 3f));
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameSize, FrameSize);
			Vector2 centre = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Vector2 position = new((int)(centre.X - FrameSize * 0.5f), (int)(centre.Y - FrameSize * 0.5f));
			SpriteEffects effects = Projectile.velocity.X > 0f ? SpriteEffects.FlipHorizontally : SpriteEffects.None;   // the strand trails behind
			Main.EntitySpriteDraw(texture, position, source, lightColor, 0f, Vector2.Zero, 1f, effects);
			return false;
		}
	}
}
