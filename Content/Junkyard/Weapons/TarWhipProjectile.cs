using System.Collections.Generic;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The <see cref="TarWhip"/>'s lash (ExampleMod 1.4.4 <c>ExampleWhipProjectile</c>): vanilla's whip AI and collision
	/// (<c>DefaultToWhip</c>, aiStyle 165), <see cref="Segments"/> segments at range x<see cref="RangeMultiplier"/> (the
	/// Spinal Tap's is x0.95, decompiled <c>Projectile.VanillaWhipSettings</c>, case 952). Every enemy it hits is tagged
	/// (<see cref="TarWhipDebuff"/>, the minions' target too) and coated in the Tar Plague for <see cref="PlagueTicks"/>
	/// ticks; each further enemy in one lash takes <see cref="MultihitFactor"/> of the last one's damage (the Spinal Tap's
	/// -10%, decompiled <c>Projectile.Damage</c>).
	/// <para>Art (TarWhipProjectile.png, 14 px wide, segments facing down, the joint at <see cref="JointX"/>,
	/// <see cref="JointY"/> of each): the bone handle wrapped in tar, three vertebrae (tar-stained, a drip each), the
	/// tyrant's fang at the tip; a cord of tar is drawn under them so the gaps between vertebrae never show. A whip's
	/// segments turn with the lash every frame, as every vanilla whip's do.</para>
	/// <para>D1: one reusable list for the control points (no allocation per frame), dust on clients only, a few a lash.
	/// D2: the owner's projectile; vanilla syncs it, the hit and the buffs.</para>
	/// </summary>
	public class TarWhipProjectile : CogpunkProjectile
	{
		public const int Segments = 20;
		public const float RangeMultiplier = 1f;
		public const int PlagueTicks = 120;               // 2 s a lash (+1.5 s with the Tyrant set)
		public const float MultihitFactor = 0.9f;
		public const int JointX = 7, JointY = 8;
		private const int FrameWidth = 14;
		private const int HandleY = 0, HandleHeight = 24;
		private const int SegmentY = 24, SegmentHeight = 16, SegmentKinds = 3;
		private const int TipY = 72, TipHeight = 22;
		private const int CordWidth = 2;
		private static readonly Color CordColor = new(47, 27, 20);   // Leather 0: the tar's body colour
		private const int DripOneIn = 3;

		private static readonly List<Vector2> points = new(Segments + 2);

		public override void SetStaticDefaults() {
			ProjectileID.Sets.IsAWhip[Type] = true;       // whip collision, flasks
		}

		public override void SetDefaults() {
			Projectile.DefaultToWhip();
			Projectile.WhipSettings.Segments = Segments;
			Projectile.WhipSettings.RangeMultiplier = RangeMultiplier;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			Player owner = Main.player[Projectile.owner];
			target.AddBuff(ModContent.BuffType<TarWhipDebuff>(), TarWhipDebuff.TagTicks);
			TarPlague.InflictOn(target, owner, PlagueTicks);
			owner.MinionAttackTargetNPC = target.whoAmI;
			Projectile.damage = (int)(Projectile.damage * MultihitFactor);
		}

		// Tar flicks off the tip while the lash is out (clients only).
		public override void PostAI() {
			if (Main.dedServ || !Main.rand.NextBool(DripOneIn) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			Projectile.GetWhipSettings(Projectile, out float timeToFlyOut, out _, out _);
			float t = timeToFlyOut > 0f ? Projectile.ai[0] / timeToFlyOut : 1f;
			if (t < 0.3f || t > 0.8f) {
				return;
			}
			points.Clear();
			Projectile.FillWhipControlPoints(Projectile, points);
			if (points.Count < 2) {
				return;
			}
			Vector2 tip = points[^1];
			if (SafeSpawn.TryNewDust(tip - new Vector2(4f), 8, 8, ModContent.DustType<TarSplash>(), out Dust drop)) {
				drop.velocity = (tip - points[^2]).SafeNormalize(Vector2.Zero) * 1.5f;
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
			Vector2 origin = new(JointX, JointY);
			// the cord under the vertebrae: one flat-coloured quad per gap (MagicPixel, as vanilla draws its lines)
			for (int i = 0; i < points.Count - 1; i++) {
				Vector2 diff = points[i + 1] - points[i];
				Color color = Lighting.GetColor(points[i].ToTileCoordinates(), CordColor);
				Main.EntitySpriteDraw(pixel, points[i] - Main.screenPosition, new Rectangle(0, 0, 1, 1), color, diff.ToRotation() - MathHelper.PiOver2,
					new Vector2(0.5f, 0f), new Vector2(CordWidth, diff.Length() + 1f), SpriteEffects.None);
			}
			for (int i = 0; i < points.Count - 1; i++) {
				Rectangle frame;
				if (i == 0) {
					frame = new Rectangle(0, HandleY, FrameWidth, HandleHeight);
				}
				else if (i == points.Count - 2) {
					frame = new Rectangle(0, TipY, FrameWidth, TipHeight);
				}
				else if (i % 2 == 1) {
					continue;                                  // a vertebra every other joint: the cord shows between them
				}
				else {
					frame = new Rectangle(0, SegmentY + (i / 2 % SegmentKinds) * SegmentHeight, FrameWidth, SegmentHeight);
				}
				Vector2 diff = points[i + 1] - points[i];
				Color color = Lighting.GetColor(points[i].ToTileCoordinates());
				Main.EntitySpriteDraw(texture, points[i] - Main.screenPosition, frame, color, diff.ToRotation() - MathHelper.PiOver2, origin, 1f, flip);
			}
			return false;
		}
	}
}
