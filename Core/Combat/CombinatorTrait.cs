using System.Collections.Generic;

namespace Cogpunk.Core.Combat
{
	/// <summary>The kinds of passive a base weapon lends a Combinator product (Content/Combinator, 2026-11-12).</summary>
	public enum TraitKind : byte
	{
		/// <summary>Projectiles steer at the closest enemy within <c>A</c> px, turning <c>B</c> of the way a tick.</summary>
		Homing,
		/// <summary>A hit bursts over every other enemy within <c>A</c> px for <c>B</c> of the hit's damage.</summary>
		AreaBurst,
		/// <summary><c>A</c> chance (0..1) that a shot uses no ammo.</summary>
		AmmoSaver,
		/// <summary>x<c>A</c> damage against mechanical enemies.</summary>
		BonusVsMechanical,
		/// <summary>A hit gives buff <c>C</c> for <c>D</c> ticks, <c>A</c> of the time (0..1).</summary>
		Debuff,
		/// <summary>A hit lays <c>D</c> ticks of the Tar Plague.</summary>
		TarPlague,
		/// <summary>A hit lays a stack of the jade curse.</summary>
		JadeCurse,
		/// <summary><c>A</c> chance to stun a basic enemy for <c>D</c> ticks.</summary>
		Stun,
		/// <summary>x<c>A</c> on the first hit against each enemy.</summary>
		FirstStrike,
		/// <summary>Projectiles pierce <c>D</c> more enemies.</summary>
		Pierce,
		/// <summary>Ignores <c>A</c> (0..1) of the target's defense.</summary>
		ArmorPierce,
	}

	/// <summary>One passive: a kind and up to four numbers (their meaning per <see cref="TraitKind"/>).</summary>
	public readonly struct CombinatorTrait
	{
		public readonly TraitKind Kind;
		public readonly float A, B;
		public readonly int C, D;

		public CombinatorTrait(TraitKind kind, float a = 0f, float b = 0f, int c = 0, int d = 0) {
			Kind = kind;
			A = a;
			B = b;
			C = c;
			D = d;
		}
	}

	/// <summary>
	/// A weapon that lends the Combinator its passives itself (2026-11-12, "compatibility for all future weapons"): implement
	/// it on the weapon's <c>ModItem</c> and add the traits its own code applies (its homing, its debuff, its bonus...).
	/// The Combinator asks once, at load (<c>CombinatorTraits</c>), so the method may allocate. A weapon with no passive
	/// leaves the list empty; <c>tools/check_combinator.py</c> reminds every new Cogpunk weapon to decide.
	/// </summary>
	public interface ICombinatorPassives
	{
		void AddCombinatorTraits(List<CombinatorTrait> traits);
	}
}
