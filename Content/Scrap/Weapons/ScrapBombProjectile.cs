using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Weapons
{
	/// <summary>
	/// The thrown Scrap Bomb. Flies under gravity with a lit fuse; the first tile or enemy it touches makes it explode.
	/// <para>Damage: the contact hit uses the thrown damage (<see cref="ScrapBomb.DirectDamage"/> base). The blast is a
	/// 3-tick damage window with a circular hitbox and its own hit list (<c>ResetLocalNPCHitImmunity</c>), so the target
	/// hit directly also takes the blast: 43 + 32 on a direct hit, 32 for everything else in range. Tiles are never destroyed.</para>
	/// <para>Sync: <c>ai[0]</c> = exploding, <c>ai[1..2]</c> = blast centre, all synced. Contact hits run on the
	/// owner, which syncs the explosion; tile hits are detected on every client.</para>
	/// </summary>
	public class ScrapBombProjectile : CogpunkProjectile
	{
		private const int FrameCount = 2;
		private const int FuseTicksPerFrame = 3;
		private const int FlightSize = 12;
		private const float Gravity = 0.2f;
		private const float MaxFallSpeed = 16f;
		private const float SpinFactor = 0.08f;
		public const int MaxFlightTicks = 300;          // fuse runs out after 5 s and it blows up mid-air
		private const int ExplosionTicks = 3;           // damage window, like vanilla explosives
		private const float ExplosionKnockback = 6f;
		public const int ExplosionRadius = (int)(ScrapBomb.ExplosionRadiusTiles * 16f);
		private const int BlastDustSize = ExplosionRadius * 3 / 4;   // dust spawn box, scales with the blast
		private static readonly Vector2 FuseTipOffset = new(11f, -5f); // spark pixel of the 24x12 sprite, from its centre

		private bool Exploding {
			get => Projectile.ai[0] == 1f;
			set => Projectile.ai[0] = value ? 1f : 0f;
		}

		private Vector2 BlastCentre {
			get => new(Projectile.ai[1], Projectile.ai[2]);
			set {
				Projectile.ai[1] = value.X;
				Projectile.ai[2] = value.Y;
			}
		}

		// Per client: whether this copy has applied the blast (hitbox, damage) and played its effects.
		private bool blastApplied;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = FrameCount;
		}

		public override void SetDefaults() {
			Projectile.width = FlightSize;
			Projectile.height = FlightSize;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.timeLeft = MaxFlightTicks + ExplosionTicks;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;     // each NPC once per phase (contact, then blast)
		}

		public override void AI() {
			if (Exploding) {
				if (!blastApplied) {
					ApplyBlast();                   // remote copies arrive here through the synced ai[0]
				}
				if (!Main.dedServ) {
					Lighting.AddLight(Projectile.Center, 1.1f, 0.55f, 0.2f);
				}
				return;
			}

			if (Projectile.timeLeft <= ExplosionTicks + 1) {
				Explode();
				return;
			}

			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, MaxFallSpeed);
			MathSafety.Sanitize(ref Projectile.velocity);
			Projectile.rotation += Projectile.velocity.X * SpinFactor;

			if (++Projectile.frameCounter >= FuseTicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % FrameCount;
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect() && Main.rand.NextBool(2)) {
				Vector2 fuseTip = Projectile.Center + FuseTipOffset.RotatedBy(Projectile.rotation);
				if (SafeSpawn.TryNewDust(fuseTip, 1, 1, DustID.Torch, out Dust spark)) {
					spark.noGravity = true;
					spark.scale = 0.7f;
					spark.velocity *= 0.3f;
				}
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			Explode();
			return false;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			Explode();
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			// Vanilla explosions deal a fifth of their damage to Eater of Worlds segments in Expert mode; so does the blast.
			if (Exploding && Main.expertMode && target.type >= NPCID.EaterofWorldsHead && target.type <= NPCID.EaterofWorldsTail) {
				modifiers.FinalDamage /= 5;
			}
		}

		// The blast is a circle, not the square resized hitbox.
		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (!Exploding) {
				return null;
			}
			Vector2 centre = Projectile.Center;
			Vector2 closest = new(MathHelper.Clamp(centre.X, targetHitbox.Left, targetHitbox.Right),
				MathHelper.Clamp(centre.Y, targetHitbox.Top, targetHitbox.Bottom));
			return Vector2.DistanceSquared(centre, closest) <= ExplosionRadius * ExplosionRadius;
		}

		private void Explode() {
			if (Exploding) {
				return;
			}
			BlastCentre = Projectile.Center;
			Exploding = true;
			ApplyBlast();
			Projectile.netUpdate = true;
		}

		private void ApplyBlast() {
			blastApplied = true;
			Vector2 centre = BlastCentre;
			if (!MathSafety.IsFinite(centre)) {
				centre = Projectile.Center;
			}
			Projectile.tileCollide = false;
			Projectile.velocity = Vector2.Zero;
			Projectile.timeLeft = ExplosionTicks;
			Projectile.Resize(ExplosionRadius * 2, ExplosionRadius * 2);
			Projectile.Center = centre;
			Projectile.damage = (int)Math.Round(Projectile.damage * ScrapBomb.ExplosionDamage / (float)ScrapBomb.DirectDamage);
			Projectile.knockBack = ExplosionKnockback;
			Projectile.ResetLocalNPCHitImmunity();  // the target hit directly takes the blast too (51 + 32)

			if (!Main.dedServ) {
				SpawnBlastEffects(centre);
			}
		}

		private void SpawnBlastEffects(Vector2 centre) {
			SoundEngine.PlaySound(SoundID.Item14, centre);
			float density = CogpunkClientConfig.Instance?.EffectDensity ?? 1f;
			int smoke = 6 + (int)(14 * density);
			int fire = 6 + (int)(18 * density);
			int rust = (int)(10 * density);
			Vector2 corner = centre - new Vector2(BlastDustSize / 2f);

			for (int i = 0; i < smoke; i++) {
				if (SafeSpawn.TryNewDust(corner, BlastDustSize, BlastDustSize, DustID.Smoke, out Dust dust, 0f, 0f, 100, default, 1.6f)) {
					dust.velocity *= 1.6f;
				}
			}
			for (int i = 0; i < fire; i++) {
				if (SafeSpawn.TryNewDust(corner, BlastDustSize, BlastDustSize, DustID.Torch, out Dust dust, 0f, 0f, 100, default, 2.2f)) {
					dust.noGravity = true;
					dust.velocity *= 4f;
				}
			}
			for (int i = 0; i < rust; i++) {   // flying bits of rusted pipe
				if (SafeSpawn.TryNewDust(corner, BlastDustSize, BlastDustSize, DustID.Copper, out Dust dust, 0f, -2f)) {
					dust.velocity *= 2.5f;
				}
			}
			for (int i = 0; i < 2; i++) {      // vanilla smoke-cloud gores 61-63
				if (SafeSpawn.TryNewGore(Projectile.GetSource_FromThis(), corner, Vector2.Zero, 61 + Main.rand.Next(3), out Gore cloud)) {
					cloud.velocity += new Vector2(Main.rand.NextFloat(-1f, 1f), Main.rand.NextFloat(-1f, 0f));
				}
			}
			if (CogpunkClientConfig.Instance?.ScreenShake ?? true) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(centre, Main.rand.NextVector2Unit(), 3f, 6f, 12, 600f, "Cogpunk/ScrapBomb"));
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			if (Exploding) {
				return false;
			}
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frameHeight = texture.Height / FrameCount;
			int frame = Math.Clamp(Projectile.frame, 0, FrameCount - 1);
			Rectangle source = new(0, frame * frameHeight, texture.Width, frameHeight - 2);  // skip the padding row
			Vector2 origin = source.Size() * 0.5f;
			Main.EntitySpriteDraw(texture, Projectile.Center - Main.screenPosition, source, Projectile.GetAlpha(lightColor),
				Projectile.rotation, origin, 1f, SpriteEffects.None);
			return false;
		}
	}
}
