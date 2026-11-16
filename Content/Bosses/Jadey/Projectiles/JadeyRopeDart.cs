using System;
using Cogpunk.Content.Gems;
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

namespace Cogpunk.Content.Bosses.Jadey.Projectiles
{
	/// <summary>
	/// Jadey's thrown whip, a jade rope dart (user, 2026-11-16: "she should quickly spin her jade whip for 0.4 seconds then throw
	/// it (fast speed, predicting player movement) into a player dealing high damage, it should proceed until hits a wall or
	/// floor which leaves the 3 tiles where it landed cursed for 8 seconds"): a jade blade on a crimson silk cord from her near
	/// paw. It flies straight at <see cref="Speed"/> through players (each hit: <see cref="Jadey.DartDamage"/> and a stack of
	/// the jade curse) until its tip meets a solid block; there it bites in, the three tiles along the face it struck are
	/// cursed (<see cref="JadeCursedGround"/>), and after <see cref="StuckTicks"/> she pulls it home (<see cref="ReturnTicks"/>).
	/// <para><c>ai[0]</c> Jadey's index, <c>ai[1]</c> the state (0 flying, 1 bitten in, 2 coming home), <c>ai[2]</c> ticks in the
	/// state. D2: the server spawns it with its velocity; every side moves it and tests the same tiles (deterministic), the
	/// server alone curses the ground; a hostile hit lands on the hit player's client (vanilla). D0: the tile walk is bounded
	/// and bounds-checked (<see cref="TileSafety"/>); a finite life; no master, no dart. D1: the cord is a loop of small
	/// unrotated links (at most <see cref="MaxLinks"/>), no allocation. D4: the blade is drawn from 16 pre-drawn headings.</para>
	/// </summary>
	public class JadeyRopeDart : CogpunkProjectile
	{
		public const float Speed = 20f;                         // px a tick (two updates of 10): "fast speed"
		public const int MaxFlyTicks = 70, StuckTicks = 24, ReturnTicks = 14;
		public const int MaxLinks = 200;
		private const float LinkStep = 4f, TipReach = 8f;

		private static Asset<Texture2D> cord;

		private int Master => (int)Projectile.ai[0];
		private ref float State => ref Projectile.ai[1];
		private ref float StateTime => ref Projectile.ai[2];
		private Vector2 stuckAt;

		public override void SetStaticDefaults() {
			cord = DepthLayers.RequestOptional(Texture + "_Cord");
		}

		public override void Unload() {
			cord = null;
		}

		public override void SetDefaults() {
			Projectile.width = 14;
			Projectile.height = 14;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.extraUpdates = 1;
			Projectile.timeLeft = 600;                          // updates (two a tick): 5 s at most
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		private Jadey Boss() {
			int m = Master;
			return m >= 0 && m < Main.maxNPCs && Main.npc[m].active && Main.npc[m].ModNPC is Jadey j ? j : null;
		}

		public override bool CanHitPlayer(Player target) => State == 0f;

		/// <summary>A stack of the jade curse on the hit player's own client (every attack of hers, user-set).</summary>
		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			JadeCursePlayer.Hit(target);
		}

		public override void AI() {
			Jadey boss = Boss();
			if (boss == null) {
				Projectile.Kill();
				return;
			}
			if (Projectile.localAI[0] == 0f && Projectile.velocity.LengthSquared() > 0.01f) {
				Projectile.localAI[0] = 1f + Heading(Projectile.velocity);   // the blade's heading, kept once it stops
			}
			StateTime += 0.5f;                                  // two updates a tick: the state's clock counts ticks
			switch ((int)State) {
				case 0:
					if (TipHit(out int tx, out int ty, out int face)) {
						Bite(tx, ty, face);
					}
					else if (StateTime >= MaxFlyTicks) {
						State = 2f;
						StateTime = 0f;
						stuckAt = Projectile.Center;
					}
					break;
				case 1:
					Projectile.velocity = Vector2.Zero;
					if (StateTime >= StuckTicks) {
						State = 2f;
						StateTime = 0f;
						stuckAt = Projectile.Center;
					}
					break;
				default:
					Projectile.velocity = Vector2.Zero;
					float t = Math.Min(1f, StateTime / ReturnTicks);
					if (stuckAt == Vector2.Zero) {
						stuckAt = Projectile.Center;
					}
					Projectile.Center = Vector2.Lerp(stuckAt, boss.NearPawWorld, t * t);
					if (t >= 1f) {
						Projectile.Kill();
					}
					break;
			}
			if (!Main.dedServ && State == 0f) {
				Lighting.AddLight(Projectile.Center, 0.12f, 0.5f, 0.34f);
			}
		}

		/// <summary>The tip's tile, if it is solid (bounds-checked), and which face it came in through: 0 the top (a floor), 1
		/// the bottom (a ceiling), 2 the left side, 3 the right side (walls).</summary>
		private bool TipHit(out int tx, out int ty, out int face) {
			Vector2 dir = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			Vector2 tip = Projectile.Center + dir * TipReach;
			tx = (int)(tip.X / 16f);
			ty = (int)(tip.Y / 16f);
			face = 0;
			if (!TileSafety.TryGetTile(tx, ty, out Tile tile) || !tile.HasTile || tile.IsActuated || !Main.tileSolid[tile.TileType]
				|| Main.tileSolidTop[tile.TileType]) {
				return false;
			}
			Vector2 prev = tip - Projectile.velocity;
			int px = (int)(prev.X / 16f), py = (int)(prev.Y / 16f);
			bool side = px != tx && (py == ty || Math.Abs(Projectile.velocity.X) > Math.Abs(Projectile.velocity.Y));
			face = side ? (px < tx ? 2 : 3) : (py < ty ? 0 : 1);
			return true;
		}

		/// <summary>It bites in where it struck; the server curses the three tiles along that face.</summary>
		private void Bite(int tx, int ty, int face) {
			State = 1f;
			StateTime = 0f;
			Projectile.velocity = Vector2.Zero;
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				Vector2 at = new(tx * 16f + 8f, ty * 16f + 8f);
				SafeSpawn.TryNewProjectile(Projectile.GetSource_FromThis(), at, Vector2.Zero, ModContent.ProjectileType<JadeCursedGround>(), 0, 0f,
					out _, ai0: face, ai1: tx, ai2: ty);
				Projectile.netUpdate = true;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item27 with { Pitch = -0.3f, Volume = 0.9f }, Projectile.Center);
				SoundEngine.PlaySound(SoundID.Dig with { Pitch = 0.2f, Volume = 0.6f }, Projectile.Center);
				int n = CogpunkClientConfig.RollEffect() ? 12 : 4;
				for (int i = 0; i < n; i++) {
					if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(6f), 12, 12, i % 2 == 0 ? DustID.GemEmerald : DustID.Stone, out Dust d)) {
						d.velocity = Main.rand.NextVector2Circular(3f, 3f);
						d.noGravity = i % 2 == 0;
					}
				}
			}
		}

		/// <summary>The heading index (0..15, 22.5 degrees apart, 0 = right, clockwise on screen) of a velocity.</summary>
		public static int Heading(Vector2 v) {
			int k = (int)MathF.Round(MathF.Atan2(v.Y, v.X) / (MathHelper.TwoPi / JadeyRigData.DartHeadings));
			return ((k % JadeyRigData.DartHeadings) + JadeyRigData.DartHeadings) % JadeyRigData.DartHeadings;
		}

		public override bool PreDraw(ref Color lightColor) {
			Jadey boss = Boss();
			if (boss != null) {
				DrawCord(boss.NearPawWorld, Projectile.Center, lightColor);
			}
			DrawBlade(Projectile.Center, (int)Projectile.localAI[0] - 1, lightColor);
			return false;
		}

		/// <summary>The crimson cord from <paramref name="from"/> to <paramref name="to"/>: a link every few px on the 2 px grid,
		/// sagging a little (a shallow curve), at most <see cref="MaxLinks"/>.</summary>
		public static void DrawCord(Vector2 from, Vector2 to, Color light) {
			if (cord?.IsLoaded != true) {
				return;
			}
			float length = Vector2.Distance(from, to);
			int links = Math.Min(MaxLinks, (int)(length / LinkStep));
			float sag = Math.Min(10f, length * 0.04f);
			for (int i = 1; i < links; i++) {
				float t = i / (float)links;
				Vector2 p = Vector2.Lerp(from, to, t) + new Vector2(0f, sag * 4f * t * (1f - t)) - Main.screenPosition;
				p = new Vector2(DepthLayers.Snap(p.X), DepthLayers.Snap(p.Y));
				Main.EntitySpriteDraw(cord.Value, p, null, light, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
		}

		/// <summary>The jade blade at <paramref name="center"/>, its heading one of 16 pre-drawn (D4: never rotated).</summary>
		public static void DrawBlade(Vector2 center, int heading, Color light) {
			Texture2D tex = TextureAssets.Projectile[ModContent.ProjectileType<JadeyRopeDart>()].Value;
			int cell = JadeyRigData.DartCell;
			if (tex.Height < JadeyRigData.DartHeadings * cell) {
				return;
			}
			heading = Math.Clamp(heading, 0, JadeyRigData.DartHeadings - 1);
			Rectangle src = new(0, heading * (cell + 2), cell, cell);
			Vector2 at = center - Main.screenPosition - new Vector2(cell * 0.5f);
			at = new Vector2(DepthLayers.Snap(at.X), DepthLayers.Snap(at.Y));
			Main.EntitySpriteDraw(tex, at, src, Color.Lerp(light, Color.White, 0.5f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
		}
	}
}
