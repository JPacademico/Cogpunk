using System;
using Terraria;

namespace Cogpunk.Core.Templates
{
	/// <summary>
	/// Cogpunk is balanced for <b>Expert</b> (user directive, 2026-10-27): every enemy and boss number we write is the
	/// value a player sees in Expert. Classic and Master follow vanilla's own ratios (decompiled
	/// <c>GameModeData</c>: enemy life and damage x1 / x2 / x3 in Classic / Expert / Master), so Classic gets half the
	/// Expert value and Master one and a half times it.
	/// <para><b>NPC life and contact damage</b>: vanilla multiplies the <c>SetDefaults</c> values by the mode
	/// (<c>NPC.ScaleStats_ApplyGameMode</c>), so <c>SetDefaults</c> holds <see cref="Base"/> (half the Expert value) and
	/// <c>ApplyDifficultyAndPlayerScaling</c>, which vanilla only calls in Expert and Master, right after that multiply,
	/// <see cref="Snap"/>s the result onto the exact Expert number. <see cref="CogpunkNPC.SetExpertStats"/> does both.
	/// Defense is not scaled by the mode (<c>EnemyDefenseMultiplier</c> is 1 everywhere): the Expert value is the value.</para>
	/// <para><b>Hostile projectiles</b> hit players for twice their damage field in every mode (decompiled
	/// <c>Projectile.Damage</c>: <c>Main.DamageVar(damage) * 2</c>), and nothing scales them by mode, so
	/// <see cref="HostileProjectile"/> passes a quarter / half / three quarters of the Expert number through vanilla's
	/// <c>GetAttackDamage_ForProjectiles_MultiLerp</c> (which also follows Journey's strength slider). Because of the x2,
	/// an odd number lands on the nearest even one (25 -> 26).</para>
	/// <para>Player-side numbers (weapon damage, armor, accessories, buffs) are not mode-scaled by vanilla, so they need
	/// nothing. Debuffs we put on players: modded buffs are not in <c>BuffID.Sets.LongerExpertDebuff</c>, so the written
	/// duration is the duration in every mode.</para>
	/// </summary>
	public static class ExpertStats
	{
		public const float ClassicFactor = 0.5f;           // Classic x1 / Expert x2
		public const float MasterFactor = 1.5f;            // Master x3 / Expert x2

		/// <summary>The <c>SetDefaults</c> value that vanilla's Expert x2 turns into <paramref name="expert"/> (Classic shows
		/// it as is). 0 stays 0 (no contact damage).</summary>
		public static int Base(int expert) {
			if (expert <= 0) {
				return 0;
			}
			return Math.Max(1, (int)Math.Round(expert * ClassicFactor, MidpointRounding.AwayFromZero));
		}

		/// <summary>In <c>ApplyDifficultyAndPlayerScaling</c>: <paramref name="scaled"/> is <see cref="Base"/> times the mode's
		/// multiplier by then; rescales it so Expert lands exactly on <paramref name="expert"/> (Master 1.5x it), keeping
		/// whatever multiplier vanilla applied (For the worthy adds one more).</summary>
		public static int Snap(int scaled, int expert) {
			int baseValue = Base(expert);
			if (baseValue <= 0 || scaled <= 0) {
				return scaled;
			}
			return Math.Max(1, (int)Math.Round(scaled * (expert / (2f * baseValue)), MidpointRounding.AwayFromZero));
		}

		/// <summary>The damage field for a hostile projectile that should hit for <paramref name="expert"/> in Expert
		/// (half in Classic, 1.5x in Master).</summary>
		public static int HostileProjectile(NPC npc, float expert) {
			float field = expert * 0.5f;                   // hostile hits are x2
			return npc.GetAttackDamage_ForProjectiles_MultiLerp(field * ClassicFactor + 0.5f, field + 0.5f, field * MasterFactor + 0.5f);
		}
	}
}
