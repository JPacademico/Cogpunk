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
	/// A bone Tar Tyrant's back flings out on its own every 3.5 s (user-set 2026-10-29, in place of the femur throw: "bones
	/// should automatically fly out of his upper back every 2.5 seconds bouncing once and causing small damage if it
	/// hits"; 3.5 s since the user's nerf of 2026-10-30): a broken rib or a vertebra (<c>ai[1]</c>), lobbed high under
	/// <see cref="Gravity"/> at the target's feet
	/// (<see cref="LobVelocity"/>), spinning. The first wall or floor it meets bounces it (<see cref="BounceDamping"/>); the
	/// next one shatters it. <see cref="TarTyrant.BackBoneDamage"/> in Expert and the Tar Plague.
	/// <para>D2: spawned by the server; the arc is deterministic from the synced velocity and every side bounces it on the
	/// same tiles (<c>ai[0]</c> = bounces so far, as vanilla's bouncing projectiles keep it). D0: finite lifetime; the
	/// velocity is sanitised every tick. Eight pre-rendered turns per bone (D4: never rotated at runtime).</para>
	/// </summary>
	public class TarTyrantBackBone : CogpunkProjectile
	{
		public const float Gravity = 0.3f;
		public const float MaxFallSpeed = 12f;
		public const int Lifetime = 240;
		public const int MaxBounces = 1;
		public const float BounceDamping = 0.5f;           // a floor sends it back up at half the speed...
		public const float BounceFriction = 0.7f;          // ...and takes 30% of its run
		public const int HitboxSize = 18;
		public const int SpinFrameTicks = 3;

		private ref float Bounces => ref Projectile.ai[0];
		private int Kind => Math.Clamp((int)Projectile.ai[1], 0, R.BoneKinds - 1);
		private int Age => Lifetime - Projectile.timeLeft;

		/// <summary>The launch velocity that lands on <paramref name="to"/> after <paramref name="ticks"/> under
		/// <see cref="Gravity"/> (x straight, y solved for the flight time), always upwards first. Always finite (D0).</summary>
		public static Vector2 LobVelocity(Vector2 from, Vector2 to, float ticks) {
			ticks = Math.Max(10f, ticks);
			float vx = (to.X - from.X) / ticks;
			float vy = (to.Y - from.Y - 0.5f * Gravity * ticks * ticks) / ticks;
			Vector2 v = new(MathHelper.Clamp(vx, -12f, 12f), MathHelper.Clamp(vy, -14f, -2f));
			return MathSafety.IsFinite(v) ? v : new Vector2(0f, -8f);
		}

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.BoneFrameCount;
		}

		public override void SetDefaults() {
			Projectile.width = HitboxSize;
			Projectile.height = HitboxSize;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);
			MathSafety.Sanitize(ref Projectile.velocity);
			int k = Age / SpinFrameTicks % R.BoneTurns;
			Projectile.frame = Kind * R.BoneTurns + (Projectile.velocity.X >= 0f ? k : (R.BoneTurns - k) % R.BoneTurns);   // spinning the way it flies
			if (!Main.dedServ && Main.rand.NextBool(6) && CogpunkClientConfig.RollEffect()) {
				SafeSpawn.TryNewDust(Projectile.Center - new Vector2(6f), 12, 12, ModContent.DustType<TarSplash>(), out _);   // tar dripping off it
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Bounces >= MaxBounces) {
				return true;                                // the second contact: it shatters
			}
			Bounces++;
			if (Projectile.velocity.X != oldVelocity.X) {
				Projectile.velocity.X = -oldVelocity.X * BounceFriction;
			}
			if (Projectile.velocity.Y != oldVelocity.Y) {
				Projectile.velocity.Y = -oldVelocity.Y * BounceDamping;
				Projectile.velocity.X *= BounceFriction;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.NPCHit2 with { Pitch = 0.2f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);   // a bony clack
			}
			return false;
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = 0.3f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);   // it breaks
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < 6; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Bone, out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), -Main.rand.NextFloat(1f, 3f));
				}
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(ModContent.BuffType<TarPlague>(), TarTyrant.PlagueTicks);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * (R.BoneCell + 2), R.BoneCell, R.BoneCell);
			if (source.Bottom > texture.Height) {
				return false;
			}
			Vector2 centre = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Vector2 position = new((int)(centre.X - R.BoneCell * 0.5f), (int)(centre.Y - R.BoneCell * 0.5f));
			Main.EntitySpriteDraw(texture, position, source, lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
