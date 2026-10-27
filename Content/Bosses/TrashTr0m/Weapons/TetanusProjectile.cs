using System;
using Cogpunk.Content.Bosses.TrashTr0m.Buffs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// The Tetanus lance, a held projectile (ExampleMod 1.4.4 <c>ExampleSpearProjectile</c>, like the Screwdriver's).
	/// <list type="bullet">
	/// <item><see cref="Quick"/>: over the use animation (melee speed applies) the tip punches out from
	/// <see cref="ReachMin"/> to <see cref="ReachMax"/> (8.5 tiles) in the first <see cref="QuickOut"/> of it, holds, and
	/// eases back. Local NPC immunity is cleared once at the turn, so every NPC is hit going out and again coming back.</item>
	/// <item><see cref="Charging"/> (right button held): the lance is drawn back <see cref="DrawBack"/> px and aimed at the
	/// cursor; every <see cref="Tetanus.ChargeStepTicks"/> ticks a step of charge is stored (a ping, a brass flash; rust
	/// motes spiral into the needle), up to <see cref="Tetanus.MaxChargeSteps"/>. Releasing the button switches to
	/// <see cref="Thrust"/>.</item>
	/// <item><see cref="Thrust"/>: one fast lunge to <see cref="ReachMax"/> over <see cref="ThrustTicks"/> ticks that hits
	/// every NPC on the line going out and again coming back (immunity cleared at the turn, as for the quick thrust; the
	/// animation is unchanged) for +20% damage (and knockback) per stored step, with an after-image, a flash ring at the
	/// tip and, at full charge, a camera punch.</item>
	/// </list>
	/// Every hit inflicts <see cref="TetanusDebuff"/>. In every mode the owner keeps the lance on the cursor (any
	/// direction), synced only when the aim has moved more than <see cref="AimResync"/> radians.
	/// <para>D2: <c>ai[0]</c> = mode, <c>ai[1]</c> = charge ticks, <c>ai[2]</c> = time in the current mode; every side counts
	/// them, the owner decides the aim and the release and syncs only then (and when the aim moves). Damage is decided by the
	/// owner's client. D1: no allocation; effects are client-only and throttled. The sprite points right and is rotated to
	/// the aim like every vanilla spear; it is drawn by the player as their held projectile.</para>
	/// </summary>
	public class TetanusProjectile : CogpunkProjectile
	{
		public const float Quick = 0f, Charging = 1f, Thrust = 2f;
		public const float ReachMin = 72f;               // tip distance from the player's centre at rest (the hand on the grip)
		public const float ReachMax = Tetanus.ReachTiles * 16f;   // 136 px
		public const float DrawBack = 14f;               // how far the charge pulls the lance back
		public const float QuickOut = 0.38f;             // fraction of the use spent punching out
		public const float QuickHold = 0.1f;
		public const int ThrustTicks = 22;
		public const float ThrustOut = 0.27f, ThrustHold = 0.33f;
		public const float Length = 112f;                // sprite length (2x art), the needle point at the right end
		private const float ShaftWidth = 10f;
		private const float GripInset = 14f;             // the hand covers the butt: it doesn't hit
		public const float AimResync = 0.03f;            // radians the aim must move before the owner syncs it
		private const int GlowFrames = 6;

		private static Asset<Texture2D> glow;
		private static Asset<Texture2D> flash;

		private ref float Mode => ref Projectile.ai[0];
		private ref float ChargeTicks => ref Projectile.ai[1];
		private ref float ModeTimer => ref Projectile.ai[2];

		// localAI (not synced): [0] returning (immunity cleared); [1] quick: duration; [2] last step announced (client effects).
		private ref float Returning => ref Projectile.localAI[0];
		private ref float Duration => ref Projectile.localAI[1];
		private ref float StepShown => ref Projectile.localAI[2];

		private float lastSyncedAim;
		private float tipDistance;

		public int ChargeSteps => Math.Min(Tetanus.MaxChargeSteps, (int)ChargeTicks / Tetanus.ChargeStepTicks);

		public float DamageMultiplier => Mode == Thrust ? 1f + ChargeSteps * Tetanus.ChargeStepPercent / 100f : 1f;

		public override void SetStaticDefaults() {
			if (!Main.dedServ) {
				glow = TryRequest("Cogpunk/Content/Bosses/TrashTr0m/Weapons/TetanusProjectile_Glow");
				flash = TryRequest("Cogpunk/Content/Bosses/TrashTr0m/Weapons/TetanusFlash");
			}
		}

		/// <summary>Missing art never blocks loading (D0): the effect is simply not drawn.</summary>
		internal static Asset<Texture2D> TryRequest(string path) {
			return ModContent.HasAsset(path) ? ModContent.Request<Texture2D>(path) : null;
		}

		public override void Unload() {
			glow = null;
			flash = null;
		}

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.aiStyle = -1;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.DamageType = DamageClass.Melee;
			Projectile.ownerHitCheck = true;             // no hits through walls
			Projectile.hide = true;                      // drawn by the player as heldProj
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;         // once per NPC (until the quick thrust turns around)
			Projectile.timeLeft = 60;                    // refreshed every tick while it lives
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player player = Main.player[Projectile.owner];
			if (!player.active || player.dead || player.CCed || player.noItems || player.HeldItem.type != ModContent.ItemType<Tetanus>()) {
				Projectile.Kill();
				return;
			}
			Projectile.timeLeft = 60;
			player.heldProj = Projectile.whoAmI;
			ModeTimer++;
			if (Mode == Charging) {
				UpdateCharge(player);
			}
			else {
				FollowAim(player);
			}
			Projectile.velocity = Projectile.velocity.SafeNormalize(Vector2.UnitX * player.direction);
			float progress;
			if (Mode == Quick) {
				if (Duration == 0f) {
					Duration = Math.Max(2, player.itemAnimationMax);
					if (!Main.dedServ) {
						SoundEngine.PlaySound(SoundID.Item1 with { Pitch = 0.3f }, player.Center);
					}
				}
				progress = ModeTimer / Duration;
				if (progress >= 1f) {
					Projectile.Kill();
					return;
				}
				if (progress >= QuickOut + QuickHold && Returning == 0f) {
					Returning = 1f;
					Array.Clear(Projectile.localNPCImmunity);   // second hit on the way back
				}
				tipDistance = MathHelper.Lerp(ReachMin, ReachMax, Extension(progress, QuickOut, QuickHold));
			}
			else if (Mode == Thrust) {
				progress = ModeTimer / ThrustTicks;
				if (progress >= 1f) {
					Projectile.Kill();
					return;
				}
				if (ModeTimer == 1f && !Main.dedServ) {
					ReleaseEffects(player);
				}
				if (progress >= ThrustOut + ThrustHold && Returning == 0f) {
					Returning = 1f;
					Array.Clear(Projectile.localNPCImmunity);   // the lunge hits again on the way back
				}
				tipDistance = MathHelper.Lerp(ReachMin - DrawBack, ReachMax, Extension(progress, ThrustOut, ThrustHold));
			}
			else {
				tipDistance = ReachMin - DrawBack * MathHelper.Clamp(ModeTimer / 12f, 0f, 1f);
			}
			if (Mode != Quick) {
				player.itemAnimation = player.itemTime = 2;   // keep holding the lance while charging and lunging
			}
			Projectile.Center = player.MountedCenter + Projectile.velocity * (tipDistance - Length * 0.5f);
			Projectile.rotation = Projectile.velocity.ToRotation();
			Projectile.direction = Projectile.velocity.X >= 0f ? 1 : -1;
			player.ChangeDir(Projectile.direction);
			player.itemRotation = (Projectile.velocity * player.direction).ToRotation();
			if (!Main.dedServ) {
				Effects(player);
			}
		}

		/// <summary>0 at rest, 1 fully out: a sharp punch out (cubic ease-out) over <paramref name="outPart"/> of the use, a
		/// hold of <paramref name="hold"/>, then a smooth return.</summary>
		private static float Extension(float progress, float outPart, float hold) {
			if (progress < outPart) {
				float u = 1f - progress / outPart;
				return 1f - u * u * u;
			}
			if (progress < outPart + hold) {
				return 1f;
			}
			float back = (progress - outPart - hold) / (1f - outPart - hold);
			return 1f - MathHelper.SmoothStep(0f, 1f, back);
		}

		/// <summary>Every side counts the charge; the owner aims and decides the release (synced on change only).</summary>
		private void UpdateCharge(Player player) {
			int cap = Tetanus.MaxChargeSteps * Tetanus.ChargeStepTicks;
			if (ChargeTicks < cap) {
				ChargeTicks++;
			}
			if (Projectile.owner != Main.myPlayer) {
				return;
			}
			FollowAim(player);
			if (!player.controlUseTile) {
				Mode = Thrust;                             // let go: lunge with what was stored
				ModeTimer = 0f;
				Projectile.netUpdate = true;
			}
		}

		/// <summary>Owner: the lance points at the cursor, whatever the direction (synced only when it has moved).</summary>
		private void FollowAim(Player player) {
			if (Projectile.owner != Main.myPlayer) {
				return;
			}
			Vector2 fallback = Projectile.velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 aim = (Main.MouseWorld - player.MountedCenter).SafeNormalize(fallback);
			Projectile.velocity = aim;
			float angle = aim.ToRotation();
			if (Math.Abs(MathHelper.WrapAngle(angle - lastSyncedAim)) > AimResync) {
				lastSyncedAim = angle;
				Projectile.netUpdate = true;
			}
		}

		public override bool? CanDamage() => Mode != Charging ? null : false;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 tip = Projectile.Center + Projectile.velocity * (Length * 0.5f);
			Vector2 grip = Projectile.Center - Projectile.velocity * (Length * 0.5f - GripInset);
			float collisionPoint = 0f;
			return Collision.CheckAABBvLineCollision(targetHitbox.TopLeft(), targetHitbox.Size(), grip, tip, ShaftWidth, ref collisionPoint);
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			float mult = DamageMultiplier;
			modifiers.SourceDamage *= mult;
			modifiers.Knockback *= mult;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			target.AddBuff(ModContent.BuffType<TetanusDebuff>(), Tetanus.DebuffTicks);
			if (!Main.dedServ) {
				Vector2 tip = Projectile.Center + Projectile.velocity * (Length * 0.5f);
				for (int i = 0; i < 5; i++) {
					if (SafeSpawn.TryNewDust(tip - new Vector2(6f), 12, 12, i % 2 == 0 ? DustID.Copper : DustID.Iron, out Dust d,
						Projectile.velocity.X * 3f, Projectile.velocity.Y * 3f)) {
						d.noGravity = i % 2 == 0;
					}
				}
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Effects (clients)
		// ------------------------------------------------------------------------------------------------------------

		private Vector2 TipWorld => Projectile.Center + Projectile.velocity * (Length * 0.5f);

		private void Effects(Player player) {
			if (Mode != Charging) {
				return;
			}
			int steps = ChargeSteps;
			if (steps > StepShown) {
				StepShown = steps;                         // a ping per stored step, rising in pitch; a brass flash
				bool full = steps >= Tetanus.MaxChargeSteps;
				SoundEngine.PlaySound((full ? SoundID.Item29 : SoundID.MaxMana) with { Pitch = -0.4f + steps * 0.15f, Volume = 0.7f }, TipWorld);
				for (int i = 0; i < (full ? 14 : 6); i++) {
					if (SafeSpawn.TryNewDust(TipWorld - new Vector2(4f), 8, 8, full ? DustID.PurpleTorch : DustID.Enchanted_Gold, out Dust d)) {
						d.velocity = Main.rand.NextVector2CircularEdge(2.5f, 2.5f);
						d.noGravity = true;
					}
				}
			}
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			// rust motes spiral in along the needle towards the tip, faster as the charge builds
			float charge = MathHelper.Clamp(ChargeTicks / (Tetanus.MaxChargeSteps * Tetanus.ChargeStepTicks), 0f, 1f);
			if (Main.rand.NextFloat() < 0.35f + 0.5f * charge) {
				float along = Main.rand.NextFloat(10f, Length * 0.9f);
				Vector2 normal = Projectile.velocity.RotatedBy(MathHelper.PiOver2);
				float side = Main.rand.NextBool() ? 1f : -1f;
				Vector2 at = TipWorld - Projectile.velocity * along + normal * side * Main.rand.NextFloat(6f, 16f);
				int type = charge >= 1f && Main.rand.NextBool(3) ? DustID.PurpleTorch : (Main.rand.NextBool(3) ? DustID.Enchanted_Gold : DustID.Copper);
				if (SafeSpawn.TryNewDust(at, 2, 2, type, out Dust mote, 0f, 0f, 0, default, 0.9f + 0.5f * charge)) {
					mote.noGravity = true;
					mote.velocity = (TipWorld - at) * (0.06f + 0.06f * charge) - normal * side * 0.8f;
				}
			}
		}

		private void ReleaseEffects(Player player) {
			int steps = ChargeSteps;
			bool full = steps >= Tetanus.MaxChargeSteps;
			SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.2f }, player.Center);
			if (steps > 0) {
				SoundEngine.PlaySound(SoundID.DD2_MonkStaffSwing with { Pitch = 0.2f + steps * 0.08f }, player.Center);
			}
			if (full) {
				SoundEngine.PlaySound(SoundID.Item74 with { Pitch = 0.5f, Volume = 0.6f }, player.Center);
				if (CogpunkClientConfig.Instance?.ScreenShake ?? true) {
					Main.instance.CameraModifiers.Add(new PunchCameraModifier(player.Center, Projectile.velocity, 4f, 10f, 10, 800f, "Cogpunk:Tetanus"));
				}
			}
			for (int i = 0; i < 4 + steps * 4; i++) {
				Vector2 v = Projectile.velocity.RotatedByRandom(0.35f) * Main.rand.NextFloat(3f, 9f + steps);
				if (SafeSpawn.TryNewDust(player.MountedCenter + Projectile.velocity * 40f, 4, 4, i % 3 == 0 ? DustID.Copper : DustID.Enchanted_Gold, out Dust d, v.X, v.Y)) {
					d.noGravity = true;
				}
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Drawing: rotated to the aim like vanilla's spears; flipped vertically when pointing left so the lit edge stays on
		// top. The glow (needle edge, rust cracks) brightens with the charge; the thrust leaves after-images and a flash
		// ring at the tip. Fades happen in code (D4: no semi-transparent pixels in the art).
		// ------------------------------------------------------------------------------------------------------------

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			SpriteEffects effects = Projectile.direction < 0 ? SpriteEffects.FlipVertically : SpriteEffects.None;
			Vector2 origin = texture.Size() * 0.5f;
			Vector2 centre = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Color color = Projectile.GetAlpha(lightColor);
			float charge = MathHelper.Clamp(ChargeTicks / (Tetanus.MaxChargeSteps * Tetanus.ChargeStepTicks), 0f, 1f);
			if (Mode == Thrust && ModeTimer < ThrustTicks * (ThrustOut + ThrustHold)) {
				for (int k = 3; k >= 1; k--) {             // after-images trailing the lunge
					Vector2 behind = centre - Projectile.velocity * (k * (10f + 4f * ChargeSteps));
					Main.EntitySpriteDraw(texture, behind, null, color * (0.18f * (4 - k)), Projectile.rotation, origin, 1f, effects);
				}
			}
			Vector2 shake = Vector2.Zero;
			if (Mode == Charging && charge > 0.5f && !Main.gamePaused) {
				shake = new Vector2(0f, Main.rand.Next(-1, 2) * (charge >= 1f ? 2f : 1f)).RotatedBy(Projectile.rotation);
			}
			Main.EntitySpriteDraw(texture, centre + shake, null, color, Projectile.rotation, origin, 1f, effects);
			float glowAmount = Mode == Charging ? charge : (Mode == Thrust ? 0.4f + 0.6f * ChargeSteps / Tetanus.MaxChargeSteps : 0f);
			if (glow?.IsLoaded == true && glowAmount > 0f) {
				Texture2D g = glow.Value;
				int frameHeight = g.Height / GlowFrames;
				int frame = (int)(Main.GameUpdateCount / 4 % GlowFrames);
				Rectangle source = new(0, frame * frameHeight, g.Width, frameHeight - 2);
				Main.EntitySpriteDraw(g, centre + shake, source, Color.White * glowAmount, Projectile.rotation, new Vector2(g.Width * 0.5f, (frameHeight - 2) * 0.5f), 1f, effects);
			}
			if (Mode == Thrust && flash?.IsLoaded == true && ChargeSteps > 0) {
				DrawFlash(flash.Value, centre);
			}
			return false;
		}

		/// <summary>The ring that bursts from the needle point as the lunge lands (unrotated frames, radially symmetric).</summary>
		private void DrawFlash(Texture2D texture, Vector2 centre) {
			const int Frames = 5;
			int start = (int)(ThrustTicks * ThrustOut) - 2;
			int frame = ((int)ModeTimer - start) / 2;
			if (frame < 0 || frame >= Frames) {
				return;
			}
			int size = texture.Width;
			Rectangle source = new(0, frame * (size + 2), size, size);
			Vector2 tip = centre + Projectile.velocity * (Length * 0.5f);
			Vector2 position = new(MathF.Round(tip.X - size * 0.5f), MathF.Round(tip.Y - size * 0.5f));
			float strength = 0.55f + 0.45f * ChargeSteps / Tetanus.MaxChargeSteps;
			Main.EntitySpriteDraw(texture, position, source, Color.White * strength, 0f, Vector2.Zero, 1f, SpriteEffects.None);
		}
	}
}
