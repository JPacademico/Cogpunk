using System;
using Cogpunk.Content.Coghaven.Projectiles;
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
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Coghaven.NPCs.CogscorpionRigData;

namespace Cogpunk.Content.Coghaven.NPCs
{
	/// <summary>
	/// Cogscorpion (Escorpião de Engrenagens), a Coghaven enemy (user-set 2026-11-12: "add a new enemy to coghaven being the
	/// cogscorpion. it should have a tail attack that apply jade curse"): a palace guardian built like a scorpion, bronze
	/// plates edged in red lacquer, a jade head plate and a jade sting (art/coghaven/make_cogscorpion_art.py).
	/// <para>It skitters at its target (<see cref="WalkSpeed"/>, root-motion frames, D4 rule 14). With its target within
	/// <see cref="StrikeRangeX"/> x <see cref="StrikeRangeY"/>, in sight, on the ground and its sting ready
	/// (<see cref="CooldownTicks"/> since the last), it stops and <b>raises</b> its tail for <see cref="RaiseTicks"/> ticks (a quick
	/// flare, user 2026-11-12: "way quicker"; the tail coils back, the sting glows brighter, a hiss), then <b>strikes</b>: the tail whips
	/// over its head and the sting hangs in front of its face for <see cref="CogscorpionSting.Lifetime"/> ticks
	/// (<see cref="CogscorpionSting"/>), laying the jade curse on whoever it hits (<see cref="Gems.JadeCursePlayer"/>: slower
	/// attacks, turned to jade at 3 stacks); then it recovers and walks on. Its touch hurts as any enemy's but carries no curse.</para>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; Coghaven is a T4 area): the Demon's numbers in the middle of the
	/// island's two other kinds (terraria.wiki.gg: 120 life, 8 defense, 32 contact, Demon Scythe 42 in Classic = 240 / 8 / 64 /
	/// 84 in Expert): <see cref="Life"/> life, <see cref="Defense"/> defense (bronze), <see cref="ContactDamage"/> contact, the sting
	/// <see cref="StingDamage"/> (the scythe's 84). Drops 1-2 Jade 1 time in <see cref="JadeOdds"/> (the Golem's rate).</para>
	/// <para>D2: ai[0]/ai[1] state and timer, ai[2] the ticks since its last strike, all synced; the server decides and spawns
	/// the sting (at the art's own sting point, <see cref="CogscorpionRigData.StingX"/>). Effects client-side. D0: one sting a
	/// strike through <see cref="SafeSpawn"/>; every timer bounded.</para>
	/// </summary>
	public class Cogscorpion : GridWalkerNPC
	{
		private enum Phase { Walk, Raise, Strike, Recover }

		public const int Life = 380, ContactDamage = 56, Defense = 16, StingDamage = 84;
		public const float WalkSpeed = 1.6f, WalkAccel = 0.08f, JumpSpeed = 6.5f;
		// user, 2026-11-12 (second message): "the scorpion tail attack should be way quicker": 36 ticks of raise and 32 of strike
		// and recovery became 16 and 20 (a regular enemy: D3's 30-tick telegraph floor is for bosses and minibosses)
		public const int RaiseFrameTicks = 4;
		public const int RaiseTicks = R.RaiseFrames * RaiseFrameTicks;   // 16: the telegraph (the sting flares, a hiss)
		public const int StrikeWhipTicks = 2, StrikeHoldTicks = 6, StrikeTicks = 12;
		public const int RecoverFrameTicks = 4;
		public const int RecoverTicks = R.RecoverFrames * RecoverFrameTicks;
		public const int CooldownTicks = 90;
		public const float StrikeRangeX = 4.5f * 16f, StrikeRangeY = 3f * 16f;
		public const int JadeOdds = 4, JadeMin = 1, JadeMax = 2;
		public const float SpawnWeight = 1f;
		public const float Value = 900f;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "Cogscorpion_GoreTail", "Cogscorpion_GoreClaw", "Cogscorpion_GoreBody" };

		private Phase CurrentPhase => (Phase)State;
		private ref float SinceStrike => ref NPC.ai[2];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<CoghavenBiome>().ModBiomeBestiaryInfoElement;

		protected override float GlowStrength => CurrentPhase == Phase.Raise ? 0.75f + 0.25f * Math.Min(1f, Timer / RaiseTicks) : 0.8f;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			far = near = glow = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;    // bronze and jade
		}

		public override void SetDefaults() {
			NPC.width = 60;                                  // the carapace and head (D4: matched hitbox; the tail is the sting's)
			NPC.height = 30;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0.5f;
			NPC.HitSound = SoundID.NPCHit4;                  // metal
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Value;
			NPC.aiStyle = -1;
			SpawnModBiomes = new[] { ModContent.GetInstance<CoghavenBiome>().Type };
		}

		public override void OnSpawn(IEntitySource source) {
			if (IsAuthority) {
				SinceStrike = Main.rand.Next(CooldownTicks);    // CooldownTicks > 0 (const)
				NPC.netUpdate = true;
			}
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), JadeOdds, JadeMin, JadeMax));
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			return CoghavenSpawnRules.SpawnWeight(spawnInfo, SpawnWeight);
		}

		/// <summary>The sting's point in the world (the rig's, mirrored for the side it faces).</summary>
		private Vector2 StingPoint => NPC.Bottom + new Vector2(R.StingX * -NPC.direction, R.StingY);

		private bool CanStrike(Player target) {
			Vector2 d = target.Center - NPC.Center;
			return Math.Abs(d.X) <= StrikeRangeX && Math.Abs(d.Y) <= StrikeRangeY
				&& Collision.CanHitLine(NPC.Center, 1, 1, target.position, target.width, target.height);
		}

		protected override void UpdateState() {
			if (CurrentPhase == Phase.Walk) {
				Retarget();
			}
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.Raise:
					NPC.velocity.X *= 0.8f;
					if (IsAuthority && Timer >= RaiseTicks) {
						ChangeState((int)Phase.Strike);
					}
					break;
				case Phase.Strike:
					NPC.velocity.X *= 0.8f;
					if (IsAuthority && Timer == StrikeWhipTicks) {
						Sting();
					}
					if (IsAuthority && Timer >= StrikeTicks) {
						ChangeState((int)Phase.Recover);
					}
					break;
				case Phase.Recover:
					NPC.velocity.X *= 0.85f;
					if (IsAuthority && Timer >= RecoverTicks) {
						SinceStrike = 0f;
						ChangeState((int)Phase.Walk);
					}
					break;
				default:
					SinceStrike++;
					Run(target != null ? dir : 0, WalkSpeed, WalkAccel, JumpSpeed);
					FaceMotion(dir);
					if (IsAuthority && target != null && SinceStrike >= CooldownTicks && Grounded && CanStrike(target)) {
						NPC.direction = NPC.spriteDirection = dir;
						ChangeState((int)Phase.Raise);
					}
					break;
			}
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Server: the sting, held at the art's sting point for its lifetime.</summary>
		private void Sting() {
			Vector2 at = StingPoint;
			if (!MathSafety.IsFinite(at)) {
				return;
			}
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), at, Vector2.Zero, ModContent.ProjectileType<CogscorpionSting>(),
				ExpertStats.HostileProjectile(NPC, StingDamage), 4f, out _, Main.myPlayer);
		}

		/// <summary>Clients: the hiss as the tail rises, jade sparks off the sting while it charges, the whip's whoosh.</summary>
		private void Effects() {
			if (CurrentPhase == Phase.Raise) {
				if (Timer == 1f) {
					SoundEngine.PlaySound(SoundID.Item13 with { Pitch = 0.3f, Volume = 0.55f }, NPC.Center);
				}
				if (Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()) {
					Vector2 sting = NPC.Bottom + new Vector2(-6f * -NPC.direction, -46f);
					if (SafeSpawn.TryNewDust(sting - new Vector2(6f), 12, 12, DustID.GemEmerald, out Dust d)) {
						d.noGravity = true;
						d.velocity *= 0.4f;
					}
				}
			}
			else if (CurrentPhase == Phase.Strike && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.3f }, NPC.Center);
			}
			if (Main.rand.NextBool(90) && CogpunkClientConfig.RollEffect()) {
				Vector2 vent = NPC.Bottom + new Vector2(10f * -NPC.direction, -28f);
				if (SafeSpawn.TryNewDust(vent, 2, 2, DustID.Smoke, out Dust s, 0f, -1f, 120, new Color(238, 241, 243), 0.9f)) {
					s.noGravity = true;
				}
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Raise:
					return R.Raise + Math.Min(R.RaiseFrames - 1, (int)(Timer / RaiseFrameTicks));
				case Phase.Strike:
					return R.Strike + (Timer < StrikeWhipTicks ? 0 : Timer < StrikeWhipTicks + StrikeHoldTicks ? 1 : 2);
				case Phase.Recover:
					return R.Recover + Math.Min(R.RecoverFrames - 1, (int)(Timer / RecoverFrameTicks));
			}
			if (!Grounded) {
				return R.Walk + 1;
			}
			if (Math.Abs(NPC.velocity.X) > 0.1f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= R.WalkStep * R.WalkFrames) {
					NPC.frameCounter -= R.WalkStep * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / R.WalkStep) % R.WalkFrames;
			}
			return R.Walk;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 16;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.GemEmerald : DustID.Copper, out _);
			}
			if (NPC.life > 0) {
				return;
			}
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center, NPC.velocity * 0.4f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
				}
			}
		}
	}
}
