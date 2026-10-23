using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// Makes the Junkyard's tar steam "from time to time": every <see cref="SampleInterval"/> ticks a few random on-screen
	/// columns inside the Junkyard are probed for a liquid surface (the tar pool and the puddles between the heaps), and a
	/// hit lets off a wisp of <see cref="TarSteam"/>; now and then one becomes a plume with a bubble popping under it.
	/// <para>Only while the local player is in the Junkyard, i.e. while <see cref="TarWaterStyle"/> is what the water looks
	/// like. Client-only visuals (D1/D2): nothing runs on a dedicated server or while paused. Cost: at most
	/// <see cref="SamplesPerInterval"/> x <see cref="ScanLimit"/> tile reads every <see cref="SampleInterval"/> ticks,
	/// allocation-free. Particle count follows the Effect Density setting.</para>
	/// </summary>
	public sealed class TarSteamSystem : ModSystem
	{
		public const int SampleInterval = 5;
		public const int SamplesPerInterval = 2;
		public const int ScanLimit = 90;               // rows probed per column (a 1080p screen is about 68 rows)
		public const int PlumeOneIn = 7;               // one surface hit in N becomes a plume
		public const int PlumePuffs = 5;
		private const int ScreenMargin = 2;

		private static int timer;

		public override void OnWorldUnload() {
			timer = 0;
		}

		public override void PostUpdateDusts() {
			if (Main.dedServ || Main.gamePaused || !JunkyardSystem.Exists || ++timer < SampleInterval) {
				return;
			}
			timer = 0;
			Player player = Main.LocalPlayer;
			if (player == null || !player.active || !JunkyardSystem.Contains(player.Center)) {
				return;
			}
			if (!VisibleJunkyardColumns(out int x0, out int x1, out int y0, out int y1)) {
				return;
			}
			for (int n = 0; n < SamplesPerInterval; n++) {
				int x = Main.rand.Next(x0, x1 + 1);
				if (FindSurface(x, y0, y1, out float surfaceY)) {
					EmitSteam(x, surfaceY);
				}
			}
		}

		/// <summary>The on-screen tile window clipped to the Junkyard's bounding box.</summary>
		private static bool VisibleJunkyardColumns(out int x0, out int x1, out int y0, out int y1) {
			Rectangle bounds = Rectangle.Union(JunkyardSystem.SurfaceArea, JunkyardSystem.PoolArea);
			x0 = Math.Max(bounds.Left, (int)(Main.screenPosition.X / 16f) - ScreenMargin);
			x1 = Math.Min(bounds.Right - 1, (int)((Main.screenPosition.X + Main.screenWidth) / 16f) + ScreenMargin);
			y0 = Math.Max(bounds.Top, (int)(Main.screenPosition.Y / 16f) - ScreenMargin);
			y1 = Math.Min(bounds.Bottom - 1, (int)((Main.screenPosition.Y + Main.screenHeight) / 16f) + ScreenMargin);
			return x0 <= x1 && y0 <= y1;
		}

		/// <summary>First water tile from the top with open air above it; <paramref name="surfaceY"/> is the liquid's top edge in world pixels.</summary>
		private static bool FindSurface(int x, int y0, int y1, out float surfaceY) {
			surfaceY = 0f;
			int end = Math.Min(y1, y0 + ScanLimit);
			for (int y = Math.Max(y0, 1); y <= end; y++) {
				if (!TileSafety.TryGetTile(x, y, out Tile tile)) {
					return false;
				}
				if (tile.LiquidAmount == 0) {
					continue;
				}
				if (tile.LiquidType != LiquidID.Water) {
					return false;
				}
				Tile above = Main.tile[x, y - 1];
				if (above.LiquidAmount > 0 || (above.HasTile && Main.tileSolid[above.TileType] && !Main.tileSolidTop[above.TileType])) {
					return false;                        // under a ledge: steam would rise into the block
				}
				surfaceY = y * 16f + (255 - tile.LiquidAmount) / 16f;
				return true;
			}
			return false;
		}

		private static void EmitSteam(int x, float surfaceY) {
			bool plume = Main.rand.NextBool(PlumeOneIn);
			int puffs = plume ? PlumePuffs : 1;
			for (int i = 0; i < puffs; i++) {
				if (!CogpunkClientConfig.RollEffect()) {
					continue;
				}
				Vector2 at = new(x * 16f + Main.rand.NextFloat(16f), surfaceY - 4f - i * 6f);
				if (SafeSpawn.TryNewDust(at, 0, 0, ModContent.DustType<TarSteam>(), out Dust puff)) {
					puff.position = at;
					puff.velocity = new Vector2(Main.rand.NextFloat(-0.25f, 0.25f), plume ? -Main.rand.NextFloat(0.6f, 1.1f) : -Main.rand.NextFloat(0.2f, 0.5f));
				}
			}
			if (!plume) {
				return;
			}
			// The bubble that let the plume out: a few tar droplets thrown up from the surface, and a soft blub.
			for (int i = 0; i < 4; i++) {
				if (SafeSpawn.TryNewDust(new Vector2(x * 16f + 4f, surfaceY - 2f), 8, 2, ModContent.DustType<TarSplash>(), out Dust drop)) {
					drop.velocity = new Vector2(Main.rand.NextFloat(-1f, 1f), -Main.rand.NextFloat(1.5f, 3f));
				}
			}
			if (Main.rand.NextBool(3)) {
				SoundEngine.PlaySound(SoundID.Drip with { Pitch = -0.7f, Volume = 0.5f, MaxInstances = 2 }, new Vector2(x * 16f + 8f, surfaceY));
			}
		}
	}
}
