namespace Cogpunk.Core.Combat
{
	/// <summary>
	/// A weapon whose right click is a skill run by its own <c>ModPlayer</c> rather than vanilla's alternate use (the Metal
	/// Wrench's parry, which starts in <c>PreItemCheck</c> on a fresh right click and isn't an item use). The Combinator
	/// (2026-11-12) asks for it: a combination's right click belongs to its base when the base has one, either an
	/// <c>AltFunctionUse</c> or this skill, and the skill's own code then accepts the combination as its weapon.
	/// </summary>
	public interface IRightClickSkill
	{
	}
}
