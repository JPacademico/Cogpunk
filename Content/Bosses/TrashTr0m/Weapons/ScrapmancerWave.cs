using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// The Scrapmancer's junk shockwave: Trash-Tr0m's slam wave (<see cref="Projectiles.TrashTr0mShockwave"/>: same size,
	/// hitbox and terrain following) in friendly colours, a rolling mound of scrap with brass sparks and aether crackle.
	/// It climbs steps of up to <see cref="MaxStepUp"/> tiles and drops up to <see cref="MaxDrop"/>; a taller wall or a deeper
	/// pit breaks it. It pierces every enemy, each once (<c>localNPCHitCooldown = -1</c>), and knocks them away along its
	/// path.
	/// <para>D2: the path is deterministic on synced tiles, so every side moves it the same way; hits are the owner's. D0: at
	/// most MaxStepUp + MaxDrop + 1 bounds-checked reads per tick.</para>
	/// </summary>
	public class ScrapmancerWave : CogpunkProjectile
	{
		public const int HitboxWidth = Projectiles.TrashTr0mShockwave.HitboxWidth;
		public const int HitboxHeight = Projectiles.TrashTr0mShockwave.HitboxHeight;
		public const int Lifetime = 120;                  // 120 x 16 px/tick = 1920 px: a full screen
		public const int MaxStepUp = 3;
		public const int MaxDrop = 8;
		public const int Frames = 4;
		public const int TicksPerFrame = 4;
		private const int FrameWidth = 88, FrameHeight = 60, FrameStride = 62;

		private ref float Started => ref Projectile.localAI[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
		}

		public override void SetDefaults() {
			Projectile.width = HitboxWidth;
			Projectile.height = HitboxHeight;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;          // each enemy once per wave
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			int dir = Projectile.velocity.X >= 0f ? 1 : -1;
			Projectile.direction = Projectile.spriteDirection = dir;
			if (Started == 0f) {
				Started = 1f;
				if (!Main.dedServ) {
					SlamEffects();
				}
			}
			float front = Projectile.Center.X + dir * Projectile.width * 0.5f;
			if (!FindSurface(front, Projectile.Bottom.Y, out float ground)) {
				Projectile.Kill();                         // a wall or a pit: it breaks
				return;
			}
			Projectile.velocity.Y = ground - Projectile.Bottom.Y;
			if (++Projectile.frameCounter >= TicksPerFrame) {
				Projectile.frameCounter = 0;
				Projectile.frame = (Projectile.frame + 1) % Frames;
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				SafeSpawn.TryTileDust((int)(Projectile.Center.X / 16f) - dir, (int)(ground / 16f));
				if (Main.rand.NextBool(3) && SafeSpawn.TryNewDust(Projectile.position, Projectile.width, 8,
					Main.rand.NextBool(3) ? DustID.PurpleTorch : DustID.Enchanted_Gold, out Dust spark, 0f, -2f)) {
					spark.noGravity = true;
				}
			}
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			modifiers.HitDirectionOverride = Projectile.direction;   // thrown along the wave, not by which side it touched
		}

		private void SlamEffects() {
			SoundEngine.PlaySound(SoundID.DD2_OgreGroundPound with { Pitch = 0.2f, Volume = 0.7f }, Projectile.Bottom);
			if (Projectile.owner == Main.myPlayer && (CogpunkClientConfig.Instance?.ScreenShake ?? true)) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(Projectile.Bottom, Vector2.UnitY, 3f, 10f, 10, 800f, "Cogpunk:Scrapmancer"));
			}
			int tx = (int)(Projectile.Center.X / 16f);
			int ty = (int)(Projectile.Bottom.Y / 16f);
			for (int i = 0; i < 10; i++) {
				SafeSpawn.TryTileDust(tx + Main.rand.Next(-2, 3), ty);
			}
		}

		/// <summary>Top of the first solid surface under <paramref name="worldX"/> within the climb and drop window.</summary>
		private static bool FindSurface(float worldX, float bottom, out float ground) {
			int x = (int)(worldX / 16f);
			int row = (int)((bottom - 1f) / 16f) + 1;
			bool airAbove = !Solid(x, row - MaxStepUp - 1);
			for (int y = row - MaxStepUp; y <= row + MaxDrop; y++) {
				bool solid = Solid(x, y);
				if (solid && airAbove) {
					ground = y * 16f;
					return true;
				}
				airAbove = !solid;
			}
			ground = bottom;
			return false;
		}

		internal static bool Solid(int x, int y) {
			return TileSafety.TryGetTile(x, y, out Tile tile, 1) && tile.HasTile && !tile.IsActuated
				&& (Main.tileSolid[tile.TileType] || Main.tileSolidTop[tile.TileType]);
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 12; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, i % 3 == 0 ? DustID.Enchanted_Gold : DustID.Smoke,
					out Dust d, 0f, -2f, 80, default, 1.3f)) {
					d.velocity *= 1.4f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Projectile.frame * FrameStride, FrameWidth, FrameHeight);
			Vector2 bottom = Projectile.Bottom - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY + 2f);
			Vector2 position = new((int)(bottom.X - FrameWidth * 0.5f), (int)(bottom.Y - FrameHeight));
			// The art rolls to the left; mirror it for a wave running right.
			SpriteEffects effects = Projectile.spriteDirection == 1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Color color = Color.Lerp(lightColor, Color.White, 0.35f) * Projectile.Opacity;
			Main.EntitySpriteDraw(texture, position, source, color, 0f, Vector2.Zero, 1f, effects);
			return false;
		}
	}
}
