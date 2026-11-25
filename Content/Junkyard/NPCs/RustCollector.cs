using System;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.NPCs
{
	/// <summary>
	/// Rust Collector: a headless, boxy scrap bin on two rollers (0.8x a player's height, user-set 2026-10-27), the
	/// Junkyard's common enemy. It
	/// rolls at its target and keeps accelerating the longer it rolls the same way (<see cref="BaseAccel"/> ramping to
	/// <see cref="MaxAccel"/> over <see cref="RampTicks"/>, up to <see cref="MaxSpeed"/>), so it overshoots, skids, turns and
	/// comes back faster. It can't jump (it only rolls over one-tile steps, like any walker); slamming into a wall at speed
	/// stuns it for <see cref="StunTicks"/> ticks. Its ram throws players hard, the harder the faster it was rolling
	/// (user-set 2026-10-27): knockback <see cref="BaseKnockback"/> + <see cref="KnockbackPerSpeed"/> per px/tick of speed
	/// (vanilla's contact knockback is 4.5; 12 at full speed), thrown the way it was rolling.
	/// <para>Stats (user-set 2026-10-26, Expert values like every Cogpunk number, see <see cref="ExpertStats"/>;
	/// docs/balance/npcs.csv; anchor Antlion Charger): 100 life, 8 defense, 25 contact damage. Drops 1-5 Rusted Cogs and 1-5 Rusted Metal. Spawns on the Junkyard's surface at jungle rates
	/// (<see cref="JunkyardSpawnRules"/>), off-screen like every natural spawn.</para>
	/// <para>D2: <see cref="StateMachineNPC"/> keeps the state (roll / stunned) and timer in <c>ai[0]</c>/<c>ai[1]</c>;
	/// <c>ai[2]</c> is the acceleration ramp. The server picks the target and stuns it; the rolling itself runs on every side
	/// from the synced state (vanilla movement, like a fighter's). D1: no allocation, effects client-only.</para>
	/// </summary>
	public class RustCollector : StateMachineNPC
	{
		private enum Phase { Roll, Stunned }

		public const float BaseAccel = 0.05f;
		public const float MaxAccel = 0.22f;
		public const int RampTicks = 150;
		public const float MaxSpeed = 7.5f;
		public const float SkidDecel = 0.28f;
		public const float BonkSpeed = 4f;
		public const int StunTicks = 45;
		public const int RetargetInterval = 20;
		public const int FrameCount = 11;
		public const int RollFrames = 4, FastFrame = 4, SkidFrame = 8, StunFrame = 9;
		public const float FastSpeed = 4.5f;
		public const float BaseKnockback = 4.5f;           // vanilla contact knockback (decompiled Player.Hurt default)
		public const float KnockbackPerSpeed = 1f;         // + 7.5 at MaxSpeed: 12 (velocity 12 sideways, 9.3 up)
		public const float RamSpeed = 1.5f;                // slower than this, it pushes like any enemy
		public const int Life = 100, ContactDamage = 25, Defense = 8;    // Expert (user-set)

		private ref float Ramp => ref NPC.ai[2];

		private Phase CurrentPhase => (Phase)State;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = FrameCount;
			CogpunkSets.Mechanical[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Velocity = 1f });
		}

		public override void SetDefaults() {
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = 34;                                // 0.8 x the player's 42 px
			NPC.height = 34;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0.4f;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 150f;
			NPC.aiStyle = -1;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				ModContent.GetInstance<JunkyardBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) => JunkyardSpawnRules.SurfaceSpawnWeight(spawnInfo, 1f);

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedCog>(), 1, 1, 5));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedMetal>(), 1, 1, 5));
		}

		protected override void UpdateState() {
			if (IsAuthority && (Timer % RetargetInterval == 1f || !NPC.HasValidTarget)) {
				int old = NPC.target;
				NPC.TargetClosest(false);
				if (NPC.target != old) {
					NPC.netUpdate = true;
				}
			}
			switch (CurrentPhase) {
				case Phase.Stunned:
					NPC.velocity.X *= 0.9f;
					if (Timer >= StunTicks) {
						ChangeState((int)Phase.Roll);
						Ramp = 0f;
					}
					break;
				default:
					Roll();
					break;
			}
			if (Math.Abs(NPC.velocity.X) > 0.1f) {
				NPC.direction = NPC.spriteDirection = NPC.velocity.X > 0f ? 1 : -1;
			}
		}

		private void Roll() {
			// A wall hit at speed (collideX is last tick's result; vanilla zeroed the velocity): bonk.
			if (NPC.collideX && Math.Abs(NPC.oldVelocity.X) > BonkSpeed) {
				if (!Main.dedServ) {
					BonkEffects();
				}
				if (IsAuthority) {
					ChangeState((int)Phase.Stunned);
					Ramp = 0f;
					NPC.velocity = new Vector2(-Math.Sign(NPC.oldVelocity.X) * 2.5f, -2f);   // the rebound, not a jump
				}
				return;
			}
			int want = NPC.HasValidTarget ? (Main.player[NPC.target].Center.X >= NPC.Center.X ? 1 : -1) : NPC.direction;
			float vx = NPC.velocity.X;
			if (vx == 0f || Math.Sign(vx) == want) {
				Ramp = Math.Min(Ramp + 1f, RampTicks);
				float accel = MathHelper.Lerp(BaseAccel, MaxAccel, Ramp / RampTicks);
				vx = MathHelper.Clamp(vx + want * accel, -MaxSpeed, MaxSpeed);
			}
			else {
				Ramp = 0f;                                 // overshot: skid to a stop before turning
				vx = Math.Abs(vx) <= SkidDecel ? 0f : vx - Math.Sign(vx) * SkidDecel;
				if (!Main.dedServ && Math.Abs(vx) > 2f) {
					SkidSparks();
				}
			}
			NPC.velocity.X = vx;
			Collision.StepUp(ref NPC.position, ref NPC.velocity, NPC.width, NPC.height, ref NPC.stepSpeed, ref NPC.gfxOffY);
		}

		/// <summary>The ram: knockback grows with its speed and throws the player the way it was rolling. Runs on the hit
		/// player's client (vanilla checks NPC contact there) from the synced velocity; knockback immunity still applies.</summary>
		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			float speed = Math.Abs(NPC.velocity.X);
			if (CurrentPhase == Phase.Stunned || speed < RamSpeed) {
				return;
			}
			float knockback = BaseKnockback + KnockbackPerSpeed * Math.Min(speed, MaxSpeed);
			modifiers.Knockback *= knockback / BaseKnockback;
			modifiers.HitDirectionOverride = NPC.velocity.X > 0f ? 1 : -1;
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.6f, Volume = 0.5f + 0.5f * speed / MaxSpeed }, target.Center);
			}
		}

		public bool Skidding => CurrentPhase == Phase.Roll && NPC.HasValidTarget && NPC.velocity.X != 0f
			&& Math.Sign(NPC.velocity.X) != (Main.player[NPC.target].Center.X >= NPC.Center.X ? 1 : -1);

		// --- effects (clients) -----------------------------------------------------------------------------------------

		private void BonkEffects() {
			SoundEngine.PlaySound(SoundID.NPCHit4 with { Pitch = -0.3f }, NPC.Center);
			SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.5f, Volume = 0.6f }, NPC.Center);
			for (int i = 0; i < 8; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 2 == 0 ? DustID.Iron : DustID.Copper, out _, -Math.Sign(NPC.oldVelocity.X) * 2f, -2f);
			}
		}

		private void SkidSparks() {
			if (!Main.rand.NextBool(2) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			Vector2 at = NPC.BottomLeft + new Vector2(NPC.velocity.X > 0f ? NPC.width - 4f : 0f, -4f);
			if (SafeSpawn.TryNewDust(at, 4, 4, DustID.Torch, out Dust d, -NPC.velocity.X * 0.4f, -1.5f, 0, default, 0.8f)) {
				d.noGravity = false;
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 14;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Copper : DustID.Iron, out _);
			}
			if (NPC.life <= 0) {
				Mod mod = ModContent.GetInstance<CogpunkMod>();
				foreach (string name in GoreNames) {
					if (mod.TryFind(name, out ModGore gore)) {
						SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.position, NPC.velocity * 0.5f + Main.rand.NextVector2Circular(2f, 2f), gore.Type, out _);
					}
				}
			}
		}

		private static readonly string[] GoreNames = { "RustCollector_GoreWheel", "RustCollector_GoreWheel", "RustCollector_GorePanel" };

		// --- frames (visual only) ----------------------------------------------------------------------------------------

		public override void FindFrame(int frameHeight) {
			int frame;
			if (CurrentPhase == Phase.Stunned) {
				frame = StunFrame + (int)(Timer / 6) % 2;
			}
			else if (Skidding && Math.Abs(NPC.velocity.X) > 1.5f) {
				frame = SkidFrame;
			}
			else {
				// the rollers turn with the distance covered: a frame per 5 px
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= 5.0 * RollFrames) {
					NPC.frameCounter -= 5.0 * RollFrames;
				}
				int roll = (int)(NPC.frameCounter / 5.0) % RollFrames;
				frame = (Math.Abs(NPC.velocity.X) >= FastSpeed ? FastFrame : 0) + roll;
			}
			NPC.frame.Y = frame * frameHeight;
		}
	}
}
