using System;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Armor
{
	/// <summary>
	/// Scrap armor effects that need per-player state: the leggings' softer landings and the set bonus cog volley.
	/// <para>Cog volley: while the player moves, a timer fills; every <see cref="CogInterval"/> ticks of movement a
	/// <see cref="ScrapCogProjectile"/> is lobbed. With an enemy in line of sight within <see cref="CogRange"/> it is aimed
	/// at that enemy: the launch angle is the low arc that lands on it under the cog's gravity (<see cref="AimLob"/>).
	/// With none near it is thrown from the player's back, up and behind them. Gravity pulls it into an arc and it bounces
	/// along the ground. Runs on the owning client only; the projectile syncs itself (D2).</para>
	/// </summary>
	public sealed class ScrapArmorPlayer : ModPlayer
	{
		public const int CogInterval = 45;                  // 0.75 s
		public const int CogDamage = 40;                  // 70 -> 40 (user nerf, 2026-10-28)
		public const float CogKnockback = 2f;
		public const float CogSpeed = 10f;
		public const float CogRange = 25 * 16f;             // the arc reaches about 21 tiles on flat ground, bounces carry it on
		public const float CogLaunchUp = 0.6f;              // throw with no target: (0.8, -0.6) x CogSpeed, about 37 degrees up
		public const float CogLaunchBack = 0.8f;
		private const float BackOffset = 10f;               // the idle throw leaves from the player's back
		private const float MinAimDistance = 8f;            // closer than this horizontally, aim as if it were this far
		private const float Sin45 = 0.70710677f;
		public const float FallDamageReduction = 0.5f;
		private const float MovingSpeedSquared = 0.5f * 0.5f;
		private static readonly Vector2 ChestOffset = new(0f, -4f);
		private const int FallDamageSource = 0;              // PlayerDeathReason.ByOther(0) = falling (decompiled Player.Update)

		public bool CogVolley;
		public bool SoftLanding;
		private int cogTimer;

		public override void ResetEffects() {
			CogVolley = false;
			SoftLanding = false;
		}

		public override void ModifyHurt(ref Player.HurtModifiers modifiers) {
			if (SoftLanding && modifiers.DamageSource.SourceOtherIndex == FallDamageSource) {
				modifiers.FinalDamage *= 1f - FallDamageReduction;
			}
		}

		public override void PostUpdate() {
			if (!CogVolley || Player.whoAmI != Main.myPlayer || Player.dead || Player.CCed) {
				return;
			}
			if (Player.velocity.LengthSquared() < MovingSpeedSquared) {
				return;                                     // the timer only fills while moving
			}
			if (cogTimer < CogInterval) {
				cogTimer++;
				return;
			}
			Vector2 chest = Player.MountedCenter + ChestOffset;
			NPC target = FindTarget(chest);
			Vector2 spawn = chest;
			Vector2 velocity;
			if (target != null) {
				velocity = AimLob(target.Center - chest);
			}
			else {
				spawn.X -= Player.direction * BackOffset;
				velocity = new Vector2(-CogLaunchBack * Player.direction, -CogLaunchUp) * CogSpeed;
			}
			int damage = (int)Player.GetTotalDamage(DamageClass.Generic).ApplyTo(CogDamage);
			if (SafeSpawn.TryNewProjectile(Player.GetSource_Misc("SetBonus_ScrapArmor"), spawn, velocity,
					ModContent.ProjectileType<ScrapCogProjectile>(), damage, CogKnockback, out _, Player.whoAmI)) {
				cogTimer = 0;                               // a refused spawn (array nearly full) retries next tick
			}
		}

		/// <summary>
		/// Launch velocity of length <see cref="CogSpeed"/> whose arc under <see cref="ScrapCogProjectile.Gravity"/> passes
		/// through <paramref name="offset"/>: the low solution of tan(a) = (v² - sqrt(v⁴ - g(g·x² + 2·y·v²))) / (g·x), with y
		/// measured upward. Out of reach (negative root), the 45-degree throw goes as far as it can toward the target.
		/// Pure math, no allocation; the result is always finite (D0).
		/// </summary>
		public static Vector2 AimLob(Vector2 offset) {
			const float g = ScrapCogProjectile.Gravity;
			const float v = CogSpeed;
			const float v2 = v * v;
			float side = offset.X >= 0f ? 1f : -1f;
			float x = Math.Max(Math.Abs(offset.X), MinAimDistance);
			float up = -offset.Y;
			float root = v2 * v2 - g * (g * x * x + 2f * up * v2);
			if (root < 0f) {
				return new Vector2(side * v * Sin45, -v * Sin45);
			}
			float angle = (float)Math.Atan((v2 - Math.Sqrt(root)) / (g * x));
			return new Vector2(side * v * (float)Math.Cos(angle), -v * (float)Math.Sin(angle));
		}

		// Nearest enemy the cog can reach in a straight line of sight. Allocation-free; the line check only runs for
		// enemies closer than the best one so far.
		private static NPC FindTarget(Vector2 from) {
			NPC best = null;
			float bestDistance = CogRange * CogRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy()) {
					continue;
				}
				float distance = Vector2.DistanceSquared(from, npc.Center);
				if (distance < bestDistance && Collision.CanHitLine(from, 1, 1, npc.position, npc.width, npc.height)) {
					best = npc;
					bestDistance = distance;
				}
			}
			return best;
		}
	}
}
