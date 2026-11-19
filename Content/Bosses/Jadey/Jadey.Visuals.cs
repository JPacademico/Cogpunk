using System;
using Cogpunk.Content.Bosses.Jadey.Projectiles;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.UI;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.Jadey.JadeyRigData;

namespace Cogpunk.Content.Bosses.Jadey
{
	// Jadey's looks (clients only): three planes drawn with DepthLayers (the far plane's own frame: the coin flick), the rope
	// dart spinning in her paw, the aim lines, the channel's streams, the intro's and the death's camera and effects.
	public partial class Jadey
	{
		public const float MaxParallax = 2f;
		public const float SpinRadius = 18f;                     // px: the dart's circle round her paw while she spins it
		public const int AimDots = 40;

		private static Asset<Texture2D> farSheet, nearSheet, glowSheet;
		private int frame, farFrame;
		private int lastOnce = -1;
		private bool titleShown, shattered;

		/// <summary>Gone from sight: burst into jade (the death's last ticks).</summary>
		public bool Shattered => CurrentPhase == Phase.Dying && Timer >= ShatterTick;

		private static void LoadVisuals() {
			if (Main.dedServ) {
				return;
			}
			string path = "Cogpunk/Content/Bosses/Jadey/Jadey";
			farSheet = DepthLayers.RequestOptional(path + "_Far");
			nearSheet = DepthLayers.RequestOptional(path + "_Near");
			glowSheet = DepthLayers.RequestOptional(path + "_Glow");
		}

		private static void UnloadVisuals() {
			farSheet = nearSheet = glowSheet = null;
		}

		public override void FindFrame(int frameHeight) {
			frame = BodyFrame();
			farFrame = FarFrame();
		}

		/// <summary>One-shot effects keyed to the synced timer (a resync never repeats them).</summary>
		private bool Once(int tick) {
			int key = State * 10000 + tick;
			if ((int)Timer != tick || lastOnce == key) {
				return false;
			}
			lastOnce = key;
			return true;
		}

		private float CameraLock(Player viewer) {
			if (viewer == null || !viewer.active || Vector2.DistanceSquared(viewer.Center, NPC.Center) > CameraLockRange * CameraLockRange) {
				return 0f;
			}
			if (CurrentPhase == Phase.Intro) {
				return CinematicCamera.Envelope(Timer, IntroTicks, CameraEaseTicks, CameraEaseTicks);
			}
			if (CurrentPhase == Phase.Dying) {
				return CinematicCamera.Envelope(Timer, DeathTicks, CameraEaseTicks, 40f);
			}
			return 0f;
		}

		private static void Punch(Vector2 at, float strength, int frames, string id) {
			if (CogpunkClientConfig.Instance?.ScreenShake == false) {
				return;
			}
			Main.instance.CameraModifiers.Add(new PunchCameraModifier(at, Vector2.UnitY, strength, 6f, frames, 1000f, id));
		}

		// --- per-tick effects ---------------------------------------------------------------------------------------------

		private void StateEffects() {
			int t = (int)Timer;
			Lighting.AddLight(GemWorld, 0.1f, 0.4f, 0.28f);
			switch (CurrentPhase) {
				case Phase.Intro:
					IntroEffects(t);
					break;
				case Phase.Whip:
					if (Once(6)) {
						SoundEngine.PlaySound(SoundID.Item7 with { Pitch = -0.3f, Volume = 0.9f }, NPC.Center);        // the cord whirs
					}
					if (t > 6 && t < SpinTicks && t % 6 == 0) {
						SoundEngine.PlaySound(SoundID.Item7 with { Pitch = 0.1f, Volume = 0.6f, MaxInstances = 3 }, NearPawWorld);
					}
					if (Once(SpinTicks)) {
						SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.4f }, NPC.Center);                         // the throw
					}
					break;
				case Phase.Zone:
					if (Once(2)) {
						SoundEngine.PlaySound(SoundID.Item8 with { Pitch = -0.4f }, NPC.Center);
					}
					if (Once(JadePetrifyZone.SnapTick)) {
						Punch(NPC.Center, 3f, 20, "Cogpunk:JadeyZone");
					}
					break;
				case Phase.Channel:
					ChannelEffects(t);
					break;
				case Phase.Statue:
					StatueEffects(t);
					break;
				case Phase.Laser:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.Item15 with { Pitch = 0.4f, Volume = 0.8f }, GemWorld);           // the gem hums
					}
					if (t < LaserTick(LaserShots - 1) && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
						&& SafeSpawn.TryNewDust(GemWorld - new Vector2(4f), 8, 8, DustID.GemEmerald, out Dust g)) {
						g.noGravity = true;
						g.velocity = Main.rand.NextVector2Circular(1f, 1f);
						g.scale = 0.8f;
					}
					break;
				case Phase.Leave:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.Item29 with { Pitch = 0.3f }, NPC.Center);
					}
					Motes(NPC.Center, 2);
					break;
				case Phase.Dying:
					DeathEffects(t);
					break;
			}
			if (flickTick == FlickTicks / 2) {
				SoundEngine.PlaySound(SoundID.CoinPickup with { Pitch = 0.4f, Volume = 0.7f }, FarPawWorld);           // the coin's flick
			}
		}

		private void IntroEffects(int t) {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(NPC.Center, lockAmount);
			}
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.Item29 with { Pitch = -0.4f }, NPC.Center);                              // jade light
				Motes(NPC.Center, 30);
			}
			if (t < 50 && t % 3 == 0) {
				Motes(Origin + new Vector2(Main.rand.NextFloat(-30f, 30f), -4f), 1);
			}
			if (!titleShown && t >= TitleTick && lockAmount > 0f) {
				titleShown = true;
				BossTitleSystem.Show(DisplayName, epithet, TitleHoldTicks);
			}
			if (Once(70)) {
				SoundEngine.PlaySound(SoundID.Item4 with { Pitch = 0.5f, Volume = 0.6f }, NPC.Center);                // her eyes open
			}
			if (Once(110)) {
				SoundEngine.PlaySound(SoundID.CoinPickup with { Pitch = 0.2f }, NPC.Center);                         // a cheeky coin
			}
		}

		/// <summary>The channel: jade streams from each of her minions into her (dust along the line, a few a tick), her eyes'
		/// light; at its end a burst where each minion was eaten (their death plays their own effects).</summary>
		private void ChannelEffects(int t) {
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.Item44 with { Pitch = 0.3f }, NPC.Center);
			}
			if (t < ChannelTicks && CogpunkClientConfig.RollEffect()) {
				foreach (NPC npc in Main.ActiveNPCs) {
					if (!JadeyMinion.Of(npc, NPC.whoAmI) || !Main.rand.NextBool(3)) {
						continue;
					}
					Vector2 at = Vector2.Lerp(npc.Center, NPC.Center, Main.rand.NextFloat());
					if (SafeSpawn.TryNewDust(at - new Vector2(3f), 6, 6, DustID.GemEmerald, out Dust d)) {
						d.noGravity = true;
						d.velocity = (NPC.Center - at).SafeNormalize(Vector2.Zero) * 3f;
						d.scale = 1f;
					}
				}
			}
			if (Once(ChannelTicks)) {
				SoundEngine.PlaySound(SoundID.Item4 with { Pitch = -0.2f }, NPC.Center);                              // she drinks them
				Motes(NPC.Center, 16);
			}
		}

		/// <summary>The statue: a flick per coin (drawn from the flick frames), a crack and a hush as the jade climbs her, a low hum
		/// while she stands, cracking light just before she wakes, and shards when she does (her leaving the state).</summary>
		private void StatueEffects(int t) {
			if (Once(PetrifyAt)) {
				SoundEngine.PlaySound(SoundID.Item27 with { Pitch = -0.6f, Volume = 0.9f }, NPC.Center);
				Motes(NPC.Center, 18);
			}
			if (t >= PetrifyAt && t % 40 == 0) {
				SoundEngine.PlaySound(SoundID.Item15 with { Pitch = -0.7f, Volume = 0.35f, MaxInstances = 2 }, NPC.Center);
			}
			if (t >= PetrifyAt + StatueTicks - StatueCrackWarn && Main.rand.NextBool(3)) {
				Motes(NPC.Center + Main.rand.NextVector2Circular(24f, 30f), 1);
			}
		}

		private void DeathEffects(int t) {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(NPC.Center, lockAmount);
			}
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.NPCHit5 with { Pitch = -0.4f }, NPC.Center);                             // a cry
			}
			if (t < 100 && t % 20 == 1) {
				SoundEngine.PlaySound(SoundID.Item27 with { Pitch = -0.6f + t * 0.005f, Volume = 0.6f }, NPC.Center); // the jade creeps
			}
			if (Once(140) || Once(170)) {
				SoundEngine.PlaySound(SoundID.Item70 with { Pitch = 0.6f, Volume = 0.7f }, NPC.Center);               // cracks
			}
			if (Once(ShatterTick)) {
				SoundEngine.PlaySound(SoundID.Shatter with { Pitch = -0.3f, Volume = 1f }, NPC.Center);
				SoundEngine.PlaySound(SoundID.Item70 with { Pitch = -0.2f }, NPC.Center);
				Punch(NPC.Center, 7f, 40, "Cogpunk:JadeyShatter");
				Shatter();
			}
		}

		/// <summary>Her statue bursts: head, body and cushion gores and a spray of jade (clients; vanilla caps gore and dust).</summary>
		private void Shatter() {
			if (shattered) {
				return;
			}
			shattered = true;
			string[] gores = { "Jadey_GoreHead", "Jadey_GoreBody", "Jadey_GoreCushion" };
			for (int k = 0; k < gores.Length; k++) {
				if (Mod.TryFind(gores[k], out ModGore gore)) {
					Vector2 at = Origin + new Vector2(-20f, -70f + k * 26f);
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), at, new Vector2(Main.rand.NextFloat(-3f, 3f), Main.rand.NextFloat(-5f, -2f)), gore.Type, out _);
				}
			}
			int n = CogpunkClientConfig.RollEffect() ? 70 : 20;
			for (int i = 0; i < n; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 4 == 0 ? DustID.GoldCoin : DustID.GemEmerald, out Dust d)) {
					d.velocity = Main.rand.NextVector2Circular(7f, 7f);
					d.noGravity = Main.rand.NextBool();
					d.scale = 1.4f;
				}
			}
		}

		private static void Motes(Vector2 at, int count) {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(10f), 20, 20, DustID.GemEmerald, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(2f, 2f) - Vector2.UnitY;
					d.scale = 1.1f;
				}
			}
		}

		protected override void BossHitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 3; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.GemEmerald, out _);
			}
		}

		// --- drawing ------------------------------------------------------------------------------------------------------

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			if (Shattered) {
				return false;
			}
			bool dummy = NPC.IsABestiaryIconDummy;
			Texture2D middle = TextureAssets.Npc[Type].Value;
			Vector2 anchor = (dummy ? NPC.Bottom : Origin) - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;              // the art faces left
			Color light = NPC.GetAlpha(drawColor);
			int body = dummy ? R.Idle : frame, far = dummy ? R.Idle : farFrame;
			float shift = dummy ? 0f : MaxParallax;
			Vector2 farShift = new(DepthLayers.Shift(anchor, DepthLayers.Far, shift).X, 0f);
			Vector2 nearShift = new(DepthLayers.Shift(anchor, DepthLayers.Near, shift).X, 0f);
			if (farSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, farSheet.Value, far, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor + farShift, 0, DepthLayers.Tint(light, DepthLayers.Far), flip);
			}
			DepthLayers.DrawCell(spriteBatch, middle, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY, anchor, 0, light, flip);
			if (nearSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, nearSheet.Value, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor + nearShift, 0, light, flip);
			}
			if (glowSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, glowSheet.Value, body, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY,
					anchor, 0, Color.White * NPC.Opacity, flip);
			}
			if (!dummy) {
				DrawSpin();
				DrawAimLines();
			}
			return false;
		}

		/// <summary>The spin (the whip's telegraph): the jade blade circling her raised paw on its cord, drawn from its 16
		/// headings (the tangent's), on the 2 px grid.</summary>
		private void DrawSpin() {
			int t = (int)Timer;
			if (CurrentPhase != Phase.Whip || t < 8 || t >= SpinTicks) {
				return;
			}
			Vector2 paw = NearPawWorld;
			float a = t * 0.7f;
			Vector2 blade = paw + new Vector2(MathF.Cos(a) * SpinRadius, MathF.Sin(a) * SpinRadius * 0.45f);
			Color light = Lighting.GetColor((int)(blade.X / 16f), (int)(blade.Y / 16f));
			JadeyRopeDart.DrawCord(paw, blade, light);
			Vector2 tangent = new(-MathF.Sin(a), MathF.Cos(a) * 0.45f);
			JadeyRopeDart.DrawBlade(blade, JadeyRopeDart.Heading(tangent), light);
		}

		/// <summary>The aim lines (my calls, the telegraphs): while she spins, a dotted jade line from her paw to where the dart
		/// will fly; while she aims her lasers, from her gem to her target until the last shot (blinking for its last 6 ticks).</summary>
		private void DrawAimLines() {
			int t = (int)Timer;
			Texture2D dot = TextureAssets.MagicPixel.Value;
			if (CurrentPhase == Phase.Whip && t >= 8 && t < SpinTicks && aim != Vector2.Zero) {
				DrawDots(dot, NearPawWorld, aim, 0.5f + 0.5f * t / SpinTicks);
			}
			if (CurrentPhase == Phase.Laser && t >= 4 && t < LaserTick(LaserShots - 1) && CurrentTarget is Player target) {
				bool fireSoon = false;
				for (int k = 0; k < LaserShots; k++) {
					int d = LaserTick(k) - t;
					fireSoon |= d >= 0 && d < 6;
				}
				if (!fireSoon || (t / 2) % 2 == 0) {
					DrawDots(dot, GemWorld, target.Center, 0.8f);
				}
			}
		}

		/// <summary>2x2 jade dots every 12 px from <paramref name="from"/> to <paramref name="to"/> (at most <see cref="AimDots"/>),
		/// stopping at the first solid tile (as the shot would), added onto the scene.</summary>
		private static void DrawDots(Texture2D dot, Vector2 from, Vector2 to, float strength) {
			Vector2 dir = (to - from).SafeNormalize(Vector2.Zero);
			float length = Math.Min(Vector2.Distance(from, to) + 160f, Coghaven.Projectiles.JadeRay.RayLength(from, dir, Coghaven.Projectiles.JadeRay.MaxLength));
			int count = Math.Min(AimDots, (int)(length / 12f));
			Color c = new Color(118, 220, 162, 0) * strength;
			for (int i = 1; i <= count; i++) {
				Vector2 p = from + dir * (i * 12f) - Main.screenPosition;
				Main.spriteBatch.Draw(dot, new Rectangle((int)DepthLayers.Snap(p.X), (int)DepthLayers.Snap(p.Y), 2, 2), c);
			}
		}
	}
}
