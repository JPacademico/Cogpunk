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

namespace Cogpunk.Content.Bosses.Fungimancer.Projectiles
{
	/// <summary>
	/// The Fungimancer's spore bolt (its Cast): a mote of violet light that bends towards the player it was cast at (ai[0]) for
	/// <see cref="HomingTicks"/> ticks, then flies straight; it bursts on a wall or a player. Expert damage
	/// (<see cref="Fungimancer.BoltDamage"/>) set by the caster. D0: the target index checked; finite life. D1: no allocation.
	/// </summary>
	public class SporeBolt : CogpunkProjectile
	{
		public const int Frames = 4, FrameSize = 18, Stride = 20;
		public const int HomingTicks = 70, Life = 240;
		public const float Turn = 0.035f;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 14;
			Projectile.height = 14;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			Projectile.localAI[0]++;
			int target = (int)Projectile.ai[0];
			if (Projectile.localAI[0] <= HomingTicks && target >= 0 && target < Main.maxPlayers && Main.player[target].active && !Main.player[target].dead) {
				Vector2 want = (Main.player[target].Center - Projectile.Center).SafeNormalize(Projectile.velocity);
				float speed = Projectile.velocity.Length();
				float now = Projectile.velocity.ToRotation(), goal = want.ToRotation();
				float turned = now + MathHelper.Clamp(MathHelper.WrapAngle(goal - now), -Turn, Turn);
				Projectile.velocity = turned.ToRotationVector2() * speed;
			}
			if (++Projectile.frameCounter >= 5) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.35f, 0.3f, 0.7f);
				if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.PurpleTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity *= 0.3f;
				}
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			Projectile.Kill();
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item10 with { Pitch = 0.4f, Volume = 0.5f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.PurpleTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(3f, 3f);
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Frames - 1) * Stride, FrameSize, FrameSize);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(FrameSize * 0.5f)).Floor();
			Main.EntitySpriteDraw(tex, at, source, Color.White * Projectile.Opacity, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}

	/// <summary>
	/// A glowing mushroom bursting out of the ground (the Fungimancer's Croak): spawned centred on its spot so its foot stands on
	/// the ground; for <see cref="TelegraphTicks"/> ticks a small glowing bump and rising spores show where (the telegraph),
	/// then it shoots up (<see cref="GrowTicks"/>), hurts for <see cref="HurtTicks"/> ticks and sinks back. Expert damage
	/// (<see cref="Fungimancer.SpikeDamage"/>) set by the caster. ai[0] counts its ticks (every side the same). D0: finite life.
	/// </summary>
	public class ShroomSpike : CogpunkProjectile
	{
		public const int TelegraphTicks = 50, GrowTicks = 9, HurtTicks = 40, SinkTicks = 20;
		public const int Life = TelegraphTicks + HurtTicks + SinkTicks;
		public const int Frames = 4, FrameWidth = 28, FrameHeight = 36, Stride = 38;
		public const int Height = 36;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 22;
			Projectile.height = Height;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
		}

		private int Ticks => (int)Projectile.ai[0];

		public override bool CanHitPlayer(Player target) => Ticks >= TelegraphTicks + 2 && Ticks < TelegraphTicks + HurtTicks;

		public override void AI() {
			Projectile.ai[0]++;
			Projectile.velocity = Vector2.Zero;
			if (Main.dedServ) {
				return;
			}
			Vector2 foot = Projectile.Bottom;
			Lighting.AddLight(foot - new Vector2(0f, 8f), 0.1f, 0.25f, 0.6f);
			if (Ticks < TelegraphTicks && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(foot - new Vector2(10f, 4f), 20, 4, DustID.GlowingMushroom, out Dust d)) {
				d.noGravity = true;
				d.velocity = new Vector2(Main.rand.NextFloat(-0.4f, 0.4f), -Main.rand.NextFloat(0.5f, 1.6f));
			}
			if (Ticks == TelegraphTicks) {
				SoundEngine.PlaySound(SoundID.Item69 with { Pitch = 0.5f, Volume = 0.6f, MaxInstances = 5 }, foot);
				for (int i = 0; i < 10 && CogpunkClientConfig.RollEffect(); i++) {
					if (SafeSpawn.TryNewDust(foot - new Vector2(12f, 6f), 24, 6, DustID.GlowingMushroom, out Dust burst)) {
						burst.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), -Main.rand.NextFloat(1f, 4f));
						burst.noGravity = true;
					}
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			int t = Ticks;
			int frame;
			float opacity = 1f;
			if (t < TelegraphTicks) {
				frame = 0;
			}
			else if (t < TelegraphTicks + GrowTicks) {
				frame = 1 + Math.Min(2, (t - TelegraphTicks) * 3 / GrowTicks);
			}
			else if (t < TelegraphTicks + HurtTicks) {
				frame = 3;
			}
			else {
				float s = (t - TelegraphTicks - HurtTicks) / (float)SinkTicks;
				frame = Math.Clamp(3 - (int)(s * 3f), 0, 3);
				opacity = 1f - s;
			}
			Rectangle source = new(0, frame * Stride, FrameWidth, FrameHeight);
			Vector2 at = new(DepthLayers.Snap(Projectile.Bottom.X - Main.screenPosition.X - FrameWidth * 0.5f),
				DepthLayers.Snap(Projectile.Bottom.Y - Main.screenPosition.Y - FrameHeight));
			Color light = Color.Lerp(lightColor, Color.White, 0.5f) * opacity;
			Main.EntitySpriteDraw(tex, at, source, light, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}

	/// <summary>
	/// The Fungimancer's tongue (its Tongue attack): it lashes from the boss's mouth (ai[0]: the boss) along ai[2] (radians) at <see cref="OutSpeed"/> px a tick out to <see cref="Range"/> (or the first wall), holds
	/// <see cref="Hold"/> ticks and snaps back at <see cref="BackSpeed"/>. The whole tongue hurts, mouth to tip (a line
	/// <see cref="Width"/> px wide). Expert damage (<see cref="Fungimancer.TongueDamage"/>) set by the caster. The length is a
	/// function of its ticks (every side the same); a wall stops it the same everywhere. D0: the boss index checked, finite
	/// life, the wall scan bounded.
	/// </summary>
	public class FungimancerTongue : CogpunkProjectile
	{
		public const float Range = 24f * 16f, OutSpeed = 30f, BackSpeed = 36f, Width = 10f;
		public const int Hold = 4;
		public const int OutTicks = (int)(Range / OutSpeed) + 1, BackTicks = (int)(Range / BackSpeed) + 1;
		public const int Life = OutTicks + Hold + BackTicks;
		private const int TipSize = 14;

		private Vector2 Direction => Projectile.ai[2].ToRotationVector2();     // its heading, set by the caster

		public override void SetDefaults() {
			Projectile.width = 12;
			Projectile.height = 12;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
		}

		private bool TryBoss(out Fungimancer boss) {
			boss = null;
			int i = (int)Projectile.ai[0];
			if (i < 0 || i >= Main.maxNPCs || !Main.npc[i].active || Main.npc[i].ModNPC is not Fungimancer f) {
				return false;
			}
			boss = f;
			return true;
		}

		/// <summary>The tongue's reach at its tick, the wall's stop (ai[1], found while it goes out) taken in.</summary>
		private float Length() {
			int t = (int)Projectile.localAI[0];
			float stop = Projectile.ai[1] > 0f ? Projectile.ai[1] : Range;
			float length = t <= OutTicks ? t * OutSpeed : t <= OutTicks + Hold ? Range : Range - (t - OutTicks - Hold) * BackSpeed;
			return MathHelper.Clamp(length, 0f, stop);
		}

		public override void AI() {
			if (!TryBoss(out Fungimancer boss)) {
				Projectile.Kill();
				return;
			}
			Projectile.localAI[0]++;
			Vector2 mouth = boss.MouthWorld;
			if (Projectile.ai[1] <= 0f && Projectile.localAI[0] <= OutTicks) {
				float reach = Projectile.localAI[0] * OutSpeed;
				for (float d = Math.Max(0f, reach - OutSpeed); d <= reach; d += 8f) {   // at most 5 steps a tick (D0)
					Vector2 p = mouth + Direction * d;
					if (TileSafety.TryGetTile((int)(p.X / 16f), (int)(p.Y / 16f), out Tile tile) && tile.HasTile && !tile.IsActuated
						&& Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType]) {
						Projectile.ai[1] = Math.Max(16f, d);       // it slaps the wall and comes back
						break;
					}
				}
			}
			Projectile.velocity = Vector2.Zero;
			Projectile.Center = mouth + Direction * Length();
			if (Projectile.localAI[0] >= Life) {
				Projectile.Kill();
			}
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (!TryBoss(out Fungimancer boss)) {
				return false;
			}
			float point = 0f;
			return Collision.CheckAABBvLineCollision(targetHitbox.TopLeft(), targetHitbox.Size(), boss.MouthWorld, Projectile.Center, Width, ref point);
		}

		// The tongue: a pink band 4 px wide on the 2 px grid (a darker edge under it), from the mouth to the tip, and the tip.
		public override bool PreDraw(ref Color lightColor) {
			if (!TryBoss(out Fungimancer boss)) {
				return false;
			}
			Texture2D px = TextureAssets.MagicPixel.Value;
			Vector2 from = boss.MouthWorld, to = Projectile.Center;
			float length = Vector2.Distance(from, to);
			int steps = Math.Min(200, (int)(length / 2f));
			Color light = Lighting.GetColor((int)(from.X / 16f), (int)(from.Y / 16f));
			Color edge = new Color(132, 36, 44).MultiplyRGB(light), fill = new Color(236, 122, 88).MultiplyRGB(light);
			for (int i = 0; i <= steps; i++) {
				Vector2 p = Vector2.Lerp(from, to, steps == 0 ? 0f : i / (float)steps) - Main.screenPosition;
				int x = (int)DepthLayers.Snap(p.X), y = (int)DepthLayers.Snap(p.Y);
				Main.spriteBatch.Draw(px, new Rectangle(x - 2, y, 4, 2), edge);
				Main.spriteBatch.Draw(px, new Rectangle(x - 2, y - 2, 4, 2), fill);
			}
			Texture2D tip = TextureAssets.Projectile[Type].Value;
			Vector2 at = new(DepthLayers.Snap(to.X - Main.screenPosition.X - TipSize * 0.5f), DepthLayers.Snap(to.Y - Main.screenPosition.Y - TipSize * 0.5f));
			Main.EntitySpriteDraw(tip, at, null, Lighting.GetColor((int)(to.X / 16f), (int)(to.Y / 16f)), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
