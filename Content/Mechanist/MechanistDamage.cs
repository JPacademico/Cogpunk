using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// The Mechanist's damage class (ExampleMod 1.4.4 <c>ExampleDamageClass</c>). It takes every Generic bonus in full and
	/// nothing from the other classes, so "+x% damage" armor and potions count and melee/ranged/magic bonuses don't. Its
	/// base crit is the player's Generic 4% (decompiled <c>GenericDamageClass.SetDefaultStats</c> sets 4, inherited in
	/// full), so Mechanist weapons leave <c>Item.crit = 0</c> like every other Cogpunk weapon (D3 rule 9).
	/// Mechanist weapons spend Steam (<see cref="SteamPlayer"/>, <see cref="MechanistWeapon"/>).
	/// </summary>
	public class MechanistDamage : DamageClass
	{
		public override StatInheritanceData GetModifierInheritance(DamageClass damageClass) {
			return damageClass == Generic ? StatInheritanceData.Full : StatInheritanceData.None;
		}

		public override bool GetEffectInheritance(DamageClass damageClass) => false;

		public override bool UseStandardCritCalcs => true;
	}
}
