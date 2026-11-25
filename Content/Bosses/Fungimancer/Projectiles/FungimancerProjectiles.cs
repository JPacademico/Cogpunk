using System;
using Cogpunk.Content.Bosses.Fungimancer.Polymorph;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Fungimancer.Projectiles
{
	/// <summary>The fight's rainbow, in the palette (art/bosses/fungimancer/fungimancer_fight.py SPECTRUM), for drawn effects.</summary>
	public static class Spectrum
	{
		public static readonly Color[] Colors = {
			new(206, 74, 56), new(236, 113, 40), new(255, 199, 90), new(196, 246, 48), new(78, 212, 106), new(67, 221, 248),
			new(124, 107, 224), new(228, 112, 230),
		};

		public static Color At(int i) => Colors[((i % Colors.Length) + Colors.Length) % Colors.Length];
	}

	/// <summary>
	/// A rainbow spore, the Fungimancer's delayed spells (user, 2026-11-25): "creates 5 small rainbow spore projectiles that stay
	/// in the air for 1.2 second then quickly fire in sequence at the targeted enemy dealing heavy damage and cause confusion"
	/// and "a delayed spell that stays in the air for 1.5 seconds and after that fires a fan burst of 6 quick rainbow spore
	/// projectiles". It hangs where it was conjured (harmless) until its age reaches <c>ai[0]</c>, then flies at its target
	/// (<c>ai[1]</c>, a player) turned by <c>ai[2]</c> radians (0 for the aimed volley, the fan's spread for the fan) at
	/// <see cref="Speed"/>; it hurts and confuses only in flight, and a block stops it.
	/// <para>D2: the server spawns it; every side counts its age from its fixed lifetime and fires it on the same tick; the
	/// server's velocity is sent as it fires (netUpdate). D0: the target index is range-checked; a lost target means straight on.</para>
	/// </summary>
	public class RainbowSpore : CogpunkProjectile
	{
		public const int Life = 420, Frames = 6, ConfusionTicks = 120;
		public const float Speed = 13f;

		private int Age => Life - Projectile.timeLeft;
		private bool Fired => Age >= Projectile.ai[0];

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
			ProjectileID.Sets.TrailCacheLength[Type] = 6;
			ProjectileID.Sets.TrailingMode[Type] = 0;
		}

		public override void SetDefaults() {
			Projectile.width = 14;
			Projectile.height = 14;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = 1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			if (!Fired) {
				Projectile.velocity *= 0.88f;
				Projectile.position.Y += MathF.Sin((Age + Projectile.whoAmI * 13) * 0.12f) * 0.25f;   // it bobs while it waits
			}
			else if (Age == (int)Projectile.ai[0]) {
				int t = (int)Projectile.ai[1];
				Vector2 aim = t >= 0 && t < Main.maxPlayers && Main.player[t].active && !Main.player[t].dead
					? (Main.player[t].Center - Projectile.Center).SafeNormalize(Vector2.UnitY) : Projectile.velocity.SafeNormalize(Vector2.UnitY);
				Projectile.velocity = aim.RotatedBy(Projectile.ai[2]) * Speed;
				Projectile.tileCollide = true;
				if (Main.netMode == NetmodeID.Server) {
					Projectile.netUpdate = true;
				}
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item9 with { Pitch = 0.5f, Volume = 0.6f, MaxInstances = 6 }, Projectile.Center);
				}
			}
			if (Fired) {
				Projectile.tileCollide = true;
			}
			Projectile.frame = (int)(Main.GameUpdateCount / 4 + (uint)Projectile.whoAmI) % Frames;
			if (!Main.dedServ) {
				Color c = Spectrum.At((int)(Main.GameUpdateCount / 4) + Projectile.whoAmI);
				Lighting.AddLight(Projectile.Center, c.ToVector3() * 0.4f);
				if (Main.rand.NextBool(Fired ? 2 : 6) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(3f), 6, 6, DustID.RainbowMk2, out Dust d, 0f, 0f, 0, c, 0.8f)) {
					d.noGravity = true;
					d.velocity = -Projectile.velocity * 0.15f;
				}
			}
		}

		public override bool CanHitPlayer(Player target) => Fired;

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(BuffID.Confused, ConfusionTicks);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			int fh = tex.Height / Frames;
			Rectangle src = new(0, Projectile.frame * fh, tex.Width, fh - 2);
			Vector2 origin = new(tex.Width * 0.5f, (fh - 2) * 0.5f);
			if (Fired) {
				for (int k = Projectile.oldPos.Length - 1; k > 0; k--) {   // a fading trail of itself (alpha-0: added light)
					Vector2 at = Projectile.oldPos[k] + Projectile.Size * 0.5f - Main.screenPosition;
					Color c = Spectrum.At(k + (int)(Main.GameUpdateCount / 4)) * (0.5f * (1f - k / (float)Projectile.oldPos.Length));
					Main.EntitySpriteDraw(tex, at.Floor(), src, c with { A = 0 }, 0f, origin, 1f, SpriteEffects.None);
				}
			}
			Main.EntitySpriteDraw(tex, (Projectile.Center - Main.screenPosition).Floor(), src, Color.White, 0f, origin, 1f, SpriteEffects.None);
			return false;
		}
	}

	/// <summary>
	/// The mushroom missile (user, 2026-11-25: "he shakes his hand does a delayed spell that stays in the air for 1.3 seconds and
	/// the fire a quick mushroom missile that bounces up to 3 times and deals heavy damage"): it hangs at the hand turning to
	/// follow its target (<c>ai[1]</c>: the telegraph of where it will go) until its age reaches <c>ai[0]</c>, then shoots at
	/// <see cref="Speed"/>, bounces off blocks <see cref="MaxBounces"/> times (<c>ai[2]</c> counts them) and breaks on the next.
	/// Drawn from 16 pre-rendered headings (never rotated at runtime, D4 rule 14).
	/// </summary>
	public class MushroomMissile : CogpunkProjectile
	{
		public const int Life = 360, MaxBounces = 3, Headings = 16, Cell = 32, Stride = 34;
		public const float Speed = 12f;

		private int Age => Life - Projectile.timeLeft;
		private bool Fired => Age >= Projectile.ai[0];

		public override void SetDefaults() {
			Projectile.width = 20;
			Projectile.height = 20;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		private Player Target {
			get {
				int t = (int)Projectile.ai[1];
				return t >= 0 && t < Main.maxPlayers && Main.player[t].active && !Main.player[t].dead ? Main.player[t] : null;
			}
		}

		public override void AI() {
			if (!Fired) {
				Projectile.velocity *= 0.85f;
				Player t = Target;
				if (t != null) {
					Projectile.localAI[1] = (t.Center - Projectile.Center).ToRotation();   // where it points while it waits
				}
				if (!Main.dedServ && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(8f), 16, 16, DustID.PurpleTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(1.2f, 1.2f);
				}
				return;
			}
			if (Age == (int)Projectile.ai[0]) {
				Player t = Target;
				Vector2 aim = t != null ? (t.Center - Projectile.Center).SafeNormalize(Vector2.UnitX) : Projectile.localAI[1].ToRotationVector2();
				Projectile.velocity = aim * Speed;
				Projectile.tileCollide = true;
				if (Main.netMode == NetmodeID.Server) {
					Projectile.netUpdate = true;
				}
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item61 with { Pitch = 0.3f, Volume = 0.8f }, Projectile.Center);
				}
			}
			Projectile.tileCollide = true;
			Projectile.localAI[1] = Projectile.velocity.ToRotation();
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.PurpleTorch, out Dust trail)) {
				trail.noGravity = true;
				trail.velocity = -Projectile.velocity * 0.2f;
			}
		}

		public override bool CanHitPlayer(Player target) => Fired;

		public override bool OnTileCollide(Vector2 oldVelocity) {
			Projectile.ai[2]++;
			if (Projectile.ai[2] > MaxBounces) {
				return true;                                         // the fourth wall it meets breaks it
			}
			if (Projectile.velocity.X != oldVelocity.X) {
				Projectile.velocity.X = -oldVelocity.X;
			}
			if (Projectile.velocity.Y != oldVelocity.Y) {
				Projectile.velocity.Y = -oldVelocity.Y;
			}
			if (Main.netMode == NetmodeID.Server) {
				Projectile.netUpdate = true;
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item56 with { Pitch = 0.4f, Volume = 0.7f }, Projectile.Center);
			}
			return false;
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCDeath1 with { Pitch = 0.5f, Volume = 0.6f }, Projectile.Center);
			for (int i = 0; i < 12; i++) {
				SafeSpawn.TryNewDust(Projectile.Center - new Vector2(8f), 16, 16, DustID.PurpleTorch, out _);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			float angle = Projectile.localAI[1];
			int heading = (int)MathF.Round(angle / MathHelper.TwoPi * Headings);
			heading = ((heading % Headings) + Headings) % Headings;
			Rectangle src = new(heading * Stride, 0, Cell, Cell);
			Vector2 at = Projectile.Center - Main.screenPosition - new Vector2(Cell * 0.5f);
			at = new Vector2(MathF.Round(at.X / 2f) * 2f, MathF.Round(at.Y / 2f) * 2f);
			Main.EntitySpriteDraw(tex, at, src, Color.Lerp(lightColor, Color.White, 0.6f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}

	/// <summary>
	/// The burp (user, 2026-11-25: "he quickly burps a pink accelerating homming (not heavy homing so its undodgeable, its
	/// suposed to be hard to dodge only) projectile that polymorphs the player hit into a toadstool for 2.5 seconds"): it leaves
	/// slowly (<see cref="StartSpeed"/>) and speeds up to <see cref="MaxSpeed"/>, turning towards its target (<c>ai[0]</c>) at
	/// most <see cref="Turn"/> a tick (a dash or a sharp turn beats it), through blocks; its hit polymorphs
	/// (<see cref="Polymorphed"/>, <see cref="PolymorphTicks"/>).
	/// </summary>
	public class PolymorphBolt : CogpunkProjectile
	{
		public const int Life = 240, Frames = 4, PolymorphTicks = 150;
		public const float StartSpeed = 3.5f, Accel = 0.18f, MaxSpeed = 13f, Turn = 0.028f;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Frames;
			ProjectileID.Sets.TrailCacheLength[Type] = 8;
			ProjectileID.Sets.TrailingMode[Type] = 0;
		}

		public override void SetDefaults() {
			Projectile.width = 18;
			Projectile.height = 18;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = 1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			int t = (int)Projectile.ai[0];
			Vector2 dir = Projectile.velocity.SafeNormalize(Vector2.UnitX);
			if (t >= 0 && t < Main.maxPlayers && Main.player[t].active && !Main.player[t].dead) {
				Vector2 want = (Main.player[t].Center - Projectile.Center).SafeNormalize(dir);
				float turn = MathHelper.WrapAngle(want.ToRotation() - dir.ToRotation());
				dir = dir.RotatedBy(MathHelper.Clamp(turn, -Turn, Turn));
			}
			float speed = Math.Min(MaxSpeed, Math.Max(StartSpeed, Projectile.velocity.Length()) + Accel);
			Projectile.velocity = dir * speed;
			Projectile.frame = (int)(Main.GameUpdateCount / 5) % Frames;
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.5f, 0.15f, 0.45f);
				if (Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(5f), 10, 10, DustID.PinkTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = -Projectile.velocity * 0.2f;
				}
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(ModContent.BuffType<Polymorphed>(), PolymorphTicks);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			int fh = tex.Height / Frames;
			Rectangle src = new(0, Projectile.frame * fh, tex.Width, fh - 2);
			Vector2 origin = new(tex.Width * 0.5f, (fh - 2) * 0.5f);
			for (int k = Projectile.oldPos.Length - 1; k > 0; k--) {
				Vector2 at = Projectile.oldPos[k] + Projectile.Size * 0.5f - Main.screenPosition;
				Main.EntitySpriteDraw(tex, at.Floor(), src, new Color(255, 120, 230, 0) * (0.45f * (1f - k / (float)Projectile.oldPos.Length)),
					0f, origin, 1f, SpriteEffects.None);
			}
			Main.EntitySpriteDraw(tex, (Projectile.Center - Main.screenPosition).Floor(), src, Color.White, 0f, origin, 1f, SpriteEffects.None);
			return false;
		}
	}

	/// <summary>
	/// The rainbow laser (user, 2026-11-25: "he constantly fires a thin quick rainbow colored laser every 2 seconds (0.6 second
	/// visual queue tell that it is coming) that comes diagonaly from anywhere, this happens idle as fight mechanic"): a line
	/// through the spot its target stood on when it was cast (the projectile's position), at the angle in <c>ai[0]</c>
	/// (diagonal), across the screen. For <see cref="Telegraph"/> ticks it is a thin dotted rainbow line growing brighter
	/// (harmless; step off it), then a beam for <see cref="BeamTicks"/> that hurts whoever is on it (vanilla's line test,
	/// <c>Collision.CheckAABBvLineCollision</c>, <see cref="Width"/> wide).
	/// </summary>
	public class RainbowLaser : CogpunkProjectile
	{
		public const int Telegraph = 36, BeamTicks = 12, Life = Telegraph + BeamTicks;
		public const float HalfLength = 1500f, Width = 14f;

		public override string Texture => "Cogpunk/Content/Bosses/Fungimancer/Projectiles/RainbowSpore";

		private int Age => Life - Projectile.timeLeft;

		public override void SetDefaults() {
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		private void Ends(out Vector2 a, out Vector2 b) {
			Vector2 dir = Projectile.ai[0].ToRotationVector2();
			a = Projectile.Center - dir * HalfLength;
			b = Projectile.Center + dir * HalfLength;
		}

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (Main.dedServ) {
				return;
			}
			if (Age == 1) {
				SoundEngine.PlaySound(SoundID.Item8 with { Pitch = 0.6f, Volume = 0.45f, MaxInstances = 4 }, Projectile.Center);
			}
			if (Age == Telegraph) {
				SoundEngine.PlaySound(SoundID.Item12 with { Pitch = 0.4f, Volume = 0.7f, MaxInstances = 4 }, Projectile.Center);
			}
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (Age < Telegraph) {
				return false;
			}
			Ends(out Vector2 a, out Vector2 b);
			float point = 0f;
			return Collision.CheckAABBvLineCollision(targetHitbox.TopLeft(), targetHitbox.Size(), a, b, Width, ref point);
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D px = TextureAssets.MagicPixel.Value;
			Ends(out Vector2 a, out Vector2 b);
			Vector2 dir = (b - a).SafeNormalize(Vector2.UnitX);
			bool beam = Age >= Telegraph;
			float strength = beam ? 1f - (Age - Telegraph) / (float)BeamTicks * 0.6f : 0.25f + 0.55f * Age / Telegraph;
			if (CogpunkClientConfig.Instance?.ReduceFlashing == true) {
				strength *= 0.6f;
			}
			int step = beam ? 4 : 10;
			int count = (int)(HalfLength * 2f / step);
			Rectangle view = new((int)Main.screenPosition.X - 32, (int)Main.screenPosition.Y - 32, Main.screenWidth + 64, Main.screenHeight + 64);
			int shift = (int)(Main.GameUpdateCount / 3);
			for (int i = 0; i <= count; i++) {
				Vector2 p = a + dir * (i * step);
				if (!view.Contains((int)p.X, (int)p.Y)) {
					continue;
				}
				Vector2 s = p - Main.screenPosition;
				int x = (int)s.X & ~1, y = (int)s.Y & ~1;
				Color c = Spectrum.At(i / (beam ? 4 : 1) + shift) * strength;
				if (beam) {
					Main.spriteBatch.Draw(px, new Rectangle(x - 3, y - 3, 6, 6), c with { A = 0 });
					Main.spriteBatch.Draw(px, new Rectangle(x - 1, y - 1, 2, 2), new Color(255, 255, 255, 0) * strength);
				}
				else {
					Main.spriteBatch.Draw(px, new Rectangle(x, y, 2, 2), c with { A = 0 });
				}
			}
			return false;
		}
	}

	/// <summary>
	/// The channel's blast (user, 2026-11-25: "if not destroyed it blows up dealing massive area damage to the whole screen (with
	/// quick a white flash and tinnitus rigging sound that briefly muflles the other game sounds) and stunning the players for 1.5
	/// seconds"): for its few ticks it hits every player within a screen of it (<see cref="HalfWidth"/> x <see cref="HalfHeight"/>,
	/// vanilla's 1920 x 1200 largest view and a little more), Shell-Shocked for <see cref="StunTicks"/>. Each client near it
	/// sees the white flash (<see cref="ScreenFlash"/>) and hears the ringing over muffled sound (<see cref="SoundMuffle"/>).
	/// </summary>
	public class ChannelBlast : CogpunkProjectile
	{
		public const int Life = 8, StunTicks = 90;
		public const float HalfWidth = 1000f, HalfHeight = 640f;

		public override string Texture => "Cogpunk/Content/Bosses/Fungimancer/Projectiles/RainbowSpore";

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Life;
			Projectile.aiStyle = -1;
			CooldownSlot = ImmunityCooldownID.Bosses;
		}

		public override void AI() {
			Projectile.velocity = Vector2.Zero;
			if (Projectile.localAI[0] != 0f) {
				return;
			}
			Projectile.localAI[0] = 1f;
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.5f, Volume = 1f }, Projectile.Center);
			SoundEngine.PlaySound(SoundID.Item62 with { Pitch = -0.3f, Volume = 0.9f }, Projectile.Center);
			Player me = Main.LocalPlayer;
			if (me != null && me.active && Near(me.Center)) {
				ScreenFlash.Flash(36);
				SoundMuffle.Muffle(120);
				SoundEngine.PlaySound(SoundMuffle.Tinnitus);
			}
			for (int i = 0; i < 60; i++) {
				if (i > 12 && !CogpunkClientConfig.RollEffect()) {
					continue;
				}
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(16f), 32, 32, DustID.RainbowMk2, out Dust d, 0f, 0f, 0, Spectrum.At(i), 1.6f)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2CircularEdge(1f, 1f) * Main.rand.NextFloat(6f, 18f);
				}
			}
		}

		private bool Near(Vector2 p) => Math.Abs(p.X - Projectile.Center.X) <= HalfWidth && Math.Abs(p.Y - Projectile.Center.Y) <= HalfHeight;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) => Near(targetHitbox.Center.ToVector2());

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			target.AddBuff(ModContent.BuffType<ShellShocked>(), StunTicks);
		}

		public override bool PreDraw(ref Color lightColor) => false;
	}
}
