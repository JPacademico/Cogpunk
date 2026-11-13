using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Coghaven.NPCs.FlyingBuddhaHeadRigData;

namespace Cogpunk.Content.Coghaven.NPCs
{
	/// <summary>
	/// Flying Buddha Head (Cabeça de Buda Voadora), a Coghaven enemy (user-set 2026-11-12: "it should float around and try to
	/// smash the player. high damage but slow and it should stay stunned for 2 seconds after smashing"): a colossal golden
	/// Buddha head cut from a palace statue, its curls in a tall cone, a radiant halo behind it ringed by a turning brass cog
	/// (art/coghaven/make_buddha_head_art.py; redrawn the same day after the user's reference picture). <b>It hurts only
	/// by smashing</b> (user, 2026-11-12: "It should not cause contact damage only smash damage"): touching it while it
	/// floats, rears up, lies stunned or rises does nothing (<see cref="CanHitPlayer"/>).
	/// <list type="number">
	/// <item><b>Float</b>: it drifts slowly (<see cref="FloatSpeed"/>) towards a point <see cref="HoverHeight"/> over its target,
	/// through walls (a flyer), bobbing.</item>
	/// <item>Over its target (within <see cref="AimWidth"/> sideways, at least <see cref="MinDrop"/> above), at least
	/// <see cref="FloatTicks"/> after its last smash: <b>Wrath</b> for <see cref="WrathTicks"/> ticks (the telegraph, D3 T4: at
	/// least 30): it stops, rises a little, opens its eyes blazing jade and shakes.</item>
	/// <item><b>Smash</b>: it plunges straight down (<see cref="SmashAccel"/> a tick up to <see cref="SmashSpeed"/>) and now
	/// collides with the ground; whoever it falls on takes <see cref="SmashDamage"/> ("high damage"), its only damage; on the
	/// ground it lands with a quake (a screen shake for players near, dust, a boom).</item>
	/// <item><b>Stunned</b> for <see cref="StunTicks"/> ticks (user: 2 s): still, eyes dazed, stars circling its head, a crack
	/// over its brow: the moment to hit it.</item>
	/// <item><b>Rise</b> back into the air for <see cref="RiseTicks"/> ticks, then float again. A plunge that finds no ground
	/// within <see cref="SmashMaxTicks"/> ticks just rises.</item>
	/// </list>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; a T4 area): against the island's own heavy, the Jade Golem (720 life,
	/// 22 defense, 90 contact), and vanilla's flying stone heads (the Cursed Skull: terraria.wiki.gg 40 life, 35 contact in
	/// Classic): <see cref="Life"/> life, <see cref="Defense"/> defense, immune to knockback, <see cref="SmashDamage"/> when it
	/// smashes and nothing otherwise. Slow and telegraphed, so it hits hard. Drops 1-3 Jade 1 time in
	/// <see cref="JadeOdds"/>.</para>
	/// <para>D2: ai[0]/ai[1] state and timer, ai[2] the ticks since its last smash; the server decides; the landing is decided
	/// by the server's collision and every side plays its quake when the state turns to Stunned (timer 1). The bob is drawing
	/// only. D0: every phase capped; spawns only client dust and gores through <see cref="SafeSpawn"/>.</para>
	/// </summary>
	public class FlyingBuddhaHead : GridWalkerNPC
	{
		private enum Phase { Float, Wrath, Smash, Stunned, Rise }

		public const int Life = 640, SmashDamage = 150, Defense = 22;
		public const float FloatSpeed = 1.4f, FloatAccel = 0.035f;
		public const float HoverHeight = 9f * 16f, AimWidth = 2f * 16f, MinDrop = 4f * 16f;
		public const int FloatTicks = 120;
		public const int WrathTicks = 45;                          // 3 frames x 15
		public const float SmashAccel = 0.6f, SmashSpeed = 15f;
		public const int SmashMaxTicks = 75;
		public const int StunTicks = 120;                          // user-set: 2 s
		public const int RiseTicks = 45;
		public const float RiseSpeed = 2.4f;
		public const int JadeOdds = 3, JadeMin = 1, JadeMax = 3;
		public const float SpawnWeight = 0.6f;
		public const float Value = 1500f;
		public const float QuakeRange = 40f * 16f;
		private const float StarOrbit = 22f;

		private static Asset<Texture2D> far, glow, stars;
		private static readonly string[] GoreNames = { "FlyingBuddhaHead_GoreHalf", "FlyingBuddhaHead_GoreEar", "FlyingBuddhaHead_GoreCog" };

		private Phase CurrentPhase => (Phase)State;
		private ref float SinceSmash => ref NPC.ai[2];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => null;      // a head: nothing in front of it
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement;

		/// <summary>The bob of the float (whole px, drawing only); still while stunned.</summary>
		protected override Vector2 DrawAnchor {
			get {
				float bob = CurrentPhase == Phase.Float || CurrentPhase == Phase.Rise ? MathF.Round(MathF.Sin((Main.GameUpdateCount + NPC.whoAmI * 17) * 0.05f) * 2f) : 0f;
				float shake = CurrentPhase == Phase.Wrath && Timer % 4f < 2f ? 2f : 0f;   // 0 and 2, never -/+ (D4 rule 17)
				return NPC.Bottom + new Vector2(shake, bob);
			}
		}

		protected override float GlowStrength => CurrentPhase == Phase.Stunned ? 0.45f : 1f;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
			stars = DepthLayers.RequestOptional("Cogpunk/Content/Mechanist/Buffs/StunStars");
		}

		public override void Unload() {
			far = glow = stars = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // bronze
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		public override void SetDefaults() {
			NPC.width = 64;                                  // the face and its ears, the collar up to the cap (D4: matched hitbox;
			NPC.height = 96;                                 // the halo and the thin top of the cone are decoration)
			SetExpertStats(Life, SmashDamage, Defense);
			NPC.knockBackResist = 0f;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Value;
			NPC.aiStyle = -1;
			SpawnModBiomes = new[] { ModContent.GetInstance<CoghavenBiome>().Type };
		}

		public override void OnSpawn(IEntitySource source) {
			if (IsAuthority) {
				SinceSmash = Main.rand.Next(FloatTicks);         // FloatTicks > 0 (const)
				NPC.netUpdate = true;
			}
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), JadeOdds, JadeMin, JadeMax));
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			return CoghavenSpawnRules.SpawnWeight(spawnInfo, SpawnWeight);
		}

		protected override void UpdateState() {
			if (CurrentPhase == Phase.Float) {
				Retarget();
			}
			Player target = Target;
			NPC.spriteDirection = NPC.direction = -1;          // it faces the camera: never mirrored (the light stays top-left)
			switch (CurrentPhase) {
				case Phase.Wrath:
					NPC.noTileCollide = true;
					NPC.velocity *= 0.85f;
					NPC.velocity.Y = Math.Min(NPC.velocity.Y, -0.3f);   // it rears up a little
					NPC.damage = 0;
					if (IsAuthority && Timer >= WrathTicks) {
						NPC.velocity = Vector2.Zero;
						ChangeState((int)Phase.Smash);
					}
					break;
				case Phase.Smash:
					NPC.noTileCollide = false;
					NPC.velocity.X = 0f;
					NPC.damage = NPC.defDamage;                       // its one attack
					bool landed = Timer > 2f && NPC.velocity.Y == 0f && NPC.oldVelocity.Y > 1f;
					NPC.velocity.Y = Math.Min(SmashSpeed, NPC.velocity.Y + SmashAccel);
					if (IsAuthority) {
						if (landed) {
							NPC.velocity = Vector2.Zero;
							ChangeState((int)Phase.Stunned);
						}
						else if (Timer >= SmashMaxTicks) {
							ChangeState((int)Phase.Rise);
						}
					}
					break;
				case Phase.Stunned:
					NPC.noTileCollide = false;
					NPC.velocity = Vector2.Zero;
					NPC.damage = 0;
					if (!Main.dedServ && Timer == 1f) {
						Quake();
					}
					if (IsAuthority && Timer >= StunTicks) {
						ChangeState((int)Phase.Rise);
					}
					break;
				case Phase.Rise:
					NPC.noTileCollide = true;
					NPC.damage = 0;
					NPC.velocity.X *= 0.9f;
					NPC.velocity.Y = Math.Max(NPC.velocity.Y - 0.15f, -RiseSpeed);
					if (IsAuthority && Timer >= RiseTicks) {
						SinceSmash = 0f;
						ChangeState((int)Phase.Float);
					}
					break;
				default:
					NPC.noTileCollide = true;
					NPC.damage = 0;
					SinceSmash++;
					Drift(target);
					if (IsAuthority && target != null && SinceSmash >= FloatTicks && OverTarget(target)) {
						ChangeState((int)Phase.Wrath);
					}
					break;
			}
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Every side: eases towards the hover point over the target (or upwards, with none), slowly.</summary>
		private void Drift(Player target) {
			Vector2 goal = target != null ? target.Center - new Vector2(0f, HoverHeight) : NPC.Center - new Vector2(0f, 64f);
			Vector2 to = goal - NPC.Center;
			Vector2 want = to.LengthSquared() > 64f ? to.SafeNormalize(Vector2.Zero) * FloatSpeed : Vector2.Zero;
			NPC.velocity = Vector2.Lerp(NPC.velocity, want, FloatAccel * 4f);
			if (NPC.velocity.LengthSquared() > FloatSpeed * FloatSpeed) {
				NPC.velocity = NPC.velocity.SafeNormalize(Vector2.Zero) * FloatSpeed;
			}
		}

		private bool OverTarget(Player target) {
			float dx = Math.Abs(target.Center.X - NPC.Center.X);
			float drop = target.Top.Y - NPC.Bottom.Y;
			return dx <= AimWidth && drop >= MinDrop;
		}

		/// <summary>Only the smash hurts (user-set): no contact damage in any other phase, whatever its damage field says.</summary>
		public override bool CanHitPlayer(Player target, ref int cooldownSlot) => CurrentPhase == Phase.Smash;

		public override bool CanHitNPC(NPC target) => CurrentPhase == Phase.Smash;

		/// <summary>Clients: steam out of the neck, the wrath's jade sparks and rumble, the plunge's whistle.</summary>
		private void Effects() {
			if (CurrentPhase == Phase.Wrath && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Zombie105 with { Pitch = -0.6f, Volume = 0.7f }, NPC.Center);   // a low gong of a hum
			}
			if (CurrentPhase == Phase.Smash && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Item74 with { Pitch = -0.5f, Volume = 0.6f }, NPC.Center);
			}
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			if ((CurrentPhase == Phase.Float || CurrentPhase == Phase.Rise) && Main.rand.NextBool(4)) {
				if (SafeSpawn.TryNewDust(NPC.Bottom + new Vector2(-10f, -6f), 20, 6, DustID.Smoke, out Dust d, 0f, 2f, 110, new Color(238, 241, 243), 1.1f)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-0.5f, 0.5f), Main.rand.NextFloat(1.2f, 2.4f));
					d.noGravity = true;
				}
			}
			if (CurrentPhase == Phase.Wrath && Main.rand.NextBool(2)) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height / 2, DustID.GemEmerald, out Dust j)) {
					j.noGravity = true;
					j.velocity = Main.rand.NextVector2Circular(2f, 2f);
				}
			}
		}

		/// <summary>Clients, the tick it lands: a boom, a shake for players near (behind the ScreenShake setting), a ring of dust.</summary>
		private void Quake() {
			SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f, Volume = 1f }, NPC.Bottom);
			SoundEngine.PlaySound(SoundID.NPCHit41 with { Pitch = -0.4f }, NPC.Bottom);
			Player local = Main.LocalPlayer;
			if ((CogpunkClientConfig.Instance?.ScreenShake ?? true) && local.active && Vector2.DistanceSquared(local.Center, NPC.Bottom) < QuakeRange * QuakeRange) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(NPC.Bottom, Vector2.UnitY, 9f, 8f, 24, 1000f, "Cogpunk:BuddhaQuake"));
			}
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < 24; i++) {
				if (SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(16f, 8f), NPC.width + 32, 10, i % 3 == 0 ? DustID.Copper : DustID.Smoke, out Dust d)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-5f, 5f), Main.rand.NextFloat(-3f, -0.5f));
					d.noGravity = i % 3 != 0;
				}
			}
		}

		protected override int PickFrame() {
			int turn = (int)(Main.GameUpdateCount / 8 % R.FloatFrames);     // the halo turns on its own clock
			switch (CurrentPhase) {
				case Phase.Wrath:
					return R.Wrath + Math.Min(R.WrathFrames - 1, (int)(Timer / 15f));
				case Phase.Smash:
					return R.Smash + (int)(Main.GameUpdateCount / 6 % R.SmashFrames);
				case Phase.Stunned:
					return R.Stunned + (int)(Timer / 10f) % R.StunnedFrames;
				default:
					return R.Float + turn;
			}
		}

		/// <summary>Stars circling its head while it is stunned (the Stunned buff's own sprite).</summary>
		protected override void DrawExtras(SpriteBatch spriteBatch, Vector2 anchor, Color light, bool flip, float scale, bool dummy) {
			if (dummy || CurrentPhase != Phase.Stunned || stars?.IsLoaded != true) {
				return;
			}
			Texture2D tex = stars.Value;
			const int size = 10, stride = 12, frames = 2, count = 3;
			float spin = Main.GlobalTimeWrappedHourly * 6f;
			Vector2 head = anchor - new Vector2(0f, NPC.height + 4f);
			for (int k = 0; k < count; k++) {
				float a = spin + k * MathHelper.TwoPi / count;
				int frame = (int)(Main.GameUpdateCount / 8 + k) % frames;
				Rectangle source = new(0, frame * stride, size, size);
				if (source.Bottom > tex.Height) {
					return;
				}
				Vector2 at = head + new Vector2(MathF.Cos(a) * StarOrbit, MathF.Sin(a) * StarOrbit * 0.35f);
				spriteBatch.Draw(tex, new Vector2((int)at.X, (int)at.Y), source, Color.White, 0f, new Vector2(size / 2f), 1f, SpriteEffects.None, 0f);
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 20;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Gold : DustID.Copper, out _);
			}
			if (NPC.life > 0) {
				return;
			}
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center, Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
				}
			}
		}
	}
}
