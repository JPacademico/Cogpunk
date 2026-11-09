using System;
using Cogpunk.Content.OldBrassTown.NPCs;
using Cogpunk.Core.Configs;
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
using R = Cogpunk.Content.OldBrassTown.NPCs.SheriffRigData;

namespace Cogpunk.Content.OldBrassTown.Projectiles
{
	/// <summary>
	/// One of the <see cref="Sheriff"/>'s three sheriff stars. Reworked 2026-11-06 (user: "his stars should have higher range
	/// to hit players but should attack more slowly and different: one star every 2 seconds; stars that don't hit a player
	/// should cling to the terrain where they landed and come back to the sheriff dealing damage, after the third shot, to the
	/// players on the way back"). It floats in its place over his hat, spinning, and goes through five modes:
	/// <list type="bullet">
	/// <item><b>Home</b>: floating; for <see cref="Sheriff.StarTelegraph"/> ticks before its throw (<see cref="Sheriff.LaunchTick"/>
	/// of its slot) its rim flashes and it chimes, if the Sheriff has a target in range.</item>
	/// <item><b>Out</b>: thrown at where the target was, <see cref="OutSpeed"/> for at most <see cref="OutTicks"/> ticks (36
	/// tiles; it reached 13.5 before). It hurts.</item>
	/// <item><b>Back</b>: it touched a player, so it flies home (<see cref="BackSpeed"/>, harmless: it has done its job).</item>
	/// <item><b>Stuck</b>: it missed and bit into the first block it met (<see cref="EmbedDepth"/> px in), or hangs in the air
	/// where its reach ran out. Harmless. From <see cref="Sheriff.RecallTelegraphTick"/> it rattles and a dotted line of embers
	/// marks its way home.</item>
	/// <item><b>Recall</b>: at <see cref="Sheriff.RecallTick"/>, after the third throw, it tears loose and flies straight
	/// home through everything (<see cref="RecallSpeed"/>), hurting every player on the line.</item>
	/// </list>
	/// <para>D2: spawned by the server with <c>ai[0]</c> = the Sheriff, <c>ai[1]</c> = its slot; <c>ai[2]</c> is the mode,
	/// changed by the server (throw, touch, end of reach, recall) and sent with <c>netUpdate</c>, so every client flies the
	/// same path from the same start. Tile collision is deterministic, so every side sticks a star in the same block (the
	/// server's update confirms it); the recall also follows the synced clock on every side. Hostile hits are decided by the
	/// hit player's own client as usual; the server only decides that a star touched someone (its hitbox over a living
	/// player's), which turns it home. D0: a missing, dead or changed Sheriff ends it within <see cref="KeepAliveTicks"/>
	/// ticks (its timeLeft is only refreshed while he lives); the dotted line is capped at <see cref="MaxDots"/>. D1: no
	/// allocation; sparks, sounds and the line on clients only.</para>
	/// </summary>
	public class SheriffStar : CogpunkProjectile
	{
		public enum StarMode { Home, Out, Stuck, Recall, Back }

		public const float OutSpeed = 12f;
		public const int OutTicks = 48;                     // 576 px: 36 tiles of reach (user: "higher range")
		public const float RecallSpeed = 12f;
		public const float BackSpeed = 13f;
		public const float HomeSnap = 12f;
		public const int EmbedDepth = 6;                    // px a stuck star bites into its block
		public const int KeepAliveTicks = 3;
		public const int SpinTicks = 4, FastSpinTicks = 2;
		public const int RattleTicks = 4;                   // the stuck star's flash and shake period during the recall telegraph
		public const int DotSpacing = 16;                   // px between the dots of the way home
		public const int MaxDots = 64;
		private const int Size = 26;

		private static Asset<Texture2D> glow;
		private static readonly Color DotDim = new(163, 48, 26), DotLit = new(255, 199, 90);   // Ember 1 and 3: hostile (D3)

		private int Slot => Math.Clamp((int)Projectile.ai[1], 0, Sheriff.StarCount - 1);

		public StarMode Mode {
			get => (StarMode)Math.Clamp((int)Projectile.ai[2], 0, (int)StarMode.Back);
			private set => Projectile.ai[2] = (float)value;
		}

		private ref float FlightTicks => ref Projectile.localAI[0];     // each side's own count since the mode last changed
		private ref float SeenMode => ref Projectile.localAI[1];        // the mode this side last saw (a synced change resets the count)
		private ref float HeldFrame => ref Projectile.localAI[2];       // the spin frame it stuck with (visual)

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.StarSpin * 2;                 // spin frames, then the same with the rim lit
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 20;
			Projectile.height = 20;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;                         // only while thrown (AI)
			Projectile.ignoreWater = true;
			Projectile.timeLeft = KeepAliveTicks;
			Projectile.aiStyle = -1;
		}

		private bool TryGetSheriff(out Sheriff sheriff) {
			sheriff = null;
			int index = (int)Projectile.ai[0];
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC npc = Main.npc[index];
			if (!npc.active || npc.ModNPC is not Sheriff s) {
				return false;
			}
			sheriff = s;
			return true;
		}

		private static bool IsAuthority => Main.netMode != NetmodeID.MultiplayerClient;

		private void SetMode(StarMode mode) {
			if (Mode == mode) {
				return;
			}
			Mode = mode;
			FlightTicks = 0f;
			if (IsAuthority) {
				Projectile.netUpdate = true;
			}
		}

		public override void AI() {
			if (!TryGetSheriff(out Sheriff sheriff)) {
				return;                                             // no refresh: it fades out of existence in a few ticks
			}
			Projectile.timeLeft = KeepAliveTicks;
			NPC npc = sheriff.NPC;
			int clock = (int)sheriff.StarClock;
			Vector2 home = sheriff.StarHome(Slot);
			int launch = Sheriff.LaunchTick(Slot);
			if ((int)SeenMode != (int)Mode) {
				FlightTicks = 0f;                                   // a change the server sent, or a wall's after the last tick
			}
			switch (Mode) {
				case StarMode.Home:
					Projectile.velocity = Vector2.Zero;
					Projectile.Center = home;
					if (IsAuthority && clock == launch && sheriff.StarsArmed) {
						Player target = Main.player[npc.target];
						Projectile.velocity = (target.Center - Projectile.Center).SafeNormalize(Vector2.UnitY) * OutSpeed;
						SetMode(StarMode.Out);
					}
					break;
				case StarMode.Out:
					if (++FlightTicks >= OutTicks) {
						Stop(Vector2.Zero);                         // its reach ran out in the air: it hangs there
					}
					else if (IsAuthority && TouchesPlayer()) {
						SetMode(StarMode.Back);
					}
					break;
				case StarMode.Stuck:
					Projectile.velocity = Vector2.Zero;
					if (clock >= Sheriff.RecallTick && clock < Sheriff.StarCycle) {
						SetMode(StarMode.Recall);                   // every side from the synced clock; the server's update confirms it
					}
					break;
				case StarMode.Recall:
				case StarMode.Back:
					Vector2 to = home - Projectile.Center;
					float distance = to.Length();
					if (distance < HomeSnap) {
						SetMode(StarMode.Home);
						Projectile.velocity = Vector2.Zero;
						Projectile.Center = home;
					}
					else {
						float speed = Mode == StarMode.Recall ? RecallSpeed : BackSpeed;
						Projectile.velocity = to / distance * Math.Min(speed, distance);
					}
					break;
			}
			Projectile.tileCollide = Mode == StarMode.Out;           // it flies home through everything
			MathSafety.Sanitize(ref Projectile.velocity);
			bool changed = (int)SeenMode != (int)Mode;              // any change since the last tick: synced, a wall's or this tick's
			if (changed && Mode == StarMode.Stuck) {
				HeldFrame = Projectile.frame % R.StarSpin;          // it stops turning on the frame it hit with
			}
			if (!Main.dedServ) {
				Effects(sheriff, clock, launch, changed);
			}
			SeenMode = (float)Mode;
		}

		/// <summary>Server: the star's hitbox over a living player's (every player: in co-op it turns on whoever it meets).</summary>
		private bool TouchesPlayer() {
			Rectangle box = Projectile.Hitbox;
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && !player.ghost && box.Intersects(player.Hitbox)) {
					return true;
				}
			}
			return false;
		}

		/// <summary>Sticks the star: no speed, bitten <see cref="EmbedDepth"/> px into the block along its flight (none when it
		/// stopped in the air).</summary>
		private void Stop(Vector2 flight) {
			Vector2 bite = flight.SafeNormalize(Vector2.Zero) * EmbedDepth;
			Projectile.position += bite;
			Projectile.velocity = Vector2.Zero;
			SetMode(StarMode.Stuck);
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			if (Mode == StarMode.Out) {
				Stop(oldVelocity);                                  // every side: the same block stops the same flight
			}
			return false;                                           // never killed by a wall
		}

		public override bool CanHitPlayer(Player target) => Mode == StarMode.Out || Mode == StarMode.Recall;

		/// <summary>Clients: frames, light, sparks and the one-shot sounds of each change of mode.</summary>
		private void Effects(Sheriff sheriff, int clock, int launch, bool changed) {
			StarMode mode = Mode;
			bool armed = sheriff.StarsArmed;
			bool throwTelegraph = mode == StarMode.Home && armed && clock >= launch - Sheriff.StarTelegraph && clock < launch;
			bool recallTelegraph = mode == StarMode.Stuck && clock >= Sheriff.RecallTelegraphTick && clock < Sheriff.RecallTick;
			if (mode == StarMode.Home && armed && clock == launch - Sheriff.StarTelegraph) {
				SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = 0.5f, Volume = 0.8f, MaxInstances = 2 }, Projectile.Center);
			}
			if (recallTelegraph && clock == Sheriff.RecallTelegraphTick) {
				SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = -0.3f, Volume = 0.8f, MaxInstances = 3 }, Projectile.Center);
			}
			if (changed) {
				switch (mode) {
					case StarMode.Out:
						SoundEngine.PlaySound(SoundID.Item1 with { Pitch = 0.7f, Volume = 0.6f, MaxInstances = 3 }, Projectile.Center);
						break;
					case StarMode.Stuck:
						SoundEngine.PlaySound(SoundID.NPCHit4 with { Pitch = 0.4f, Volume = 0.5f, MaxInstances = 3 }, Projectile.Center);
						for (int i = 0; i < 6; i++) {
							if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.GoldFlame, out Dust spark)) {
								spark.noGravity = true;
								spark.velocity *= 1.2f;
							}
						}
						break;
					case StarMode.Recall:
						SoundEngine.PlaySound(SoundID.Item1 with { Pitch = 0.3f, Volume = 0.7f, MaxInstances = 3 }, Projectile.Center);
						break;
				}
			}
			bool fast = mode != StarMode.Home || throwTelegraph;
			int spin = fast ? FastSpinTicks : SpinTicks;
			int turn = (int)(Main.GameUpdateCount / (uint)spin + (uint)Slot) % R.StarSpin;
			if (mode == StarMode.Stuck) {
				int held = Math.Clamp((int)HeldFrame, 0, R.StarSpin - 1);
				bool flash = recallTelegraph && Main.GameUpdateCount / RattleTicks % 2 == 0;
				Projectile.frame = held + (flash ? R.StarSpin : 0);
			}
			else {
				Projectile.frame = turn + (throwTelegraph || mode == StarMode.Recall ? R.StarSpin : 0);
			}
			Lighting.AddLight(Projectile.Center, 0.45f, 0.3f, 0.1f);
			bool flying = mode == StarMode.Out || mode == StarMode.Recall || mode == StarMode.Back;
			if (flying && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.GoldFlame, out Dust trail)) {
				trail.noGravity = true;
				trail.velocity *= 0.3f;
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 6; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.GoldCoin, out _);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, R.StarSpin * 2 - 1) * (Size + 2), Size, Size);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Size * 0.5f)).Floor();
			if (Mode == StarMode.Stuck && TryGetSheriff(out Sheriff sheriff)) {
				int clock = (int)sheriff.StarClock;
				if (clock >= Sheriff.RecallTelegraphTick && clock < Sheriff.RecallTick) {
					DrawWayHome(sheriff.StarHome(Slot));
					at.X += Main.GameUpdateCount / RattleTicks % 2 * 2f;     // a 0/2 px rattle (one art pixel, never -1/+1)
				}
			}
			Main.EntitySpriteDraw(texture, at, source, Color.Lerp(lightColor, Color.White, 0.5f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true) {
				Main.EntitySpriteDraw(glow.Value, at, source, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}

		/// <summary>The recall's telegraph: a dotted line of 4x4 px embers (one art pixel at 2x) from the star to its place over
		/// the Sheriff's hat, the lit dot marching homewards so the way it will fly reads at a glance.</summary>
		private void DrawWayHome(Vector2 home) {
			Vector2 from = Projectile.Center;
			Vector2 span = home - from;
			float length = span.Length();
			if (!float.IsFinite(length) || length < DotSpacing) {
				return;
			}
			Vector2 step = span / length * DotSpacing;
			int dots = Math.Min(MaxDots, (int)(length / DotSpacing));
			int march = (int)(Main.GameUpdateCount / 3 % 3);
			Texture2D pixel = TextureAssets.MagicPixel.Value;
			Rectangle one = new(0, 0, 1, 1);
			for (int k = 1; k <= dots; k++) {
				Vector2 p = (from + step * k - Main.screenPosition).Floor();
				p.X -= p.X % 2f;                                    // on the 2 px grid
				p.Y -= p.Y % 2f;
				Color color = (k + 3 - march) % 3 == 0 ? DotLit : DotDim;
				Main.EntitySpriteDraw(pixel, p - new Vector2(2f), one, color, 0f, Vector2.Zero, 4f, SpriteEffects.None);
			}
		}
	}
}
