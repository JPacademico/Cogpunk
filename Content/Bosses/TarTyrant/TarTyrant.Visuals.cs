using System;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.UI;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Bosses.TarTyrant.TarTyrantRigData;

namespace Cogpunk.Content.Bosses.TarTyrant
{
	/// <summary>
	/// Tar Tyrant's looks (clients). The frame is a pure function of the synced state and timer
	/// (<see cref="ResolveFrame"/>), so the server's hit strips and every client's sprite agree. Every move goes through
	/// its tweened frames (user, 2026-10-29: the first version snapped between too few of them): rises and sinks are drawn
	/// frames now, not a ground-line clip. The sprite is drawn at <see cref="Size"/> (it shrinks as it sheds tar, as vanilla's
	/// King Slime does: the one runtime scale on a Cogpunk boss, asked for by the user; the vent overlay on its back is part
	/// of that body and scales with it), its top-left snapped to whole pixels. One-shot sounds are keyed by tick
	/// (<see cref="Once"/>) so a timer resync never replays them.
	/// D1: textures cached once; effects throttled; no allocation.
	/// </summary>
	public partial class TarTyrant
	{
		private const string Path = "Cogpunk/Content/Bosses/TarTyrant/";
		public const float MaxParallax = 4f;
		public const int MoveFrameTicks = 6, IdleFrameTicks = 8;

		/// <summary>The tick each of the 32 death frames starts on (2026-10-29, the user asked for more of them): a recoil and a
		/// last roar, its bones working loose (the femur slides out of its back), the slump (slowing as it spreads, the femur
		/// toppling off), the settling, the last bubble.</summary>
		public static readonly short[] DeathFrameTicks = { 0, 10, 20, 30, 40, 48, 56, 64, 72, 80, 89, 97, 106, 114, 123, 131, 140, 148, 157, 165,
			174, 182, 191, 199, 208, 218, 228, 238, 248, 262, 276, 290 };

		private static Asset<Texture2D>[] bodyPages, glowPages, nearPages, farPages;
		private static Asset<Texture2D> patchTexture, ventTexture;
		private static readonly string[] goreNames = { "Skull", "Jaw", "Horn", "Claw", "Rib", "Rib", "Femur", "Vertebra" };
		private static readonly int[] goreTypes = new int[8];

		private static void LoadVisuals() {
			if (Main.dedServ) {
				return;
			}
			bodyPages = DepthLayers.RequestPages(Path + "TarTyrant", R.BodyPages);
			glowPages = DepthLayers.RequestPages(Path + "TarTyrant_Glow", R.GlowPages);
			nearPages = DepthLayers.RequestPages(Path + "TarTyrant_Near", R.NearPages);
			farPages = DepthLayers.RequestPages(Path + "TarTyrant_Far", R.FarPages);
			patchTexture = DepthLayers.RequestOptional(Path + "Projectiles/TarTyrantClaw");
			ventTexture = DepthLayers.RequestOptional(Path + "TarTyrant_Vent");
			Mod mod = ModContent.GetInstance<CogpunkMod>();
			for (int i = 0; i < goreNames.Length; i++) {
				goreTypes[i] = mod.TryFind("TarTyrant_Gore" + goreNames[i], out ModGore gore) ? gore.Type : 0;
			}
		}

		private static void UnloadVisuals() {
			bodyPages = glowPages = nearPages = farPages = null;
			patchTexture = ventTexture = null;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Pose (synced state only)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>The frame for the synced state and timer; -1 while it is wholly under the tar (unless
		/// <paramref name="allowHidden"/> is false: then the last melt frame, for the AI points).</summary>
		public int ResolveFrame(bool allowHidden = true) {
			int t = (int)Timer;
			switch (CurrentPhase) {
				case Phase.Emerge:
					return t < RiseTicks ? R.Rise0 + Math.Min(R.RiseFrames - 1, t * R.RiseFrames / RiseTicks) : RoarFrame(t - RiseTicks, RoarTicks);
				case Phase.Idle:
					return Math.Abs(NPC.velocity.X) > 0.35f ? R.Move0 + t / MoveFrameTicks % R.MoveFrames : R.Idle0 + t / IdleFrameTicks % R.IdleFrames;
				case Phase.Burp:
					if (t < BurpTick) {
						return R.Burp0 + Math.Min(BurpFrame - 1, t * BurpFrame / BurpTick);
					}
					return t < BurpTick + 8 ? R.Burp0 + BurpFrame : R.Burp0 + Math.Min(R.BurpFrames - 1, BurpFrame + 1 + (t - BurpTick - 8) / 7);
				case Phase.Spit:
					return t < SpitTick ? R.Spit0 + Math.Min(SpitFrame - 1, t * SpitFrame / SpitTick) : R.Spit0 + Math.Min(R.SpitFrames - 1, SpitFrame + (t - SpitTick) / 6);
				case Phase.Melt:
					if (t < MeltUnderTick) {
						return R.Melt0 + Math.Min(R.MeltFrames - 1, t / MeltFrameTicks);
					}
					if (t < MeltRiseTick) {
						return allowHidden ? -1 : R.Melt0 + R.MeltFrames - 1;
					}
					return R.Rise0 + Math.Min(R.RiseFrames - 1, (t - MeltRiseTick) / RiseFrameTicks);
				case Phase.Summon:
					if (t < SummonFieldTick) {
						return R.Summon0 + Math.Min(3, t * 4 / SummonFieldTick);
					}
					if (t < SummonPlungeTick) {
						return R.Summon0 + 4 + (t - SummonFieldTick) / 4 % 2;       // the clenched claw shakes
					}
					if (t < SummonPlungeTick + 3) {
						return R.Summon0 + 6;
					}
					if (t < SummonPlungeTick + 8) {
						return R.Summon0 + 7;
					}
					return t < 110 ? R.Summon0 + 8 : (t < 124 ? R.Summon0 + 9 : R.Idle0);
				case Phase.Rage:
					if (t < RageGrowlTicks) {
						return RoarFrame(t, RageGrowlTicks);
					}
					if (t < RageClawStart) {
						return R.Melt0 + Math.Min(R.MeltFrames - 1, (t - RageGrowlTicks) / MeltFrameTicks);
					}
					if (t < RageRiseTick) {
						return allowHidden ? -1 : R.Melt0 + R.MeltFrames - 1;
					}
					return t < RageRoarTick ? R.Rise0 + Math.Min(R.RiseFrames - 1, (t - RageRiseTick) / RiseFrameTicks) : RoarFrame(t - RageRoarTick, RoarTicks);
				case Phase.Retreat:
					if (t < MeltUnderTick) {
						return R.Melt0 + Math.Min(R.MeltFrames - 1, t / MeltFrameTicks);
					}
					return allowHidden ? -1 : R.Melt0 + R.MeltFrames - 1;
				case Phase.Dying:
					return R.Death0 + TableFrame(DeathFrameTicks, t);
				default:
					return R.Idle0 + t / IdleFrameTicks % R.IdleFrames;
			}
		}

		/// <summary>The roar over <paramref name="length"/> ticks: draw breath, three shaking frames looped, close.</summary>
		private static int RoarFrame(int t, int length) {
			if (t < 8) {
				return R.Roar0;
			}
			if (t < 16) {
				return R.Roar0 + 1;
			}
			if (t >= length - 8) {
				return R.Roar0 + 5;
			}
			return R.Roar0 + 2 + (t - 16) / 4 % 3;
		}

		/// <summary>The last frame whose start tick is reached (the tables are ascending).</summary>
		private static int TableFrame(short[] starts, int t) {
			int k = 0;
			for (int i = 1; i < starts.Length; i++) {
				if (t >= starts[i]) {
					k = i;
				}
			}
			return k;
		}

		/// <summary>0..1: how firmly <paramref name="viewer"/>'s camera is locked on the boss (intro and death).</summary>
		public float CameraLock(Player viewer) {
			if (viewer == null || !viewer.active || Vector2.DistanceSquared(viewer.Center, CameraFocus) > CameraLockRange * CameraLockRange) {
				return 0f;
			}
			if (IsEmerging) {
				return CinematicCamera.Envelope(Timer, EmergeTicks, CameraEaseTicks, CameraEaseTicks);
			}
			if (IsDying) {
				return CinematicCamera.Envelope(Timer, DeathTicks, CameraEaseTicks, 40f);
			}
			return 0f;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Client effects
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>True once per tick of the current state, in ascending order (a resync never replays one).</summary>
		private bool Once(int tick) {
			if (Timer < tick || LastEffectKey >= tick + 1) {
				return false;
			}
			LastEffectKey = tick + 1;
			return true;
		}

		private int effectState = -1;

		private void ResetEffectKeys() {
			if (State != effectState) {
				effectState = State;
				LastEffectKey = 0f;
			}
		}

		private static bool Shake => CogpunkClientConfig.Instance?.ScreenShake ?? true;

		private static void Punch(Vector2 at, Vector2 direction, float strength, int frames, string id) {
			if (Shake) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(at, direction, strength, 10f, frames, 2400f, id));
			}
		}

		private static void Splash(Vector2 at, int width, int count, float up) {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			int dust = ModContent.DustType<TarSplash>();
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(width * 0.5f, 6f), width, 8, dust, out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-2.5f, 2.5f), -Main.rand.NextFloat(up * 0.5f, up));
				}
			}
		}

		private static void Bones(Vector2 at, int width, int count) {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(width * 0.5f, 8f), width, 10, DustID.Bone, out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), -Main.rand.NextFloat(1.5f, 4f));
				}
			}
		}

		private void StateEffects() {
			int t = (int)Timer;
			int frame = ResolveFrame(false);
			if (!Submerged && !Hidden) {
				float level = Enraged ? 1.15f : 0.85f;
				float pulse = (0.8f + 0.2f * MathF.Sin(Main.GlobalTimeWrappedHourly * 4f)) * level;
				Lighting.AddLight(RigPoint(R.Eye, frame), 0.8f * pulse, 0.36f * pulse, 0.08f * pulse);
				if (Enraged && Main.rand.NextBool(4) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(RigPoint(R.Eye, frame) - new Vector2(6f, 6f), 12, 12, DustID.Torch, out Dust fire, 0f, -1.5f, 0, default, 1.2f)) {
					fire.noGravity = true;                     // the enraged ember spills out of its eye
				}
			}
			if (TryGetRisingSpot(out Vector2 spot)) {
				RisingSpotEffects(spot, t);
			}
			switch (CurrentPhase) {
				case Phase.Emerge:
					EmergeEffects(t);
					break;
				case Phase.Idle:
					if (Math.Abs(NPC.velocity.X) > 0.35f && t % 8 == 0) {
						Splash(NPC.Bottom, (int)(160 * Size), 2, 2f);
					}
					break;
				case Phase.Burp:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.Item95 with { Pitch = -0.8f }, NPC.Center);           // it swells
					}
					if (t < BurpTick && t % 6 == 0) {
						Splash(RigPoint(R.Mouth, frame), 20, 1, 1.5f);
					}
					if (Once(BurpTick)) {
						SoundEngine.PlaySound(SoundID.Item85 with { Pitch = -0.7f, Volume = 1f }, RigPoint(R.Mouth, frame));
						SoundEngine.PlaySound(SoundID.NPCDeath13 with { Pitch = -0.6f }, RigPoint(R.Mouth, frame));
						Splash(RigPoint(R.Mouth, frame), 30, 10, 4f);
					}
					break;
				case Phase.Spit:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.Item95 with { Pitch = -0.5f }, NPC.Center);
					}
					if (Once(SpitTick)) {
						SoundEngine.PlaySound(SoundID.NPCDeath13 with { Pitch = -0.3f, Volume = 0.9f }, RigPoint(R.Mouth, frame));
						Splash(RigPoint(R.Mouth, frame), 24, 8, 3f);
					}
					break;
				case Phase.Melt:
				case Phase.Retreat:
					MeltEffects(t, 0);
					break;
				case Phase.Summon:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = -0.6f, Volume = 0.7f }, NPC.Center);   // its bones creak
					}
					if (Once(SummonFieldTick)) {
						SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.4f, Volume = 0.8f }, NPC.Center);
						SoundEngine.PlaySound(SoundID.Item85 with { Pitch = -0.8f }, NPC.Center);
					}
					if (t >= SummonFieldTick && t < SummonPlungeTick && t % 5 == 0) {
						Lighting.AddLight(RigPoint(R.Hand, frame), 0.9f, 0.4f, 0.1f);
					}
					if (Once(SummonPlungeTick + 3)) {
						Vector2 hand = RigPoint(R.Hand, frame);
						SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f }, hand);
						Punch(hand, Vector2.UnitY, 7f, 26, "Cogpunk:TarTyrantPlunge");
						Splash(new Vector2(hand.X, NPC.Bottom.Y), 60, 16, 6f);
					}
					break;
				case Phase.Rage:
					RageEffects(t);
					break;
				case Phase.Dying:
					DeathEffects(t);
					break;
			}
		}

		/// <summary>The ground boiling where it will rise (the melt's and the rage's warning).</summary>
		private static void RisingSpotEffects(Vector2 spot, int t) {
			if (t % 3 == 0) {
				Splash(spot, 120, 2, 3.5f);
			}
			if (t % 14 == 0) {
				SoundEngine.PlaySound(SoundID.Item85 with { Pitch = -0.6f, Volume = 0.6f, MaxInstances = 3 }, spot);   // bubbling
			}
			Lighting.AddLight(spot - new Vector2(0f, 8f), 0.35f, 0.15f, 0.05f);
		}

		/// <summary>Sinking and rising (the melt, the retreat, the rage's own melt and rise; <paramref name="offset"/> = the
		/// tick the melt starts at).</summary>
		private void MeltEffects(int t, int offset) {
			int m = t - offset;
			if (Once(offset + 1)) {
				SoundEngine.PlaySound(SoundID.Item95 with { Pitch = -0.9f }, NPC.Bottom);                 // it slumps
				SoundEngine.PlaySound(SoundID.NPCDeath13 with { Pitch = -0.8f, Volume = 0.8f }, NPC.Bottom);
			}
			if (m >= 0 && m < MeltUnderTick && m % 3 == 0) {
				Splash(NPC.Bottom, (int)(170 * Size), 3, 3f);
			}
			int rise = CurrentPhase == Phase.Rage ? RageRiseTick : MeltRiseTick;
			if (CurrentPhase != Phase.Retreat && Once(rise)) {
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.5f }, NPC.Bottom);
				SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.6f, Volume = 0.7f }, NPC.Center);
				SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = -0.4f }, NPC.Center);              // the bones burst out
				Punch(NPC.Bottom, Vector2.UnitY, 10f, 30, "Cogpunk:TarTyrantRise");
				Splash(NPC.Bottom, (int)(200 * Size), 30, 7f);
				Bones(NPC.Bottom, (int)(120 * Size), 8);
			}
		}

		private void EmergeEffects(int t) {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(CameraFocus, lockAmount);
			}
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.Item95 with { Pitch = -1f, Volume = 1f }, NPC.Bottom);
				Punch(NPC.Bottom, Vector2.UnitY, 3f, RiseTicks, "Cogpunk:TarTyrantRumble");
			}
			if (t < RiseTicks && t % 3 == 0) {
				Splash(NPC.Bottom, 170, 3, 4f);
			}
			if (Once(EmergeSolidTick)) {
				SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = -0.5f }, NPC.Center);              // the skull breaks the surface
				Bones(NPC.Bottom, 100, 6);
			}
			if (TitleShown == 0f && t >= TitleTick && lockAmount > 0f) {
				TitleShown = 1f;
				BossTitleSystem.Show(DisplayName, epithet, TitleHoldTicks);
			}
			if (Once(RiseTicks + 16)) {
				SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.7f }, NPC.Center);
				Punch(NPC.Center, Vector2.UnitX, 9f, 40, "Cogpunk:TarTyrantRoar");
				Splash(RigPoint(R.Mouth, R.Roar0 + 2), 40, 10, 3f);
			}
		}

		/// <summary>The hump before a volley (<paramref name="t"/> = ticks into the telegraph): it gurgles as it heaves, its
		/// bones creak at the halfway mark, tar spits off it (clients).</summary>
		private void VentTelegraph(int t) {
			Vector2 vent = RigPoint(R.Vent, ResolveFrame(false));
			if (t == 0) {
				SoundEngine.PlaySound(SoundID.Item85 with { Pitch = -0.5f, Volume = 0.7f, MaxInstances = 3 }, vent);   // it boils
			}
			if (t == VentTelegraphTicks / 2) {
				SoundEngine.PlaySound(SoundID.NPCHit2 with { Pitch = -0.7f, Volume = 0.6f, MaxInstances = 3 }, vent);  // bones grind inside
			}
			if (t % 6 == 0) {
				Splash(vent, (int)(24 * Size), 1, 2f);
			}
		}

		/// <summary>The volley bursts out of its back: a wet crack and a splash of tar (clients).</summary>
		private void VentLaunchEffects() {
			Vector2 vent = RigPoint(R.Vent, ResolveFrame(false));
			SoundEngine.PlaySound(SoundID.NPCDeath13 with { Pitch = -0.4f, Volume = 0.8f, MaxInstances = 3 }, vent);
			SoundEngine.PlaySound(SoundID.NPCHit2 with { Pitch = -0.3f, MaxInstances = 3 }, vent);
			Splash(vent, (int)(40 * Size), 8, 4f);
			Bones(vent, (int)(24 * Size), 3);
		}

		private void RageEffects(int t) {
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.9f, Volume = 1f }, NPC.Center);       // the growl
				SoundEngine.PlaySound(SoundID.NPCDeath10 with { Pitch = -0.6f, Volume = 0.6f }, NPC.Center);
				Punch(NPC.Center, Vector2.UnitX, 3f, RageGrowlTicks, "Cogpunk:TarTyrantGrowl");          // one long shake, not one per beat
			}
			if (t < RageGrowlTicks && t % 4 == 0) {
				Splash(NPC.Bottom, (int)(160 * Size), 2, 3f);
			}
			MeltEffects(t, RageGrowlTicks);
			if (Once(RageRoarTick + 16)) {
				SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.5f }, NPC.Center);
				Punch(NPC.Center, Vector2.UnitX, 10f, 40, "Cogpunk:TarTyrantEnraged");
			}
		}

		private void DeathEffects(int t) {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(CameraFocus, lockAmount);
			}
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = -0.7f }, NPC.Center);
			}
			if (Once(DeathFrameTicks[1])) {
				SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.9f }, NPC.Center);              // its last roar
				Punch(NPC.Center, Vector2.UnitX, 6f, 30, "Cogpunk:TarTyrantDeath");
			}
			for (int k = 4; k < 8; k++) {
				if (Once(DeathFrameTicks[k])) {                    // its bones work loose, the femur grinding out of its back
					SoundEngine.PlaySound(SoundID.NPCHit2 with { Pitch = -0.8f + 0.1f * k, Volume = 0.6f, MaxInstances = 4 }, RigPoint(R.Top, R.Death0 + k));
				}
			}
			if (t >= DeathFrameTicks[8] && t % 4 == 0) {
				Splash(NPC.Bottom, (int)(200 * Size), 3, 3f + t / 100);
			}
			for (int k = 8; k < 24; k += 4) {
				if (Once(DeathFrameTicks[k])) {
					SoundEngine.PlaySound(SoundID.NPCDeath13 with { Pitch = -0.9f, Volume = 0.8f }, NPC.Center);   // it slumps
					Punch(NPC.Bottom, Vector2.UnitY, 4f, 16, "Cogpunk:TarTyrantSlump");
				}
			}
			if (Once(DeathFrameTicks[30])) {
				SoundEngine.PlaySound(SoundID.Item54 with { Pitch = -0.6f }, NPC.Center);              // the last bubble pops
			}
			if (Once(DeathSinkTick)) {
				SoundEngine.PlaySound(SoundID.NPCDeath2 with { Pitch = -0.5f }, NPC.Center);
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.7f, Volume = 0.6f }, NPC.Center);
				Punch(NPC.Center, Vector2.UnitY, 8f, 30, "Cogpunk:TarTyrantGone");
				Splash(NPC.Bottom, (int)(220 * Size), 30, 6f);
				for (int i = 0; i < goreTypes.Length; i++) {                   // the tar lets go of its bones
					if (goreTypes[i] > 0) {
						Vector2 at = NPC.Bottom + new Vector2(Main.rand.NextFloat(-90f, 90f) * Size, -24f);
						SafeSpawn.TryNewGore(NPC.GetSource_Death(), at, new Vector2(Main.rand.NextFloat(-3f, 3f), -Main.rand.NextFloat(3f, 6f)), goreTypes[i], out _,
							Size);                                     // its bones are as small as it got
					}
				}
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Drawing
		// ------------------------------------------------------------------------------------------------------------

		public override void FindFrame(int frameHeight) {
			NPC.frame = new Rectangle(0, 0, R.BoundsWidth, R.BoundsHeight);   // the bestiary sizes its box from this
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			bool dummy = NPC.IsABestiaryIconDummy;
			if (!dummy && TryGetRisingSpot(out Vector2 spot)) {
				DrawRisingSpot(spriteBatch, spot - screenPos);
			}
			int frame = dummy ? R.Idle0 : ResolveFrame();
			if (frame < 0) {
				return false;                                  // under the tar
			}
			float scale = dummy ? NPC.scale : Size;
			Vector2 anchor = (dummy ? NPC.Bottom : RigOrigin) - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;
			Color light = NPC.GetAlpha(drawColor);
			Vector2 farShift = dummy ? Vector2.Zero : new Vector2(DepthLayers.Shift(anchor, DepthLayers.Far, MaxParallax).X, 0f);
			Vector2 nearShift = dummy ? Vector2.Zero : new Vector2(DepthLayers.Shift(anchor, DepthLayers.Near, MaxParallax).X, 0f);
			DepthLayers.DrawFrame(spriteBatch, farPages, R.FarFrames, frame, anchor + farShift, 0, DepthLayers.Tint(light, DepthLayers.Far), flip, scale);
			DepthLayers.DrawFrame(spriteBatch, bodyPages, R.BodyFrames, frame, anchor, 0, light, flip, scale);
			float pulse = 0.8f + 0.2f * MathF.Sin(Main.GlobalTimeWrappedHourly * 4f);
			DepthLayers.DrawFrame(spriteBatch, glowPages, R.GlowFrames, frame, anchor, 0, Color.White * pulse * NPC.Opacity, flip, scale);
			if (!dummy) {
				DrawVent(spriteBatch, frame, anchor, flip, scale, light);
			}
			DepthLayers.DrawFrame(spriteBatch, nearPages, R.NearFrames, frame, anchor + nearShift, 0, light, flip, scale);
			return false;
		}

		/// <summary>The vent on its back before and as a volley bursts out (TarTyrant_Vent.png, its origin on the frame's
		/// <see cref="R.Vent"/> point; mirrored and scaled like the body it sits on).</summary>
		private void DrawVent(SpriteBatch spriteBatch, int frame, Vector2 anchor, bool flip, float scale, Color light) {
			int k = VentFrame;
			if (k < 0 || ventTexture?.IsLoaded != true) {
				return;
			}
			int i = frame * 2;
			if (i < 0 || i + 1 >= R.Vent.Length) {
				return;
			}
			Texture2D texture = ventTexture.Value;
			Rectangle source = new(0, k * (R.VentHeight + 2), R.VentWidth, R.VentHeight);
			if (source.Bottom > texture.Height) {
				return;
			}
			Vector2 at = anchor + new Vector2(flip ? -R.Vent[i] : R.Vent[i], R.Vent[i + 1]) * scale;
			Vector2 origin = new(flip ? R.VentWidth - R.VentOriginX : R.VentOriginX, R.VentOriginY);
			at = new Vector2(MathF.Round(at.X), MathF.Round(at.Y));
			spriteBatch.Draw(texture, at, source, light, 0f, origin, scale, flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None, 0f);
		}

		/// <summary>The boiling patch (the claw's warning frames, 8 tiles of tar) where it is about to rise.</summary>
		private void DrawRisingSpot(SpriteBatch spriteBatch, Vector2 bottom) {
			if (patchTexture?.IsLoaded != true) {
				return;
			}
			Texture2D texture = patchTexture.Value;
			int k = R.ClawWarn0 + (int)(Main.GameUpdateCount / 6 % R.ClawWarnFrames);
			Rectangle source = Projectiles.TarTyrantClaw.Cell(k);
			if (source.Bottom > texture.Height || source.Right > texture.Width) {
				return;
			}
			Color light = Lighting.GetColor((int)((bottom.X + Main.screenPosition.X) / 16f), (int)((bottom.Y + Main.screenPosition.Y - 8f) / 16f));
			Vector2 position = new(MathF.Round(bottom.X - R.ClawWidth * 0.5f), MathF.Round(bottom.Y - R.ClawHeight + 2f));
			spriteBatch.Draw(texture, position, source, light, 0f, Vector2.Zero, 1f, SpriteEffects.None, 0f);
		}
	}
}
