using System;
using Cogpunk.Content.Mechanist.Buffs;
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

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// The <see cref="FireworkCannon"/>'s firework (2026-11-17): a little cinnabar rocket with a gilt cone, trailing sparks, that
	/// flies straight and fast and bursts (state <see cref="Bursting"/>) when it strikes an enemy, hits a wall or has flown
	/// <see cref="RangeTiles"/> tiles. The strike deals <see cref="ContactShare"/> of its damage; the burst deals all of it to every
	/// enemy within <see cref="BurstRadius"/> px of its centre, the one it struck included, and stuns each basic enemy 1 time in
	/// <see cref="StunOneIn"/> for <see cref="StunTicks"/> ticks (<see cref="StunnedNPC.TryStun"/>, the Barrel Gun's stun).
	/// <para>D2: a player's projectile: the owner judges its hits (vanilla runs <c>Projectile.Damage</c> on the owner's client),
	/// so the owner decides when it bursts (<c>ai[0]</c>, synced with <c>netUpdate</c>); every client plays the burst from the
	/// synced state (<c>localAI[1]</c> remembers what it last saw). The burst hurts only in its first <see cref="HurtTicks"/>
	/// ticks (<see cref="CanDamage"/>), as a circle (<see cref="Colliding"/>), each enemy once (local immunity, cleared as it
	/// starts so the struck enemy is caught too). D0: finite <c>timeLeft</c>; no feedback (the burst spawns nothing that can
	/// burst again); NaN-safe headings. D1: no allocation; sparks on clients only, throttled.</para>
	/// <para>Art (art/bosses/jadey/make_jadey_loot_art.py): the rocket rendered at <see cref="Headings"/> headings (never turned
	/// at runtime), <see cref="Cell"/> px cells; the burst <see cref="BurstFrames"/> frames of <see cref="BurstCell"/> px (gilt,
	/// jade and aether stars: friendly Brass and Aether, D3 colour rule), drawn added onto the scene.</para>
	/// </summary>
	public class FireworkRocket : CogpunkProjectile
	{
		public const int RangeTiles = 22;                  // user-set
		public const float RangePx = RangeTiles * 16f;
		public const float ContactShare = 0.3f;            // "small contact damage"
		public const float BurstRadius = 44f;              // a burst about 5.5 tiles across
		public const int StunOneIn = 4;                    // my call: 25%
		public const int StunTicks = 60;                   // my call: 1 s, the Barrel Gun's
		public const int HurtTicks = 2;
		public const int Headings = 16, Cell = 36, Gap = 2;
		public const int BurstFrames = 6, BurstFrameTicks = 3, BurstCell = 96;
		public const int BurstTicks = BurstFrames * BurstFrameTicks;
		public const int SparkOneIn = 2;

		private static Asset<Texture2D> burst;

		private ref float State => ref Projectile.ai[0];
		private ref float BurstAge => ref Projectile.ai[1];
		private ref float Travelled => ref Projectile.localAI[0];
		private ref float SeenState => ref Projectile.localAI[1];

		public bool Bursting => State >= 1f;

		public override void SetStaticDefaults() {
			if (!Main.dedServ && ModContent.HasAsset(Texture + "_Burst")) {
				burst = ModContent.Request<Texture2D>(Texture + "_Burst");
			}
		}

		public override void Unload() {
			burst = null;
		}

		public override void SetDefaults() {
			Projectile.width = 12;
			Projectile.height = 12;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = 90;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
		}

		public override void AI() {
			if (!Bursting) {
				Travelled += Projectile.velocity.Length();
				if (Projectile.owner == Main.myPlayer && Travelled >= RangePx) {
					Burst();
				}
				else if (!Main.dedServ && Main.rand.NextBool(SparkOneIn) && CogpunkClientConfig.RollEffect()) {
					Vector2 back = Projectile.Center - Projectile.velocity.SafeNormalize(Vector2.UnitX) * 8f;
					if (SafeSpawn.TryNewDust(back - new Vector2(2f), 4, 4, Main.rand.NextBool() ? DustID.GoldFlame : DustID.GemEmerald, out Dust spark)) {
						spark.velocity = -Projectile.velocity * 0.15f + Main.rand.NextVector2Circular(0.6f, 0.6f);
						spark.noGravity = true;
						spark.scale = 0.9f;
					}
				}
				Lighting.AddLight(Projectile.Center, 0.6f, 0.45f, 0.2f);
			}
			else {
				if (BurstAge == 0f) {
					Array.Clear(Projectile.localNPCImmunity);  // the struck enemy is caught in the burst too
				}
				Projectile.velocity = Vector2.Zero;
				BurstAge++;
				Lighting.AddLight(Projectile.Center, 0.9f, 0.75f, 0.45f);
				if (BurstAge >= BurstTicks) {
					Projectile.Kill();
					return;
				}
			}
			PlayBurst();
		}

		/// <summary>The owner: the firework bursts where it is.</summary>
		private void Burst() {
			if (Bursting) {
				return;
			}
			State = 1f;
			BurstAge = 0f;
			Projectile.velocity = Vector2.Zero;
			Projectile.tileCollide = false;
			Projectile.timeLeft = BurstTicks + 4;
			Projectile.netUpdate = true;
		}

		/// <summary>Every client, once: the bang and the stars (from the synced state).</summary>
		private void PlayBurst() {
			if (!Bursting || SeenState >= 1f) {
				return;
			}
			SeenState = 1f;
			Projectile.tileCollide = false;
			Projectile.timeLeft = Math.Min(Projectile.timeLeft, BurstTicks + 4);
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item14 with { Pitch = 0.45f, Volume = 0.75f }, Projectile.Center);
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < 16; i++) {
				int dust = (i % 3) switch { 0 => DustID.GoldFlame, 1 => DustID.GemEmerald, _ => DustID.PurpleTorch };
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, dust, out Dust star)) {
					star.velocity = Main.rand.NextVector2CircularEdge(1f, 1f) * Main.rand.NextFloat(2.5f, 5f);
					star.noGravity = true;
					star.scale = 1.3f;
				}
			}
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Projectile.owner == Main.myPlayer) {
				Burst();
			}
			return false;
		}

		public override bool? CanDamage() => Bursting ? BurstAge < HurtTicks : null;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (!Bursting) {
				return null;
			}
			Vector2 c = Projectile.Center;
			float dx = c.X < targetHitbox.Left ? targetHitbox.Left - c.X : c.X > targetHitbox.Right ? c.X - targetHitbox.Right : 0f;
			float dy = c.Y < targetHitbox.Top ? targetHitbox.Top - c.Y : c.Y > targetHitbox.Bottom ? c.Y - targetHitbox.Bottom : 0f;
			return dx * dx + dy * dy <= BurstRadius * BurstRadius;
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (!Bursting) {
				modifiers.SourceDamage *= ContactShare;
			}
			else {
				modifiers.HitDirectionOverride = target.Center.X < Projectile.Center.X ? -1 : 1;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (!Bursting) {
				if (Projectile.owner == Main.myPlayer) {
					Burst();
				}
				return;
			}
			if (Main.rand.NextBool(StunOneIn)) {
				StunnedNPC.TryStun(target, StunTicks);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Vector2 at = Projectile.Center - Main.screenPosition;
			at = new Vector2(MathF.Round(at.X), MathF.Round(at.Y));
			if (!Bursting) {
				Texture2D rocket = TextureAssets.Projectile[Type].Value;
				float angle = Projectile.velocity.ToRotation();
				int heading = float.IsFinite(angle) ? (int)MathF.Round(angle / MathHelper.TwoPi * Headings) : 0;
				heading = ((heading % Headings) + Headings) % Headings;
				Rectangle frame = new(0, heading * (Cell + Gap), Cell, Cell);
				if (frame.Bottom <= rocket.Height) {
					Main.EntitySpriteDraw(rocket, at, frame, Color.White, 0f, new Vector2(Cell / 2f), 1f, SpriteEffects.None);
				}
				return false;
			}
			if (burst?.IsLoaded == true) {
				Texture2D b = burst.Value;
				int f = Math.Clamp((int)(BurstAge / BurstFrameTicks), 0, BurstFrames - 1);
				Rectangle frame = new(0, f * (BurstCell + Gap), BurstCell, BurstCell);
				float fade = f < BurstFrames - 2 ? 1f : 0.6f;
				if (frame.Bottom <= b.Height) {
					Main.EntitySpriteDraw(b, at, frame, new Color(255, 255, 255, 0) * fade, 0f, new Vector2(BurstCell / 2f), 1f, SpriteEffects.None);
				}
			}
			return false;
		}
	}
}
