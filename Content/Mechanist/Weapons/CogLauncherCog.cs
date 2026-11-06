using System;
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

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// The Cog-launcher's cog (user-set 2026-11-05): a Rusted Cog spinning through the air in a straight line (no gravity,
	/// unlike the Scrap armor's lobbed cog), passing through <see cref="Pierce"/> enemies (the next one stops it), rebounding off
	/// <see cref="MaxBounces"/> walls (the next wall breaks it), and hitting an enemy it has already hit for
	/// <see cref="RepeatBonus"/>x (a rebound that comes back through the same enemy).
	/// <para>2026-11-05b (user: "the cog launcher should shoot spinning rusted cogs like the scrap armor does (but without
	/// bullet drop gravity) and not this golden cog projectile"): it is the Scrap armor's cog now, the Rusted Cog item sprite
	/// turning <see cref="SpinSpeed"/> radians a tick the way it flies (<see cref="Scrap.Armor.ScrapCogProjectile"/>'s look and
	/// spin), rust flaking off where it strikes; the gilt cog sheet is gone.</para>
	/// <para>Each enemy can be hit again once <see cref="HitCooldown"/> ticks have passed (local immunity), so a cog that
	/// passes through an enemy hits it once, and again only on its way back. D2: the owner's projectile (the owner decides its
	/// hits; the bounces are deterministic from the synced flight); <c>ai[0]</c> counts the bounces. D1/D0: no allocation (the
	/// enemies it hit are three ints), finite <see cref="Lifetime"/>.</para>
	/// </summary>
	public class CogLauncherCog : CogpunkProjectile
	{
		public const int Pierce = 2, MaxBounces = 3;               // user-set
		public const float RepeatBonus = 1.5f;                     // user-set: +50% on an enemy this cog already hit
		public const int Lifetime = 180;
		public const int HitCooldown = 12;
		public const float SpinSpeed = 0.35f;                      // the Scrap armor's cog's spin (radians a tick)
		private const string CogTexture = "Cogpunk/Content/Scrap/Items/RustedCog";   // the Rusted Cog item, as the Scrap armor's

		private int hitA = -1, hitB = -1, hitC = -1;
		private string texture;

		public override string Texture => texture ??= TextureFallback.Resolve(CogTexture);

		private ref float Bounces => ref Projectile.ai[0];

		public override void SetDefaults() {
			Projectile.width = 18;
			Projectile.height = 18;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = ModContent.GetInstance<MechanistDamage>();
			Projectile.penetrate = Pierce + 1;
			Projectile.tileCollide = true;
			Projectile.timeLeft = Lifetime;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = HitCooldown;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			Projectile.rotation += SpinSpeed * (Projectile.velocity.X >= 0f ? 1f : -1f);   // it rolls the way it flies
			if (Projectile.localAI[0] == 0f) {
				Projectile.localAI[0] = 1f;
				if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
					PistonPuff();
				}
			}
		}

		/// <summary>Every client, the cog's first tick: the piston's exhaust, a puff of steam blown back out of the cup.</summary>
		private void PistonPuff() {
			Vector2 back = -Projectile.velocity.SafeNormalize(Vector2.UnitX);
			for (int i = 0; i < 4; i++) {
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.Smoke, out Dust puff, 0f, 0f, 120, default, 0.9f)) {
					puff.noGravity = true;
					puff.velocity = back.RotatedBy(Main.rand.NextFloat(-0.6f, 0.6f)) * Main.rand.NextFloat(0.8f, 2f) + new Vector2(0f, -0.4f);
				}
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Bounces >= MaxBounces) {
				return true;                                       // the fourth wall: it breaks
			}
			Bounces++;
			Vector2 v = oldVelocity;
			if (Projectile.velocity.X != oldVelocity.X) {
				v.X = -oldVelocity.X;
			}
			if (Projectile.velocity.Y != oldVelocity.Y) {
				v.Y = -oldVelocity.Y;
			}
			Projectile.velocity = v;
			if (Projectile.owner == Main.myPlayer) {
				Projectile.netUpdate = true;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item10 with { Pitch = 0.4f, Volume = 0.6f, MaxInstances = 4 }, Projectile.Center);   // a clang
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 3; i++) {
						SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Copper, out _);   // rust flakes
					}
				}
			}
			return false;
		}

		private bool HasHit(int npc) => npc == hitA || npc == hitB || npc == hitC;

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (HasHit(target.whoAmI)) {
				modifiers.SourceDamage *= RepeatBonus;             // back through an enemy it already cut
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (!HasHit(target.whoAmI)) {
				if (hitA < 0) {
					hitA = target.whoAmI;
				}
				else if (hitB < 0) {
					hitB = target.whoAmI;
				}
				else {
					hitC = target.whoAmI;
				}
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				for (int i = 0; i < 4; i++) {
					SafeSpawn.TryNewDust(target.position, target.width, target.height, DustID.Copper, out _);
				}
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item52 with { Pitch = 0.3f, Volume = 0.6f, MaxInstances = 4 }, Projectile.Center);   // it breaks
			for (int i = 0; i < 6; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 2 == 0 ? DustID.Copper : DustID.Iron, out _);
			}
		}

		/// <summary>Drawn like the Scrap armor's cog: the Rusted Cog turned about its centre.</summary>
		public override bool PreDraw(ref Color lightColor) {
			Texture2D cog = TextureAssets.Projectile[Type].Value;
			Main.EntitySpriteDraw(cog, Projectile.Center - Main.screenPosition, null, Projectile.GetAlpha(lightColor), Projectile.rotation,
				cog.Size() * 0.5f, 1f, SpriteEffects.None);
			return false;
		}
	}
}
