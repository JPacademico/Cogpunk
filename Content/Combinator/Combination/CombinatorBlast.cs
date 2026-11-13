using System;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>
	/// The area-burst trait's blast (<see cref="TraitKind.AreaBurst"/>, from bases whose own shots burst: the Scrap Launcher,
	/// the Tar Bone Staff): an invisible owner projectile, a circle of <c>ai[0]</c> px that hurts every enemy in it once in its
	/// first update, except the one the hit already struck (<c>ai[1]</c>), for the share of that hit's damage it was spawned
	/// with (already the full hit's numbers: no class bonus or crit on top). A steam and brass puff shows it.
	/// <para>D0: no loop: it is spawned from <c>EntitySource_Misc</c>, so <see cref="CombinedProjectile"/> gives it no traits,
	/// and a player bursts at most once every <see cref="CooldownTicks"/> ticks; through <see cref="SafeSpawn"/> (refused when
	/// the projectile array is near full). D2: spawned on the owner's client, synced by vanilla like any player projectile.</para>
	/// </summary>
	public class CombinatorBlast : CogpunkProjectile
	{
		public const int CooldownTicks = 6;
		public const float MaxRadius = 8f * 16f;
		private static readonly uint[] lastBurst = new uint[Main.maxPlayers + 1];

		public override string Texture => TextureFallback.Placeholder;      // never drawn

		public override void SetDefaults() {
			Projectile.width = Projectile.height = 16;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = 3;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
			Projectile.DamageType = DamageClass.Default;
			Projectile.hide = true;
		}

		/// <summary>The owner's client: a burst at <paramref name="at"/> of <paramref name="radius"/> px for
		/// <paramref name="damage"/>, sparing <paramref name="spare"/> (the NPC the hit struck).</summary>
		public static void Burst(Player owner, Vector2 at, float radius, int damage, int spare, DamageClass damageClass) {
			if (owner == null || owner.whoAmI != Main.myPlayer || damage <= 0 || !MathSafety.IsFinite(at)) {
				return;
			}
			uint now = Main.GameUpdateCount;
			if (now - lastBurst[owner.whoAmI] < CooldownTicks) {
				return;
			}
			lastBurst[owner.whoAmI] = now;
			radius = Math.Clamp(radius, 16f, MaxRadius);
			SafeSpawn.TryNewProjectile(owner.GetSource_Misc("CombinatorBurst"), at, Vector2.Zero, ModContent.ProjectileType<CombinatorBlast>(),
				damage, 0f, out _, owner.whoAmI, radius, spare);
		}

		public override bool? CanHitNPC(NPC target) {
			if (target.whoAmI == (int)Projectile.ai[1]) {
				return false;
			}
			return null;
		}

		public override bool? CanDamage() => Projectile.timeLeft >= 2;      // the first update only

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			float r = Math.Clamp(Projectile.ai[0], 16f, MaxRadius);
			Vector2 c = Projectile.Center;
			float nx = Math.Clamp(c.X, targetHitbox.Left, targetHitbox.Right), ny = Math.Clamp(c.Y, targetHitbox.Top, targetHitbox.Bottom);
			float dx = c.X - nx, dy = c.Y - ny;
			return dx * dx + dy * dy <= r * r;
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			modifiers.DisableCrit();
			modifiers.Knockback *= 0f;
		}

		public override void AI() {
			if (Projectile.localAI[0] != 0f || Main.dedServ) {
				return;
			}
			Projectile.localAI[0] = 1f;
			SoundEngine.PlaySound(SoundID.Item14 with { Volume = 0.45f, Pitch = 0.3f }, Projectile.Center);
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			float r = Math.Clamp(Projectile.ai[0], 16f, MaxRadius);
			for (int i = 0; i < 14; i++) {
				Vector2 dir = Main.rand.NextVector2CircularEdge(1f, 1f);
				if (SafeSpawn.TryNewDust(Projectile.Center + dir * r * 0.3f, 0, 0, i % 2 == 0 ? DustID.Smoke : DustID.Torch, out Dust d)) {
					d.velocity = dir * r / 16f;
					d.noGravity = true;
					d.scale = i % 2 == 0 ? 1.3f : 1.1f;
				}
			}
		}
	}
}
