using Terraria;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// A weapon of any class with a skill or secondary attack that costs steam (user, 2026-11-04: the Metal Wrench's parry
	/// and the Tar-Shower's charge, 10 steam each). The skill pays through <see cref="SteamPlayer.TryPayAttack"/> by a
	/// Mechanist weapon's rules (the cost multiplier, the "No steam tank!" hint, the overheat); the steam gauge shows while
	/// one is held with a tank to pay from; and the Spring Gloves count the steam a use took
	/// (<see cref="SteamPlayer.SteamForUse"/>).
	/// <para>D1: both members are read in per-tick hooks (the gauge, <c>ModifyWeaponDamage</c>): plain field reads, no
	/// allocation.</para>
	/// </summary>
	public interface ISteamSkill
	{
		/// <summary>The skill's steam cost before the player's cost multiplier (tooltips and the gauge).</summary>
		int SkillSteamCost { get; }

		/// <summary>The steam (after the cost multiplier) the use of this item that is starting or under way takes from the
		/// tank, or 0 when that use isn't the skill. A skill that isn't an item use (the wrench's parry) returns 0 and boosts
		/// its own payoff.</summary>
		int SteamForUse(Player player) => 0;
	}
}
