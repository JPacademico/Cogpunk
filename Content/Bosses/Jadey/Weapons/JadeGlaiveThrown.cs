using System;
using Cogpunk.Content.Gems;
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
using R = Cogpunk.Content.Bosses.Jadey.Weapons.JadeGlaiveRigData;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// A thrown <see cref="JadeCursedGlaives"/> glaive (2026-11-17, user: "throw the glaive up to 18 tiles dealing damage and
	/// returning (like a boomerang, pierces one enemy only and hits on the way back as well) deals bonus damage to jade petrified
	/// enemies (50%)"). It flies straight out at <see cref="ThrowSpeed"/> until it has gone <see cref="RangeTiles"/> tiles or
	/// meets a wall, then turns and flies back through everything to its thrower's hand (<see cref="ReturnSpeed"/>, turning
	/// <see cref="ReturnTurn"/> of the way a tick), where it is caught. Going out it passes through the first enemy it meets and
	/// hits nothing else; coming back the same (<c>ai[1]</c> counts the phase's hit; the local immunities are cleared as it
	/// turns, so the same enemy can be hit both ways). An enemy turned to jade (<see cref="JadeCurseNPC.Petrified"/>) takes
	/// x<see cref="PetrifiedBonus"/>.
	/// <para>Art: the glaive spinning in a plane tipped towards the viewer, <see cref="R.SpinFrames"/> pre-rendered turns of
	/// <see cref="R.SpinCell"/> px (never rotated at runtime), <see cref="SpinFramesPerTick"/> frames a tick (2026-11-24, user:
	/// "increase the rotation speed ... so it looks better like a fan spining": four times the old 1 frame every 2 ticks), the
	/// turns it just passed through drawn faintly over it (<see cref="BlurFrames"/>: a fan's blurred disc), and two fading
	/// afterimages from its recent positions (the fades in code, D4 rule 9).</para>
	/// <para>Boxes (user, 2026-11-26: "the right mouse hitbox hits the ground before hiting enemies ... make it hitbox for tiles
	/// smaller and for entities bigger"): it meets enemies with a <see cref="HitSize"/> px box (the spinning blades' disc) but
	/// walls only with its <see cref="TileSize"/> px middle (<see cref="TileCollideStyle"/>); thrown level from the hand, its
	/// old 60 px box reached under the wielder's feet and bounced off the floor at once.</para>
	/// <para>D2: the owner's projectile: the owner turns it (wall, range) and counts its hits (<c>ai[0]</c> phase, <c>ai[1]</c>
	/// hits, synced with <c>netUpdate</c>); every side flies it home the same way. D0: <c>timeLeft</c> caps a glaive that
	/// can't get home; it dies with its thrower. D1: no allocation.</para>
	/// </summary>
	public class JadeGlaiveThrown : CogpunkProjectile
	{
		public const int RangeTiles = 22;                  // user-set 18 (2026-11-17), "the range a bit" more on 2026-11-24 (+4: my call)
		public const float RangePx = RangeTiles * 16f;
		public const float ThrowSpeed = 16f;
		public const float ReturnSpeed = 18f;
		public const float ReturnTurn = 0.2f;
		public const float CatchDistance = 24f;
		public const float PetrifiedBonus = JadeCursedGlaives.PetrifiedBonus;
		public const int SpinFramesPerTick = 2;            // 45 degrees a tick (2026-11-24; was half a frame a tick)
		public const int BlurFrames = 3;                   // the turns just passed, drawn fainter and fainter behind it
		public const int WhooshTicks = 8;                  // the whirr of a faster spin (2026-11-24; 12 before)
		public const int HitSize = 96;                     // its box for enemies (2026-11-26; 60 before): the blades' disc
		public const int TileSize = 20;                    // its box for walls and floors (2026-11-26): the hub

		private ref float Phase => ref Projectile.ai[0];
		private ref float PhaseHits => ref Projectile.ai[1];
		private ref float Travelled => ref Projectile.localAI[0];
		private ref float Spin => ref Projectile.localAI[1];

		public override void SetStaticDefaults() {
			ProjectileID.Sets.TrailCacheLength[Type] = 6;
			ProjectileID.Sets.TrailingMode[Type] = 0;
		}

		public override void SetDefaults() {
			Projectile.width = HitSize;                          // enemies: the spinning blades (TileCollideStyle shrinks it for tiles)
			Projectile.height = HitSize;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Melee;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
			Projectile.timeLeft = 300;
		}

		public override void AI() {
			Player owner = Main.player[Projectile.owner];
			if (!owner.active || owner.dead) {
				Projectile.Kill();
				return;
			}
			Spin++;
			if (!Main.dedServ && (int)Spin % WhooshTicks == 1) {
				SoundEngine.PlaySound(SoundID.Item7 with { Pitch = 0.2f, Volume = 0.6f }, Projectile.Center);
			}
			Lighting.AddLight(Projectile.Center, 0.25f, 0.6f, 0.4f);
			if (Phase < 0.5f) {
				Travelled += Projectile.velocity.Length();
				if (Projectile.owner == Main.myPlayer && Travelled >= RangePx) {
					TurnBack();
				}
				return;
			}
			Projectile.tileCollide = false;
			Vector2 home = owner.MountedCenter - Projectile.Center;
			float distance = home.Length();
			if (distance < CatchDistance || !float.IsFinite(distance)) {
				Projectile.Kill();
				return;
			}
			Vector2 want = home / distance * ReturnSpeed;
			Projectile.velocity = Vector2.Lerp(Projectile.velocity, want, ReturnTurn);
		}

		/// <summary>The owner: it turns for home; the enemies hit going out may be hit again coming back.</summary>
		private void TurnBack() {
			if (Phase >= 0.5f) {
				return;
			}
			Phase = 1f;
			PhaseHits = 0f;
			Array.Clear(Projectile.localNPCImmunity);
			Projectile.tileCollide = false;
			Projectile.netUpdate = true;
		}

		/// <summary>Walls and floors stop only its middle (<see cref="TileSize"/>), centred; enemies meet the whole box.</summary>
		public override bool TileCollideStyle(ref int width, ref int height, ref bool fallThrough, ref Vector2 hitboxCenterFrac) {
			width = TileSize;
			height = TileSize;
			hitboxCenterFrac = new Vector2(0.5f, 0.5f);
			return true;
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Projectile.owner == Main.myPlayer) {
				TurnBack();
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Dig with { Pitch = 0.4f, Volume = 0.6f }, Projectile.Center);
			}
			Projectile.velocity = -oldVelocity * 0.5f;
			return false;
		}

		public override bool? CanHitNPC(NPC target) => PhaseHits >= 1f ? false : null;

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (JadeCurseNPC.Petrified(target)) {
				modifiers.SourceDamage *= PetrifiedBonus;
			}
			modifiers.HitDirectionOverride = Projectile.velocity.X < 0f ? -1 : 1;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			PhaseHits = 1f;
			Projectile.netUpdate = true;
			if (Main.dedServ || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			bool shattered = JadeCurseNPC.Petrified(target);
			for (int i = 0; i < (shattered ? 12 : 5); i++) {
				if (SafeSpawn.TryNewDust(target.position, target.width, target.height, DustID.GemEmerald, out Dust shard)) {
					shard.velocity = Main.rand.NextVector2Circular(shattered ? 4f : 2.5f, shattered ? 4f : 2.5f);
					shard.noGravity = true;
					shard.scale = shattered ? 1.3f : 1f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D sheet = TextureAssets.Projectile[Type].Value;
			int frames = Math.Max(1, R.SpinFrames);
			int spin = Projectile.velocity.X < 0f ? -1 : 1;       // it spins the way it flies
			int f = SpinFrame((int)Spin * SpinFramesPerTick * spin, frames);
			Rectangle frame = SpinRect(f);
			if (frame.Bottom > sheet.Height) {
				return false;
			}
			Vector2 origin = new(R.SpinCell / 2f);
			Color lit = Color.Lerp(Lighting.GetColor(Projectile.Center.ToTileCoordinates()), Color.White, 0.35f);
			for (int k = 2; k >= 1; k--) {
				Vector2 old = Projectile.oldPos[Math.Min(k * 2, Projectile.oldPos.Length - 1)];
				if (old == Vector2.Zero) {
					continue;
				}
				Vector2 trailAt = old + Projectile.Size / 2f - Main.screenPosition;
				Main.EntitySpriteDraw(sheet, new Vector2(MathF.Round(trailAt.X), MathF.Round(trailAt.Y)), frame, lit * (0.3f / k), 0f, origin, 1f, SpriteEffects.None);
			}
			Vector2 at = Projectile.Center - Main.screenPosition;
			Vector2 snapped = new(MathF.Round(at.X), MathF.Round(at.Y));
			// the fan: the turns it passed through this tick and the last, fainter the further back (a blurred disc of blades)
			for (int k = BlurFrames; k >= 1; k--) {
				Rectangle blur = SpinRect(SpinFrame(f - spin * k, frames));
				if (blur.Bottom <= sheet.Height) {
					Main.EntitySpriteDraw(sheet, snapped, blur, lit * (0.5f / (k + 1)), 0f, origin, 1f, SpriteEffects.None);
				}
			}
			Main.EntitySpriteDraw(sheet, snapped, frame, lit, 0f, origin, 1f, SpriteEffects.None);
			return false;
		}

		private static int SpinFrame(int f, int frames) => (f % frames + frames) % frames;

		/// <summary>A turn's cell: the sheet is in columns of <see cref="R.SpinRows"/> (2026-11-18).</summary>
		private static Rectangle SpinRect(int f) {
			int rows = Math.Max(1, R.SpinRows);
			return new Rectangle(f / rows * (R.SpinCell + R.Gap), f % rows * (R.SpinCell + R.Gap), R.SpinCell, R.SpinCell);
		}
	}
}
