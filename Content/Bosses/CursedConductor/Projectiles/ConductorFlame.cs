using System;
using Cogpunk.Content.Bosses.CursedConductor.Buffs;
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
	/// The Cursed Conductor's lantern bolt (user-set 2026-11-05: "a cursed projectile without bullet drop gravity and more
	/// space between the shots; if it hits a player it curses it for 6 seconds; projectiles that hit the ground or a wall
	/// spawn a ghost 1.5 seconds after they landed, with a visual cue for the place where it will spawn"): ghost fire flung
	/// in a fan from his lantern, flying straight. A player it hits gets the <see cref="ConductorCurse"/>; where it strikes a
	/// block a <see cref="GhostRift"/> opens and a <see cref="NPCs.ConductorGhost"/> rises out of it
	/// <see cref="CursedConductor.RiftDelay"/> ticks later (none when the ghosts are at their cap). Hostile colours (ghost
	/// green with a white heart, D3); four hand-drawn frames, never rotated (D4).
	/// <para><c>ai[0]</c> = 1 when he was furious (out of town): its ghost is too. D2: the server's (spawned by the boss); its
	/// flight follows from the synced velocity; the curse is added on the hit player's client (vanilla syncs it); the rift
	/// is the server's. D0/D1: finite <see cref="Lifetime"/>, no allocation.</para>
	/// </summary>
	public class ConductorFlame : CogpunkProjectile
	{
		public const int Lifetime = 150, FrameTicks = 5;

		private bool landed;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.FlameFrames;
		}

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			if (++Projectile.frameCounter >= FrameTicks) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % R.FlameFrames;
			}
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.15f, 0.5f, 0.4f);
				if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.CursedTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = -Projectile.velocity * 0.15f;
				}
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(ModContent.BuffType<ConductorCurse>(), ConductorCurse.Ticks);
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			landed = true;
			return true;
		}

		public override void OnKill(int timeLeft) {
			if (landed && Main.netMode != NetmodeID.MultiplayerClient) {
				Vector2 back = Projectile.velocity.SafeNormalize(Vector2.UnitY) * 10f;
				CursedConductor.OpenRift(Projectile.GetSource_Death(), Projectile.Center - back, CursedConductor.RiftDelay, Projectile.ai[0] == 1f);
			}
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item10 with { Pitch = -0.3f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.CursedTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity *= 1.6f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int cell = R.FlameCell;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, R.FlameFrames - 1) * (cell + 2), cell, cell);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(cell * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
