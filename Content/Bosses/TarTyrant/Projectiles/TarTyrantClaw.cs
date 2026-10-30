using System;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.TarTyrant.TarTyrantRigData;

namespace Cogpunk.Content.Bosses.TarTyrant.Projectiles
{
	/// <summary>
	/// Tar Tyrant's enrage attack (user-set 2026-10-29): while it is under the tar, a claw of tar and bone comes up out of
	/// the ground under its target, 8 tiles wide (<see cref="HitboxWidth"/>), every 2 s, five times. For
	/// <see cref="WarnTicks"/> (1.5 s, the user's time to dodge) a "!" hangs over the spot and the tar boils across the
	/// whole width; then the claw bursts up, snaps shut and sinks. <see cref="TarTyrant.ClawDamage"/> in Expert (125, the
	/// user's number; hostile hits are x2, so it lands as 126), and the Tar Plague.
	/// <para>D2: spawned by the server on the target's ground, standing still; everything follows from its age. The hitbox
	/// grows with the drawn claw.</para>
	/// </summary>
	public class TarTyrantClaw : CogpunkProjectile
	{
		public const int HitboxWidth = 8 * 16, HitboxHeight = 10 * 16;
		public const int WarnTicks = 90;
		public const int WarnFrameTicks = 6, RiseFrameTicks = 3, GrabFrameTicks = 4, SinkFrameTicks = 4;
		public const int RiseTicks = R.ClawRiseFrames * RiseFrameTicks;
		public const int GrabTicks = R.ClawGrabFrames * GrabFrameTicks;
		public const int SinkTicks = R.ClawSinkFrames * SinkFrameTicks;
		public const int Lifetime = WarnTicks + RiseTicks + GrabTicks + SinkTicks;
		public const int HurtStart = WarnTicks + RiseFrameTicks, HurtEnd = WarnTicks + RiseTicks + GrabTicks;
		public const float SignHeight = 7f * 16f;          // the "!" floats this far over the ground
		private static readonly float[] RiseReach = { 0.25f, 0.62f, 1f, 1f };

		private static Asset<Texture2D> signTexture;

		private int Age => Lifetime - Projectile.timeLeft;

		public override void SetStaticDefaults() {
			signTexture = DepthLayers.RequestOptional("Cogpunk/Content/Bosses/TarTyrant/Projectiles/TarTyrantClaw_Warning");
		}

		public override void Unload() {
			signTexture = null;
		}

		public override void SetDefaults() {
			Projectile.width = HitboxWidth;
			Projectile.height = HitboxHeight;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (Main.dedServ) {
				return;
			}
			int age = Age;
			Vector2 ground = Projectile.Bottom;
			if (age == 0) {
				SoundEngine.PlaySound(SoundID.Item85 with { Pitch = -0.9f, Volume = 0.8f }, ground);     // the tar starts to boil
				SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = -0.7f, Volume = 0.6f }, ground);     // the warning chime
			}
			if (age < WarnTicks) {
				Lighting.AddLight(ground - new Vector2(0f, SignHeight), 0.6f, 0.25f, 0.06f);
				int every = age > WarnTicks - 30 ? 2 : 5;                       // it boils harder as the claw comes
				if (age % every == 0 && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.BottomLeft - new Vector2(0f, 6f), Projectile.width, 6, ModContent.DustType<TarSplash>(), out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-0.8f, 0.8f), -Main.rand.NextFloat(1.5f, 3.5f));
				}
			}
			else if (age == WarnTicks) {
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f }, ground);
				SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = -0.5f }, ground);
				if (CogpunkClientConfig.Instance?.ScreenShake ?? true) {
					Main.instance.CameraModifiers.Add(new Terraria.Graphics.CameraModifiers.PunchCameraModifier(ground, Vector2.UnitY, 8f, 10f, 20, 2000f,
						"Cogpunk:TarTyrantClaw"));
				}
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 20; i++) {
						if (SafeSpawn.TryNewDust(Projectile.BottomLeft - new Vector2(0f, 10f), Projectile.width, 10, ModContent.DustType<TarSplash>(), out Dust d)) {
							d.velocity = new Vector2(Main.rand.NextFloat(-3f, 3f), -Main.rand.NextFloat(3f, 7f));
						}
					}
				}
			}
		}

		/// <summary>How much of the claw is out of the ground (0..1), from the drawn frames.</summary>
		private float Reach() {
			int age = Age;
			if (age < WarnTicks) {
				return 0f;
			}
			int e = age - WarnTicks;
			if (e < RiseTicks) {
				return RiseReach[Math.Clamp(e / RiseFrameTicks, 0, RiseReach.Length - 1)];
			}
			return e < RiseTicks + GrabTicks ? 1f : 0f;
		}

		public override bool CanHitPlayer(Player target) => Age >= HurtStart && Age < HurtEnd;

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

		/// <summary>Frame <paramref name="k"/> of the sheet: columns of <see cref="R.ClawRows"/> frames, 2 px apart.</summary>
		public static Rectangle Cell(int k) {
			return new Rectangle(k / R.ClawRows * (R.ClawWidth + 2), k % R.ClawRows * (R.ClawHeight + 2), R.ClawWidth, R.ClawHeight);
		}

		private int Frame() {
			int age = Age;
			if (age < WarnTicks) {
				return R.ClawWarn0 + Math.Min(R.ClawWarnFrames - 1, age * R.ClawWarnFrames / WarnTicks);   // the patch spreads
			}
			int e = age - WarnTicks;
			if (e < RiseTicks) {
				return R.ClawRise0 + Math.Min(R.ClawRiseFrames - 1, e / RiseFrameTicks);
			}
			e -= RiseTicks;
			if (e < GrabTicks) {
				return R.ClawGrab0 + Math.Min(R.ClawGrabFrames - 1, e / GrabFrameTicks);
			}
			e -= GrabTicks;
			return R.ClawSink0 + Math.Min(R.ClawSinkFrames - 1, e / SinkFrameTicks);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = Cell(Frame());
			if (source.Bottom > texture.Height || source.Right > texture.Width) {
				return false;
			}
			Vector2 bottom = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY + 2f);
			Vector2 position = new((int)(bottom.X - R.ClawWidth * 0.5f), (int)(bottom.Y - R.ClawHeight));
			Main.EntitySpriteDraw(texture, position, source, lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			int age = Age;
			if (age < WarnTicks && signTexture?.IsLoaded == true) {
				Texture2D sign = signTexture.Value;
				int k = age / 4 % R.WarnFrameCount;
				Rectangle cell = new(0, k * (R.WarnHeight + 2), R.WarnWidth, R.WarnHeight);
				float bob = MathF.Round(MathF.Sin(age * 0.2f) * 2f) * 2f;              // whole art pixels only
				Vector2 at = new((int)(bottom.X - R.WarnWidth * 0.5f), (int)(bottom.Y - SignHeight - R.WarnHeight + bob));
				if (cell.Bottom <= sign.Height) {
					Main.EntitySpriteDraw(sign, at, cell, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);   // full bright: it must read in the dark
				}
			}
			return false;
		}
	}
}
