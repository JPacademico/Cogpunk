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
using R = Cogpunk.Content.OldBrassTown.NPCs.DinamitromRigData;

namespace Cogpunk.Content.OldBrassTown.Projectiles
{
	/// <summary>
	/// The Dinamitrom's detonation: a hostile blast of <see cref="Radius"/> px (4 tiles) that hurts every player it reaches in
	/// its first <see cref="HurtTicks"/> ticks (a circle, <see cref="Colliding"/>) and throws them away from its centre, then
	/// <see cref="R.BlastFrames"/> frames of fireball, splinters of stave and hoop, and smoke, faded in code (D4 rule 9).
	/// Hostile effects in the Ember and Steam ramps (D3). Built like the Boombot's blast.
	/// <para>D2: spawned by the server and synced like any hostile projectile; each client checks its own player (vanilla
	/// <c>Projectile.Damage</c>); the effects run once per client on its first tick. D1: no allocation; finite
	/// <see cref="LifeTicks"/>. It never touches tiles.</para>
	/// </summary>
	public class DinamitromBlast : CogpunkProjectile
	{
		public const float Radius = 64f;
		public const int HurtTicks = 3;
		public const int TicksPerFrame = 4;
		public const int LifeTicks = R.BlastFrames * TicksPerFrame;
		public const float VanillaKnockback = 4.5f;        // hostile hits on players push 4.5 whatever the projectile's own (SKILL 3.9)
		private static readonly string[] GoreNames = { "Dinamitrom_GoreStave", "Dinamitrom_GoreHoop", "Dinamitrom_GoreStick" };

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
			if (!Main.dedServ && age < 14) {
				Lighting.AddLight(Projectile.Center, 1.4f * (1f - age / 14f), 0.65f * (1f - age / 14f), 0.15f);
			}
		}

		public override bool CanHitPlayer(Player target) => LifeTicks - Projectile.timeLeft < HurtTicks;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 c = Projectile.Center;
			float nx = MathHelper.Clamp(c.X, targetHitbox.Left, targetHitbox.Right);
			float ny = MathHelper.Clamp(c.Y, targetHitbox.Top, targetHitbox.Bottom);
			return Vector2.DistanceSquared(c, new Vector2(nx, ny)) <= Radius * Radius;
		}

		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			modifiers.HitDirectionOverride = target.Center.X >= Projectile.Center.X ? 1 : -1;
			modifiers.Knockback *= NPCs.Dinamitrom.BlastKnockback / VanillaKnockback;
		}

		private void Effects() {
			SoundEngine.PlaySound(SoundID.Item14 with { Volume = 1f, Pitch = -0.2f }, Projectile.Center);
			SoundEngine.PlaySound(SoundID.DD2_ExplosiveTrapExplode with { Volume = 0.6f }, Projectile.Center);
			for (int i = 0; i < 24; i++) {
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(20f), 40, 40, i % 3 == 0 ? DustID.Smoke : (i % 3 == 1 ? DustID.Torch : DustID.WoodFurniture),
					out Dust d, 0f, 0f, 0, default, i % 3 == 0 ? 1.8f : 1.4f)) {
					d.velocity = Main.rand.NextVector2Circular(8f, 8f);
					d.noGravity = i % 3 == 1;
				}
			}
			CogpunkMod mod = ModContent.GetInstance<CogpunkMod>();
			foreach (string name in GoreNames) {
				if (mod.TryFind(name, out ModGore gore)) {
					SafeSpawn.TryNewGore(Projectile.GetSource_FromThis(), Projectile.Center, Main.rand.NextVector2Circular(6f, 6f) - Vector2.UnitY * 3f, gore.Type, out _);
				}
			}
			if ((CogpunkClientConfig.Instance?.ScreenShake ?? true) && Vector2.DistanceSquared(Main.LocalPlayer.Center, Projectile.Center) < 900f * 900f) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(Projectile.Center, Vector2.UnitY, 5f, 8f, 14, 1100f, "Cogpunk:DinamitromBlast"));
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frameHeight = R.BlastSize + 2;
			Rectangle source = new(0, Projectile.frame * frameHeight, R.BlastSize, R.BlastSize);
			int age = LifeTicks - Projectile.timeLeft;
			float fade = age < LifeTicks - 8 ? 1f : Math.Max(0f, (LifeTicks - age) / 8f);
			Vector2 at = Projectile.Center - Main.screenPosition;
			at = new Vector2(MathF.Round(at.X / 2f) * 2f, MathF.Round(at.Y / 2f) * 2f);
			Main.EntitySpriteDraw(texture, at, source, Color.White * fade, 0f, new Vector2(R.BlastSize / 2f), 1f, SpriteEffects.None);
			return false;
		}
	}
}
