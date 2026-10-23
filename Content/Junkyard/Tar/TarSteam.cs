using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// A puff of steam rising off the tar (<see cref="TarSteamSystem"/>). It grows by switching between three hand-drawn
	/// sizes instead of being scaled (no mixels, D4 rule 1) and fades in code (D4 rule 9). Sheet: 2 variants (columns) x
	/// 3 growth stages (rows), 32x32 cells on a 34 px stride. Client only, like all dust.
	/// </summary>
	public class TarSteam : ModDust
	{
		public const int Variants = 2;
		public const int Stages = 3;
		public const int CellSize = 32;
		public const int CellStride = 34;
		public const int SpawnAlpha = 70;
		public const int FadePerTick = 2;             // alpha 70 -> 255 in about 93 ticks (1.5 s)
		public const float RiseAcceleration = 0.012f;
		public const float MaxRiseSpeed = 1.3f;
		private const float MaxOpacity = 0.85f;
		private static readonly int[] StageEnd = { 120, 190, 256 };   // alpha at which each growth stage ends

		public override void OnSpawn(Dust dust) {
			dust.alpha = SpawnAlpha;
			dust.noGravity = true;
			dust.noLight = true;
			dust.scale = 1f;
			dust.rotation = 0f;
			dust.frame = new Rectangle(Main.rand.Next(Variants) * CellStride, 0, CellSize, CellSize);
		}

		public override bool Update(Dust dust) {
			dust.position += dust.velocity;
			dust.velocity.X = dust.velocity.X * 0.97f + Main.windSpeedCurrent * 0.015f;
			dust.velocity.Y = Math.Max(dust.velocity.Y - RiseAcceleration, -MaxRiseSpeed);
			dust.alpha += FadePerTick;
			if (dust.alpha >= 255) {
				dust.active = false;
				return false;
			}
			int stage = 0;
			while (stage < Stages - 1 && dust.alpha >= StageEnd[stage]) {
				stage++;
			}
			dust.frame.Y = stage * CellStride;
			return false;
		}

		public override bool PreDraw(Dust dust) {
			float opacity = (255 - dust.alpha) / 255f * MaxOpacity;
			Point tile = dust.position.ToTileCoordinates();
			// Pale steam keeps a little of its own brightness so it still reads over the dark pool.
			Color light = Color.Lerp(Lighting.GetColor(tile.X, tile.Y), Color.White, 0.2f);
			Vector2 origin = new(CellSize * 0.5f, CellSize * 0.5f);
			Main.spriteBatch.Draw(Texture2D.Value, dust.position - Main.screenPosition, dust.frame, light * opacity, 0f, origin, 1f, SpriteEffects.None, 0f);
			return false;
		}
	}
}
