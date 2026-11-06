using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Weapons
{
	/// <summary>
	/// The Sheriff's Revolver's bullet (user-set 2026-11-04: "a high speed bullet that bounces once, also on enemies, not
	/// only walls, and always bounces in the direction of an enemy"): fast (32 px a tick: two updates a tick), it bounces
	/// once, off the first wall it strikes or the first enemy it hits, and the bounce turns it at the nearest enemy in
	/// sight within <see cref="BounceRange"/> (never the one it just hit: each enemy is hit once). With nobody to turn to it
	/// glances off the wall as a ricochet would, or flies back off the enemy. Its second hit or wall ends it.
	/// <para>A ricochet hits harder (user, 2026-11-05: "shots that ricochet onto an enemy should deal 50% more damage"): every
	/// hit after the bounce deals <see cref="RicochetBonus"/>x. A thin smoke trail follows it and fades in half a second
	/// (<see cref="SmokeTrails"/>, user 2026-11-05).</para>
	/// <para>Friendly colours (Brass and Aether, D3); <see cref="Headings"/> pre-rendered headings (D4: never rotated).
	/// D2: the owner's projectile; the owner picks the bounce's target and syncs the turn (other clients run the same
	/// deterministic choice meanwhile). D1: one pass over the NPCs per bounce, no allocation; finite
	/// <see cref="Lifetime"/>.</para>
	/// </summary>
	public class SheriffsBullet : CogpunkProjectile
	{
		public const int Headings = 16;                       // 22.5 degrees apart (2026-11-05: 45 made true shots look off)
		public const float RicochetBonus = 1.5f;              // user-set 2026-11-05
		public const int Lifetime = 240;                        // updates (two a tick): 2 s
		public const float BounceRange = 40f * 16f;
		private const int Cell = 14, Stride = 16;

		private ref float Bounces => ref Projectile.ai[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Headings;
		}

		public override void SetDefaults() {
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = -1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;                    // each enemy once
			Projectile.tileCollide = true;
			Projectile.extraUpdates = 1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			float a = Projectile.velocity.ToRotation();
			Projectile.frame = (int)Math.Round(MathHelper.WrapAngle(a) / MathHelper.TwoPi * Headings + Headings) % Headings;
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.35f, 0.3f, 0.15f);
				SmokeTrails.Add(Projectile.Center, Projectile.Center + Projectile.velocity);   // this update's flight
			}
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (Bounces >= 1f) {
				modifiers.SourceDamage *= RicochetBonus;            // a ricochet's hit
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (Bounces >= 1f) {
				Projectile.Kill();
				return;
			}
			Bounce(target.whoAmI, -Projectile.velocity);            // nobody else in sight: it flies back off the enemy
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Bounces >= 1f) {
				return true;
			}
			Vector2 ricochet = oldVelocity;
			if (Projectile.velocity.X != oldVelocity.X) {
				ricochet.X = -oldVelocity.X;
			}
			if (Projectile.velocity.Y != oldVelocity.Y) {
				ricochet.Y = -oldVelocity.Y;
			}
			Projectile.velocity = oldVelocity;                      // keep the speed for the turn
			Bounce(-1, ricochet);
			return false;
		}

		/// <summary>The one bounce: at the nearest enemy in sight (not <paramref name="exclude"/>), else along
		/// <paramref name="fallback"/>, at the same speed.</summary>
		private void Bounce(int exclude, Vector2 fallback) {
			Bounces = 1f;
			float speed = Math.Max(1f, Projectile.velocity.Length());
			int best = -1;
			float bestSq = BounceRange * BounceRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.whoAmI == exclude || !npc.CanBeChasedBy(Projectile) || Projectile.localNPCImmunity[npc.whoAmI] != 0) {
					continue;
				}
				float sq = Vector2.DistanceSquared(npc.Center, Projectile.Center);
				if (sq < bestSq && Collision.CanHitLine(Projectile.Center, 1, 1, npc.position, npc.width, npc.height)) {
					best = npc.whoAmI;
					bestSq = sq;
				}
			}
			Vector2 heading = best >= 0 ? Main.npc[best].Center - Projectile.Center : fallback;
			Projectile.velocity = heading.SafeNormalize(-Projectile.velocity.SafeNormalize(Vector2.UnitX)) * speed;
			if (Projectile.owner == Main.myPlayer) {
				Projectile.netUpdate = true;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item10 with { Pitch = 0.6f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);   // the ricochet's whine
				for (int i = 0; i < 4; i++) {
					SafeSpawn.TryNewDust(Projectile.Center - new Vector2(3f), 6, 6, DustID.Gold, out _);
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Headings - 1) * Stride, Cell, Cell);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Cell * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, Color.Lerp(lightColor, Color.White, 0.6f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
