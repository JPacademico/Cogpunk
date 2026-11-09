using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Weapons
{
	/// <summary>
	/// A lost soul let go by the <see cref="CursedLantern"/>: a slow violet wisp (D3: friendly effects are Aether). While an
	/// enemy is within <see cref="HomingRange"/> of it (10 tiles, user-set) it bends towards the closest one at
	/// <see cref="ChaseSpeed"/>; with none that close it coasts on (about 14 tiles, <see cref="Slow"/>), slows to a drift
	/// (<see cref="DriftSpeed"/>) and floats there, bobbing,
	/// until one comes or its <see cref="Lifetime"/> runs out. It bursts on the first enemy it touches or on a wall.
	/// <para>D2: the owner's projectile; every side runs the same steering from synced positions, and the owner sends an
	/// update when its target changes. D0: finite lifetime; at most <see cref="MaxSouls"/> per player (the oldest fades
	/// first); the target index is bounds-checked. D1: one pass over the active NPCs every <see cref="SeekInterval"/> ticks
	/// (or when its target is lost), no allocation; light and sparks on clients only.</para>
	/// </summary>
	public class SoulFire : CogpunkProjectile
	{
		public const float HomingRange = 10f * 16f;          // user-set: 10 tiles round the soul
		public const float ChaseSpeed = 3.5f;
		public const float DriftSpeed = 0.35f;
		public const float Turn = 0.08f;                     // how fast it bends towards its target (a lerp a tick)
		public const float Slow = 0.985f;                    // its speed's decay a tick with no enemy near: it coasts ~14 tiles, then floats
		public const int Lifetime = 300;                     // 5 s
		public const int MaxSouls = 10;
		public const int SeekInterval = 6;
		public const int Frames = 4, FrameTicks = 5;
		private const int FrameW = 20, FrameH = 28;

		private static Asset<Texture2D> glow;

		/// <summary>ai[0] = target + 1, so 0 is "none" (synced).</summary>
		private int Target {
			get => (int)Projectile.ai[0] - 1;
			set => Projectile.ai[0] = value + 1;
		}

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 14;
			Projectile.height = 14;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = 1;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void OnSpawn(IEntitySource source) {
			if (Projectile.owner != Main.myPlayer) {
				return;
			}
			int count = 0, oldest = -1, oldestLeft = int.MaxValue;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == Type && p.owner == Projectile.owner && p.whoAmI != Projectile.whoAmI) {
					count++;
					if (p.timeLeft < oldestLeft) {
						oldestLeft = p.timeLeft;
						oldest = p.whoAmI;
					}
				}
			}
			if (count >= MaxSouls && oldest >= 0) {
				Main.projectile[oldest].Kill();             // the oldest soul fades, so the lantern never floods the screen
			}
		}

		private bool ValidTarget(int index) {
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC npc = Main.npc[index];
			return npc.CanBeChasedBy(Projectile) && Vector2.DistanceSquared(npc.Center, Projectile.Center) < HomingRange * HomingRange;
		}

		/// <summary>The closest enemy within <see cref="HomingRange"/> of the soul, or -1.</summary>
		private int Seek() {
			int best = -1;
			float bestDistance = HomingRange * HomingRange;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}
				float d = Vector2.DistanceSquared(npc.Center, Projectile.Center);
				if (d < bestDistance) {
					bestDistance = d;
					best = npc.whoAmI;
				}
			}
			return best;
		}

		public override void AI() {
			int age = Lifetime - Projectile.timeLeft;
			if (age % SeekInterval == 0 || !ValidTarget(Target)) {
				int next = Seek();
				if (next != Target) {
					Target = next;
					if (Projectile.owner == Main.myPlayer) {
						Projectile.netUpdate = true;        // only when it changes (D1, D2)
					}
				}
			}
			if (ValidTarget(Target)) {
				Vector2 want = (Main.npc[Target].Center - Projectile.Center).SafeNormalize(Vector2.UnitY) * ChaseSpeed;
				Projectile.velocity = Vector2.Lerp(Projectile.velocity, want, Turn);
			}
			else if (Projectile.velocity.LengthSquared() > DriftSpeed * DriftSpeed) {
				Projectile.velocity *= Slow;                // no enemy close: it slows to a drift and floats there
			}
			MathSafety.Sanitize(ref Projectile.velocity);
			if (++Projectile.frameCounter >= FrameTicks) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.32f, 0.26f, 0.62f);
				if (Main.rand.NextBool(6) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.PurpleTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = d.velocity * 0.3f - Projectile.velocity * 0.2f;
					d.scale = 0.9f;
				}
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCDeath6 with { Pitch = 0.4f, Volume = 0.35f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.PurpleTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity *= 1.6f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			int frame = Math.Clamp(Projectile.frame, 0, Frames - 1);
			Rectangle source = new(0, frame * (FrameH + 2), FrameW, FrameH);
			if (source.Bottom > texture.Height) {
				return false;                               // the fallback texture: draw nothing rather than garbage
			}
			int age = Lifetime - Projectile.timeLeft;
			float bob = age / 20 % 2 * 2f;                      // a 0/2 px bob (one art pixel; never -1/+1)
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(FrameW * 0.5f, FrameH * 0.5f + 4f)).Floor();
			at.Y += bob;
			float fade = Projectile.timeLeft < 30 ? Projectile.timeLeft / 30f : 1f;
			Main.EntitySpriteDraw(texture, at, source, Color.Lerp(lightColor, Color.White, 0.6f) * fade, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true) {
				Main.EntitySpriteDraw(glow.Value, at, source, Color.White * fade, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}
}
