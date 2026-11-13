using Cogpunk.Content.Gems;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Content.Junkyard.Weapons;
using Cogpunk.Content.Mechanist.Buffs;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>
	/// What a base's <see cref="CombinatorTrait"/>s do to a hit, shared by the product's own swings
	/// (<see cref="CombinedWeapon"/>) and its projectiles (<see cref="CombinedProjectile"/>). Every hook here runs where
	/// vanilla works out a player's hit, the owner's client, and each effect syncs itself the way its own weapon does
	/// (buffs through <c>NPC.AddBuff</c>, the jade curse and the Tar Plague through their own helpers, the burst as a synced
	/// owner projectile). D0: no feedback loop (a burst's own hits carry no traits, and bursts are rate-limited per player,
	/// <see cref="CombinatorBlast"/>); D1: a loop over a handful of traits, no allocation.
	/// </summary>
	public static class TraitEffects
	{
		public static void ModifyHit(CombinatorTrait[] traits, NPC target, ref NPC.HitModifiers modifiers) {
			if (traits == null) {
				return;
			}
			for (int k = 0; k < traits.Length; k++) {
				CombinatorTrait t = traits[k];
				switch (t.Kind) {
					case TraitKind.BonusVsMechanical:
						if (CogpunkSets.IsMechanical(target)) {
							modifiers.SourceDamage *= t.A;
						}
						break;
					case TraitKind.FirstStrike:
						if (!MacuahuitlStruck.Struck(target)) {
							modifiers.SourceDamage *= t.A;
						}
						break;
					case TraitKind.ArmorPierce:
						modifiers.ScalingArmorPenetration += t.A;
						break;
				}
			}
		}

		public static void OnHit(CombinatorTrait[] traits, NPC target, Player player, int damageDone, Vector2 at, DamageClass damageClass) {
			if (traits == null || player == null || player.whoAmI != Main.myPlayer) {
				return;
			}
			for (int k = 0; k < traits.Length; k++) {
				CombinatorTrait t = traits[k];
				switch (t.Kind) {
					case TraitKind.Debuff:
						if (t.C > 0 && t.C < BuffLoader.BuffCount && t.D > 0 && Main.rand.NextFloat() < t.A) {
							target.AddBuff(t.C, t.D);
						}
						break;
					case TraitKind.TarPlague:
						TarPlague.InflictOn(target, player, t.D);
						break;
					case TraitKind.JadeCurse:
						JadeCurseNPC.Hit(target);
						break;
					case TraitKind.Stun:
						if (Main.rand.NextFloat() < t.A && StunnedNPC.CanStun(target)) {
							target.AddBuff(ModContent.BuffType<Stunned>(), t.D);
						}
						break;
					case TraitKind.FirstStrike:
						MacuahuitlStruck.Mark(target);
						break;
					case TraitKind.AreaBurst:
						CombinatorBlast.Burst(player, at, t.A, (int)(damageDone * t.B), target.whoAmI, damageClass);
						break;
				}
			}
		}
	}
}
