using System;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Projectiles
{
	/// <summary>
	/// The Jade Golem's ray (user-set 2026-11-06: "a precise jade green electric ray that does great damage at great range"):
	/// an instant beam from his fist along the line he locked, up to <see cref="MaxLength"/> (50 tiles) or the first solid
	/// tile. It hurts for its first <see cref="HitTicks"/> ticks (each player is struck once: vanilla's immunity after a
	/// hit), then fades over the rest of its <see cref="Lifetime"/>. Drawn as a chain of electric nodes, never rotated (D4
	/// rule 14), jittering across the line every few ticks, with a flare where it ends.
	/// <para>D2: a hostile projectile the server spawns; ai[0] is the beam's angle and ai[1] its length, both computed by
	/// the server and synced with the spawn, so every client tests its own player against the same line. D0: a finite
	/// lifetime; the length raycast (<see cref="RayLength"/>) is capped and bounds-checks every tile. D1: no allocation; the
	/// line test (<see cref="SwingPose.CapsuleHitsRect"/>) allocates nothing; drawing, light, dust and sound on clients.</para>
	/// </summary>
	public class JadeRay : CogpunkProjectile
	{
		public const float MaxLength = 50f * 16f;            // "great range"
		public const int Lifetime = 24, HitTicks = 8;
		public const float Radius = 7f;                      // half the hurting width
		private const float NodeSpacing = 6f, RayStep = 8f;
		private const int NodeFrames = 3, NodeSize = 16, OrbFrames = 5, OrbSize = 24, Gap = 2;

		private static Asset<Texture2D> orb;

		private float Length => MathHelper.Clamp(Projectile.ai[1], 0f, MaxLength);
		private Vector2 Direction => new((float)Math.Cos(Projectile.ai[0]), (float)Math.Sin(Projectile.ai[0]));
		private Vector2 Start => Projectile.Center;
		private Vector2 End => Start + Direction * Length;

		public override void SetStaticDefaults() {
			orb = DepthLayers.RequestOptional(Texture + "_Orb");
		}

		public override void Unload() {
			orb = null;
		}

		public override void SetDefaults() {
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		/// <summary>How far a ray from <paramref name="start"/> along the unit <paramref name="dir"/> runs before a solid tile
		/// (at most <paramref name="max"/>): 8 px steps, a fixed cap (D0), every tile bounds-checked.</summary>
		public static float RayLength(Vector2 start, Vector2 dir, float max) {
			if (!float.IsFinite(start.X) || !float.IsFinite(start.Y) || !float.IsFinite(dir.X) || !float.IsFinite(dir.Y)) {
				return 0f;
			}
			int steps = (int)(Math.Min(max, MaxLength) / RayStep);
			for (int i = 1; i <= steps; i++) {
				Vector2 p = start + dir * (i * RayStep);
				if (!TileSafety.TryGetTile((int)(p.X / 16f), (int)(p.Y / 16f), out Tile tile)) {
					return i * RayStep;                     // the world's edge
				}
				if (tile.HasTile && !tile.IsActuated && Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType]) {
					return i * RayStep;
				}
			}
			return steps * RayStep;
		}

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (Main.dedServ) {
				return;
			}
			if (Projectile.localAI[0] == 0f) {
				Projectile.localAI[0] = 1f;
				Burst();
			}
			float fade = Projectile.timeLeft / (float)Lifetime;
			Vector2 dir = Direction;
			float length = Length;
			for (float d = 0f; d <= length; d += 64f) {      // at most 13 lights (800 px / 64)
				Lighting.AddLight(Start + dir * d, 0.12f * fade, 0.6f * fade, 0.4f * fade);
			}
		}

		/// <summary>The shot (clients, once): the crack of the ray, sparks at the fist and where it strikes.</summary>
		private void Burst() {
			SoundEngine.PlaySound(SoundID.Item72 with { Pitch = -0.3f, Volume = 0.9f }, Start);
			int sparks = CogpunkClientConfig.RollEffect() ? 10 : 3;
			for (int i = 0; i < sparks; i++) {
				Vector2 at = i % 2 == 0 ? End : Start;
				if (SafeSpawn.TryNewDust(at - new Vector2(6f), 12, 12, i % 3 == 0 ? DustID.Electric : DustID.GreenTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(3f, 3f);
					d.scale = 1.2f;
				}
			}
		}

		public override bool CanHitPlayer(Player target) {
			return Lifetime - Projectile.timeLeft < HitTicks;
		}

		/// <summary>The ray lays a stack of the jade curse (user, 2026-11-10; on the hit player's own client, see
		/// <see cref="Gems.JadeCursePlayer"/>).</summary>
		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			Gems.JadeCursePlayer.Hit(target);
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			return SwingPose.CapsuleHitsRect(Start, End, Radius, targetHitbox);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D nodes = TextureAssets.Projectile[Type].Value;
			if (nodes.Height < NodeFrames * NodeSize) {
				return false;                               // the fallback texture: draw nothing rather than garbage
			}
			float fade = Projectile.timeLeft / (float)Lifetime;
			Color color = Color.White * fade;
			Vector2 dir = Direction;
			Vector2 normal = new(-dir.Y, dir.X);
			int tick = (int)(Main.GameUpdateCount / 3);
			int count = (int)(Length / NodeSpacing);
			Vector2 half = new(NodeSize * 0.5f);
			for (int i = 0; i <= count; i++) {
				int hash = (i * 73 + tick * 151) & 7;
				Vector2 at = Start + dir * (i * NodeSpacing) + normal * (hash % 5 - 2) - Main.screenPosition - half;
				Rectangle source = new(0, (i + tick) % NodeFrames * (NodeSize + Gap), NodeSize, NodeSize);
				Main.EntitySpriteDraw(nodes, at.Floor(), source, color, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			if (orb?.IsLoaded == true && orb.Value.Height >= OrbFrames * OrbSize) {
				Rectangle flare = new(0, (OrbFrames - 1) * (OrbSize + Gap), OrbSize, OrbSize);
				Vector2 end = End - Main.screenPosition - new Vector2(OrbSize * 0.5f);
				Main.EntitySpriteDraw(orb.Value, end.Floor(), flare, color, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}
}
