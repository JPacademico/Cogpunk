using System;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// A glob of tar spat by a <see cref="TarSlimeMinion"/>: it flies straight like a hornet's stinger, bursts on the first
	/// enemy or tile, and coats what it hits in the Tar Plague for <see cref="PlagueTicks"/> ticks (the enemy version: 10
	/// every half second and half speed, <see cref="TarPlagueNPC"/>). Minion damage skips vanilla's crit roll, so it rolls
	/// its own crit (D3 rule 9; tModLoader passes the minion's crit chance on to what it spawns).
	/// <para>Art: <see cref="Headings"/> pre-rendered headings (0 = flying right, clockwise), never rotated at runtime (D4).</para>
	/// </summary>
	public class TarSlimeShot : CogpunkProjectile
	{
		public const int Headings = 16;
		public const int PlagueTicks = 120;
		private const int FrameSize = 20, FrameStride = 22;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = Headings;
			ProjectileID.Sets.MinionShot[Type] = true;
			CogpunkSets.RollsOwnCrit[Type] = true;          // its ModifyHitNPC rolls CritChance (the Bottle of Lost Souls skips it)
		}

		public override void SetDefaults() {
			Projectile.width = 10;
			Projectile.height = 10;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = 1;
			Projectile.tileCollide = true;
			Projectile.timeLeft = 90;                      // about 56 tiles at 10 px a tick
			Projectile.aiStyle = -1;
		}

		public override void AI() {
			MathSafety.Sanitize(ref Projectile.velocity);
			float angle = MathHelper.WrapAngle(Projectile.velocity.ToRotation());
			Projectile.frame = ((int)Math.Round(angle / MathHelper.TwoPi * Headings) % Headings + Headings) % Headings;
			if (!Main.dedServ && Main.rand.NextBool(4) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust trail)) {
				trail.velocity = Projectile.velocity * 0.1f;
			}
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (Main.rand.Next(100) < Projectile.CritChance) {
				modifiers.SetCrit();
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			TarPlague.InflictOn(target, Main.player[Projectile.owner], PlagueTicks);
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCDeath1 with { Volume = 0.3f, Pitch = 0.3f, MaxInstances = 4 }, Projectile.Center);
			for (int i = 0; i < 5; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, ModContent.DustType<TarSplash>(), out Dust d)) {
					d.velocity = Main.rand.NextVector2Circular(2f, 2f) - Projectile.velocity * 0.1f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, Headings - 1) * FrameStride, FrameSize, FrameSize);
			Vector2 position = (Projectile.Center - Main.screenPosition - new Vector2(FrameSize * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, position, source, Projectile.GetAlpha(lightColor), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			return false;
		}
	}
}
