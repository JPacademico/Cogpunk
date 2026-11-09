using System;
using Cogpunk.Content.Bosses.CursedConductor.Projectiles;
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
using R = Cogpunk.Content.Bosses.CursedConductor.CursedConductorRigData;

namespace Cogpunk.Content.Bosses.CursedConductor
{
	/// <summary>
	/// The Cursed Conductor's look (clients only): his frames from the synced state and timers, his two planes drawn with
	/// <see cref="DepthLayers"/> (2-column grid sheets, art/bosses/cursedconductor/make_conductor_art.py; the far plane went
	/// with the ghost tail, 2026-11-05b: the lantern arm is in front of him now) and the glow sheet at full brightness; his
	/// turbine (2026-11-05b): its vanes spinning past the drum's window on their own clock (an overlay sheet riding each
	/// frame's bob, <see cref="CursedConductorRigData.Bob"/>) and the soot it pumps out of the bell (a pool of pixel-art puffs
	/// drawn behind him); the telegraphs: the passive train's stretch of ghost track across its target's screen with a ghost
	/// rift where it will come out, the loop's ring of ghost lights, the whistle's wave of lights; the camera locks of his
	/// intro and death, his sounds, his ghost-light dust, the fury's flare, and his death: the last train blows him to bits.
	/// <para>D1: textures requested once in <see cref="LoadVisuals"/>; a telegraph is a run of one small sprite (at most ~130
	/// draws), the smoke at most <see cref="SmokeCapacity"/> draws from a fixed array (allocated once, on the first client
	/// update); no allocation per frame. D4: every sprite drawn at whole pixels, never rotated or scaled (a puff may be
	/// mirrored); the fades are opacity only.</para>
	/// </summary>
	public partial class CursedConductor
	{
		public const float MaxParallax = 4f;
		public const int IdleFrameTicks = 8;
		private const int RailPiece = 16;                   // game px between pieces of the track (the piece's length)
		private const int RingDots = 48;
		private const int WaveDot = 24;                     // game px between the wave's lights
		public const int DeathBits = 40;
		// the turbine (2026-11-05b): the vanes advance a frame every RotorTicks (FuryRotorTicks furious; slowing to a stop as
		// he dies); a puff of smoke every SmokeInterval ticks (fewer as he dies), each living SmokeLife ticks
		public const int RotorTicks = 2, FuryRotorTicks = 1, DyingRotorTicks = 6;
		public const int SmokeCapacity = 32, SmokeLife = 48, SmokeInterval = 3, FurySmokeInterval = 2, DyingSmokeInterval = 7;
		public const float SmokeSpeed = 2.9f, SmokeDrag = 0.94f, SmokeRise = 0.05f, SmokeSpread = 6f, SmokeOpacity = 0.85f;

		private static Asset<Texture2D> nearSheet, glowSheet, rail, railDiagonal, riftSheet, rotorSheet, smokeSheet, lanternGlowSheet;
		public const int InBetweenTicks = 6;                // an in-between frame out of the rest pose or back into it
		public const int PointTicks = 40;                   // the arm out, sending the loop's train

		private struct SmokePuff
		{
			public Vector2 Position, Velocity;
			public short Age, Life;
			public bool Flip;
		}

		private SmokePuff[] smoke;
		private int smokeNext;

		private ref float TitleShown => ref NPC.localAI[0];
		private ref float LastEffectKey => ref NPC.localAI[1];
		private int effectState = -1;
		private bool enrageSeen, furySeen;

		private static void LoadVisuals() {
			if (Main.dedServ) {
				return;
			}
			const string path = "Cogpunk/Content/Bosses/CursedConductor/CursedConductor";
			nearSheet = DepthLayers.RequestOptional(path + "_Near");
			glowSheet = DepthLayers.RequestOptional(path + "_Glow");
			rotorSheet = DepthLayers.RequestOptional(path + "_Rotor");
			smokeSheet = DepthLayers.RequestOptional(path + "_Smoke");
			lanternGlowSheet = DepthLayers.RequestOptional(path + "_LanternGlow");
			rail = DepthLayers.RequestOptional("Cogpunk/Content/Bosses/CursedConductor/Projectiles/GhostTrain_Rail");
			railDiagonal = DepthLayers.RequestOptional("Cogpunk/Content/Bosses/CursedConductor/Projectiles/GhostTrain_RailDiagonal");
			riftSheet = DepthLayers.RequestOptional("Cogpunk/Content/Bosses/CursedConductor/Projectiles/GhostRift");
		}

		private static void UnloadVisuals() {
			nearSheet = glowSheet = rail = railDiagonal = riftSheet = rotorSheet = smokeSheet = lanternGlowSheet = null;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Frames
		// ------------------------------------------------------------------------------------------------------------

		private static int IdleFrame => R.Idle + (int)(Main.GameUpdateCount / IdleFrameTicks % R.IdleFrames);

		/// <summary>The frame for the current state and tick (every side computes the same from the synced state). Since
		/// 2026-11-09 every sequence leaves the rest pose (the lantern held before his chest) through an in-between and comes
		/// back through one; the lantern attack has no frames (its cue is the halo, <see cref="DrawLanternGlow"/>).</summary>
		public int ResolveFrame() {
			int t = (int)Timer;
			switch (CurrentPhase) {
				case Phase.Intro:
					if (t < TipStart - InBetweenTicks || t >= TipEnd + InBetweenTicks) {
						return IdleFrame;
					}
					if (t < TipStart) {
						return R.TipIn;
					}
					if (t >= TipEnd) {
						return R.TipOut;
					}
					return R.Tip + (t < TipRaise ? 0 : t < TipBow ? 1 : 2);
				case Phase.Loop:
					if (t < LoopTelegraph) {
						return t < InBetweenTicks ? R.Whistle : R.Call + (t / 8 % R.CallFrames);   // the whistle up, blowing
					}
					int p = t - LoopTelegraph;
					if (p < InBetweenTicks) {
						return R.PointIn;
					}
					if (p < PointTicks) {
						return R.Point + (p / 10 % R.PointFrames);
					}
					return p < PointTicks + InBetweenTicks ? R.PointOut : IdleFrame;
				case Phase.Whistle:
					if (t < 8 || t >= WhistleTicks - 8) {
						return R.Whistle;                       // the hand on its way up, and down again at the end
					}
					if (t < 14) {
						return R.Whistle + 1;
					}
					return R.Call + (t / 8 % R.CallFrames);   // the whistle shrieking, the lantern blazing
				case Phase.Dying:
					return R.Dying + Math.Min(R.DyingFrames - 1, t / 30);
				default:
					return IdleFrame;
			}
		}

		/// <summary>0..1: how much of him there is (materializing, fading away, blown to bits).</summary>
		public float Fade {
			get {
				return CurrentPhase switch {
					Phase.Intro => MathHelper.Clamp(Timer / FadeTicks, 0f, 1f),
					Phase.Leaving => MathHelper.Clamp(1f - Timer / LeaveTicks, 0f, 1f),
					Phase.Dying => Timer >= PickupTick ? 0f : 1f,
					_ => 1f,
				};
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Drawing
		// ------------------------------------------------------------------------------------------------------------

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			bool dummy = NPC.IsABestiaryIconDummy;
			if (!dummy) {
				DrawTelegraphs(spriteBatch, screenPos);
				DrawSmoke(spriteBatch, screenPos);              // behind him: it pours out under the bell
			}
			float fade = dummy ? 1f : Fade;
			if (fade <= 0f) {
				return false;
			}
			Vector2 anchor = (dummy ? NPC.Bottom - new Vector2(0f, R.BodyBottom) : RigOrigin) - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;              // the art faces left
			int frame = dummy ? R.Idle : ResolveFrame();
			// a ghost: the world's light only darkens him so far (his curse glows), and he fades as a whole; furious, the curse
			// burns through brighter
			Color light = Color.Lerp(drawColor, Color.White, Furious ? 0.55f : 0.35f) * fade;
			Texture2D middle = TextureAssets.Npc[Type].Value;
			float shift = dummy ? 0f : MaxParallax;
			Vector2 nearShift = new(DepthLayers.Shift(anchor, DepthLayers.Near, shift).X, 0f);
			DepthLayers.DrawCell(spriteBatch, middle, frame, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY, anchor, 0, light, flip);
			DrawRotor(spriteBatch, anchor, frame, dummy ? 0 : RotorFrame, flip, light);
			if (nearSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, nearSheet.Value, frame, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY, anchor + nearShift, 0,
					light, flip);
			}
			if (glowSheet?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, glowSheet.Value, frame, R.Columns, R.CellWidth, R.CellHeight, 2, R.OriginX, R.OriginY, anchor, 0,
					Color.White * fade, flip);
			}
			if (!dummy) {
				DrawLanternGlow(spriteBatch, anchor + nearShift, frame, flip, fade);
			}
			return false;
		}

		/// <summary>The lantern attack's cue (user, 2026-11-09: "the visual cue for the attack is just a glow on the lantern"): a
		/// halo of ghost light round the glass, swelling through the sheet's first three frames over <see cref="ThrowWindup"/>
		/// ticks, its flash frame for a few ticks as the bolts fly, then fading. Light: full brightness, opacity only (D4).</summary>
		private void DrawLanternGlow(SpriteBatch spriteBatch, Vector2 anchor, int frame, bool flip, float fade) {
			if (throwTick < 0 || CurrentPhase == Phase.Dying || lanternGlowSheet?.IsLoaded != true) {
				return;
			}
			int k;
			float alpha;
			if (throwTick < ThrowWindup) {
				float u = throwTick / (float)ThrowWindup;
				k = Math.Min(2, (int)(u * 3f));
				alpha = 0.35f + 0.65f * u;
			}
			else if (throwTick < ThrowWindup + 6) {
				k = 3;
				alpha = 1f;
			}
			else {
				k = 2;
				alpha = MathHelper.Clamp(1f - (throwTick - ThrowWindup - 6) / (float)Math.Max(1, ThrowTicks - ThrowWindup - 6), 0f, 1f);
			}
			Texture2D texture = lanternGlowSheet.Value;
			int cell = R.LanternGlowCell;
			Rectangle source = new(0, k * (cell + 2), cell, cell);
			if (source.Bottom > texture.Height || alpha <= 0f) {
				return;
			}
			int bob = frame >= 0 && frame < R.Bob.Length ? R.Bob[frame] : 0;
			float x = anchor.X + (flip ? -R.LanternX : R.LanternX) - cell / 2;
			float y = anchor.Y + R.LanternY + bob - cell / 2;
			spriteBatch.Draw(texture, new Vector2(MathF.Round(x), MathF.Round(y)), source, Color.White * (alpha * fade));
		}

		// ------------------------------------------------------------------------------------------------------------
		// The turbine
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>The vanes' frame on the client's own clock (purely visual: no sync), faster furious, slowing as he dies.</summary>
		private int RotorFrame {
			get {
				int ticks = Furious ? FuryRotorTicks : RotorTicks;
				if (CurrentPhase == Phase.Dying) {
					ticks = RotorTicks + (int)(Timer / (PickupTick / (float)DyingRotorTicks));
				}
				return (int)(Main.GameUpdateCount / (uint)Math.Max(1, ticks) % R.RotorFrames);
			}
		}

		/// <summary>The vanes over the drum's window, at the window moved by this frame's bob, mirrored with him (DrawCell's
		/// mirror: an art rect [x, x + w) facing right is [-x - w, -x) from the origin).</summary>
		private static void DrawRotor(SpriteBatch spriteBatch, Vector2 anchor, int frame, int rotorFrame, bool flip, Color light) {
			if (rotorSheet?.IsLoaded != true) {
				return;
			}
			Texture2D texture = rotorSheet.Value;
			Rectangle source = new(0, rotorFrame * (R.RotorHeight + 2), R.RotorWidth, R.RotorHeight);
			if (source.Bottom > texture.Height) {
				return;
			}
			int bob = frame >= 0 && frame < R.Bob.Length ? R.Bob[frame] : 0;
			float x = flip ? anchor.X - R.RotorX - R.RotorWidth : anchor.X + R.RotorX;
			spriteBatch.Draw(texture, new Vector2(x, anchor.Y + R.RotorY + bob), source, light, 0f, Vector2.Zero, 1f,
				flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None, 0f);
		}

		/// <summary>How often the bell puffs now, or false while it doesn't (unseen, blown to bits, fading in or out).</summary>
		private bool Pumping(out int interval) {
			interval = Furious ? FurySmokeInterval : SmokeInterval;
			switch (CurrentPhase) {
				case Phase.Intro:
					return Timer >= FadeTicks / 2;
				case Phase.Leaving:
					return Timer < LeaveTicks / 2;
				case Phase.Dying:
					interval = DyingSmokeInterval;
					return Timer < PickupTick;
				default:
					return true;
			}
		}

		/// <summary>Clients, every tick: the puffs drift (a jet that slows, then rises a little as it cools), and a new one
		/// leaves the bell's mouth every so often, carried a little by his own motion.</summary>
		private void UpdateSmoke() {
			smoke ??= new SmokePuff[SmokeCapacity];
			for (int i = 0; i < smoke.Length; i++) {
				ref SmokePuff puff = ref smoke[i];
				if (puff.Age >= puff.Life) {
					continue;
				}
				puff.Age++;
				puff.Velocity *= SmokeDrag;
				puff.Velocity.Y -= SmokeRise;
				puff.Position += puff.Velocity;
			}
			if (!Pumping(out int interval) || Main.GameUpdateCount % (uint)interval != 0 || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			int frame = ResolveFrame();
			int bob = frame >= 0 && frame < R.Bob.Length ? R.Bob[frame] : 0;
			Vector2 mouth = RigPoint(R.ExhaustX, R.ExhaustY + bob);
			if (!MathSafety.IsFinite(mouth)) {
				return;
			}
			ref SmokePuff next = ref smoke[smokeNext];
			smokeNext = (smokeNext + 1) % smoke.Length;
			next.Position = mouth + new Vector2(Main.rand.NextFloat(-SmokeSpread, SmokeSpread), 0f);
			next.Velocity = new Vector2(Main.rand.NextFloat(-0.6f, 0.6f), SmokeSpeed * Main.rand.NextFloat(0.85f, 1.15f)) + NPC.velocity * 0.4f;
			next.Age = 0;
			next.Life = (short)(SmokeLife + Main.rand.Next(-6, 7));
			next.Flip = Main.rand.NextBool();
		}

		/// <summary>The puffs, each grown through the sheet's frames over its life and faded out over its last 40%, lit by the
		/// world (soot isn't light), at whole pixels.</summary>
		private void DrawSmoke(SpriteBatch spriteBatch, Vector2 screenPos) {
			if (smoke == null || smokeSheet?.IsLoaded != true) {
				return;
			}
			Texture2D texture = smokeSheet.Value;
			int cell = R.SmokeCell;
			for (int i = 0; i < smoke.Length; i++) {
				ref SmokePuff puff = ref smoke[i];
				if (puff.Age >= puff.Life || puff.Life <= 0) {
					continue;
				}
				float t = puff.Age / (float)puff.Life;
				int frame = Math.Min(R.SmokeFrames - 1, (int)(t * R.SmokeFrames));
				Rectangle source = new(0, frame * (cell + 2), cell, cell);
				if (source.Bottom > texture.Height) {
					continue;
				}
				float alpha = SmokeOpacity * (t < 0.6f ? 1f : 1f - (t - 0.6f) / 0.4f);
				Color light = Lighting.GetColor((int)(puff.Position.X / 16f), (int)(puff.Position.Y / 16f));
				Vector2 at = puff.Position - screenPos - new Vector2(cell * 0.5f);
				spriteBatch.Draw(texture, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), source, light * alpha, 0f, Vector2.Zero, 1f,
					puff.Flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None, 0f);
			}
		}

		/// <summary>The warnings in progress: the passive train's track (and the rift it comes out of), the loop's ring, the
		/// whistle's wave.</summary>
		private void DrawTelegraphs(SpriteBatch spriteBatch, Vector2 screenPos) {
			if (rail?.IsLoaded != true) {
				return;
			}
			Texture2D texture = rail.Value;
			int cell = R.RailCell;
			Vector2 half = new(cell * 0.5f);
			if (PassiveTelegraphNowFor(out Vector2 entry, out Vector2 exit, out byte kind, out float strength)) {
				Rectangle source = new(0, (kind == KindExpress ? 0 : 1) * (cell + 2), cell, cell);
				if (kind == KindDiagonal) {
					DrawDiagonalTrack(spriteBatch, screenPos, entry, exit, strength);
					DrawRift(spriteBatch, entry - screenPos, strength);
				}
				else if (source.Bottom <= texture.Height) {
					Color color = Color.White * (0.85f * strength);
					Vector2 d = exit - entry;
					float length = d.Length();
					Vector2 u = length > 1f ? d / length : Vector2.UnitX;
					for (float s = 0f; s <= length; s += RailPiece) {
						Vector2 at = entry + u * s - screenPos - half;
						spriteBatch.Draw(texture, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), source, color);
					}
					DrawRift(spriteBatch, entry - screenPos, strength);
				}
			}
			int t = (int)Timer;
			if (CurrentPhase == Phase.Loop && locked != Vector2.Zero) {
				float ring = TelegraphStrength(t, LoopTelegraph + LoopEnter);
				Rectangle source = new(0, 2 * (cell + 2), cell, cell);
				if (ring > 0f && source.Bottom <= texture.Height) {
					Color color = Color.White * (0.85f * ring);
					for (int k = 0; k < RingDots; k++) {
						float a = MathHelper.TwoPi * k / RingDots;
						Vector2 at = locked + new Vector2(MathF.Cos(a), MathF.Sin(a)) * LoopRadius - screenPos - half;
						spriteBatch.Draw(texture, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), source, color);
					}
				}
			}
			if (CurrentPhase == Phase.Whistle && locked != Vector2.Zero && WavePass(t, out int pass, out int local)) {
				float wave = TelegraphStrength(local, WaveTelegraph);
				Rectangle source = new(0, 2 * (cell + 2), cell, cell);
				if (wave > 0f && source.Bottom <= texture.Height) {
					Color color = Color.White * (0.85f * wave);
					float dir = pass == 0 ? 1f : -1f;
					for (float run = 0f; run <= 2f * ScreenHalfWidth; run += WaveDot) {
						float x = locked.X - dir * ScreenHalfWidth + dir * run;
						float y = locked.Y + GhostTrain.WaveAmplitude * MathF.Sin(wavePhase + MathHelper.TwoPi * run / GhostTrain.WaveLength);
						Vector2 at = new Vector2(x, y) - screenPos - half;
						spriteBatch.Draw(texture, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), source, color);
					}
					DrawRift(spriteBatch, new Vector2(locked.X - dir * ScreenHalfWidth, locked.Y + GhostTrain.WaveAmplitude * MathF.Sin(wavePhase)) - screenPos, wave);
				}
			}
		}

		/// <summary>The diagonal dive's warning (2026-11-09): its 45-degree track, a piece every
		/// <see cref="CursedConductorRigData.RailDiagonalStep"/> px each way (the pieces overlap into one line; at most about 70),
		/// mirrored for a track running down to the left.</summary>
		private static void DrawDiagonalTrack(SpriteBatch spriteBatch, Vector2 screenPos, Vector2 entry, Vector2 exit, float strength) {
			if (railDiagonal?.IsLoaded != true) {
				return;
			}
			Texture2D texture = railDiagonal.Value;
			int cell = R.RailDiagonalCell;
			if (texture.Width < cell || texture.Height < cell) {
				return;
			}
			Vector2 d = exit - entry;
			float sx = d.X >= 0f ? 1f : -1f, sy = d.Y >= 0f ? 1f : -1f;
			SpriteEffects effects = sx * sy < 0f ? SpriteEffects.FlipHorizontally : SpriteEffects.None;   // the art runs down-right
			Vector2 step = new(sx * R.RailDiagonalStep, sy * R.RailDiagonalStep);
			int count = Math.Min(200, (int)(Math.Abs(d.X) / R.RailDiagonalStep));
			Color color = Color.White * (0.85f * strength);
			Vector2 half = new(cell * 0.5f);
			for (int k = 0; k <= count; k++) {
				Vector2 at = entry + step * k - screenPos - half;
				spriteBatch.Draw(texture, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), null, color, 0f, Vector2.Zero, 1f, effects, 0f);
			}
		}

		/// <summary>A ghost rift opening where a train will burst out (the rift sheet, its frame by the warning's strength).</summary>
		private static void DrawRift(SpriteBatch spriteBatch, Vector2 at, float strength) {
			if (riftSheet?.IsLoaded != true) {
				return;
			}
			Texture2D texture = riftSheet.Value;
			int cell = R.RiftCell;
			int frame = Math.Clamp((int)(strength * R.RiftFrames), 0, R.RiftFrames - 1);
			Rectangle source = new(0, frame * (cell + 2), cell, cell);
			if (source.Bottom > texture.Height) {
				return;
			}
			Vector2 p = at - new Vector2(cell * 0.5f);
			spriteBatch.Draw(texture, new Vector2(MathF.Round(p.X), MathF.Round(p.Y)), source, Color.White * strength);
		}

		/// <summary>0..1 over a telegraph of <paramref name="length"/> ticks: in over its first third, held to its end, then
		/// out over 12 ticks as the train comes.</summary>
		private static float TelegraphStrength(int t, int length) {
			if (t <= 0) {
				return 0f;
			}
			if (t <= length) {
				return MathHelper.Clamp(t / (length / 3f), 0f, 1f);
			}
			return MathHelper.Clamp(1f - (t - length) / 12f, 0f, 1f);
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

		/// <summary>0..1: how firmly <paramref name="viewer"/>'s camera is locked on him (the intro and the death).</summary>
		public float CameraLock(Player viewer) {
			if (viewer == null || !viewer.active || Vector2.DistanceSquared(viewer.Center, CameraFocus) > CameraLockRange * CameraLockRange) {
				return 0f;
			}
			if (CurrentPhase == Phase.Intro) {
				return CinematicCamera.Envelope(Timer, IntroTicks, CameraEaseTicks, CameraEaseTicks);
			}
			if (IsDying) {
				return CinematicCamera.Envelope(Timer, DeathTicks, CameraEaseTicks, 40f);
			}
			return 0f;
		}

		private static readonly SoundStyle WhistleSound = SoundID.DD2_WyvernScream with { Pitch = 0.6f, Volume = 0.55f, MaxInstances = 2 };

		private void StateEffects() {
			int t = (int)Timer;
			GhostLight();
			UpdateSmoke();
			if (Enraged && !enrageSeen) {
				enrageSeen = true;
				SoundEngine.PlaySound(WhistleSound with { Pitch = 0.9f, Volume = 0.8f }, NPC.Center);   // the shriek of the enrage
				Steam(RigPoint(R.WhistleX, R.WhistleY), 10);
			}
			if (Furious != furySeen) {
				furySeen = Furious;
				if (Furious) {
					SoundEngine.PlaySound(SoundID.NPCDeath6 with { Pitch = -0.6f, Volume = 0.9f }, NPC.Center);   // furious: you left his town
					Mist(NPC.Center, 18);
				}
			}
			if (throwTick == 1) {
				SoundEngine.PlaySound(SoundID.Item8 with { Pitch = -0.4f }, NPC.Center);              // the flame flares
			}
			if (throwTick == ThrowWindup) {
				SoundEngine.PlaySound(SoundID.Item20 with { Pitch = -0.2f }, NPC.Center);
			}
			if (passiveTick == 1) {
				SoundEngine.PlaySound(SoundID.Item103 with { Pitch = -0.6f, Volume = 0.5f, MaxInstances = 2 }, passivePoint);   // the rift moans open
			}
			switch (CurrentPhase) {
				case Phase.Intro:
					IntroEffects(t);
					break;
				case Phase.Loop:
					if (Once(4)) {
						SoundEngine.PlaySound(WhistleSound with { Pitch = 0.4f }, NPC.Center);
						Steam(RigPoint(R.WhistleX, R.WhistleY), 6);
					}
					break;
				case Phase.Whistle:
					if (Once(10) || Once(WavePass2 - 10)) {
						SoundEngine.PlaySound(WhistleSound with { Pitch = 0.75f, Volume = 0.85f }, NPC.Center);   // the long shriek
						Steam(RigPoint(R.WhistleX, R.WhistleY), 10);
						Punch(NPC.Center, Vector2.UnitY, 3f, 24, "Cogpunk:ConductorWhistle");
					}
					if (t % 4 == 0 && t > 10 && CogpunkClientConfig.RollEffect()) {
						Steam(RigPoint(R.WhistleX, R.WhistleY), 1);
					}
					break;
				case Phase.Leaving:
					if (Once(1)) {
						SoundEngine.PlaySound(SoundID.NPCDeath6 with { Pitch = 0.2f, Volume = 0.6f }, NPC.Center);
					}
					if (t % 3 == 0) {
						Mist(NPC.Center, 2);
					}
					break;
				case Phase.Dying:
					DeathEffects(t);
					break;
			}
		}

		/// <summary>His eyes, his lantern and the cursed fire in his turbine's bell light the town around him; now and then a
		/// cursed spark spits out of the bell.</summary>
		private void GhostLight() {
			if (Fade <= 0f || Hidden) {
				return;
			}
			float k = Fade * (Furious ? 1.4f : 1f);
			Lighting.AddLight(RigPoint(R.EyesX, R.EyesY), 0.15f * k, 0.45f * k, 0.35f * k);
			float flare = throwTick >= 0 && throwTick <= ThrowWindup + 6 ? 1f + throwTick / (float)ThrowWindup : 1f;   // the attack's glow
			Lighting.AddLight(LanternPoint, 0.2f * k * flare, 0.6f * k * flare, 0.45f * k * flare);
			Lighting.AddLight(RigPoint(R.ExhaustX, R.ExhaustY), 0.1f * k, 0.35f * k, 0.25f * k);
			if (Main.rand.NextBool(Furious ? 4 : 10) && CogpunkClientConfig.RollEffect()) {
				Mist(RigPoint(R.ExhaustX, R.ExhaustY + 8), 1);
			}
		}

		private static void Mist(Vector2 at, int count) {
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(8f), 16, 16, DustID.CursedTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = new Vector2(Main.rand.NextFloat(-0.6f, 0.6f), Main.rand.NextFloat(0.2f, 1.2f));
					d.scale = Main.rand.NextFloat(0.8f, 1.3f);
				}
			}
		}

		private static void Steam(Vector2 at, int count) {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(4f), 8, 8, DustID.Smoke, out Dust d)) {
					d.noGravity = true;
					d.velocity = new Vector2(Main.rand.NextFloat(-1.6f, -0.4f), -Main.rand.NextFloat(0.6f, 2f));
					d.alpha = 120;
				}
			}
		}

		private void IntroEffects(int t) {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(CameraFocus, lockAmount);
			}
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.NPCDeath6 with { Pitch = -0.5f }, NPC.Center);          // a wail out of the dark
			}
			if (t < FadeTicks && t % 2 == 0) {
				Mist(NPC.Center + Main.rand.NextVector2Circular(50f, 80f), 2);
			}
			if (TitleShown == 0f && t >= TitleTick && lockAmount > 0f) {
				TitleShown = 1f;
				BossTitleSystem.Show(DisplayName, epithet, TitleHoldTicks);
			}
			if (Once(TipRaise)) {
				SoundEngine.PlaySound(WhistleSound with { Pitch = 0.3f }, NPC.Center);                // "all aboard"
				Steam(RigPoint(R.WhistleX, R.WhistleY), 8);
				Punch(NPC.Center, Vector2.UnitX, 4f, 30, "Cogpunk:ConductorIntro");
			}
		}

		private void DeathEffects(int t) {
			float lockAmount = CameraLock(Main.LocalPlayer);
			if (lockAmount > 0f) {
				CinematicCamera.Request(CameraFocus, lockAmount);
			}
			if (Once(1)) {
				SoundEngine.PlaySound(SoundID.NPCDeath6 with { Pitch = -0.3f }, NPC.Center);
			}
			if (Once(60)) {
				SoundEngine.PlaySound(SoundID.Item13 with { Pitch = -0.6f }, NPC.Center);              // the lantern goes out
				Mist(RigPoint(R.LanternX, R.LanternY), 6);
			}
			if (Once(FarewellTick)) {
				SoundEngine.PlaySound(WhistleSound with { Pitch = 0.2f, Volume = 0.8f }, NPC.Center);  // the last train's whistle, far off
			}
			if (Once(PickupTick)) {
				// the last train hits him: he explodes in tiny bits (user-set 2026-11-05)
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.2f }, NPC.Center);
				SoundEngine.PlaySound(SoundID.NPCDeath14 with { Pitch = -0.4f }, NPC.Center);
				Punch(NPC.Center, Vector2.UnitX, 9f, 45, "Cogpunk:ConductorPickup");
				Explode();
				Mist(NPC.Center, 30);
			}
		}

		/// <summary>The explosion as the last train hits him: <see cref="DeathBits"/> tiny pieces of him (brass, coat, plate,
		/// a wisp, a tooth, a bolt) thrown out the way the train runs, his cap and his lantern among them, a flash of ghost
		/// light. Gore and dust on clients only (vanilla caps both: at the cap the rest are refused).</summary>
		private void Explode() {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			float push = Side >= 0f ? -1f : 1f;                // the train runs from his side across him
			Vector2 centre = NPC.Center;
			for (int k = 0; k < DeathBits; k++) {
				if (Mod.TryFind("CursedConductor_Bit" + (k % R.Bits), out ModGore bit)) {
					Vector2 at = centre + Main.rand.NextVector2Circular(NPC.width * 0.5f, NPC.height * 0.5f);
					Vector2 v = Main.rand.NextVector2Circular(6f, 6f) + new Vector2(push * Main.rand.NextFloat(3f, 9f), -Main.rand.NextFloat(1f, 4f));
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), at, v, bit.Type, out _);
				}
			}
			for (int k = 0; k < ShellGores.Length; k++) {
				if (Mod.TryFind(ShellGores[k], out ModGore gore)) {
					Vector2 v = new(push * Main.rand.NextFloat(4f, 8f), -Main.rand.NextFloat(3f, 6f));
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), centre + new Vector2(0f, -NPC.height * 0.3f + k * 30f), v, gore.Type, out _);
				}
			}
			for (int i = 0; i < 24; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Smoke : DustID.CursedTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(7f, 7f) + new Vector2(push * 3f, 0f);
					d.scale = Main.rand.NextFloat(1.1f, 1.8f);
				}
			}
		}

		private static readonly string[] ShellGores = { "CursedConductor_GoreCap", "CursedConductor_GoreLantern", "CursedConductor_GoreTurbine" };

		protected override void BossHitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 3; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i == 0 ? DustID.CursedTorch : DustID.Iron, out _);
			}
		}
	}
}
