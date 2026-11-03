using System;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Rain.Projectiles
{
	/// <summary>
	/// A glob of water from the <see cref="NPCs.Splasher"/>'s gun: a lob aimed to land on the target (<see cref="AimAt"/>),
	/// bursting on the first tile or player and leaving them Wet (vanilla's harmless debuff, <see cref="WetTicks"/>).
	/// <para>Art: <see cref="Headings"/> pre-rendered headings (0 = flying right, clockwise), never rotated at runtime (D4);
	/// steam-white spray (hostile colours), the blue comes from vanilla's water dust trailing it. D0: a finite
	/// <c>timeLeft</c>; D1: a dust now and then on clients.</para>
	/// </summary>
	public class SplasherWater : CogpunkProjectile
	{
		public const float Gravity = 0.16f;
		public const int Headings = 16;
		public const int WetTicks = 180;
		private const int FrameSize = 20, FrameStride = 22;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Headings;
		}

		public override void SetDefaults() {
			Projectile.width = 10;
			Projectile.height = 10;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 120;
			Projectile.aiStyle = -1;
		}

		/// <summary>The launch velocity of a lob from <paramref name="from"/> that lands on <paramref name="to"/>: the flight
		/// time grows with distance (14-40 ticks), clamped so a far or high target gets the strongest shot (mid range).</summary>
		public static Vector2 AimAt(Vector2 from, Vector2 to) {
			Vector2 d = to - from;
			float time = MathHelper.Clamp(Math.Abs(d.X) / 9f, 14f, 40f);
			float vx = d.X / time;
			float vy = (d.Y - 0.5f * Gravity * time * time) / time;
			return new Vector2(MathHelper.Clamp(vx, -11f, 11f), MathHelper.Clamp(vy, -10f, 8f));
		}

		public override void AI() {
			Projectile.velocity.Y = Math.Min(Projectile.velocity.Y + Gravity, 12f);
			MathSafety.Sanitize(ref Projectile.velocity);
			int k = (int)MathF.Round(Projectile.velocity.ToRotation() / MathHelper.TwoPi * Headings);
			Projectile.frame = ((k % Headings) + Headings) % Headings;
			if (!Main.dedServ && Main.rand.NextBool(2)
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Water, out Dust d)) {
				d.velocity = Projectile.velocity * 0.2f;
				d.noGravity = false;
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(BuffID.Wet, WetTicks);
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item85 with { Pitch = 0.4f, Volume = 0.35f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 8; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Water, out _,
					Main.rand.NextFloat(-2f, 2f), -Main.rand.NextFloat(1f, 3f));
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Headings - 1) * FrameStride, FrameSize, FrameSize);
			Vector2 centre = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Vector2 position = new((int)(centre.X - FrameSize * 0.5f), (int)(centre.Y - FrameSize * 0.5f));
			Main.EntitySpriteDraw(texture, position, source, lightColor, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
