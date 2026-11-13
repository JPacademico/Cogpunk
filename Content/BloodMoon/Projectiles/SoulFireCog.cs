using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.BloodMoon.Projectiles
{
	/// <summary>
	/// The Mechromancer's Soul Fire Cog (user-set 2026-11-12: "shoots soul fire cogs"): a brass cog wreathed in soul fire,
	/// flung from its staff in a volley (<see cref="NPCs.Mechromancer"/>), flying straight and spinning (four pre-drawn
	/// frames, never rotated: D4), breaking on the first block it meets in a burst of soul fire. Ghost green like the
	/// Cursed Conductor's soul fire (the mod's undead flame), its heart white.
	/// <para>D2: the server's (spawned by the Mechromancer's AI); its flight follows from the synced velocity. D0/D1: a finite
	/// <see cref="Lifetime"/>, no allocation; light and dust on clients only.</para>
	/// </summary>
	public class SoulFireCog : CogpunkProjectile
	{
		public const int Lifetime = 180, FrameTicks = 3, Frames = 4, Cell = 28;

		private static Asset<Texture2D> glow;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 18;                               // the cog's teeth (the fire round it is light, not body)
			Projectile.height = 18;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			if (++Projectile.frameCounter >= FrameTicks) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (Main.dedServ) {
				return;
			}
			Lighting.AddLight(Projectile.Center, 0.12f, 0.45f, 0.35f);
			if (Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.CursedTorch, out Dust d)) {
				d.noGravity = true;
				d.velocity = -Projectile.velocity * 0.2f;
				d.scale = 1.1f;
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item10 with { Pitch = 0.2f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 10; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 3 == 0 ? DustID.Copper : DustID.CursedTorch,
					out Dust d)) {
					d.noGravity = i % 3 != 0;
					d.velocity *= 1.8f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Frames - 1) * Cell, Cell, Cell);
			if (source.Bottom > texture.Height) {
				return false;                                    // the fallback texture: draw nothing rather than garbage
			}
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Cell * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, Color.Lerp(lightColor, Color.White, 0.55f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true) {
				Main.EntitySpriteDraw(glow.Value, at, source, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);   // the fire: fullbright
			}
			return false;
		}
	}
}
