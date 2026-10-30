using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.MechArmy.MechArmyRigData;

namespace Cogpunk.Content.MechArmy.Projectiles
{
	/// <summary>
	/// The Boombot's detonation: a hostile blast of <see cref="Radius"/> px that hurts every player it reaches in its first
	/// <see cref="HurtTicks"/> ticks (a circle, not the square sprite: <see cref="Colliding"/>), and throws them away from
	/// its centre. Then <see cref="R.BlastFrames"/> frames of fireball and smoke, fading in code (D4 rule 9: no
	/// semi-transparent pixels in the sheet). Hostile effects in the ember and steam ramps (D3).
	/// <para>D2: spawned by the server and synced like any hostile projectile; each client checks its own player (vanilla
	/// <c>Projectile.Damage</c>). Effects (sound, dust, a small shake) run once per client on its first tick. D1: no
	/// allocation; <see cref="Projectile.timeLeft"/> is <see cref="LifeTicks"/>.</para>
	/// </summary>
	public class BoombotBlast : CogpunkProjectile
	{
		public const float Radius = 48f;
		public const int HurtTicks = 3;
		public const int TicksPerFrame = 4;
		public const int LifeTicks = R.BlastFrames * TicksPerFrame;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.BlastFrames;
		}

		public override void SetDefaults() {
			Projectile.width = Projectile.height = (int)(Radius * 2f);
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = LifeTicks;
		}

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (Projectile.localAI[0] == 0f) {
				Projectile.localAI[0] = 1f;
				if (!Main.dedServ) {
					Effects();
				}
			}
			int age = LifeTicks - Projectile.timeLeft;
			Projectile.frame = Math.Clamp(age / TicksPerFrame, 0, R.BlastFrames - 1);
			if (!Main.dedServ && age < 12) {
				Lighting.AddLight(Projectile.Center, 1.2f * (1f - age / 12f), 0.55f * (1f - age / 12f), 0.15f);
			}
		}

		public override bool CanHitPlayer(Player target) => LifeTicks - Projectile.timeLeft < HurtTicks;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 c = Projectile.Center;
			float nx = MathHelper.Clamp(c.X, targetHitbox.Left, targetHitbox.Right);
			float ny = MathHelper.Clamp(c.Y, targetHitbox.Top, targetHitbox.Bottom);
			return Vector2.DistanceSquared(c, new Vector2(nx, ny)) <= Radius * Radius;
		}

		/// <summary>Thrown away from the centre, harder than a normal hit: vanilla hurts players with its default contact
		/// knockback (4.5; decompiled <c>Projectile.Damage</c> never passes the projectile's own), so the
		/// <see cref="NPCs.Boombot.BlastKnockback"/> is applied here.</summary>
		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			modifiers.HitDirectionOverride = target.Center.X >= Projectile.Center.X ? 1 : -1;
			modifiers.Knockback *= NPCs.Boombot.BlastKnockback / NPCs.Jaeger.VanillaKnockback;
		}

		private void Effects() {
			SoundEngine.PlaySound(SoundID.Item14 with { Volume = 0.9f }, Projectile.Center);
			for (int i = 0; i < 18; i++) {
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(16f), 32, 32, i % 3 == 0 ? DustID.Smoke : DustID.Torch, out Dust d,
					0f, 0f, 0, default, i % 3 == 0 ? 1.6f : 1.3f)) {
					d.velocity = Main.rand.NextVector2Circular(6f, 6f);
					d.noGravity = i % 3 != 0;
				}
			}
			Gores();
			if ((CogpunkClientConfig.Instance?.ScreenShake ?? true) && Vector2.DistanceSquared(Main.LocalPlayer.Center, Projectile.Center) < 800f * 800f) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(Projectile.Center, Vector2.UnitY, 3f, 8f, 10, 1000f, "Cogpunk:BoombotBlast"));
			}
		}

		private void Gores() {
			CogpunkMod mod = ModContent.GetInstance<CogpunkMod>();
			if (mod.TryFind("Boombot_GoreShell", out ModGore shell)) {
				SafeSpawn.TryNewGore(Projectile.GetSource_FromThis(), Projectile.Center, Main.rand.NextVector2Circular(5f, 5f) - Vector2.UnitY * 2f, shell.Type, out _);
			}
			if (mod.TryFind("Boombot_GoreLamp", out ModGore lamp)) {
				SafeSpawn.TryNewGore(Projectile.GetSource_FromThis(), Projectile.Center, Main.rand.NextVector2Circular(4f, 4f) - Vector2.UnitY * 3f, lamp.Type, out _);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frameHeight = texture.Height / R.BlastFrames;
			Rectangle source = new(0, Projectile.frame * frameHeight, texture.Width, frameHeight - 2);
			int age = LifeTicks - Projectile.timeLeft;
			float fade = age < LifeTicks - 8 ? 1f : Math.Max(0f, (LifeTicks - age) / 8f);
			Vector2 at = Projectile.Center - Main.screenPosition;
			at = new Vector2(MathF.Round(at.X / 2f) * 2f, MathF.Round(at.Y / 2f) * 2f);
			Main.EntitySpriteDraw(texture, at, source, Color.White * fade, 0f, new Vector2(texture.Width / 2f, (frameHeight - 2) / 2f), 1f, SpriteEffects.None);
			return false;
		}
	}
}
