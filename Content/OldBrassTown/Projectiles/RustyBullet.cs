using System;
using Cogpunk.Content.OldBrassTown.NPCs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;

namespace Cogpunk.Content.OldBrassTown.Projectiles
{
	/// <summary>
	/// A rusty slug from an Old Brass Town six-shooter (the Brass Bandit's and the Sheriff's): straight, fast, stopped by
	/// walls, a thin smoke trail behind it that fades in half a second (<see cref="SmokeTrails"/>, user 2026-11-05: "to add
	/// more impact to the shots"). <see cref="Headings"/> pre-rendered headings (D4: never rotated). Hostile
	/// (Ember and Steam colours, D3). The shooter passes its damage through <c>ExpertStats.HostileProjectile</c>.
	/// <para>D2: spawned by the server, synced like any hostile projectile; each client checks its own player. D1: finite
	/// <see cref="Lifetime"/>, smoke client-side and throttled.</para>
	/// </summary>
	public class RustyBullet : CogpunkProjectile
	{
		public const int Headings = BrassBanditRigData.BulletHeadings;
		public const int Lifetime = 150;
		private const int Cell = 14, Stride = 16;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Headings;
		}

		public override void SetDefaults() {
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = 1;
			Projectile.tileCollide = true;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
			Projectile.extraUpdates = 1;                   // 2 steps a tick: a fast slug doesn't skip a thin player
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			float a = Projectile.velocity.ToRotation();
			Projectile.frame = (int)Math.Round(MathHelper.WrapAngle(a) / MathHelper.TwoPi * Headings + Headings) % Headings;
			if (!Main.dedServ) {
				SmokeTrails.Add(Projectile.Center, Projectile.Center + Projectile.velocity, new Color(138, 144, 150));   // Steam 0: a dirtier smoke
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 3; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Copper, out _);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Headings - 1) * Stride, Cell, Cell);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Cell * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, Color.Lerp(lightColor, Color.White, 0.4f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
