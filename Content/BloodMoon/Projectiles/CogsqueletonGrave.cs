using System;
using Cogpunk.Content.BloodMoon.NPCs;
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
	/// The Mechromancer's summon telegraph: a ring of soul fire burnt into the ground with a cog's sign in it, flames licking
	/// up and green sparks rising, where a <see cref="Cogsqueleton"/> will climb out when it burns out
	/// (<see cref="Mechromancer.SummonTelegraph"/> ticks: D3 T3, at least 30). Harmless (neither friendly nor hostile).
	/// <c>ai[0]</c> is the Mechromancer's index: no master left, no skeleton.
	/// <para>D2: the server's (marked by the Mechromancer); the skeleton is spawned by the server when it expires
	/// (<see cref="SafeSpawn"/>, which refuses rather than overflow), and every side plays the sparks. D0/D1: finite, no
	/// allocation.</para>
	/// </summary>
	public class CogsqueletonGrave : CogpunkProjectile
	{
		public const int Width = 44, Height = 20, Frames = 4, FrameTicks = 5;

		private static Asset<Texture2D> glow;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = Width;
			Projectile.height = Height;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.tileCollide = false;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Mechromancer.SummonTelegraph;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage() => false;

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (++Projectile.frameCounter >= FrameTicks) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (Main.dedServ) {
				return;
			}
			if (Projectile.timeLeft == Mechromancer.SummonTelegraph - 1) {
				SoundEngine.PlaySound(SoundID.Item45 with { Pitch = -0.7f, Volume = 0.6f, MaxInstances = 4 }, Projectile.Center);
			}
			Lighting.AddLight(Projectile.Center, 0.1f, 0.4f, 0.3f);
			if (Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position + new Vector2(6f, 4f), Projectile.width - 12, 6, DustID.CursedTorch, out Dust d)) {
				d.noGravity = true;
				d.velocity = new Vector2(Main.rand.NextFloat(-0.4f, 0.4f), Main.rand.NextFloat(-2.4f, -0.8f));
			}
		}

		public override void OnKill(int timeLeft) {
			int m = (int)Projectile.ai[0];
			bool master = m >= 0 && m < Main.maxNPCs && Main.npc[m].active && Main.npc[m].type == ModContent.NPCType<Mechromancer>();
			if (master && timeLeft <= 0 && Main.netMode != NetmodeID.MultiplayerClient) {
				SafeSpawn.TryNewNPC(Projectile.GetSource_FromThis(), (int)Projectile.Center.X, (int)Projectile.Bottom.Y, ModContent.NPCType<Cogsqueleton>(),
					out _, ai2: m);
			}
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 10; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 2 == 0 ? DustID.Dirt : DustID.CursedTorch,
					out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), Main.rand.NextFloat(-3f, -1f));
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Frames - 1) * Height, Width, Height);
			if (source.Bottom > texture.Height) {
				return false;
			}
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Width * 0.5f, Height * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true) {
				Main.EntitySpriteDraw(glow.Value, at, source, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}
}
