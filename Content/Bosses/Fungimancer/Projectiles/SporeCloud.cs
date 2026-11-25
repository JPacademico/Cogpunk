using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Fungimancer.Projectiles
{
	/// <summary>
	/// A cloud of the glowing mushrooms' spores: 4 x 4 tiles for 1.5 s that hurts and confuses the players inside it (user,
	/// 2026-11-25, the Fungimancer's falling mushrooms: "if destroyed or when it lands on the ground it should burst a 4x4 spore
	/// cloud that lasts 1.5 seconds and damage and aply confusion to players who touch it"; the Toadstools "burst into a spore
	/// cloud when killed", the same cloud). Vanilla's Confused (<see cref="ConfusionTicks"/>, the same 2 s as the mushrooms'
	/// touch). Hostile, spawned by the server; the damage is the spawner's (<c>ExpertStats.HostileProjectile</c>). It hurts only
	/// while it is thick (not in its last <see cref="ThinTicks"/>); a player's hurt immunity keeps it to one hit at a time.
	/// <para>Art: art/bosses/fungimancer/make_toadstool_art.py (6 frames: billowing, then thinning; faded in code at the end).
	/// D1: a little light and at most one dust a tick, clients only.</para>
	/// </summary>
	public class SporeCloud : CogpunkProjectile
	{
		public const int Size = 64, Lifetime = 90, Frames = 6, ConfusionTicks = 120, ThinTicks = 14, FadeTicks = 24;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = Size;
			Projectile.height = Size;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			Projectile.velocity *= 0.9f;
			int age = Lifetime - Projectile.timeLeft;
			Projectile.frame = Math.Clamp(age * Frames / Lifetime, 0, Frames - 1);
			if (Main.dedServ) {
				return;
			}
			float glow = Projectile.timeLeft < FadeTicks ? Projectile.timeLeft / (float)FadeTicks : 1f;
			Lighting.AddLight(Projectile.Center, 0.30f * glow, 0.10f * glow, 0.34f * glow);
			if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, Main.rand.NextBool(3) ? DustID.GlowingMushroom : DustID.PurpleTorch, out Dust d)) {
				d.noGravity = true;
				d.velocity = Main.rand.NextVector2Circular(0.8f, 0.8f) - Vector2.UnitY * 0.3f;
				d.scale = 0.9f;
			}
		}

		public override bool CanHitPlayer(Player target) => Projectile.timeLeft > ThinTicks;

		/// <summary>Each frame's cloud, game px (SporeCloud.png's opaque bounds, 2026-11-25): it hurts only as far as it is drawn,
		/// the whole 4 x 4 tiles once it has billowed out (tools/check_hitboxes.py).</summary>
		private static readonly Point[] FrameSize = { new(38, 38), new(54, 56), new(60, 62), new(58, 60), new(52, 52), new(48, 46) };

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Point size = FrameSize[Math.Clamp(Projectile.frame, 0, Frames - 1)];
			Rectangle cloud = new((int)Projectile.Center.X - size.X / 2, (int)Projectile.Center.Y - size.Y / 2, size.X, size.Y);
			return cloud.Intersects(targetHitbox);
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(BuffID.Confused, ConfusionTicks);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frameHeight = texture.Height / Frames;
			Rectangle source = new(0, Projectile.frame * frameHeight, texture.Width, frameHeight - 2);
			float fade = Projectile.timeLeft < FadeTicks ? Projectile.timeLeft / (float)FadeTicks : 1f;
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(texture.Width * 0.5f, (frameHeight - 2) * 0.5f)).Floor();
			at = new Vector2(MathF.Round(at.X / 2f) * 2f, MathF.Round(at.Y / 2f) * 2f);     // on the 2 px grid
			Main.EntitySpriteDraw(texture, at, source, Color.White * (0.85f * fade), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
