using System;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Content.Mechanist;
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

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The <see cref="TarShower"/>'s right-click charge, a held projectile (like the Tetanus lance's charge): while the
	/// button is held a ball of tar swells at the nozzle (<see cref="Stages"/> sizes, a gurgle at each, a chime and an aether
	/// rim at full), the gun stays aimed at the cursor, and the damage climbs from x1 to
	/// x<see cref="TarShower.MaxChargeMultiplier"/> over <see cref="TarShower.MaxChargeTicks"/> ticks. Letting go throws it:
	/// a <see cref="TarShowerBigGlob"/> at full charge, else a <see cref="TarShowerGlob"/> for its share.
	/// <para>The charge cost <see cref="TarShower.ChargeSteamCost"/> steam when it started (its damage already holds the Spring
	/// Gloves' bonus for it: <see cref="TarShower.SteamForUse"/>); while it is held the steam doesn't refill, as while a
	/// Mechanist weapon fires (<see cref="SteamPlayer.NoteAttack"/>).</para>
	/// <para>D2: <c>ai[0]</c> = charge ticks (every side counts them); the owner aims (synced only when the aim has moved more
	/// than <see cref="AimResync"/> radians) and decides the release. The gun itself is drawn by vanilla (the player keeps
	/// using it); this draws the ball. D1: no allocation; effects client-side and throttled.</para>
	/// </summary>
	public class TarShowerCharge : CogpunkProjectile
	{
		public const int Stages = 5;
		public const float AimResync = 0.03f;
		public const float GlobSpeed = 9f, BigGlobSpeed = 10f;
		private const int FrameSize = 32, FrameStride = 34;
		private const float BallDistance = 44f;           // from the hand to the ball at the nozzle

		private ref float ChargeTicks => ref Projectile.ai[0];
		private ref float StageShown => ref Projectile.localAI[0];
		private float lastSyncedAim;

		/// <summary>0..1 of a full charge.</summary>
		public float Charge => MathHelper.Clamp(ChargeTicks / TarShower.MaxChargeTicks, 0f, 1f);

		public bool Full => ChargeTicks >= TarShower.MaxChargeTicks;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Stages + 1;
		}

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = 60;                      // refreshed every tick while it is held
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage() => false;

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player player = Main.player[Projectile.owner];
			if (!player.active || player.dead || player.CCed || player.noItems || player.HeldItem.ModItem is not TarShower) {
				Projectile.Kill();
				return;
			}
			Projectile.timeLeft = 60;
			if (ChargeTicks < TarShower.MaxChargeTicks) {
				ChargeTicks++;
			}
			if (Projectile.owner == Main.myPlayer) {
				player.GetModPlayer<SteamPlayer>().NoteAttack();   // still attacking: no refill yet
				FollowAim(player);
				if (!player.controlUseTile) {
					Release(player);
					return;
				}
			}
			Projectile.velocity = Projectile.velocity.SafeNormalize(Vector2.UnitX * player.direction);
			player.itemAnimation = player.itemTime = 2;   // keep holding the gun while charging
			player.ChangeDir(Projectile.velocity.X >= 0f ? 1 : -1);
			player.itemRotation = (Projectile.velocity * player.direction).ToRotation();
			Projectile.Center = player.MountedCenter + Projectile.velocity * BallDistance;
			int stage = Full ? Stages : Math.Min(Stages - 1, (int)(Charge * Stages));
			Projectile.frame = stage;
			if (!Main.dedServ) {
				Effects(stage);
			}
		}

		/// <summary>Owner: the gun points at the cursor (synced only when it has moved).</summary>
		private void FollowAim(Player player) {
			Vector2 fallback = Projectile.velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 aim = (Main.MouseWorld - player.MountedCenter).SafeNormalize(fallback);
			Projectile.velocity = aim;
			float angle = aim.ToRotation();
			if (Math.Abs(MathHelper.WrapAngle(angle - lastSyncedAim)) > AimResync) {
				lastSyncedAim = angle;
				Projectile.netUpdate = true;
			}
		}

		/// <summary>Owner: let go. The glob leaves from the ball (if the nozzle isn't in a wall), and the charge is spent.</summary>
		private void Release(Player player) {
			float mult = 1f + (TarShower.MaxChargeMultiplier - 1f) * Charge;
			int damage = (int)Math.Round(Projectile.damage * mult);
			Vector2 from = player.MountedCenter + Projectile.velocity * BallDistance;
			if (!Collision.CanHit(player.MountedCenter, 0, 0, from, 0, 0)) {
				from = player.MountedCenter;
			}
			if (Full) {
				SafeSpawn.TryNewProjectile(Projectile.GetSource_FromThis(), from, Projectile.velocity * BigGlobSpeed + player.velocity * 0.3f,
					ModContent.ProjectileType<TarShowerBigGlob>(), damage, Projectile.knockBack * 2f, out _, Projectile.owner);
			}
			else {
				SafeSpawn.TryNewProjectile(Projectile.GetSource_FromThis(), from, Projectile.velocity * GlobSpeed + player.velocity * 0.3f,
					ModContent.ProjectileType<TarShowerGlob>(), damage, Projectile.knockBack * (1f + Charge), out _, Projectile.owner);
			}
			Projectile.Kill();
		}

		private void Effects(int stage) {
			if (stage > StageShown) {
				StageShown = stage;
				if (stage == Stages) {
					SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = -0.3f, Volume = 0.7f }, Projectile.Center);
				}
				else {
					SoundEngine.PlaySound(SoundID.Item85 with { Pitch = -0.7f + stage * 0.12f, Volume = 0.45f, MaxInstances = 3 }, Projectile.Center);
				}
			}
			if (Main.rand.NextBool(Full ? 4 : 8) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, ModContent.DustType<TarSplash>(), out Dust drip)) {
				drip.velocity = new Vector2(Main.rand.NextFloat(-0.4f, 0.4f), Main.rand.NextFloat(0.5f, 1.5f));
			}
			if (Full) {
				Lighting.AddLight(Projectile.Center, 0.2f, 0.18f, 0.45f);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Stages) * FrameStride, FrameSize, FrameSize);
			Vector2 wobble = Full && !Main.gamePaused ? new Vector2(0f, Main.GameUpdateCount / 4 % 2) : Vector2.Zero;   // 0/1 px, never -1/+1
			Vector2 position = (Projectile.Center - Main.screenPosition - new Vector2(FrameSize * 0.5f) + wobble).Floor();
			Main.EntitySpriteDraw(texture, position, source, Full ? Color.Lerp(lightColor, Color.White, 0.35f) : lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
