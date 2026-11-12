using System;
using Cogpunk.Content.Underworld.NPCs;
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

namespace Cogpunk.Content.Underworld.Projectiles
{
	/// <summary>
	/// The Dragonete Miúdo's fire bolt (user-set 2026-11-11b: "spits fire bolts at a distance and if it misses it comes
	/// flying trying to bite the player"): a little fireball flying straight at where its target stood, flickering, burning
	/// out after <see cref="Lifetime"/> ticks or on the first wall. A hit may set the player on fire (<see cref="BurnChance"/>,
	/// <see cref="BurnTicks"/>: vanilla's On Fire!, doubled in Expert by vanilla, decompiled <c>Player.AddBuff</c>).
	/// <para>The miss: vanilla hurts a player with a hostile projectile on that player's own client (decompiled
	/// <c>Projectile.Damage</c>), and the projectile's hit hook runs there only (<c>PlayerLoader.OnHurt</c>: the local
	/// player), so the server judges it by its own overlap with any living player (<see cref="Touched"/>; the bolt goes out a
	/// tick later, so the player's client sees the hit first); in singleplayer the hit hook marks it. A bolt that dies
	/// untouched tells its dragonet (<c>ai[0]</c>, checked to be one) it missed (<see cref="DragoneteMiudo.BoltMissed"/>),
	/// on the server or in singleplayer only. The hit player's client puts its own copy out at once.</para>
	/// <para>D0/D1: finite life; no allocation; light, dust and sound on clients.</para>
	/// </summary>
	public class DragoneteFireBolt : CogpunkProjectile
	{
		public const int Lifetime = 90;
		public const int Frames = 4, FrameTicks = 4, FrameSize = 16, FrameStride = 18;
		public const float BurnChance = 0.5f;                       // my call
		public const int BurnTicks = 120;                           // 2 s in Classic, 4 s in Expert (vanilla's LongerExpertDebuff)

		private bool touched;                                       // the server's or the hit client's: it reached a player
		private int touchedAt = -1;

		/// <summary>True once it has reached a player (server: by overlap; singleplayer: by the hit).</summary>
		public bool Touched => touched;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = 12;
			Projectile.height = 12;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = false;
			Projectile.timeLeft = Lifetime;
			Projectile.penetrate = -1;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			Projectile.rotation = Projectile.velocity.ToRotation();
			if (++Projectile.frameCounter >= FrameTicks) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (Main.netMode == NetmodeID.Server) {
				if (touchedAt >= 0 && Projectile.timeLeft <= touchedAt - 1) {
					Projectile.Kill();                               // a tick after it reached a player
					return;
				}
				if (!touched) {
					Rectangle box = Projectile.Hitbox;
					box.Inflate(2, 2);
					foreach (Player player in Main.ActivePlayers) {
						if (!player.dead && box.Intersects(player.Hitbox)) {
							touched = true;
							touchedAt = Projectile.timeLeft;
							break;
						}
					}
				}
			}
			if (Main.dedServ) {
				return;
			}
			Lighting.AddLight(Projectile.Center, 0.9f, 0.45f, 0.1f);
			if (Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Torch, out Dust d)) {
				d.noGravity = true;
				d.velocity = -Projectile.velocity * 0.2f;
				d.scale = 1.2f;
			}
		}

		/// <summary>The hit player's client: it may burn, and this client's copy goes out at once (singleplayer: that is the
		/// bolt, and the hit counts as no miss).</summary>
		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			if (Main.rand.NextFloat() < BurnChance) {
				target.AddBuff(BuffID.OnFire, BurnTicks);
			}
			touched = true;
			Projectile.Kill();
		}

		/// <summary>Server or singleplayer: a bolt that dies untouched missed; its dragonet hears of it. Every client: a puff of
		/// flame.</summary>
		public override void OnKill(int timeLeft) {
			if (Main.netMode != NetmodeID.MultiplayerClient && !touched) {
				int parent = (int)Projectile.ai[0];
				if (parent >= 0 && parent < Main.maxNPCs && Main.npc[parent].active && Main.npc[parent].ModNPC is DragoneteMiudo dragonet) {
					dragonet.BoltMissed();
				}
			}
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item20 with { Volume = 0.5f, Pitch = 0.3f, MaxInstances = 4 }, Projectile.Center);
			for (int k = 0; k < 8 && CogpunkClientConfig.RollEffect(); k++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Torch, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(2.5f, 2.5f);
					d.scale = 1.4f;
				}
			}
		}

		/// <summary>Its frame at full brightness (it is fire), pointing the way it flies.</summary>
		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameSize, FrameSize);
			if (source.Bottom > tex.Height) {
				return false;
			}
			Main.EntitySpriteDraw(tex, Projectile.Center - Main.screenPosition, source, Color.White, Projectile.rotation,
				new Vector2(FrameSize / 2f), 1f, SpriteEffects.None);
			return false;
		}
	}
}
