using System;
using Cogpunk.Content.Bosses.CursedConductor.NPCs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.CursedConductor.CursedConductorRigData;

namespace Cogpunk.Content.Bosses.CursedConductor.Projectiles
{
	/// <summary>
	/// Where one of the Cursed Conductor's ghosts will rise (user, 2026-11-05: "add a visual cue for the place where it will
	/// spawn"): a rift of ghost light that widens over its <c>ai[0]</c> ticks, motes rising out of it, a low moan at the end,
	/// then a <see cref="ConductorGhost"/> comes out of it. Harmless (neither hostile nor friendly). Opened where a lantern
	/// bolt struck a block (1.5 s), round the player trapped in the loop and out of the ground during the whistle.
	/// <para><c>ai[1]</c> = 1 for a furious (out of town) ghost. D2: the server's; the ghost is spawned by the server
	/// through <see cref="SafeSpawn"/> (refused, never forced, when the NPC array is full) and only while the ghosts are
	/// under their cap (<see cref="CursedConductor.GhostRoom"/>). D4: four pre-drawn frames at whole pixels, at full
	/// brightness (it is light).</para>
	/// </summary>
	public class GhostRift : CogpunkProjectile
	{
		private bool started;
		private int length;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.RiftFrames;
		}

		public override void SetDefaults() {
			Projectile.width = 32;
			Projectile.height = 32;
			Projectile.hostile = false;
			Projectile.friendly = false;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 300;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage() => false;

		public override void AI() {
			if (!started) {
				started = true;
				length = Math.Clamp((int)Projectile.ai[0], 10, 300);
				Projectile.timeLeft = length;
			}
			Projectile.velocity = Vector2.Zero;
			float t = 1f - Projectile.timeLeft / (float)Math.Max(1, length);
			Projectile.frame = Math.Clamp((int)(t * R.RiftFrames), 0, R.RiftFrames - 1);
			if (Main.dedServ) {
				return;
			}
			Lighting.AddLight(Projectile.Center, 0.1f + 0.2f * t, 0.35f + 0.4f * t, 0.3f + 0.3f * t);
			if (Main.rand.NextFloat() < 0.2f + 0.5f * t && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(10f, 4f), 20, 8, DustID.CursedTorch, out Dust d)) {
				d.noGravity = true;
				d.velocity = new Vector2(Main.rand.NextFloat(-0.3f, 0.3f), -Main.rand.NextFloat(0.8f, 2.2f));
			}
			if (Projectile.timeLeft == 12) {
				SoundEngine.PlaySound(SoundID.NPCHit36 with { Pitch = -0.4f, Volume = 0.5f, MaxInstances = 3 }, Projectile.Center);   // a moan
			}
		}

		public override void OnKill(int timeLeft) {
			if (timeLeft > 0 || Main.netMode == NetmodeID.MultiplayerClient || CursedConductor.GhostRoom(Projectile.whoAmI) <= 0) {
				return;                                         // only a rift that ran its course, on the server, under the cap
			}
			if (SafeSpawn.TryNewNPC(Projectile.GetSource_FromThis(), (int)Projectile.Center.X, (int)Projectile.Center.Y + 22,
					ModContent.NPCType<ConductorGhost>(), out NPC ghost, ai0: Projectile.ai[1])) {
				ghost.netUpdate = true;
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int cell = R.RiftCell;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, R.RiftFrames - 1) * (cell + 2), cell, cell);
			if (source.Bottom > texture.Height) {
				return false;
			}
			float pulse = 0.75f + 0.25f * MathF.Sin(Main.GlobalTimeWrappedHourly * 9f);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(cell * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, Color.White * pulse, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
