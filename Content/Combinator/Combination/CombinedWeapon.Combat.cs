using Cogpunk.Core.Combat;
using Terraria;

namespace Cogpunk.Content.Combinator.Combination
{
	// The base's traits on the product's own swings and shots (its projectiles: CombinedProjectile).
	public sealed partial class CombinedWeapon
	{
		public override void ModifyHitNPC(Item item, Player player, NPC target, ref NPC.HitModifiers modifiers) {
			if (IsProduct) {
				TraitEffects.ModifyHit(Traits, target, ref modifiers);
			}
		}

		public override void OnHitNPC(Item item, Player player, NPC target, NPC.HitInfo hit, int damageDone) {
			if (IsProduct) {
				TraitEffects.OnHit(Traits, target, player, damageDone, target.Center, item.DamageType);
			}
		}

		/// <summary>The ammo-saving trait (vanilla's own weapons save theirs by type, decompiled
		/// <c>Player.IsAmmoFreeThisShot</c>, which still runs for the augment's type). Rolled on the shooting client.</summary>
		public override bool CanConsumeAmmo(Item weapon, Item ammo, Player player) {
			if (IsProduct && CombinatorTraits.Has(Traits, TraitKind.AmmoSaver, out CombinatorTrait saver) && Main.rand.NextFloat() < saver.A) {
				return false;
			}
			return true;
		}
	}
}
