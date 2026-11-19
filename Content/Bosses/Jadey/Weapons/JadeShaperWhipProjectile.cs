using System.Collections.Generic;
using Cogpunk.Content.Gems;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// The <see cref="JadeShaperWhip"/>'s lash (ExampleMod 1.4.4 <c>ExampleWhipProjectile</c>): vanilla's whip AI and collision
	/// (<c>DefaultToWhip</c>, aiStyle 165), <see cref="Segments"/> segments at range x<see cref="RangeMultiplier"/>. A hit on an
	/// enemy turned to jade deals x<see cref="PetrifiedBonus"/> (<see cref="ModifyHitNPC"/>, the owner's client, where vanilla works
	/// out a player's hit); every enemy it hits is tagged (<see cref="JadeShaperWhipDebuff"/>) and becomes the minions' target;
	/// each further enemy in one lash takes <see cref="MultihitFactor"/> of the last one's damage.
	/// <para>Art (JadeShaperWhipProjectile.png, <see cref="FrameWidth"/> px wide, every piece pointing down the lash): the gilt
	/// handle with a crimson tassel, a jade bead and a gilt bead taking turns along the cord, and Jadey's jade dart at the tip; the
	/// crimson cord is drawn under them (one flat quad a gap, as vanilla draws its lines) so the gaps never show. The pieces turn
	/// with the lash every frame, as every vanilla whip's do.</para>
	/// <para>D1: one reusable list for the control points; jade motes on clients only, a few a lash. D2: the owner's projectile;
	/// vanilla syncs it, the hit and the buffs.</para>
	/// </summary>
	public class JadeShaperWhipProjectile : CogpunkProjectile
	{
		public const int Segments = 20;
		public const float RangeMultiplier = 1.05f;
		public const float PetrifiedBonus = 1.5f;          // user-set: +50%
		public const float MultihitFactor = 0.92f;
		public const int FrameWidth = 16;
		public const int HandleY = 0, HandleHeight = 28;
		public const int BeadY = 30, BeadHeight = 10, BeadKinds = 2, BeadStride = 12;
		public const int TipY = 54, TipHeight = 26;
		private const int CordWidth = 2;
		private static readonly Color CordColor = new(126, 30, 36);    // crimson 2: Jadey's cord
		private const int MoteOneIn = 4;

		private static readonly List<Vector2> points = new(Segments + 2);

		public override void SetStaticDefaults() {
			ProjectileID.Sets.IsAWhip[Type] = true;
		}

		public override void SetDefaults() {
			Projectile.DefaultToWhip();
			Projectile.WhipSettings.Segments = Segments;
			Projectile.WhipSettings.RangeMultiplier = RangeMultiplier;
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (JadeCurseNPC.Petrified(target)) {
				modifiers.SourceDamage *= PetrifiedBonus;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			target.AddBuff(ModContent.BuffType<JadeShaperWhipDebuff>(), JadeShaperWhipDebuff.TagTicks);
			Main.player[Projectile.owner].MinionAttackTargetNPC = target.whoAmI;
			Projectile.damage = (int)(Projectile.damage * MultihitFactor);
			if (!Main.dedServ && JadeCurseNPC.Petrified(target) && CogpunkClientConfig.RollEffect()) {
				for (int i = 0; i < 6; i++) {
					if (SafeSpawn.TryNewDust(target.position, target.width, target.height, DustID.GemEmerald, out Dust shard)) {
						shard.velocity = Main.rand.NextVector2Circular(3f, 3f);
						shard.noGravity = true;
					}
				}
			}
		}

		// Jade motes off the dart while the lash is out (clients only).
		public override void PostAI() {
			if (Main.dedServ || !Main.rand.NextBool(MoteOneIn) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			Projectile.GetWhipSettings(Projectile, out float timeToFlyOut, out _, out _);
			float t = timeToFlyOut > 0f ? Projectile.ai[0] / timeToFlyOut : 1f;
			if (t < 0.3f || t > 0.85f) {
				return;
			}
			points.Clear();
			Projectile.FillWhipControlPoints(Projectile, points);
			if (points.Count < 2) {
				return;
			}
			if (SafeSpawn.TryNewDust(points[^1] - new Vector2(4f), 8, 8, DustID.GemEmerald, out Dust mote)) {
				mote.velocity *= 0.3f;
				mote.noGravity = true;
				mote.scale = 0.9f;
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			points.Clear();
			Projectile.FillWhipControlPoints(Projectile, points);
			if (points.Count < 2) {
				return false;
			}
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Texture2D pixel = TextureAssets.MagicPixel.Value;
			SpriteEffects flip = Projectile.spriteDirection < 0 ? SpriteEffects.None : SpriteEffects.FlipHorizontally;
			for (int i = 0; i < points.Count - 1; i++) {
				Vector2 diff = points[i + 1] - points[i];
				Color color = Lighting.GetColor(points[i].ToTileCoordinates(), CordColor);
				Main.EntitySpriteDraw(pixel, points[i] - Main.screenPosition, new Rectangle(0, 0, 1, 1), color, diff.ToRotation() - MathHelper.PiOver2,
					new Vector2(0.5f, 0f), new Vector2(CordWidth, diff.Length() + 1f), SpriteEffects.None);
			}
			for (int i = 0; i < points.Count - 1; i++) {
				Rectangle frame;
				Vector2 origin;
				if (i == 0) {
					frame = new Rectangle(0, HandleY, FrameWidth, HandleHeight);
					origin = new Vector2(FrameWidth / 2, 10);
				}
				else if (i == points.Count - 2) {
					frame = new Rectangle(0, TipY, FrameWidth, TipHeight);
					origin = new Vector2(FrameWidth / 2, 3);
				}
				else if (i % 2 == 1) {
					continue;                                  // a bead every other joint: the cord shows between them
				}
				else {
					frame = new Rectangle(0, BeadY + (i / 2 % BeadKinds) * BeadStride, FrameWidth, BeadHeight);
					origin = new Vector2(FrameWidth / 2, BeadHeight / 2);
				}
				Vector2 diff = points[i + 1] - points[i];
				Color color = Lighting.GetColor(points[i].ToTileCoordinates());
				Main.EntitySpriteDraw(texture, points[i] - Main.screenPosition, frame, color, diff.ToRotation() - MathHelper.PiOver2, origin, 1f, flip);
			}
			return false;
		}
	}
}
