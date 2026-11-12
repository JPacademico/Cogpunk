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
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Projectiles
{
	/// <summary>
	/// The <see cref="Items.JadeStaff"/>'s bolt (user-set 2026-11-09: "a wave motion jade magic projectile, like the diamond
	/// staff projectile but jade green"): a jade spark that weaves either side of its course (<see cref="WaveAmplitude"/> px,
	/// one wave every <see cref="WavePeriod"/> ticks) trailing green gem dust, as vanilla's gem bolts trail theirs (decompiled
	/// 1.4.4 <c>Projectile.SetDefaults</c> 124, the Emerald Bolt: 10x10, magic, through one enemy into a second). It lays the
	/// jade curse on every enemy it hits (<see cref="JadeCurseNPC"/>), and breaks on blocks.
	/// <para><b>Homing</b> (user, 2026-11-10: "jade staff projectiles should home in petrified enemies"): with an enemy turned
	/// to jade (<see cref="JadeCurseNPC.Petrified"/>) within <see cref="HomingRange"/>, the course turns towards the nearest
	/// one, at most <see cref="HomingTurn"/> a tick, still weaving; it hits each enemy once (local immunity), so it never
	/// circles back into the one it just struck. Unfrozen enemies are not chased (my call: the curse's stacks still come
	/// from aiming).</para>
	/// <para>D2: the course (the line it weaves about) is in <c>ai[0]</c>, <c>ai[1]</c>, and its age in <c>ai[2]</c>, all
	/// synced; every side weaves and homes it alike from them (the centreline point is where it is less this tick's
	/// sideways offset, so a client that joins mid-flight gets the same line), and while it homes its owner resyncs it every
	/// <see cref="HomingSyncTicks"/> ticks. The curse is laid by the owner's hit through the server
	/// (<see cref="JadeCurseNPC.Hit"/>). D0: a finite life, NaN guarded. D1: one pass over the NPCs a tick, no allocation.
	/// D4: a small rotation-free spark drawn at full brightness (it is magic light).</para>
	/// </summary>
	public class JadeBolt : CogpunkProjectile
	{
		public const float WaveAmplitude = 10f;
		public const int WavePeriod = 20, Lifetime = 300;
		public const float HomingRange = 25f * 16f;            // my call: 25 tiles
		public const float HomingTurn = 0.12f;                 // my call: about 7 degrees a tick
		public const int HomingSyncTicks = 10;

		private ref float Age => ref Projectile.ai[2];

		public override void SetDefaults() {
			Projectile.width = 10;
			Projectile.height = 10;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = 2;                              // the Emerald Bolt's
			Projectile.timeLeft = Lifetime;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;               // each enemy once a bolt (the homing never doubles back)
			Projectile.localNPCHitCooldown = -1;
		}

		/// <summary>The weave's sideways offset at <paramref name="age"/> ticks.</summary>
		public static float Offset(float age) => WaveAmplitude * MathF.Sin(MathHelper.TwoPi * age / WavePeriod);

		private static Vector2 Side(Vector2 course) => new Vector2(-course.Y, course.X).SafeNormalize(Vector2.UnitY);

		/// <summary>The nearest enemy turned to jade within <see cref="HomingRange"/> of <paramref name="from"/> that this bolt
		/// hasn't struck yet, or null.</summary>
		private NPC FindPetrified(Vector2 from) {
			NPC best = null;
			float bestDistance = HomingRange * HomingRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy(Projectile) || Projectile.localNPCImmunity[npc.whoAmI] != 0 || !JadeCurseNPC.Petrified(npc)) {
					continue;
				}
				float d = Vector2.DistanceSquared(from, npc.Center);
				if (d < bestDistance) {
					bestDistance = d;
					best = npc;
				}
			}
			return best;
		}

		public override void AI() {
			Vector2 course = new(Projectile.ai[0], Projectile.ai[1]);
			if (!MathSafety.IsFinite(course) || course.LengthSquared() < 0.01f) {
				course = Projectile.velocity.LengthSquared() > 0.01f ? Projectile.velocity : Vector2.UnitX * 8f;
			}
			// the centreline point it weaves about: where it is, less this tick's sideways offset
			Vector2 line = Projectile.Center - Side(course) * Offset(Age);
			NPC mark = FindPetrified(line);
			if (mark != null) {                                    // turn the course towards it (user, 2026-11-10)
				float speed = course.Length();
				float now = course.ToRotation();
				float turn = MathHelper.Clamp(MathHelper.WrapAngle((mark.Center - line).ToRotation() - now), -HomingTurn, HomingTurn);
				Vector2 turned = (now + turn).ToRotationVector2() * speed;
				if (MathSafety.IsFinite(turned)) {
					course = turned;
					Projectile.ai[0] = course.X;
					Projectile.ai[1] = course.Y;
					if (Projectile.owner == Main.myPlayer && (int)Age % HomingSyncTicks == 0) {
						Projectile.netUpdate = true;
					}
				}
			}
			// where the weave puts it next tick; vanilla moves it there by this velocity (and stops it on a block)
			Vector2 next = line + course + Side(course) * Offset(Age + 1f);
			Projectile.velocity = next - Projectile.Center;
			MathSafety.Sanitize(ref Projectile.velocity);
			Age++;
			Lighting.AddLight(Projectile.Center, 0.12f, 0.5f, 0.32f);
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity *= 0.2f;
					d.scale = 1.1f;
				}
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			JadeCurseNPC.Hit(target);
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			return true;
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item10 with { Volume = 0.6f, Pitch = 0.3f }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(2.5f, 2.5f);
				}
			}
		}

		public override Color? GetAlpha(Color lightColor) => Color.White;

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Vector2 at = Projectile.Center - Main.screenPosition - new Vector2(texture.Width / 2, texture.Height / 2);
			Main.EntitySpriteDraw(texture, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), null, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
