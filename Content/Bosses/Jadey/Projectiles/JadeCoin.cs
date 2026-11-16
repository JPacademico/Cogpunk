using System;
using Cogpunk.Content.Bosses.Jadey.NPCs;
using Cogpunk.Content.Coghaven.NPCs;
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
	/// Jadey's jade coin (user, 2026-11-16: "Jadey should quickly throw a jade coin every 4 seconds during the fight, this jade
	/// coin should spawn at random a jade golem, or 2 jade bats or jade beetle (...) were it lands after 0.5 seconds"): flicked
	/// from her far paw in a short arc, spinning; where it lands it stands glowing for <see cref="HatchTicks"/> ticks (0.5 s,
	/// the telegraph: a jade light rising, its colour telling what comes: a tall pillar for the Golem, two motes for the bats,
	/// a low glow for the beetle), then bursts into its minion(s), made hers (<see cref="JadeyMinion"/>). Harmless itself.
	/// <para><c>ai[0]</c>: what it hatches (<see cref="Kind"/>, rolled by the server at the throw, so every side shows the same
	/// telegraph); <c>ai[1]</c>: Jadey's index; <c>ai[2]</c>: ticks since it landed (0: still flying). D2: the server's; every
	/// side runs the same arc and the same landing (vanilla tile collision), and the server kills it and makes the minions
	/// (<see cref="SafeSpawn"/>, refused rather than overflow). D0: a finite life (<see cref="MaxTicks"/>); no master, no
	/// minion. D1: no allocation; dust and sound on clients.</para>
	/// </summary>
	public class JadeCoin : CogpunkProjectile
	{
		public enum Kind { Golem, Bats, Beetle }

		public const int HatchTicks = 30;                       // user-set: 0.5 s after it lands
		public const int MaxTicks = 300;
		public const float Gravity = 0.3f, MaxFall = 12f;
		public const int FrameTicks = 3;

		private static Asset<Texture2D> glow;

		private Kind Hatches => (Kind)Math.Clamp((int)Projectile.ai[0], 0, 2);
		private ref float Landed => ref Projectile.ai[2];

		public override void SetStaticDefaults() {
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 12;
			Projectile.height = 12;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = MaxTicks;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage() => false;

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Landed <= 0f && oldVelocity.Y > 0f && Projectile.velocity.Y == 0f) {
				Landed = 1f;                                       // on the ground: it stands and glows
				Projectile.velocity = Vector2.Zero;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item27 with { Pitch = 0.6f, Volume = 0.5f }, Projectile.Center);
				}
			}
			else if (Projectile.velocity.X != oldVelocity.X) {
				Projectile.velocity.X = -oldVelocity.X * 0.4f;     // off a wall
			}
			return false;
		}

		public override void AI() {
			if (Landed > 0f) {
				Projectile.velocity = Vector2.Zero;
				Landed++;
				if (Main.netMode != NetmodeID.MultiplayerClient && Landed >= HatchTicks + 1) {
					Projectile.Kill();
					return;
				}
			}
			else {
				Projectile.velocity.Y = Math.Min(MaxFall, Projectile.velocity.Y + Gravity);
				Projectile.velocity.X *= 0.995f;
			}
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.1f, 0.45f, 0.3f);
				if (Landed > 0f && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()) {
					float height = Hatches == Kind.Golem ? 3.2f : Hatches == Kind.Bats ? 2.2f : 1.2f;
					if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f, 6f), 8, 6, DustID.GemEmerald, out Dust d)) {
						d.noGravity = true;
						d.velocity = new Vector2(Main.rand.NextFloat(-0.3f, 0.3f), -height);
						d.scale = 0.9f;
					}
				}
			}
		}

		/// <summary>The server: the coin bursts into what it hatches, made Jadey's (the spawn source names this coin:
		/// <see cref="JadeyMinion.OnSpawn"/>). Every side: a burst of jade.</summary>
		public override void OnKill(int timeLeft) {
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item29 with { Pitch = -0.2f, Volume = 0.7f }, Projectile.Center);
				int n = CogpunkClientConfig.RollEffect() ? 14 : 4;
				for (int i = 0; i < n; i++) {
					if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(8f), 16, 16, DustID.GemEmerald, out Dust d)) {
						d.velocity = Main.rand.NextVector2Circular(3f, 3f) - Vector2.UnitY;
						d.noGravity = Main.rand.NextBool();
						d.scale = 1.2f;
					}
				}
			}
			if (Main.netMode == NetmodeID.MultiplayerClient || Landed < HatchTicks) {
				return;                                             // a coin that never landed (its time ran out) hatches nothing
			}
			int m = (int)Projectile.ai[1];
			if (m < 0 || m >= Main.maxNPCs || !Main.npc[m].active || Main.npc[m].type != ModContent.NPCType<Jadey>()) {
				return;
			}
			int x = (int)Projectile.Center.X, bottom = (int)Projectile.Bottom.Y;
			var source = Projectile.GetSource_FromThis();
			switch (Hatches) {
				case Kind.Golem:
					SafeSpawn.TryNewNPC(source, x, bottom, ModContent.NPCType<JadeGolem>(), out _);
					break;
				case Kind.Bats:
					SafeSpawn.TryNewNPC(source, x - 14, bottom - 24, ModContent.NPCType<JadeBat>(), out _);
					SafeSpawn.TryNewNPC(source, x + 14, bottom - 30, ModContent.NPCType<JadeBat>(), out _);
					break;
				default:
					SafeSpawn.TryNewNPC(source, x, bottom, ModContent.NPCType<JadeBeetle>(), out _);
					break;
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			int cell = JadeyRigData.CoinCell;
			if (tex.Height < JadeyRigData.CoinFrames * cell) {
				return false;
			}
			int frame = Landed > 0f ? 0 : (int)((Main.GameUpdateCount / FrameTicks + (uint)Projectile.whoAmI) % JadeyRigData.CoinFrames);
			Rectangle src = new(0, frame * (cell + 2), cell, cell);
			Vector2 at = Projectile.Center - Main.screenPosition - new Vector2(cell * 0.5f);
			at = new Vector2(DepthLayers.Snap(at.X), DepthLayers.Snap(at.Y));
			Main.EntitySpriteDraw(tex, at, src, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true) {
				float pulse = Landed > 0f ? 0.6f + 0.4f * MathF.Sin(Landed * 0.4f) : 0.7f;
				Main.EntitySpriteDraw(glow.Value, at, src, new Color(255, 255, 255, 0) * pulse, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}
}
