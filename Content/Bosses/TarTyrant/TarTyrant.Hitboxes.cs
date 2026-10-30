using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.TarTyrant.TarTyrantRigData;

namespace Cogpunk.Content.Bosses.TarTyrant
{
	/// <summary>
	/// Hitboxes that follow the art (boss-fight rule, 2026-10-26), as Trash-Tr0m's: the NPC rectangle (the idle frame's
	/// box, at <see cref="Size"/>) is only the broad phase; contact damage, melee swings and projectiles meet the
	/// silhouette strips the art generator measured from the current frame (<see cref="R.Hit"/>, the puddle left out: it
	/// is harmless), scaled with the boss and mirrored when it faces right. Nothing while it is under the tar.
	/// D1: at most <see cref="R.Strips"/> rectangle tests and one pose lookup per check, no allocation.
	/// </summary>
	public partial class TarTyrant
	{
		private Rectangle Strip(int frame, int k) {
			int i = (frame * R.Strips + k) * 4;
			if (i < 0 || i + 3 >= R.Hit.Length) {
				return Rectangle.Empty;
			}
			float s = Size;
			int x0 = R.Hit[i], y0 = R.Hit[i + 1], x1 = R.Hit[i + 2], y1 = R.Hit[i + 3];
			if (x1 <= x0 || y1 <= y0) {
				return Rectangle.Empty;
			}
			Vector2 origin = RigOrigin;
			float left = NPC.spriteDirection == 1 ? origin.X - x1 * s : origin.X + x0 * s;
			int width = (int)((x1 - x0) * s);
			int top = (int)(origin.Y + y0 * s);
			int bottom = (int)(origin.Y + y1 * s);
			return width > 0 && bottom > top ? new Rectangle((int)left, top, width, bottom - top) : Rectangle.Empty;
		}

		/// <summary>True if <paramref name="box"/> meets the silhouette of the current pose; <paramref name="hit"/> is the strip.</summary>
		public bool TouchesSilhouette(Rectangle box, out Rectangle hit) {
			hit = Rectangle.Empty;
			if (Submerged || Hidden) {
				return false;
			}
			int frame = ResolveFrame();
			if (frame < 0) {
				return false;
			}
			for (int k = 0; k < R.Strips; k++) {
				hit = Strip(frame, k);
				if (hit.Intersects(box)) {
					return true;
				}
			}
			hit = Rectangle.Empty;
			return false;
		}

		public override bool ModifyCollisionData(Rectangle victimHitbox, ref int immunityCooldownSlot, ref MultipliableFloat damageMultiplier, ref Rectangle npcHitbox) {
			npcHitbox = TouchesSilhouette(victimHitbox, out Rectangle hit) ? hit : Rectangle.Empty;   // empty never intersects
			return false;
		}

		public override bool? CanCollideWithPlayerMeleeAttack(Player player, Item item, Rectangle meleeAttackHitbox) {
			return TouchesSilhouette(meleeAttackHitbox, out _) ? null : false;
		}

		public override bool? CanBeHitByProjectile(Projectile projectile) {
			Rectangle box = projectile.Hitbox;
			if (!box.Intersects(NPC.Hitbox)) {
				return Submerged || Hidden ? false : null;     // custom-shaped collision (beams, whips): its own code decides
			}
			return TouchesSilhouette(box, out _) ? null : false;
		}
	}
}
