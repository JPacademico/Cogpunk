using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Armor
{
	/// <summary>
	/// The Tyrant armor's set-bonus claw (user-set 2026-10-29, restored 2026-11-06: "the set bonus should maintain the tar
	/// claw effect"). Every <see cref="ClawInterval"/> ticks (4 s) a tar claw like Tar Tyrant's own (<see cref="TyrantClaw"/>,
	/// 5 tiles wide) erupts from the ground under the closest enemy within <see cref="ClawRange"/> that the wearer can see and
	/// that stands within <see cref="GroundReach"/> tiles of the ground (the claw comes out of it, so a bird high overhead is
	/// passed over for the next enemy). It deals <see cref="ClawDamage"/> magic damage (the user's "high damage", my number)
	/// to every enemy in it, scaled by the wearer's magic damage and rolling their magic crit. With no such enemy it waits,
	/// charged, and erupts as soon as one comes; taking the set off empties the charge.
	/// <para>D2: runs on the wearer's client; the claw is the wearer's projectile and syncs itself. D1: one pass over the
	/// active NPCs only while charged, bounded ground checks (<see cref="TarTyrant.FindSurface(float, float, int, int, out bool)"/>),
	/// no allocation.</para>
	/// </summary>
	public sealed class TyrantArmorPlayer : ModPlayer
	{
		public const int ClawInterval = 240;            // 4 s, user-set (2026-10-29)
		public const int ClawDamage = 100;              // magic, my call (2026-10-29)
		public const float ClawKnockback = 7f;
		public const float ClawRange = 40f * 16f;
		public const int GroundReach = 6;               // tiles between an enemy's feet and the ground under it, at most

		public bool ClawSet;
		private int clawTimer;

		public override void ResetEffects() {
			ClawSet = false;
		}

		public override void PostUpdate() {
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			if (!ClawSet || Player.dead) {
				clawTimer = 0;
				return;
			}
			if (clawTimer < ClawInterval) {
				clawTimer++;
				return;
			}
			if (Player.CCed || !FindTarget(out Vector2 ground)) {
				return;                                     // charged: it waits for an enemy
			}
			int damage = (int)Player.GetTotalDamage(DamageClass.Magic).ApplyTo(ClawDamage);
			float knockback = Player.GetTotalKnockback(DamageClass.Magic).ApplyTo(ClawKnockback);
			// a projectile parented to the player takes the player's crit for its class (decompiled Projectile.ApplyStatsFromSource)
			if (SafeSpawn.TryNewProjectile(Player.GetSource_FromThis("SetBonus_TyrantArmor"), ground - new Vector2(0f, TyrantClaw.HitboxHeight * 0.5f),
					Vector2.Zero, ModContent.ProjectileType<TyrantClaw>(), damage, knockback, out _, Player.whoAmI)) {
				clawTimer = 0;                              // a refused spawn (array nearly full) retries next tick
			}
		}

		/// <summary>The closest enemy in range and in sight with ground under it within <see cref="GroundReach"/> tiles; the
		/// ground point under its middle. The line and ground checks only run for enemies closer than the best so far.</summary>
		private bool FindTarget(out Vector2 ground) {
			ground = Vector2.Zero;
			float best = ClawRange * ClawRange;
			bool found = false;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy()) {
					continue;
				}
				float distance = Vector2.DistanceSquared(Player.Center, npc.Center);
				if (distance >= best || !Collision.CanHitLine(Player.Center, 1, 1, npc.position, npc.width, npc.height)) {
					continue;
				}
				float y = TarTyrant.FindSurface(npc.Center.X, npc.Bottom.Y, 1, GroundReach, out _);
				if (y == float.MaxValue) {
					continue;
				}
				best = distance;
				ground = new Vector2(npc.Center.X, y);
				found = true;
			}
			return found;
		}
	}
}
