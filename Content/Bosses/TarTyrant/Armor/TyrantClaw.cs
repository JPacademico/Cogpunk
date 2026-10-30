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

namespace Cogpunk.Content.Bosses.TarTyrant.Armor
{
	/// <summary>
	/// The Tyrant armor's set bonus (user-set 2026-10-29: "a tar claw (like the boss one) erupts from the gound underneath
	/// the closest enemy dealing high damage on the area"): Tar Tyrant's enrage claw cut down to a player's size, 5 tiles
	/// wide (<see cref="HitboxWidth"/>). The ground boils for <see cref="WarnTicks"/>, the claw bursts up, snaps shut and
	/// sinks; while it is out it hits every enemy in it once (magic, the damage <see cref="TyrantArmorPlayer"/> gave it, the
	/// wearer's magic crit). Spawned by <see cref="TyrantArmorPlayer"/>.
	/// <para>D2: the wearer's projectile (it syncs itself), standing still; everything follows from its age. The hitbox grows
	/// with the drawn claw, as the boss's does.</para>
	/// </summary>
	public class TyrantClaw : CogpunkProjectile
	{
		public const int HitboxWidth = 5 * 16, HitboxHeight = 6 * 16;
		public const int WarnFrameTicks = 4, RiseFrameTicks = 3, GrabFrameTicks = 4, SinkFrameTicks = 4;
		public const int WarnTicks = R.TyrantClawWarnFrames * WarnFrameTicks;
		public const int RiseTicks = R.TyrantClawRiseFrames * RiseFrameTicks;
		public const int GrabTicks = R.TyrantClawGrabFrames * GrabFrameTicks;
		public const int SinkTicks = R.TyrantClawSinkFrames * SinkFrameTicks;
		public const int Lifetime = WarnTicks + RiseTicks + GrabTicks + SinkTicks;
		public const int HurtStart = WarnTicks + RiseFrameTicks, HurtEnd = WarnTicks + RiseTicks + GrabTicks;
		private static readonly float[] RiseReach = { 0.25f, 0.62f, 1f, 1f };

		private int Age => Lifetime - Projectile.timeLeft;

		public override void SetDefaults() {
			Projectile.width = HitboxWidth;
			Projectile.height = HitboxHeight;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;            // every enemy in it once
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (Main.dedServ) {
				return;
			}
			int age = Age;
			Vector2 ground = Projectile.Bottom;
			if (age == 0) {
				SoundEngine.PlaySound(SoundID.Item85 with { Pitch = -0.6f, Volume = 0.6f, MaxInstances = 3 }, ground);    // the ground boils
			}
			if (age < WarnTicks && age % 2 == 0 && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.BottomLeft - new Vector2(0f, 6f), Projectile.width, 6, ModContent.DustType<TarSplash>(), out Dust d)) {
				d.velocity = new Vector2(Main.rand.NextFloat(-0.8f, 0.8f), -Main.rand.NextFloat(1.5f, 3f));
			}
			if (age == WarnTicks) {
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.3f, Volume = 0.6f, MaxInstances = 3 }, ground);
				SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = -0.2f, Volume = 0.6f, MaxInstances = 3 }, ground);
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 10; i++) {
						if (SafeSpawn.TryNewDust(Projectile.BottomLeft - new Vector2(0f, 8f), Projectile.width, 8, ModContent.DustType<TarSplash>(), out Dust s)) {
							s.velocity = new Vector2(Main.rand.NextFloat(-2.5f, 2.5f), -Main.rand.NextFloat(2.5f, 5f));
						}
					}
				}
			}
		}

		/// <summary>How much of the claw is out of the ground (0..1), from the drawn frames.</summary>
		private float Reach() {
			int e = Age - WarnTicks;
			if (e < 0) {
				return 0f;
			}
			if (e < RiseTicks) {
				return RiseReach[Math.Clamp(e / RiseFrameTicks, 0, RiseReach.Length - 1)];
			}
			return e < RiseTicks + GrabTicks ? 1f : 0f;
		}

		public override bool? CanDamage() => Age >= HurtStart && Age < HurtEnd ? null : false;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			int h = (int)(HitboxHeight * Reach());
			if (h <= 0) {
				return false;
			}
			return new Rectangle(projHitbox.X, projHitbox.Bottom - h, projHitbox.Width, h).Intersects(targetHitbox);
		}

		private int Frame() {
			int age = Age;
			if (age < WarnTicks) {
				return R.TyrantClawWarn0 + Math.Min(R.TyrantClawWarnFrames - 1, age / WarnFrameTicks);
			}
			int e = age - WarnTicks;
			if (e < RiseTicks) {
				return R.TyrantClawRise0 + Math.Min(R.TyrantClawRiseFrames - 1, e / RiseFrameTicks);
			}
			e -= RiseTicks;
			if (e < GrabTicks) {
				return R.TyrantClawGrab0 + Math.Min(R.TyrantClawGrabFrames - 1, e / GrabFrameTicks);
			}
			e -= GrabTicks;
			return R.TyrantClawSink0 + Math.Min(R.TyrantClawSinkFrames - 1, e / SinkFrameTicks);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Frame() * (R.TyrantClawHeight + 2), R.TyrantClawWidth, R.TyrantClawHeight);
			if (source.Bottom > texture.Height) {
				return false;
			}
			Vector2 bottom = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY + 2f);
			Vector2 position = new((int)(bottom.X - R.TyrantClawWidth * 0.5f), (int)(bottom.Y - R.TyrantClawHeight));
			Main.EntitySpriteDraw(texture, position, source, lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
