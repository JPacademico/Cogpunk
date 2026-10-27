using System;
using Cogpunk.Content.Scrap.Tiles;
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
using R = Cogpunk.Content.Bosses.TrashTr0m.TrashTr0mRigData;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	public partial class TrashTr0m
	{
		/// <summary>Largest parallax shift of the arm layers, in px, at the edge of the screen (DepthLayers).</summary>
		public const float MaxParallax = 4f;

		/// <summary>Ticks each in-between pose of the death is held (DeathJoltSag, DeathSagSlump, DeathSlumpDown).</summary>
		public const int DeathTweenTicks = 12;

		private const string Path = "Cogpunk/Content/Bosses/TrashTr0m/";
		private static Asset<Texture2D>[] bodyPages;
		private static Asset<Texture2D>[] glowPages;
		private static Asset<Texture2D>[] nearPages;
		private static Asset<Texture2D>[] farPages;
		private static readonly int[] goreTypes = new int[6];
		private static readonly string[] goreNames = { "Tyre", "Jaw", "Crest", "Gear", "Piston", "Plate" };

		private ref float LastEffectKey => ref NPC.localAI[1];

		private ref float GoresThrown => ref NPC.localAI[2];

		private static void LoadVisuals() {
			if (Main.dedServ) {
				return;
			}
			bodyPages = RequestPages(Path + "TrashTr0m", R.BodyPages);
			glowPages = RequestPages(Path + "TrashTr0m_Glow", R.GlowPages);
			nearPages = RequestPages(Path + "TrashTr0m_ArmNear", R.NearPages);
			farPages = RequestPages(Path + "TrashTr0m_ArmFar", R.FarPages);
			Mod mod = ModContent.GetInstance<CogpunkMod>();
			for (int i = 0; i < goreNames.Length; i++) {
				goreTypes[i] = mod.TryFind("TrashTr0m_Gore" + goreNames[i], out ModGore gore) ? gore.Type : 0;
			}
		}

		/// <summary>A layer's pages (Name, Name_Page1, ...); a missing page stays null and its frames are simply not drawn (D0).</summary>
		private static Asset<Texture2D>[] RequestPages(string path, int count) {
			var pages = new Asset<Texture2D>[count];
			for (int k = 0; k < count; k++) {
				string name = k == 0 ? path : path + "_Page" + k;
				pages[k] = ModContent.HasAsset(name) ? ModContent.Request<Texture2D>(name) : null;
			}
			return pages;
		}

		private static void UnloadVisuals() {
			bodyPages = null;
			glowPages = null;
			nearPages = null;
			farPages = null;
			Array.Clear(goreTypes);
		}

		// ------------------------------------------------------------------------------------------------------------
		// Pose: which body and arm frames to show (pure function of the synced state, so the mouth and hand points the AI
		// reads are the same on every side)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>
		/// The pose for the synced state and timer. Every key pose is reached through an in-between (2026-10-26): the
		/// fist leaves the ground, rises, cocks back and swings through before it lands, then lifts and lowers back to
		/// rest; the body leans into the wind-up, through the strike and settles; the jaw opens and closes in steps; the
		/// spit has a wind-up and a follow-through; the death sags through three tweens.
		/// </summary>
		public void ResolvePose(out int body, out int arm) {
			int t = (int)Timer;
			body = R.BodyIdle0 + (int)(Main.GameUpdateCount / 8 % 4);
			arm = R.RestFrame;
			switch (CurrentPhase) {
				case Phase.Emerge:
					if (t < RumbleTicks + RiseTicks) {
						arm = CrawlStep(t) % R.CrawlFrames;              // clawing its way out
						body = R.BodyIdle0;
					}
					else {
						int roar = t - RumbleTicks - RiseTicks;           // the jaw drops open, then the roar
						body = roar < 3 ? R.BodyJawOpen1 : (roar < 6 ? R.BodyJawOpen2 : R.BodySuck0 + (t / 3) % 4);
					}
					break;
				case Phase.Crawl:
					arm = CrawlFrame;
					body = R.BodyIdle0 + (t / 9) % 4;
					break;
				case Phase.SlamWindup:
					if (Arg == 1f) {                                         // enraged second slam: the far claw
						int strike = SecondSlamWindupTicks - StrikeTicks;
						if (t < 4) {
							body = R.BodySlamHit;                            // the near fist has just landed
							arm = R.ArmSlamHit;
						}
						else if (t < SecondSlamLiftTicks) {
							body = R.BodySlamSettle;
							arm = R.ArmSlamLift;
						}
						else if (t < SecondSlamPrepTicks) {
							body = R.BodySlamWind0;
							arm = R.ArmFarSlamPrep;                          // the fist goes down, the claw comes up
						}
						else {
							body = t >= strike ? R.BodySlamStrike : R.BodySlamWind;
							arm = t < SecondSlamRaiseTicks ? R.ArmFarSlamRaise : (t < strike ? R.ArmFarSlamHigh : R.ArmFarSlamStrike);
						}
					}
					else if (t < SlamLiftTicks) {
						body = R.BodySlamWind0;
						arm = R.ArmSlamRaise0;                               // the fist leaves the ground
					}
					else if (t < SlamRiseTicks) {
						body = R.BodySlamWind;
						arm = R.ArmSlamRaise1;
					}
					else {
						int strike = SlamWindupTicks - StrikeTicks;
						body = t >= strike ? R.BodySlamStrike : R.BodySlamWind;
						arm = t < SlamRaiseTicks ? R.ArmSlamRaise : (t < SlamCockTick ? R.ArmSlamHigh : (t < strike ? R.ArmSlamCock : R.ArmSlamStrike));
					}
					break;
				case Phase.SlamRecover:
					body = t < 12 ? R.BodySlamHit : (t < 24 ? R.BodySlamSettle : R.BodyIdle0);
					if (Arg == 1f) {
						arm = t < 20 ? R.ArmFarSlamHit : (t < 27 ? R.ArmFarSlamLift : (t < 34 ? R.ArmFarSlamLower : R.RestFrame));
					}
					else {
						arm = t < 20 ? R.ArmSlamHit : (t < 27 ? R.ArmSlamLift : (t < 34 ? R.ArmSlamLower : R.RestFrame));
					}
					break;
				case Phase.SuckWindup:
					body = t < 15 ? R.BodyJawOpen1 : (t < 30 ? R.BodyJawOpen2 : R.BodySuck0 + (t / 3) % 4);
					break;
				case Phase.Suck:
					body = R.BodySuck0 + (t / 3) % 4;
					break;
				case Phase.SwallowPlayer:
				case Phase.Gulp:
					body = t < 3 ? R.BodyJawOpen2 : (t < 6 ? R.BodyJawOpen1 : R.BodyGulp0 + (t / 8) % 2);   // the jaw shuts in steps
					break;
				case Phase.SpitPlayer:
					body = SpitBody(t, SpitReleaseTick);
					break;
				case Phase.SpitScrap:
					if (t < SpitVolleyInterval) {
						body = t < 6 ? R.BodySpitWind0 : R.BodySpitWind;
					}
					else {
						int beat = t % SpitVolleyInterval;                   // spit on the volley tick, follow through, wind again
						body = beat < 3 ? R.BodySpit : (beat < 6 ? R.BodySpitFollow : R.BodySpitWind);
					}
					break;
				case Phase.SpitBall:
					body = SpitBody(t, SpitBallWindTicks);
					break;
				case Phase.Retreat:
					arm = CrawlStep(t) % R.CrawlFrames;
					break;
				case Phase.Dying:
					if (t < DeathSagTick) {
						body = R.BodyDeathJolt;
						arm = R.ArmDeathJolt;
					}
					else if (t < DeathSagTick + DeathTweenTicks) {
						body = R.BodyDeathJoltSag;
						arm = R.ArmDeathJoltSag;
					}
					else if (t < DeathSlumpTick) {
						body = R.BodyDeathSag;
						arm = R.ArmDeathSag;
					}
					else if (t < DeathSlumpTick + DeathTweenTicks) {
						body = R.BodyDeathSagSlump;
						arm = R.ArmDeathSagSlump;
					}
					else if (t < DeathDownTick) {
						body = R.BodyDeathSlump;
						arm = R.ArmDeathSlump;
					}
					else if (t < DeathDownTick + DeathTweenTicks) {
						body = R.BodyDeathSlumpDown;
						arm = R.ArmDeathSlumpDown;
					}
					else {
						body = R.BodyDeathDown;
						arm = R.ArmDeathDown;
					}
					break;
			}
			// Body idle frames only animate breathing, never the mouth: the AI reads the mouth from body frames, and the
			// idle frames share one mouth point, so the GameUpdateCount term above cannot desync anything.
		}

		/// <summary>A spit that releases at <paramref name="release"/>: a wind-up, the spit, a follow-through, then rest.</summary>
		private static int SpitBody(int t, int release) {
			if (t < release) {
				return t < 6 ? R.BodySpitWind0 : R.BodySpitWind;
			}
			return t < release + 8 ? R.BodySpit : (t < release + 16 ? R.BodySpitFollow : R.BodyIdle0);
		}

		// ------------------------------------------------------------------------------------------------------------
		// Intro / death timing shared by the camera and the drawing
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>0..1: how firmly <paramref name="viewer"/>'s camera is locked on the boss right now.</summary>
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

		/// <summary>Pixels of the rig still below the ground line (even, so the 2x art stays on its grid).</summary>
		private int BuriedPixels() {
			float buried;
			int full = R.BodyMaxHeight + 44;                 // enough to hide the raised parts too
			switch (CurrentPhase) {
				case Phase.Emerge:
					if (Timer < RumbleTicks) {
						return full;
					}
					float p = MathHelper.Clamp((Timer - RumbleTicks) / RiseTicks, 0f, 1f);
					float eased = 1f - (1f - p) * (1f - p);
					eased += 0.035f * MathF.Sin(p * MathHelper.TwoPi * 3f) * (1f - p);   // three heaves, settling
					buried = (1f - MathHelper.Clamp(eased, 0f, 1f)) * full;
					break;
				case Phase.Retreat:
					float q = MathHelper.Clamp(Timer / RetreatTicks, 0f, 1f);
					buried = q * q * full;
					break;
				default:
					return 0;
			}
			return Math.Clamp((int)(buried * 0.5f) * 2, 0, full);
		}

		// ------------------------------------------------------------------------------------------------------------
		// Client effects (every effect is derived from the synced state; one-shots are keyed so a timer resync from the
		// server never plays them twice)
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>True once per tick of the current state, for one-shot sounds and bursts on clients. Keys only grow within
		/// a state (callers ask in ascending tick order), so a timer resync from the server never replays one; entering
		/// a state resets them (<see cref="ResetEffectKeys"/>).</summary>
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

		private void Punch(Vector2 at, Vector2 direction, float strength, int frames, string id) {
			if (Shake) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(at, direction, strength, 10f, frames, 2400f, id));
			}
		}

		private void EmergeEffects() {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(CameraFocus, lockAmount);
			}
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.DeerclopsRubbleAttack with { Pitch = -0.5f }, NPC.Bottom);
				Punch(NPC.Bottom, Vector2.UnitY, 3f, RumbleTicks + RiseTicks, "Cogpunk:TrashTr0mRumble");
			}
			int t = (int)Timer;
			if (t < RumbleTicks + RiseTicks && t % 2 == 0) {
				GroundDebris(t < RumbleTicks ? 1 : 3);
			}
			if (Once(BurstTick)) {
				SoundEngine.PlaySound(SoundID.DD2_ExplosiveTrapExplode with { Pitch = -0.4f }, NPC.Bottom);
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f }, NPC.Bottom);
				Punch(NPC.Bottom, Vector2.UnitY, FromHeap ? 14f : 8f, 30, "Cogpunk:TrashTr0mBurst");
				BurstDebris(FromHeap ? 70 : 30);
			}
			if (Once(RumbleTicks + 45) || Once(RumbleTicks + 90)) {
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f, Volume = 0.8f }, NPC.Bottom);   // a heave
			}
			if (TitleShown == 0f && t >= TitleTick && lockAmount > 0f) {
				TitleShown = 1f;
				BossTitleSystem.Show(DisplayName, epithet, TitleHoldTicks);
			}
			if (Once(RumbleTicks + RiseTicks)) {
				SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.45f }, NPC.Center);
				Punch(NPC.Center, Vector2.UnitX, 9f, 40, "Cogpunk:TrashTr0mRoar");
			}
			if (t >= RumbleTicks + RiseTicks && t % 15 == 0) {
				SoundEngine.PlaySound(SoundID.Item22 with { Pitch = -0.4f, MaxInstances = 2 }, MouthWorld());
				ExhaustPuff(3);
			}
		}

		/// <summary>Per-state visuals and sounds while fighting.</summary>
		private void StateEffects() {
			EnrageEffects();
			int t = (int)Timer;
			switch (CurrentPhase) {
				case Phase.Crawl:
					if ((t + NPC.whoAmI * 7) % 24 == 0) {
						ExhaustPuff(1);
					}
					break;
				case Phase.SlamWindup:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.Item23 with { Pitch = -0.7f, Volume = 0.9f }, NPC.Center);   // hydraulics
					}
					if (FarArmSlam && Once(2)) {
						SlamImpact(SlamPoint(false));              // the near fist's blow (the state changed on its impact tick)
					}
					if (Once(FarArmSlam ? SecondSlamRaiseTicks : SlamRaiseTicks)) {
						SoundEngine.PlaySound(SoundID.DD2_OgreAttack with { Pitch = FarArmSlam ? -0.1f : -0.3f }, NPC.Center);
					}
					if (t % 4 == 0) {
						SlamTelegraph();
					}
					break;
				case Phase.SlamRecover:
					if (Once(0)) {
						SlamImpact(SlamPoint(FarArmSlam));
					}
					break;
				case Phase.SuckWindup:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.DD2_BetsyWindAttack with { Pitch = -0.6f }, MouthWorld());
					}
					break;
				case Phase.Suck:
					if (t % 30 == 0) {
						SoundEngine.PlaySound(SoundID.DD2_BookStaffTwisterLoop with { Pitch = -0.5f, MaxInstances = 2 }, MouthWorld());
					}
					SuckStreaks();
					break;
				case Phase.SwallowPlayer:
					if (Once(0)) {
						SoundEngine.PlaySound(SoundID.NPCDeath14 with { Pitch = 0.3f, Volume = 0.7f }, MouthWorld());
					}
					if (t % 8 == 0) {
						SoundEngine.PlaySound(SoundID.Item22 with { Pitch = -0.2f, Volume = 0.6f, MaxInstances = 2 }, MouthWorld());
					}
					break;
				case Phase.Gulp:
					if (Once(0)) {
						SoundEngine.PlaySound(SoundID.Item2 with { Pitch = -0.8f }, MouthWorld());      // gulp
					}
					break;
				case Phase.SpitPlayer:
					if (Once(SpitReleaseTick)) {
						SoundEngine.PlaySound(SoundID.Item62 with { Pitch = -0.4f }, MouthWorld());
						SpitDust(18, backwards: true);             // the player goes up and back over it
					}
					break;
				case Phase.SpitScrap:
					if (t >= SpitVolleyInterval && t % SpitVolleyInterval == 0 && Once(t)) {
						SoundEngine.PlaySound(SoundID.Item61 with { Pitch = -0.3f }, MouthWorld());
						SpitDust(8);
					}
					break;
				case Phase.SpitBall:
					if (Once(SpitBallWindTicks)) {
						SoundEngine.PlaySound(SoundID.Item62 with { Pitch = -0.6f }, MouthWorld());
						SpitDust(14);
					}
					break;
			}
		}

		private void SlamImpact(Vector2 fist) {
			SoundEngine.PlaySound(SoundID.DD2_OgreGroundPound with { Pitch = -0.2f }, fist);
			SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.3f }, fist);
			Punch(fist, Vector2.UnitY, 12f, 24, "Cogpunk:TrashTr0mSlam");
			ImpactDust(fist, 26);
		}

		/// <summary>Once per client when the enraged flag arrives: a roar, steam venting from every seam, a shake.</summary>
		private void EnrageEffects() {
			if (!Enraged || NPC.localAI[3] != 0f || IsDying) {
				return;
			}
			NPC.localAI[3] = 1f;
			SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.6f }, NPC.Center);
			SoundEngine.PlaySound(SoundID.Item34 with { Pitch = -0.4f }, NPC.Center);
			Punch(NPC.Center, Vector2.UnitX, 10f, 36, "Cogpunk:TrashTr0mEnrage");
			for (int i = 0; i < 40; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 4 == 0 ? DustID.Torch : DustID.Smoke, out Dust d,
					0f, -2f, 80, new Color(238, 241, 243), 1.6f)) {
					d.velocity *= 2f;
					d.noGravity = true;
				}
			}
		}

		private void DeathEffects() {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(CameraFocus, lockAmount);
			}
			int t = (int)Timer;
			if (Once(0)) {
				SoundEngine.PlaySound(SoundID.NPCDeath14 with { Pitch = -0.5f }, NPC.Center);
				SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.8f, Volume = 0.8f }, NPC.Center);
				Punch(NPC.Center, Vector2.UnitX, 10f, 30, "Cogpunk:TrashTr0mDeath0");
			}
			if (t < DeathBlastTick && t % 11 == 0) {
				SmallBlast();                              // the machine pops apart, part by part
			}
			if (Once(DeathSlumpTick)) {
				SoundEngine.PlaySound(SoundID.DD2_OgreGroundPound with { Pitch = -0.6f }, NPC.Bottom);
				Punch(NPC.Bottom, Vector2.UnitY, 10f, 30, "Cogpunk:TrashTr0mDeath1");
				GroundDebris(30);
			}
			if (Once(DeathDownTick)) {
				SoundEngine.PlaySound(SoundID.Item34 with { Pitch = -0.8f }, NPC.Center);          // the last steam escapes
			}
			if (t >= DeathDownTick && t % 3 == 0) {
				ExhaustPuff(2);
			}
			if (Once(DeathBlastTick)) {
				SoundEngine.PlaySound(SoundID.DD2_ExplosiveTrapExplode with { Pitch = -0.6f }, NPC.Center);
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.8f }, NPC.Center);
				Punch(NPC.Center, Vector2.UnitY, 16f, 40, "Cogpunk:TrashTr0mDeath2");
				ThrowGores();                              // the defeat card follows from BossNPC (DefeatCardTick)
			}
		}

		private void DragEffects() {
			int arm = CrawlFrame;
			int previous = (arm + R.CrawlFrames - 1) % R.CrawlFrames;
			Vector2 hand = previous >= 3 && previous <= 5 ? NearHandWorld(arm) : FarHandWorld(arm);   // whichever hand drags
			for (int i = 0; i < 2; i++) {
				if (CogpunkClientConfig.RollEffect()) {
					SafeSpawn.TryTileDust((int)(hand.X / 16f) + Main.rand.Next(-1, 2), (int)(hand.Y / 16f) + 1);
				}
			}
			if (Main.rand.NextBool(3)) {
				SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.8f, Volume = 0.35f, MaxInstances = 2 }, hand);   // scraping
			}
		}

		private void SlamTelegraph() {
			Vector2 fist = SlamPoint(FarArmSlam);
			if (CogpunkClientConfig.RollEffect() && SafeSpawn.TryNewDust(fist - new Vector2(24f, 4f), 48, 4, DustID.Torch, out Dust d, 0f, -1f)) {
				d.noGravity = true;                        // ember sparks mark where the fist will land (hostile colours)
				d.velocity *= 0.3f;
			}
			if (CogpunkClientConfig.RollEffect() && SafeSpawn.TryNewDust(NPC.Center + new Vector2(-NPC.spriteDirection * 20f, -150f), 30, 20,
				DustID.Smoke, out Dust s, 0f, -1.5f, 100, new Color(195, 200, 205), 1.2f)) {
				s.noGravity = true;                        // hydraulic steam from the raised arm
			}
		}

		private void SuckStreaks() {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			Vector2 mouth = MouthWorld();
			float strength = SuckStrength;
			for (int i = 0; i < 2; i++) {
				float angle = (NPC.spriteDirection == 1 ? 0f : MathHelper.Pi) + Main.rand.NextFloat(-0.9f, 0.9f);
				float dist = Main.rand.NextFloat(120f, 420f) * (Enraged ? EnragedSuckScale : 1f);
				Vector2 at = mouth + angle.ToRotationVector2() * dist;
				if (SafeSpawn.TryNewDust(at, 4, 4, DustID.Smoke, out Dust d, 0f, 0f, 120, new Color(238, 241, 243), 0.9f)) {
					d.noGravity = true;                    // air streaks rushing into the mouth
					d.velocity = (mouth - at).SafeNormalize(Vector2.Zero) * (6f + 6f * strength);
					d.fadeIn = 0.6f;
				}
			}
		}

		private void EatEffect(Vector2 at) {
			for (int i = 0; i < 4; i++) {
				if (SafeSpawn.TryNewDust(at, 4, 4, DustID.Torch, out Dust d)) {
					d.velocity *= 0.8f;
				}
			}
		}

		private void SpitDust(int count, bool backwards = false) {
			Vector2 mouth = MouthWorld();
			for (int i = 0; i < count; i++) {
				float vx = NPC.spriteDirection * Main.rand.NextFloat(2f, 6f) * (backwards ? -0.6f : 1f);
				float vy = backwards ? Main.rand.NextFloat(-7f, -3f) : Main.rand.NextFloat(-3f, 1f);
				if (CogpunkClientConfig.RollEffect() && SafeSpawn.TryNewDust(mouth - new Vector2(10f), 20, 20, i % 3 == 0 ? DustID.Torch : DustID.Smoke,
					out Dust d, vx, vy, 80, default, 1.3f)) {
					d.noGravity = i % 3 != 0;
				}
			}
		}

		/// <summary>The stacks before a cog: a rattling hiss, puffs of steam growing, sparks at the very end (clients).</summary>
		private void CogTelegraph(int t) {
			Vector2 stack = CogStackWorld;
			if (t == 0) {
				SoundEngine.PlaySound(SoundID.Item34 with { Pitch = -0.5f, Volume = 0.45f, MaxInstances = 2 }, stack);   // the valve hisses
			}
			if (t % 10 == 5) {
				SoundEngine.PlaySound(SoundID.Item52 with { Pitch = 0.5f, Volume = 0.3f, MaxInstances = 3 }, stack);    // the cog rattles inside
			}
			if (t % 3 == 0 && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(stack - new Vector2(8f, 6f), 16, 8, DustID.Smoke, out Dust s, 0f, -1.5f - t * 0.05f, 100,
					new Color(195, 200, 205), 1f + t * 0.03f)) {
				s.noGravity = true;
			}
			if (t >= CogTelegraphTicks - 8 && Main.rand.NextBool(2)
				&& SafeSpawn.TryNewDust(stack - new Vector2(4f), 8, 8, DustID.Torch, out Dust e, 0f, -2f)) {
				e.noGravity = true;
			}
		}

		/// <summary>The cog leaves the stack: a cough of smoke and embers (clients).</summary>
		private void CogLaunchEffects() {
			Vector2 stack = CogStackWorld;
			SoundEngine.PlaySound(SoundID.Item61 with { Pitch = 0.2f, Volume = 0.7f, MaxInstances = 3 }, stack);
			for (int i = 0; i < 10; i++) {
				if (SafeSpawn.TryNewDust(stack - new Vector2(8f), 16, 16, i % 3 == 0 ? DustID.Torch : DustID.Smoke, out Dust d,
					Main.rand.NextFloat(-1.5f, 1.5f), -Main.rand.NextFloat(2f, 5f), 80, i % 3 == 0 ? default : new Color(127, 135, 148), 1.3f)) {
					d.noGravity = i % 3 != 0;
				}
			}
		}

		private void ImpactDust(Vector2 at, int count) {
			int tileX = (int)(at.X / 16f);
			int tileY = (int)(at.Y / 16f);
			for (int i = 0; i < count; i++) {
				if (!SafeSpawn.TryTileDust(tileX + Main.rand.Next(-3, 4), tileY + 1)
					&& SafeSpawn.TryNewDust(at - new Vector2(30f, 6f), 60, 8, DustID.Smoke, out Dust d, Main.rand.NextFloat(-4f, 4f), -Main.rand.NextFloat(1f, 5f))) {
					d.noGravity = false;
				}
			}
		}

		/// <summary>Scrap dust thrown up along the ground line under the boss.</summary>
		private void GroundDebris(int count) {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			int left = (int)((NPC.Bottom.X - 200f) / 16f);
			int row = (int)(NPC.Bottom.Y / 16f);
			for (int i = 0; i < count; i++) {
				int x = left + Main.rand.Next(25);
				if (!SafeSpawn.TryTileDust(x, row) && !SafeSpawn.TryTileDust(x, row - 1)) {
					SafeSpawn.TryNewDust(new Vector2(x * 16f, row * 16f - 8f), 16, 8, DustID.Smoke, out _, 0f, -1.5f, 120, new Color(127, 135, 148));
				}
			}
		}

		/// <summary>The heap blowing apart: scrap dust flung up and out over the burst (the tiles themselves are cleared
		/// by the server, <see cref="TrashTr0mSummon.ClearHeapRows"/>).</summary>
		private void BurstDebris(int count) {
			int dust = ModContent.GetInstance<RustedScrapTile>().DustType;
			for (int i = 0; i < count; i++) {
				Vector2 at = NPC.Bottom + new Vector2(Main.rand.NextFloat(-220f, 220f), -Main.rand.NextFloat(0f, 180f));
				float vx = (at.X - NPC.Bottom.X) * 0.04f + Main.rand.NextFloat(-2f, 2f);
				if (SafeSpawn.TryNewDust(at, 8, 8, i % 4 == 0 ? DustID.Smoke : dust, out Dust d, vx, -Main.rand.NextFloat(4f, 11f), 0, default, 1.4f)) {
					d.noGravity = false;
				}
			}
		}

		private void ExhaustPuff(int count) {
			for (int i = 0; i < count; i++) {
				Vector2 at = RigToWorld(Main.rand.NextBool() ? 106 : 132, Main.rand.NextBool() ? -326 : -306);
				if (CogpunkClientConfig.RollEffect() && SafeSpawn.TryNewDust(at - new Vector2(4f), 8, 8, DustID.Smoke, out Dust smoke, 0f, 0f, 100, new Color(195, 200, 205), 1.4f)) {
					smoke.velocity = new Vector2(Main.rand.NextFloat(-0.4f, 0.4f) + NPC.spriteDirection * -0.6f, -Main.rand.NextFloat(1.5f, 2.5f));
					smoke.noGravity = true;
				}
			}
		}

		private void SmallBlast() {
			Vector2 at = NPC.Center + new Vector2(Main.rand.NextFloat(-150f, 150f), Main.rand.NextFloat(-110f, 90f));
			SoundEngine.PlaySound(SoundID.Item14 with { Pitch = 0.2f, Volume = 0.55f, MaxInstances = 3 }, at);
			for (int i = 0; i < 10; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(8f), 16, 16, i < 4 ? DustID.Torch : DustID.Smoke, out Dust d, 0f, 0f, 60, default, i < 4 ? 1.6f : 1.3f)) {
					d.velocity *= i < 4 ? 2.4f : 1.2f;
					d.noGravity = i >= 4;
				}
			}
		}

		/// <summary>The final blast: parts fly off (the tyre, the jaw, the crest, a gear, a piston, a plate).</summary>
		private void ThrowGores() {
			if (GoresThrown != 0f) {
				return;
			}
			GoresThrown = 1f;
			for (int i = 0; i < goreTypes.Length; i++) {
				if (goreTypes[i] <= 0) {
					continue;
				}
				Vector2 at = NPC.Center + new Vector2(Main.rand.NextFloat(-120f, 120f), Main.rand.NextFloat(-120f, 40f));
				Vector2 velocity = new(Main.rand.NextFloat(-7f, 7f), -Main.rand.NextFloat(5f, 11f));
				SafeSpawn.TryNewGore(NPC.GetSource_Death(), at, velocity, goreTypes[i], out _);
			}
			for (int i = 0; i < 40; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Torch : DustID.Smoke, out Dust d, 0f, -2f, 60, default, 1.8f)) {
					d.velocity *= 2.5f;
				}
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int sparks = NPC.life > 0 ? 3 : 30;
			for (int i = 0; i < sparks; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, NPC.life > 0 ? DustID.Iron : DustID.Torch, out Dust d)) {
					d.velocity *= NPC.life > 0 ? 1f : 3f;
				}
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Drawing (clients): far arm, body, glow, near arm, with a small multiplane parallax (Core/Visuals/DepthLayers)
		// ------------------------------------------------------------------------------------------------------------

		public override void FindFrame(int frameHeight) {
			NPC.frame = new Rectangle(0, 0, R.BodyBoundsWidth, R.BodyBoundsHeight);   // the bestiary sizes its box from this
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			bool dummy = NPC.IsABestiaryIconDummy;
			float scale = dummy ? NPC.scale : 1f;
			int body, arm;
			if (dummy) {
				body = R.BodyIdle0;
				arm = R.RestFrame;
			}
			else {
				ResolvePose(out body, out arm);
			}
			int buried = dummy ? 0 : BuriedPixels();
			Vector2 anchor = RigOrigin - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;
			Color light = NPC.GetAlpha(drawColor);
			Vector2 farShift = dummy ? Vector2.Zero : DepthLayers.Shift(anchor, DepthLayers.Far, MaxParallax);
			Vector2 nearShift = dummy ? Vector2.Zero : DepthLayers.Shift(anchor, DepthLayers.Near, MaxParallax);
			DepthLayers.DrawFrame(spriteBatch, farPages, R.FarFrames, arm, anchor + farShift, buried, DepthLayers.Tint(light, DepthLayers.Far), flip, scale);
			DepthLayers.DrawFrame(spriteBatch, bodyPages, R.BodyFrames, body, anchor, buried, light, flip, scale);
			// Eyes, furnace, throat and the live wire at full brightness; they flicker out as it dies.
			float pulse = 0.85f + 0.15f * MathF.Sin(Main.GlobalTimeWrappedHourly * 4f);
			if (IsDying) {
				pulse = Timer >= DeathDownTick ? 0f : (Main.rand.NextBool(4) ? 0.3f : 0.9f);
			}
			if (pulse > 0f) {
				DepthLayers.DrawFrame(spriteBatch, glowPages, R.GlowFrames, body, anchor, buried, Color.White * pulse * NPC.Opacity, flip, scale);
			}
			DepthLayers.DrawFrame(spriteBatch, nearPages, R.NearFrames, arm, anchor + nearShift, buried, light, flip, scale);
			return false;
		}
	}
}
