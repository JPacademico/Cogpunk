using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.TarTyrant.TarTyrantRigData;

namespace Cogpunk.Content.Bosses.TarTyrant.Projectiles
{
	/// <summary>
	/// Tar left on the ground by a <see cref="TarTyrantGlob"/> (user-set 2026-10-29: 3 tiles, 3 seconds, 1 second of tar
	/// poisoning): for <see cref="Lifetime"/> ticks a player standing in it gets the Tar Plague for
	/// <see cref="TarTyrant.PlagueTicks"/>, refreshed while inside. It deals no damage of its own (it never "hits": the
	/// debuff is applied by each player's own client, which owns its movement and buffs; vanilla syncs player buffs, D2).
	/// At most <see cref="MaxAlive"/> at once (D0/D1: the glob checks <see cref="CanSpawnMore"/>).
	/// </summary>
	public class TarTyrantPuddle : CogpunkProjectile
	{
		public const int HitboxWidth = 3 * 16, HitboxHeight = 12;
		public const int Lifetime = 180;
		public const int MaxAlive = 12;
		public const int Frames = 4;
		public const int TicksPerFrame = 9;
		public const int FadeTicks = 30;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = HitboxWidth;
			Projectile.height = HitboxHeight;
			Projectile.hostile = false;
			Projectile.friendly = false;
			Projectile.tileCollide = false;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		/// <summary>Server: room for another puddle (a fixed loop over the projectiles, called once per landing glob).</summary>
		public static bool CanSpawnMore() {
			int type = ModContent.ProjectileType<TarTyrantPuddle>();
			int count = 0;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == type && ++count >= MaxAlive) {
					return false;
				}
			}
			return true;
		}

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			Projectile.Opacity = Projectile.timeLeft < FadeTicks ? Projectile.timeLeft / (float)FadeTicks : 1f;
			if (Main.dedServ) {
				return;
			}
			Player local = Main.LocalPlayer;
			if (local.active && !local.dead && Projectile.timeLeft > FadeTicks / 2 && local.Hitbox.Intersects(Projectile.Hitbox)) {
				local.AddBuff(ModContent.BuffType<TarPlague>(), TarTyrant.PlagueTicks);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * (R.PuddleHeight + 2), R.PuddleWidth, R.PuddleHeight);
			Vector2 bottom = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY + 2f);
			Vector2 position = new((int)(bottom.X - R.PuddleWidth * 0.5f), (int)(bottom.Y - R.PuddleHeight));
			Main.EntitySpriteDraw(texture, position, source, lightColor * Projectile.Opacity, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
