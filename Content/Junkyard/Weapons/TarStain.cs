using System;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The stain a full-charge <see cref="TarShowerBigGlob"/> leaves (user-set 2026-10-30: "a big (6 tiles) tar stain on the
	/// ground that apply tar poisoning to enemies that touch it"): <see cref="WidthTiles"/> tiles of glossy tar on the
	/// ground for <see cref="Lifetime"/> ticks. Every enemy touching it gets the Tar Plague (10 every half second and half
	/// speed, <see cref="TarPlagueNPC"/>), topped up while it stands in it. It deals no damage of its own.
	/// <para>D2/D1: the owner's projectile; the owner's client applies the buff (vanilla syncs NPC buffs from <c>AddBuff</c>),
	/// checking every <see cref="CheckInterval"/> ticks and only when an enemy has less than <see cref="RefreshBelow"/> ticks
	/// of it left, so an enemy standing in it costs one buff packet a second at most. D0: at most
	/// <see cref="MaxPerPlayer"/> per player (the oldest gives way).</para>
	/// </summary>
	public class TarStain : CogpunkProjectile
	{
		public const int WidthTiles = 6;
		public const int HitboxWidth = WidthTiles * 16, HitboxHeight = 12;
		public const int Lifetime = 300;                    // 5 s (user-set 2026-11-04; it already was)
		public const int FadeTicks = 30;
		public const int PlagueTicks = 120;
		public const int CheckInterval = 10;
		public const int RefreshBelow = 60;
		public const int MaxPerPlayer = 4;
		public const int Frames = 4, TicksPerFrame = 9;
		private const int FrameWidth = 96, FrameHeight = 12, FrameStride = 14;

		/// <summary>Owner: lays a stain with its bottom on <paramref name="ground"/>, the oldest of this player's going first
		/// once <see cref="MaxPerPlayer"/> are down (a fixed loop over the projectiles, once per landing).</summary>
		public static void Spawn(Projectile glob, Vector2 ground) {
			int type = ModContent.ProjectileType<TarStain>();
			int count = 0;
			Projectile oldest = null;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == type && p.owner == glob.owner) {
					count++;
					if (oldest == null || p.timeLeft < oldest.timeLeft) {
						oldest = p;
					}
				}
			}
			if (count >= MaxPerPlayer) {
				oldest?.Kill();
			}
			SafeSpawn.TryNewProjectile(glob.GetSource_FromThis(), new Vector2(ground.X, ground.Y - HitboxHeight * 0.5f), Vector2.Zero, type, 0, 0f,
				out _, glob.owner);
		}

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = HitboxWidth;
			Projectile.height = HitboxHeight;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage() => false;

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			Projectile.Opacity = Projectile.timeLeft < FadeTicks ? Projectile.timeLeft / (float)FadeTicks : 1f;
			if (Projectile.owner != Main.myPlayer || Projectile.timeLeft % CheckInterval != 0 || Projectile.timeLeft < FadeTicks / 2) {
				return;
			}
			int plague = ModContent.BuffType<TarPlague>();
			Player owner = Main.player[Projectile.owner];
			Rectangle area = Projectile.Hitbox;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.friendly || npc.townNPC || npc.dontTakeDamage || npc.lifeMax <= 5 || !npc.Hitbox.Intersects(area)) {
					continue;
				}
				int index = npc.FindBuffIndex(plague);
				if (index < 0 || npc.buffTime[index] < RefreshBelow) {
					TarPlague.InflictOn(npc, owner, PlagueTicks);
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Frames - 1) * FrameStride, FrameWidth, FrameHeight);
			Vector2 bottom = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY + 2f);
			Vector2 position = new((int)(bottom.X - FrameWidth * 0.5f), (int)(bottom.Y - FrameHeight));
			Main.EntitySpriteDraw(texture, position, source, lightColor * Projectile.Opacity, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
