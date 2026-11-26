using System;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Underground.NPCs.CrystalLizardRigData;

namespace Cogpunk.Content.Underground.Gores
{
	/// <summary>
	/// A Crystal Lizard's dropped tail (user, 2026-11-26: "a small chance to let go of his tail which keeps twitching on the ground
	/// for some seconds while he scapes (just for cool detail animation)"): it falls and lies where it lands, its tip flicking up
	/// (the sheet's four curls, never rotated: D4) in jerks that come slower and weaker, with a little hop on the strongest, for
	/// <see cref="TwitchTicks"/>; then it lies still and fades away over <see cref="FadeTicks"/>.
	/// <para>A gore: clients only, nothing synced (each client drops its own when the synced lizard lets go,
	/// <see cref="NPCs.CrystalLizard"/>). Its own update replaces vanilla's (no spin, no bounce): gravity, the tiles' collision
	/// (vanilla's <c>Collision.TileCollision</c>), friction on the ground. D0: a finite life; slow motion holds it like any gore.</para>
	/// </summary>
	public class CrystalLizard_Tail : ModGore
	{
		public const int TwitchTicks = 4 * 60;                  // "keeps twitching on the ground for some seconds" (my call: 4 s)
		public const int FadeTicks = 40;
		private const float Gravity = 0.25f, MaxFall = 9f;

		public override void SetStaticDefaults() {
			ChildSafety.SafeGore[Type] = true;                   // a lizard's tail, not blood: shown with the gore setting off too
		}

		public override void OnSpawn(Gore gore, IEntitySource source) {
			gore.Frame = new SpriteFrame(2, R.TailFrames);
			gore.timeLeft = TwitchTicks + FadeTicks;
			gore.rotation = 0f;
			gore.alpha = 0;
			gore.sticky = false;
		}

		/// <summary>The lizard faced right (1) or left (-1): the sheet's mirrored column, or the drawn one.</summary>
		public static void Face(Gore gore, int facing) {
			gore.Frame.CurrentColumn = (byte)(facing == 1 ? 1 : 0);
		}

		public override bool Update(Gore gore) {
			if (gore.timeLeft-- <= 0) {
				gore.active = false;
				return false;
			}
			int age = TwitchTicks + FadeTicks - gore.timeLeft;
			Vector2 v = gore.velocity;
			v.Y = Math.Min(v.Y + Gravity, MaxFall);
			Vector2 moved = Collision.TileCollision(gore.position, v, R.TailCellWidth, R.TailCellHeight);
			bool grounded = moved.Y != v.Y && v.Y > 0f;
			if (grounded) {
				moved.X *= 0.8f;
				moved.Y = 0f;
			}
			gore.position += moved;
			gore.velocity = moved;
			gore.rotation = 0f;

			byte curl = 0;
			if (age < TwitchTicks) {
				int period = 9 + age / 6;                          // the jerks come slower ...
				int strength = age < 90 ? 3 : age < 170 ? 2 : 1;   // ... and weaker
				int phase = age % period;
				curl = (byte)(phase < strength ? phase + 1 : Math.Max(0, 2 * strength - phase - 1));
				if (phase == 0 && strength == 3 && grounded && Main.rand.NextBool(2)) {
					gore.velocity = new Vector2(Main.rand.NextFloat(-0.8f, 0.8f), -1.6f);   // the strongest flicks make it hop
				}
			}
			else {
				gore.alpha = Math.Min(255, (age - TwitchTicks) * 255 / FadeTicks);
			}
			gore.Frame.CurrentRow = Math.Min(curl, (byte)(R.TailFrames - 1));
			return false;
		}

		public override Color? GetAlpha(Gore gore, Color lightColor) => lightColor * ((255 - gore.alpha) / 255f);
	}
}
