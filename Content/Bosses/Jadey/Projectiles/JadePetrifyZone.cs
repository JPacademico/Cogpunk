using System;
using Cogpunk.Content.Gems;
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
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Projectiles
{
	/// <summary>
	/// Jadey's petrify zone (user, 2026-11-16: "she should mark a 12 tile area on the ground and after 1.2 seconds petrify in jade
	/// any player on the area (like it has recieved 3 stacks of jade curse)"): a band of jade glyphs <see cref="WidthTiles"/>
	/// long laid along the ground under her target, brightening, motes rising up to its top (<see cref="HeightTiles"/> tiles:
	/// my call, how high "on the area" reaches: a jump clears it only at its peak), and after <see cref="SnapTick"/> ticks jade
	/// erupts from it: every player inside is turned to jade (<see cref="JadeCursePlayer.Petrify"/>: the ward of a recent
	/// petrification keeps it off, as a third stack would). It harms no one otherwise.
	/// <para><c>ai[0]</c> the band's left tile, <c>ai[1]</c> the ground's tile row (the band lies on top of it). D2: the snap is
	/// judged by each player's own client for its own player, at the same moment on every side (the projectile's synced age);
	/// the petrification rides vanilla's buff sync. D0: finite; nothing spawned but client dust. D1: no allocation.</para>
	/// </summary>
	public class JadePetrifyZone : CogpunkProjectile
	{
		public const int WidthTiles = 12;                       // user-set
		public const int HeightTiles = 5;                       // my call
		public const int SnapTick = 72;                         // user-set: 1.2 s
		public const int FadeTicks = 24;
		public const int Lifetime = SnapTick + FadeTicks;

		private int Age => Lifetime - Projectile.timeLeft;

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.tileCollide = false;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage() => false;

		/// <summary>The zone in the world: the band's tiles and the air over them up to <see cref="HeightTiles"/>.</summary>
		public Rectangle Area => new((int)Projectile.ai[0] * 16, ((int)Projectile.ai[1] - HeightTiles) * 16, WidthTiles * 16, HeightTiles * 16);

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			Rectangle area = Area;
			if (Age == SnapTick) {
				if (Main.netMode != NetmodeID.Server) {
					Player me = Main.LocalPlayer;
					if (me.active && !me.dead && me.Hitbox.Intersects(area)) {
						JadeCursePlayer.Petrify(me);
					}
				}
				if (!Main.dedServ) {
					Erupt(area);
				}
			}
			if (Main.dedServ) {
				return;
			}
			float strength = Age < SnapTick ? 0.3f + 0.7f * Age / SnapTick : 1f - (Age - SnapTick) / (float)FadeTicks;
			Lighting.AddLight(new Vector2(area.Center.X, area.Bottom - 8), 0.1f * strength, 0.5f * strength, 0.34f * strength);
			if (Age < SnapTick && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(new Vector2(area.X, area.Bottom - 6), area.Width, 6, DustID.GemEmerald, out Dust d)) {
				d.noGravity = true;
				d.velocity = new Vector2(0f, -HeightTiles * 16f / 40f);   // a mote climbs the zone's height in about 40 ticks
				d.scale = 0.9f;
			}
		}

		/// <summary>Clients, at the snap: jade shards burst up out of the band through the whole zone, with a crack.</summary>
		private static void Erupt(Rectangle area) {
			SoundEngine.PlaySound(SoundID.Item70 with { Pitch = 0.5f, Volume = 0.9f }, area.Center.ToVector2());
			SoundEngine.PlaySound(SoundID.Item27 with { Pitch = -0.4f }, area.Center.ToVector2());
			int n = CogpunkClientConfig.RollEffect() ? 40 : 10;
			for (int i = 0; i < n; i++) {
				if (SafeSpawn.TryNewDust(new Vector2(area.X, area.Bottom - 10), area.Width, 10, DustID.GemEmerald, out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-1f, 1f), Main.rand.NextFloat(-7f, -3f));
					d.noGravity = Main.rand.NextBool(3);
					d.scale = 1.3f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			const int w = 16, h = 8;
			if (tex.Height < JadeyRigData.PetrifyFrames * h) {
				return false;
			}
			float strength = Age < SnapTick ? 0.35f + 0.65f * Age / SnapTick : 1f - (Age - SnapTick) / (float)FadeTicks;
			bool blink = Age >= SnapTick - 18 && Age < SnapTick && (Age / 3) % 2 == 0;   // its last 0.3 s: it blinks (move!)
			Color c = new Color(255, 255, 255, 0) * MathHelper.Clamp(blink ? 1f : strength, 0f, 1f);
			Rectangle area = Area;
			int frame = (int)((Main.GameUpdateCount / 5) % JadeyRigData.PetrifyFrames);
			for (int k = 0; k < WidthTiles; k++) {
				Vector2 at = new Vector2(area.X + k * 16, area.Bottom - h) - Main.screenPosition;
				at = new Vector2(DepthLayers.Snap(at.X), DepthLayers.Snap(at.Y));
				Rectangle src = new(0, ((frame + k) % JadeyRigData.PetrifyFrames) * (h + 2), w, h);
				Main.EntitySpriteDraw(tex, at, src, c, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}
}
