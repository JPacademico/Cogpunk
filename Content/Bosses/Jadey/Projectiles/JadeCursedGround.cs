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
	/// The curse Jadey's rope dart leaves where it bites (user, 2026-11-16: "leaves the 3 tiles where it landed cursed for 8
	/// seconds, if a player steps on a cursed tile it gives 1 stack of jade curse and cleanses the cursed spot"): a band of
	/// glowing jade cracks over the face of the three tiles it struck (the floor's top, a ceiling's underside or a wall's side:
	/// <c>ai[0]</c> 0..3, the struck tile in <c>ai[1]</c>, <c>ai[2]</c>), for <see cref="Lifetime"/> ticks. A player touching it
	/// takes one stack of the curse and the whole spot is gone.
	/// <para>D2: a touch is judged on the touching player's own client (it curses its own player and puts its copy out at once:
	/// the curse's stacks are that client's, <see cref="JadeCursePlayer"/>) and on the server by its own overlap test with every
	/// player (which puts the spot out for everyone a tick later, a synced kill): the Dragonete's pattern. D0: finite; the
	/// face's rectangle from the synced tile; no spawn. D1: one rectangle test per player a tick. D4: drawn from a pre-drawn
	/// band, turned only by exact quarter turns (lossless), on the 2 px grid, added onto the scene.</para>
	/// </summary>
	public class JadeCursedGround : CogpunkProjectile
	{
		public const int Lifetime = 480;                        // user-set: 8 s
		public const int Tiles = 3;                             // user-set
		private const int Band = 8;                             // px deep over the face
		private const int Touch = 2;                            // px the player's hitbox is grown by (standing on it touches it)

		private int Face => Math.Clamp((int)Projectile.ai[0], 0, 3);

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

		/// <summary>The cursed face's band in the world: three tiles along the struck face, <see cref="Band"/> px deep.</summary>
		public Rectangle Spot {
			get {
				int tx = (int)Projectile.ai[1], ty = (int)Projectile.ai[2];
				return Face switch {
					0 => new Rectangle((tx - 1) * 16, ty * 16 - Band + 2, Tiles * 16, Band),
					1 => new Rectangle((tx - 1) * 16, (ty + 1) * 16 - 2, Tiles * 16, Band),
					2 => new Rectangle(tx * 16 - Band + 2, (ty - 1) * 16, Band, Tiles * 16),
					_ => new Rectangle((tx + 1) * 16 - 2, (ty - 1) * 16, Band, Tiles * 16),
				};
			}
		}

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			Rectangle spot = Spot;
			if (Main.netMode != NetmodeID.Server) {
				Player me = Main.LocalPlayer;
				if (me.active && !me.dead && Touches(me, spot)) {
					JadeCursePlayer.Hit(me);
					Cleanse();
					return;
				}
			}
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				foreach (Player p in Main.ActivePlayers) {
					if (!p.dead && Touches(p, spot)) {
						Cleanse();
						return;
					}
				}
			}
			if (!Main.dedServ) {
				Lighting.AddLight(spot.Center.ToVector2(), 0.08f, 0.32f, 0.22f);
				if (Main.rand.NextBool(6) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(spot.TopLeft(), spot.Width, spot.Height, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity = Face switch { 0 => new Vector2(0f, -0.8f), 1 => new Vector2(0f, 0.8f), 2 => new Vector2(-0.8f, 0f), _ => new Vector2(0.8f, 0f) };
					d.scale = 0.8f;
				}
			}
		}

		private static bool Touches(Player p, Rectangle spot) {
			Rectangle box = p.Hitbox;
			box.Inflate(Touch, Touch);
			return box.Intersects(spot);
		}

		/// <summary>The spot is gone (here at once; the server's kill reaches every client).</summary>
		private void Cleanse() {
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item27 with { Pitch = 0.4f, Volume = 0.6f }, Spot.Center.ToVector2());
				int n = CogpunkClientConfig.RollEffect() ? 10 : 3;
				Rectangle spot = Spot;
				for (int i = 0; i < n; i++) {
					if (SafeSpawn.TryNewDust(spot.TopLeft(), spot.Width, spot.Height, DustID.GemEmerald, out Dust d)) {
						d.velocity = Main.rand.NextVector2Circular(2f, 2f);
						d.scale = 1.1f;
					}
				}
			}
			Projectile.Kill();
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			const int w = 48, h = 8;
			if (tex.Height < JadeyRigData.GroundFrames * h) {
				return false;
			}
			int frame = (int)((Main.GameUpdateCount / 6 + (uint)Projectile.whoAmI) % JadeyRigData.GroundFrames);
			Rectangle src = new(0, frame * (h + 2), w, h);
			float fade = Math.Min(1f, Projectile.timeLeft / 30f);
			Color c = new Color(255, 255, 255, 0) * fade;
			Rectangle spot = Spot;
			Vector2 centre = spot.Center.ToVector2() - Main.screenPosition;
			float rot = Face switch { 0 => 0f, 1 => MathHelper.Pi, 2 => -MathHelper.PiOver2, _ => MathHelper.PiOver2 };
			Vector2 at = new(DepthLayers.Snap(centre.X), DepthLayers.Snap(centre.Y));
			Main.EntitySpriteDraw(tex, at, src, c, rot, new Vector2(w / 2f, h / 2f), 1f, SpriteEffects.None);
			return false;
		}
	}
}
