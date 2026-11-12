using System;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.OldBrassTown.NPCs.MechanicalBullRigData;

namespace Cogpunk.Content.OldBrassTown.NPCs
{
	/// <summary>
	/// Mechanical Bull (user-set 2026-11-04: "a bull that charges then rams the player dealing massive contact damage and
	/// knockback"), Old Brass Town's steam-driven bull. It trots after its target; with the target roughly level with it
	/// (<see cref="ChargeHeight"/>) and in sight within <see cref="ChargeRange"/> it lowers its head and paws the ground (the
	/// telegraph, <see cref="PawTicks"/> ticks: steam snorted from its nostrils, a hoof scraping, its eyes flaring), then
	/// charges straight at where the target was, up to <see cref="ChargeSpeed"/>: it doesn't turn, so a jump or a step aside
	/// clears it. A charge that slams into a wall leaves it stunned (<see cref="StunTicks"/>); one that overshoots by
	/// <see cref="Overshoot"/> skids to a stop (<see cref="SkidTicks"/>) and turns. While charging it hits for
	/// x<see cref="ChargeDamageMultiplier"/> its contact damage and throws the player x<see cref="ChargeKnockback"/> as far
	/// (vanilla contact knockback 4.5 -> 9: about 20 tiles on flat ground, SKILL 3.9).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Antlion Charger, the underground desert's charger,
	/// decompiled 1.4.4 NPC 508: 110 life, 16 defense, 38 contact in Classic = 220 / 16 / 76 in Expert, value 175):
	/// <see cref="Life"/> life, <see cref="Defense"/> defense, <see cref="TrotDamage"/> contact while trotting and twice that
	/// charging. Spawns only in Old Brass Town (<see cref="SpawnWeight"/>). Drops 2-3 Tarnished Brass Bars and 2-4 Rusted
	/// Cogs.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the charge's direction (locked by the server with the
	/// state change), <c>ai[3]</c> the cooldown; the server decides; every side runs the movement and sets the contact damage
	/// from the synced state (each client checks its own player's contact). D1: no allocation; steam and sounds on
	/// clients.</para>
	/// </summary>
	public class MechanicalBull : GridWalkerNPC
	{
		private enum Phase { Trot, Paw, Charge, Skid, Stunned }

		public const int Life = 360, TrotDamage = 50, Defense = 18;       // Expert
		public const float ChargeDamageMultiplier = 2f;                    // 100 in Expert: the user's "massive contact damage"
		public const float ChargeKnockback = 2f;                           // "massive knockback": 9 instead of vanilla's 4.5
		public const int Width = 56, Height = 40;
		public const float KnockbackResist = 0.1f;
		public const float TrotSpeed = 1.5f, TrotAccel = 0.06f, JumpSpeed = 6f;
		public const float ChargeSpeed = 9.5f, ChargeAccel = 0.45f;
		public const float ChargeRange = 28f * 16f;
		public const float ChargeHeight = 4f * 16f;
		public const float Overshoot = 6f * 16f;
		public const int PawTicks = 45;                                     // the telegraph (D3: >= 30 at T0-T4)
		public const int ChargeMaxTicks = 110;
		public const int SkidTicks = 30;
		public const int StunTicks = 90;
		public const float WallStunSpeed = 4f;
		public const int ChargeCooldown = 75;
		public const float SpawnWeight = 0.45f;
		/// <summary>Game px of travel per trot frame: the art's own hoof step, so a planted hoof never slips. 2026-11-05b (user:
		/// "the legs animation is too fast when he is not ramming"): the stride doubled (6 frames over 18 px became 10 over
		/// 40), so at <see cref="TrotSpeed"/> the legs cycle 2.25 times a second instead of 5; only the charge's gallop keeps
		/// the fast cycle (<see cref="GallopAnimDistance"/>: 48 px a cycle at up to <see cref="ChargeSpeed"/>).</summary>
		public const float TrotAnimDistance = R.TrotStep;
		public const float GallopAnimDistance = 12f;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "MechanicalBull_GoreHead", "MechanicalBull_GoreHorn", "MechanicalBull_GoreLeg", "MechanicalBull_GoreLeg" };

		private Phase CurrentPhase => (Phase)State;
		private ref float ChargeDir => ref NPC.ai[2];
		private ref float Cooldown => ref NPC.ai[3];
		private float targetX;

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<OldBrassTownBiome>().ModBiomeBestiaryInfoElement;

		/// <summary>The eyes flare while it paws and charges.</summary>
		protected override float GlowStrength => CurrentPhase == Phase.Paw || CurrentPhase == Phase.Charge ? 1f : 0.6f;

		private bool Charging => CurrentPhase == Phase.Charge;

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
			CogpunkSets.Mechanical[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, TrotDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 300f;
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) => OldBrassTownSpawnRules.TownSpawnWeight(spawnInfo, SpawnWeight);

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<TarnishedBrassBar>(), 1, 2, 3));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedCog>(), 1, 2, 4));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<Accessories.RedCloth>(), Accessories.RedCloth.DropOneIn));   // user-set 2026-11-10b
		}

		protected override void UpdateState() {
			if (Cooldown > 0f) {
				Cooldown--;
			}
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			// contact damage from the synced state, on every side (defDamage holds the mode-scaled contact damage)
			NPC.damage = Charging ? (int)(NPC.defDamage * ChargeDamageMultiplier) : (CurrentPhase == Phase.Stunned ? 0 : NPC.defDamage);
			switch (CurrentPhase) {
				case Phase.Paw:
					Run(0, 0f, TrotAccel * 4f, JumpSpeed);
					NPC.direction = NPC.spriteDirection = dir;
					if (!Main.dedServ) {
						PawEffects();
					}
					if (IsAuthority && Timer >= PawTicks) {
						ChargeDir = dir;
						ChangeState((int)Phase.Charge);
					}
					break;
				case Phase.Charge:
					DoCharge(target);
					break;
				case Phase.Skid:
					NPC.velocity.X *= 0.9f;
					if (!Main.dedServ && Timer % 4f == 0f) {
						SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(0f, 4f), NPC.width, 4, DustID.Sand, out _, -NPC.velocity.X * 0.3f, -1f);
					}
					if (IsAuthority && Timer >= SkidTicks) {
						Cooldown = ChargeCooldown;
						ChangeState((int)Phase.Trot);
					}
					break;
				case Phase.Stunned:
					NPC.velocity.X *= 0.85f;
					if (!Main.dedServ && Main.rand.NextBool(4) && CogpunkClientConfig.RollEffect()) {
						SafeSpawn.TryNewDust(NPC.Top + new Vector2(-8f, -12f), 16, 8, DustID.Smoke, out _, 0f, -1.5f);
					}
					if (IsAuthority && Timer >= StunTicks) {
						Cooldown = ChargeCooldown;
						ChangeState((int)Phase.Trot);
					}
					break;
				default:
					Run(target != null ? dir : 0, TrotSpeed, TrotAccel, JumpSpeed);
					FaceMotion(dir);
					if (IsAuthority && target != null && Grounded && Cooldown <= 0f && Math.Abs(dx) < ChargeRange
						&& Math.Abs(target.Bottom.Y - NPC.Bottom.Y) < ChargeHeight
						&& Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height)) {
						NPC.direction = NPC.spriteDirection = dir;
						ChangeState((int)Phase.Paw);
					}
					break;
			}
			if (!Main.dedServ && Main.rand.NextBool(Charging ? 2 : 10) && CogpunkClientConfig.RollEffect()) {
				int face = NPC.direction == 0 ? -1 : NPC.direction;
				Vector2 stack = NPC.Bottom + new Vector2(R.StackX * -face, R.StackY);
				if (SafeSpawn.TryNewDust(stack - new Vector2(3f), 6, 6, DustID.Smoke, out Dust puff, 0f, -1.5f, 100, new Color(238, 241, 243), 1.1f)) {
					puff.noGravity = true;
				}
			}
		}

		/// <summary>Straight along the locked direction, never turning; a wall at speed stuns it, overshooting the target (as
		/// it stood when the charge began) by <see cref="Overshoot"/> or running out of time makes it skid (server).</summary>
		private void DoCharge(Player target) {
			int dir = ChargeDir >= 0f ? 1 : -1;
			if (Timer == 1f) {
				targetX = target != null ? target.Center.X : NPC.Center.X + dir * ChargeRange;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.DD2_OgreRoar with { Pitch = 0.4f, Volume = 0.55f, MaxInstances = 2 }, NPC.Center);   // the bellow
				}
			}
			Run(dir, ChargeSpeed, ChargeAccel, JumpSpeed * 0.6f);
			NPC.direction = NPC.spriteDirection = dir;
			if (!Main.dedServ && Timer % 3f == 0f) {
				SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(0f, 4f), NPC.width, 4, DustID.Sand, out _, -dir * 2f, -1.5f);
			}
			if (!IsAuthority) {
				return;
			}
			if (NPC.collideX && Math.Abs(NPC.oldVelocity.X) > WallStunSpeed) {
				NPC.velocity.X = -dir * 2f;                     // bounced off the wall
				ChangeState((int)Phase.Stunned);
				return;
			}
			bool past = dir > 0 ? NPC.Center.X > targetX + Overshoot : NPC.Center.X < targetX - Overshoot;
			if (past || Timer >= ChargeMaxTicks || RammedSomeone()) {
				ChangeState((int)Phase.Skid);
			}
		}

		/// <summary>Server: a ram ends the charge in a skid. The thrown player flies at 9 px/tick and the bull runs at 9.5, so
		/// a charge that kept going caught them again once their hurt immunity ran out (seen in the D5 sim, 2026-11-04). The
		/// touch is tested here like the Boombot's (player hitboxes as the server has them, a little slack), since vanilla
		/// decides the contact hit on the hit player's own client.</summary>
		private bool RammedSomeone() {
			Rectangle box = NPC.Hitbox;
			box.Inflate(4, 4);
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && box.Intersects(player.Hitbox)) {
					return true;
				}
			}
			return false;
		}

		/// <summary>Clients: the telegraph's steam snorts from the nostrils and the hoof scrapes, keyed to the timer.</summary>
		private void PawEffects() {
			int face = NPC.direction == 0 ? -1 : NPC.direction;
			Vector2 nostril = NPC.Bottom + new Vector2(R.NostrilX * -face, R.NostrilY);
			if (Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Item34 with { Pitch = -0.6f, Volume = 0.7f, MaxInstances = 2 }, nostril);   // a snort of steam
			}
			if (Timer % 12f == 6f) {
				SoundEngine.PlaySound(SoundID.NPCHit41 with { Pitch = -0.3f, Volume = 0.5f, MaxInstances = 3 }, NPC.Bottom);   // a hoof scrapes
				SafeSpawn.TryNewDust(NPC.Bottom + new Vector2(-face * 16f - 6f, -6f), 12, 4, DustID.Sand, out _, face * 1.5f, -1f);
			}
			if (Timer % 15f < 5f && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(nostril - new Vector2(3f), 6, 6, DustID.Smoke, out Dust snort, face * 2f, 0.5f, 100, new Color(238, 241, 243), 1.2f)) {
				snort.noGravity = true;
			}
		}

		/// <summary>The charge throws the player <see cref="ChargeKnockback"/> times as far, the way the bull runs (vanilla
		/// hurts players with contact knockback 4.5 whatever the NPC's own; decompiled <c>Player.Hurt</c>).</summary>
		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			if (Charging) {
				modifiers.Knockback *= ChargeKnockback;
				modifiers.HitDirectionOverride = ChargeDir >= 0f ? 1 : -1;
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			if (Charging && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.NPCHit4 with { Pitch = -0.5f, Volume = 0.9f, MaxInstances = 2 }, target.Center);
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Paw:
					return R.Paw + (int)(Timer / 6f) % R.PawFrames;
				case Phase.Charge:
					NPC.frameCounter += Math.Abs(NPC.velocity.X);
					if (NPC.frameCounter >= GallopAnimDistance * R.ChargeFrames) {
						NPC.frameCounter -= GallopAnimDistance * R.ChargeFrames;
					}
					return R.Charge + (int)(NPC.frameCounter / GallopAnimDistance) % R.ChargeFrames;
				case Phase.Skid:
					return R.Skid;
				case Phase.Stunned:
					return R.Stunned + (int)(Timer / 6f) % R.StunnedFrames;
			}
			if (Math.Abs(NPC.velocity.X) > 0.15f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= TrotAnimDistance * R.TrotFrames) {
					NPC.frameCounter -= TrotAnimDistance * R.TrotFrames;
				}
				return R.Trot + (int)(NPC.frameCounter / TrotAnimDistance) % R.TrotFrames;
			}
			return R.Trot;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 18;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Copper : DustID.Iron, out _);
			}
			if (NPC.life <= 0) {
				foreach (string name in GoreNames) {
					if (Mod.TryFind(name, out ModGore gore)) {
						SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.position + new Vector2(Main.rand.Next(NPC.width), Main.rand.Next(NPC.height)),
							NPC.velocity * 0.5f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
					}
				}
			}
		}
	}
}
