using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.TrashTr0m.TrashTr0mRigData;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	/// <summary>
	/// Hitboxes that follow the art. The NPC rectangle (<see cref="HitboxWidth"/> x <see cref="HitboxHeight"/>, the idle
	/// body's box measured from the sprite) is only the broad phase: a hunched, three-quarter body leaves big empty corners
	/// in it (above the head, under the waist). The narrow phase uses the silhouette strips the art generator measures
	/// from every frame (<see cref="R.BodyHit"/>, <see cref="R.NearHit"/>, <see cref="R.FarHit"/>: vertical strips, each
	/// the box of the opaque pixels in it), for the pose the boss is in right now (<see cref="ResolvePose"/>, synced
	/// state only, so the server and every client agree).
	/// <list type="bullet">
	/// <item><b>Contact damage</b> (<see cref="ModifyCollisionData"/>, decompiled <c>NPC.GetMeleeCollisionData</c>: the
	/// player is hit if its hitbox meets the rectangle this returns): the strip the player touches, or an empty rectangle.
	/// So the fists and the far claw on the ground hurt, the air above the head doesn't.</item>
	/// <item><b>Melee swings</b> (<see cref="CanCollideWithPlayerMeleeAttack"/>, the exact swing rectangle) and
	/// <b>projectiles</b> (<see cref="CanBeHitByProjectile"/>) hit only where they meet a strip. A projectile whose own
	/// rectangle is outside the NPC rectangle (lasers, beams, whips that collide by their own shape) is left to its own
	/// collision code.</item>
	/// </list>
	/// <para>D1: at most 12 rectangle tests and one pose lookup per check, no allocation.</para>
	/// </summary>
	public partial class TrashTr0m
	{
		/// <summary>World rectangle of strip <paramref name="k"/> of <paramref name="frame"/> (empty if the strip is empty).</summary>
		private Rectangle Strip(short[] boxes, int frame, int strips, int k) {
			int i = (frame * strips + k) * 4;
			if (i < 0 || i + 3 >= boxes.Length) {
				return Rectangle.Empty;
			}
			int x0 = boxes[i], y0 = boxes[i + 1], x1 = boxes[i + 2], y1 = boxes[i + 3];
			if (x1 <= x0 || y1 <= y0) {
				return Rectangle.Empty;
			}
			Vector2 origin = RigOrigin;
			int left = NPC.spriteDirection == 1 ? (int)origin.X - x1 : (int)origin.X + x0;   // mirrored when facing right
			return new Rectangle(left, (int)origin.Y + y0, x1 - x0, y1 - y0);
		}

		/// <summary>True if <paramref name="box"/> meets the silhouette of the current pose; <paramref name="hit"/> is the strip.</summary>
		public bool TouchesSilhouette(Rectangle box, out Rectangle hit) {
			ResolvePose(out int body, out int arm);
			for (int k = 0; k < R.BodyStrips; k++) {
				hit = Strip(R.BodyHit, body, R.BodyStrips, k);
				if (hit.Intersects(box)) {
					return true;
				}
			}
			for (int k = 0; k < R.ArmStrips; k++) {
				hit = Strip(R.NearHit, arm, R.ArmStrips, k);
				if (hit.Intersects(box)) {
					return true;
				}
				hit = Strip(R.FarHit, arm, R.ArmStrips, k);
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
				return null;                               // custom-shaped collision (beams, whips): its own code decides
			}
			return TouchesSilhouette(box, out _) ? null : false;
		}
	}
}
