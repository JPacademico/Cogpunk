using System;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The <see cref="TarBoneStaff"/>'s tyrant skull. In flight it homes the way the Book of Skulls' skull does (decompiled
	/// <c>Projectile.AI</c>, type 837): it locks the nearest chaseable enemy within <see cref="AcquireRange"/> px (counted
	/// |dx| + |dy|) that it can see, keeps chasing it within <see cref="KeepRange"/>, and turns by blending
	/// 1/<see cref="Steering"/> of the way to it each tick at its launch speed; it snaps its jaw as it flies and faces where it
	/// goes (rotated like vanilla's skull). On the first enemy it bites it bursts (<see cref="Blast"/>): a circle
	/// <see cref="BlastDiameter"/> px across (5 tiles, user-set) that hurts every other enemy in it once, with
	/// <see cref="BlastShare"/> of the damage (the bitten one already took the bite: local immunity, once per NPC; the share was
	/// the whole damage until the user's "decrease a bit the area damage of the skull staff", 2026-11-17). A wall just breaks it.
	/// <para>D2: <c>ai[0]</c> = phase (synced when the owner's bite sets it), <c>ai[1]</c> = the locked target + 1 (synced as
	/// vanilla's does). Damage is decided by the owner's client. D0: finite life, the target index validated every tick.</para>
	/// </summary>
	public class TyrantSkullBolt : CogpunkProjectile
	{
		public const float Flying = 0f, Blast = 1f;
		public const float AcquireRange = 300f;
		public const float KeepRange = 1000f;
		public const int Steering = 32;
		public const int BlastDiameter = 5 * 16;
		public const float BlastShare = 0.7f;           // my call on the user's "a bit" (2026-11-17): 70% of the bite
		public const int Lifetime = 480;                // 8 s (the Book of Skulls' 1.4.5 life; 1.4.4's was a minute)
		public const int BlastFrames = 6, BlastFrameTicks = 3, BlastTicks = BlastFrames * BlastFrameTicks;
		private const int BlastHurtTicks = 2;
		private const int JawFrames = 3, JawFrameTicks = 5;
		private const int FrameWidth = 32, FrameHeight = 22, FrameStride = 24;
		private const int BlastFrameSize = 80, BlastFrameStride = 82;

		private static Asset<Texture2D> blast;

		private ref float Phase => ref Projectile.ai[0];
		private ref float Target => ref Projectile.ai[1];
		private ref float Speed => ref Projectile.localAI[0];
		private ref float BlastApplied => ref Projectile.localAI[1];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = JawFrames;
			if (!Main.dedServ) {
				const string path = "Cogpunk/Content/Junkyard/Weapons/TyrantSkullBlast";
				blast = ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
			}
		}

		public override void Unload() {
			blast = null;
		}

		public override void SetDefaults() {
			Projectile.width = 20;
			Projectile.height = 20;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.timeLeft = Lifetime;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;           // the bite, then the burst: every enemy once
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			if (Phase == Blast) {
				UpdateBlast();
				return;
			}
			if (Speed == 0f) {
				Speed = Math.Max(0.5f, Projectile.velocity.Length());
			}
			Home();
			Projectile.direction = Projectile.velocity.X >= 0f ? 1 : -1;
			Projectile.spriteDirection = Projectile.direction;
			Projectile.rotation = Projectile.direction > 0 ? Projectile.velocity.ToRotation() : (-Projectile.velocity).ToRotation();
			if (++Projectile.frameCounter >= JawFrameTicks) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % JawFrames;
			}
			if (Main.dedServ) {
				return;
			}
			Lighting.AddLight(Projectile.Center, 0.25f, 0.2f, 0.55f);
			if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust drip)) {
				drip.velocity = -Projectile.velocity * 0.2f;
			}
		}

		/// <summary>Book of Skulls homing (decompiled type 837), allocation-free: find, keep, steer at a constant speed.</summary>
		private void Home() {
			Vector2 centre = Projectile.Center;
			if (Target == 0f) {
				float best = AcquireRange;
				int found = -1;
				foreach (NPC npc in Main.ActiveNPCs) {
					if (!npc.CanBeChasedBy(Projectile)) {
						continue;
					}
					float d = Math.Abs(centre.X - npc.Center.X) + Math.Abs(centre.Y - npc.Center.Y);
					if (d < best && Collision.CanHit(centre, 1, 1, npc.position, npc.width, npc.height)) {
						best = d;
						found = npc.whoAmI;
					}
				}
				if (found >= 0) {
					Target = found + 1;
				}
			}
			if (Target <= 0f) {
				return;
			}
			int index = (int)Target - 1;
			if (index < 0 || index >= Main.maxNPCs || !Main.npc[index].active || !Main.npc[index].CanBeChasedBy(Projectile, ignoreDontTakeDamage: true)
				|| Main.npc[index].dontTakeDamage) {
				Target = 0f;
				return;
			}
			Vector2 to = Main.npc[index].Center - centre;
			if (Math.Abs(to.X) + Math.Abs(to.Y) >= KeepRange) {
				return;
			}
			Vector2 desired = to.SafeNormalize(Vector2.Zero) * Speed;
			Projectile.velocity = (Projectile.velocity * (Steering - 1) + desired) / Steering;
		}

		private void UpdateBlast() {
			Projectile.velocity = Vector2.Zero;
			if (BlastApplied == 0f) {
				BlastApplied = 1f;                         // every side, when the phase arrives: the burst's circle
				Projectile.tileCollide = false;
				Projectile.Resize(BlastDiameter, BlastDiameter);
				Projectile.timeLeft = BlastTicks;
				Projectile.frame = 0;
				if (!Main.dedServ) {
					BurstEffects();
				}
			}
			Projectile.frame = Math.Clamp((BlastTicks - Projectile.timeLeft) / BlastFrameTicks, 0, BlastFrames - 1);
		}

		private void BurstEffects() {
			SoundEngine.PlaySound(SoundID.Item14 with { Volume = 0.5f, Pitch = 0.25f, MaxInstances = 4 }, Projectile.Center);
			SoundEngine.PlaySound(SoundID.NPCHit2 with { Volume = 0.6f, Pitch = -0.2f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 12; i++) {
				if (i > 4 && !CogpunkClientConfig.RollEffect()) {
					continue;
				}
				Vector2 v = Main.rand.NextVector2CircularEdge(1f, 1f) * Main.rand.NextFloat(2f, 5f);
				int type = i % 3 == 0 ? DustID.Bone : ModContent.DustType<TarSplash>();
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(8f), 16, 16, type, out Dust d, v.X, v.Y)) {
					d.velocity = v;
				}
			}
			Lighting.AddLight(Projectile.Center, 0.5f, 0.4f, 0.9f);
		}

		public override bool? CanDamage() => Phase == Blast && BlastTicks - Projectile.timeLeft > BlastHurtTicks ? false : null;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (Phase != Blast) {
				return null;
			}
			Vector2 nearest = targetHitbox.ClosestPointInRect(Projectile.Center);   // a circle, not the square box
			return Vector2.DistanceSquared(nearest, Projectile.Center) <= BlastDiameter * BlastDiameter * 0.25f;
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (Phase == Blast) {
				modifiers.SourceDamage *= BlastShare;      // the burst on the others: a share of the bite
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (Phase == Flying && Projectile.owner == Main.myPlayer) {
				Phase = Blast;                             // the bite: burst here (synced; every side resizes in UpdateBlast)
				Projectile.netUpdate = true;
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.NPCHit2 with { Volume = 0.4f, Pitch = 0.3f, MaxInstances = 4 }, Projectile.Center);
				for (int i = 0; i < 6; i++) {
					SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 2 == 0 ? DustID.Bone : ModContent.DustType<TarSplash>(), out _);
				}
			}
			return true;                                   // a wall breaks it (no burst: it bursts on enemies)
		}

		public override bool PreDraw(ref Color lightColor) {
			if (Phase == Blast) {
				if (blast?.IsLoaded == true) {
					Rectangle frame = new(0, Math.Clamp(Projectile.frame, 0, BlastFrames - 1) * BlastFrameStride, BlastFrameSize, BlastFrameSize);
					Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(BlastFrameSize * 0.5f)).Floor();
					Main.EntitySpriteDraw(blast.Value, at, frame, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
				}
				return false;
			}
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, JawFrames - 1) * FrameStride, FrameWidth, FrameHeight);
			Vector2 position = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			SpriteEffects effects = Projectile.spriteDirection < 0 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), Projectile.rotation, new Vector2(FrameWidth, FrameHeight) * 0.5f, 1f, effects);
			return false;
		}
	}
}
