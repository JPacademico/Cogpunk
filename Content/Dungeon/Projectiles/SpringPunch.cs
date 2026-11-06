using System;
using Cogpunk.Content.Dungeon.NPCs;
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

namespace Cogpunk.Content.Dungeon.Projectiles
{
	/// <summary>
	/// One of the <see cref="BeatBoxer"/>'s spring punches: a fist on a coiled spring fixed at its shoulder. It shoots out
	/// along the boxer's facing to <c>ai[2]</c> px (at most 7 tiles, locked when the volley started) in <see cref="OutTicks"/>
	/// ticks, holds for <see cref="HoldTicks"/> and is reeled back in <see cref="BackTicks"/>; only the fist hurts (its own
	/// <see cref="FistSize"/> box), with 1.5x vanilla's push (hostile projectiles push 4.5 whatever their own knockback:
	/// SKILL 3.9, so <see cref="ModifyHitPlayer"/> scales it). Decompiled <c>Player.Hurt</c> launches the player at the
	/// knockback sideways and 7/9 of it upwards, so this is 6.75 and 5.25 px/tick: about 11 tiles on flat ground, twice
	/// a vanilla hit's ~5 (2x was tried first and threw players about 20 tiles: tools/sim/update_2026_11_03b_sim.py).
	/// <para>Art: the near fist is the red glove with the white cross (SpringPunch.png), the far one the golden microphone
	/// (SpringPunch_Mic.png), both facing left like the boxer; the spring is a coil cell (SpringPunch_Spring.png) repeated
	/// from the shoulder to the fist. Horizontal only, so nothing is rotated (D4).</para>
	/// <para>D2: spawned by the server with <c>ai[0]</c> = the boxer, <c>ai[1]</c> = the arm, <c>ai[2]</c> = the reach; every
	/// side places it from the boxer's synced position. D0: a missing, dead or changed boxer ends it at once.</para>
	/// </summary>
	public class SpringPunch : CogpunkProjectile
	{
		public const int NearArm = 0, FarArm = 1;
		public const int OutTicks = 6, HoldTicks = 4, BackTicks = 12;
		public const int Lifetime = OutTicks + HoldTicks + BackTicks;
		public const int FistSize = 26;
		public const float KnockbackMultiplier = 1.5f;    // "good knockback" (user): 6.75 instead of vanilla's 4.5
		private const int FistWidth = 28, FistHeight = 24, SpringCell = 8, SpringHeight = 10;

		private static Asset<Texture2D> mic, spring;

		private int Age => Lifetime - Projectile.timeLeft;

		public override void SetStaticDefaults() {
			mic = DepthLayers.RequestOptional(Texture + "_Mic");
			spring = DepthLayers.RequestOptional(Texture + "_Spring");
		}

		public override void Unload() {
			mic = spring = null;
		}

		public override void SetDefaults() {
			Projectile.width = FistSize;
			Projectile.height = FistSize;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		/// <summary>How far out the fist is (0..1 of the reach) at an age: eased out, held, reeled back.</summary>
		public static float Extension(int age) {
			if (age < OutTicks) {
				float t = (age + 1f) / OutTicks;
				return 1f - (1f - t) * (1f - t);
			}
			if (age < OutTicks + HoldTicks) {
				return 1f;
			}
			float back = (age - OutTicks - HoldTicks + 1f) / BackTicks;
			return Math.Max(0f, 1f - back * back);
		}

		private bool TryGetBoxer(out BeatBoxer boxer) {
			boxer = null;
			int index = (int)Projectile.ai[0];
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC npc = Main.npc[index];
			if (!npc.active || npc.ModNPC is not BeatBoxer b) {
				return false;
			}
			boxer = b;
			return true;
		}

		public override void AI() {
			if (!TryGetBoxer(out BeatBoxer boxer)) {
				Projectile.Kill();
				return;
			}
			int arm = Projectile.ai[1] == FarArm ? FarArm : NearArm;
			float reach = MathHelper.Clamp(Projectile.ai[2], 0f, BeatBoxer.PunchReach);
			int dir = Projectile.velocity.X >= 0f ? 1 : -1;
			Vector2 shoulder = boxer.Shoulder(arm);
			// vanilla moves it by its velocity (the facing, length 1) after this: start that much short
			Projectile.Center = shoulder + new Vector2(dir * (FistWidth * 0.5f + reach * Extension(Age)), 0f) - Projectile.velocity;
			Projectile.direction = Projectile.spriteDirection = dir;
			if (Age == 0 && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.6f, Volume = 0.8f, MaxInstances = 4 }, Projectile.Center);
			}
		}

		// Only while it is out: a reeling fist doesn't hit.
		public override bool CanHitPlayer(Player target) => Age < OutTicks + HoldTicks;

		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			modifiers.Knockback *= KnockbackMultiplier;
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info) {
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.NPCHit4 with { Pitch = -0.3f, MaxInstances = 3 }, Projectile.Center);
			for (int i = 0; i < 6; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.GoldFlame, out Dust d, Projectile.direction * 2f, -1f);
				if (d != null) {
					d.noGravity = true;
				}
			}
		}

		// The coil from the shoulder to the fist (cells of the spring sheet, the last one cut to fit), then the fist; every
		// cell snapped to whole pixels, mirrored with the facing, never rotated or stretched (D4).
		public override bool PreDraw(ref Color lightColor) {
			if (!TryGetBoxer(out BeatBoxer boxer)) {
				return false;
			}
			int arm = Projectile.ai[1] == FarArm ? FarArm : NearArm;
			int dir = Projectile.direction >= 0 ? 1 : -1;
			SpriteEffects effects = dir > 0 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Vector2 shoulder = boxer.Shoulder(arm) - Main.screenPosition;
			Vector2 fist = Projectile.Center - Main.screenPosition;
			float length = Math.Abs(fist.X - shoulder.X) - FistWidth * 0.5f;
			if (spring?.IsLoaded == true && length > 0f) {
				Texture2D coil = spring.Value;
				int cells = (int)(length / SpringCell);
				for (int k = 0; k <= cells; k++) {
					int w = k < cells ? SpringCell : (int)length - cells * SpringCell;
					if (w <= 0) {
						continue;
					}
					float x = dir > 0 ? shoulder.X + k * SpringCell : shoulder.X - k * SpringCell - w;
					Vector2 at = new((int)x, (int)(shoulder.Y - SpringHeight * 0.5f));
					Main.EntitySpriteDraw(coil, at, new Rectangle(0, 0, w, SpringHeight), lightColor, 0f, Vector2.Zero, 1f, effects);
				}
			}
			Texture2D texture = arm == FarArm && mic?.IsLoaded == true ? mic.Value : TextureAssets.Projectile[Type].Value;
			Vector2 position = new((int)(fist.X - FistWidth * 0.5f), (int)(fist.Y - FistHeight * 0.5f));
			Main.EntitySpriteDraw(texture, position, new Rectangle(0, 0, FistWidth, FistHeight), lightColor, 0f, Vector2.Zero, 1f, effects);
			return false;
		}
	}
}
