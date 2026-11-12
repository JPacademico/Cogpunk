using System;
using Cogpunk.Content.OldBrassTown.Projectiles;
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
using R = Cogpunk.Content.OldBrassTown.NPCs.DinamitromRigData;

namespace Cogpunk.Content.OldBrassTown.NPCs
{
	/// <summary>
	/// Dinamitrom (user-set 2026-11-04: "a dynamite barrel robot that jumps at the player and explodes, low health and high
	/// damage"), a walking powder keg of Old Brass Town. It hops after its target on its spring legs (one hop every
	/// <see cref="HopInterval"/> ticks); with the target in sight within <see cref="LeapRange"/> it crouches and its fuse
	/// flares (the telegraph, <see cref="WindupTicks"/> ticks: a hiss, sparks), then leaps on an arc aimed to land on where
	/// the target stood, and blows up (<see cref="DinamitromBlast"/>: <see cref="BlastDamage"/> to everyone within 4 tiles) on
	/// landing or the moment it touches a player. Killed first, it only pops: no blast.
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchors the Boombot, Cogpunk's T1 kamikaze, 40 life and a 70
	/// blast in Expert, and the underground desert's Antlion Swarmer for the tier, decompiled 1.4.4 NPC 509: 90 life, 12
	/// defense, 34 contact in Classic = 180 / 12 / 68 in Expert): <see cref="Life"/> life (the user's "low health"),
	/// <see cref="Defense"/> defense, no contact damage (the blast is the damage, the user's "high damage"). Spawns only in Old
	/// Brass Town (<see cref="SpawnWeight"/>). Killed, it drops <see cref="DynamiteMin"/>-<see cref="DynamiteMax"/> Dynamite
	/// 1 time in <see cref="DynamiteOdds"/> (user-set 2026-11-10: "1-2 dynamite at 50% chance") and 1-2 Rusted Scrap; blown
	/// up, nothing (it was spent).</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the hop timer; the leap's velocity is set by the
	/// server with the state change (synced); the server sees the touch (player hitboxes plus <see cref="TouchMargin"/> px of
	/// slack), spawns the synced blast and removes it (SyncNPC), like the Boombot. D0: the blast through
	/// <see cref="SafeSpawn"/>; if it is refused the Dinamitrom stays and tries again next tick. D1: one pass over the players
	/// per tick on the server; sparks and sounds on clients.</para>
	/// </summary>
	public class Dinamitrom : GridWalkerNPC
	{
		private enum Phase { Hop, Windup, Leap }

		public const int Life = 70, Defense = 6;                            // Expert
		public const int BlastDamage = 110;                                 // Expert
		public const float BlastKnockback = 8f;
		public const int Width = 26, Height = 40;
		public const float KnockbackResist = 0.6f;
		public const int HopInterval = 40;
		public const float HopSpeedX = 3.2f, HopSpeedY = 6f;
		public const float LeapRange = 12f * 16f, LeapHeight = 7f * 16f;
		public const int WindupTicks = 36;                                  // the telegraph (D3: >= 30 at T0-T4)
		public const float Gravity = 0.3f;                                  // vanilla's NPC gravity (decompiled NPC.UpdateNPC_UpdateGravity)
		public const float LeapMaxUp = 11f;
		public const int LeapMinTicks = 20, LeapMaxTicks = 45;
		public const int LeapTimeout = 120;
		public const int TouchMargin = 4;
		public const float SpawnWeight = 0.6f;
		public const int DynamiteOdds = 2, DynamiteMin = 1, DynamiteMax = 2;   // user-set 2026-11-10: 1-2 Dynamite at 50% (was 1 in 4)

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "Dinamitrom_GoreStave", "Dinamitrom_GoreHoop", "Dinamitrom_GoreStick" };

		private Phase CurrentPhase => (Phase)State;
		private ref float HopTimer => ref NPC.ai[2];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => ModContent.GetInstance<OldBrassTownBiome>().ModBiomeBestiaryInfoElement;

		/// <summary>The fuse sputters: brighter while it flares for the leap.</summary>
		protected override float GlowStrength => CurrentPhase == Phase.Hop ? 0.7f + 0.3f * ((int)Timer / 6 % 2) : 1f;

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
			NPCID.Sets.NeedsExpertScaling[Type] = true;     // no contact damage: without this vanilla skips its mode scaling (NPC.ScaleStats)
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, 0, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = null;                          // the pop is its own (HitEffect)
			NPC.value = 150f;
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) => OldBrassTownSpawnRules.TownSpawnWeight(spawnInfo, SpawnWeight);

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ItemID.Dynamite, DynamiteOdds, DynamiteMin, DynamiteMax));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedScrap>(), 1, 1, 2));
		}

		protected override void UpdateState() {
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.Windup:
					NPC.velocity.X *= 0.8f;
					NPC.direction = NPC.spriteDirection = dir;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(SoundID.Item34 with { Pitch = 0.4f, Volume = 0.6f, MaxInstances = 3 }, NPC.Center);   // the fuse hisses
					}
					if (IsAuthority && Timer >= WindupTicks) {
						Leap(target, dir);
					}
					break;
				case Phase.Leap:
					NPC.direction = NPC.spriteDirection = NPC.velocity.X >= 0f ? 1 : -1;
					if (IsAuthority && ((Timer > 4f && Grounded) || Timer >= LeapTimeout)) {
						Detonate();
						return;
					}
					break;
				default:
					if (Grounded) {
						NPC.velocity.X *= 0.82f;
						if (++HopTimer >= HopInterval && target != null && IsAuthority) {
							HopTimer = 0f;
							NPC.velocity = new Vector2(dir * HopSpeedX, -HopSpeedY);
							NPC.netUpdate = true;
						}
					}
					FaceMotion(dir);
					if (IsAuthority && target != null && Grounded && Math.Abs(dx) < LeapRange && Math.Abs(target.Center.Y - NPC.Center.Y) < LeapHeight
						&& Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height)) {
						NPC.direction = NPC.spriteDirection = dir;
						ChangeState((int)Phase.Windup);
					}
					break;
			}
			if (IsAuthority && NPC.active) {
				CheckTouch();
			}
			if (!Main.dedServ && NPC.active) {
				FuseEffects();
			}
		}

		/// <summary>Server: the arc that lands on the target's feet as they stand now (flight time from the distance, clamped;
		/// the climb capped at <see cref="LeapMaxUp"/>), synced with the state change.</summary>
		private void Leap(Player target, int dir) {
			Vector2 velocity = new(dir * 4f, -7f);
			if (target != null) {
				float dx = target.Center.X - NPC.Center.X;
				float dy = target.Bottom.Y - NPC.Bottom.Y;
				float t = MathHelper.Clamp(Math.Abs(dx) / 6f, LeapMinTicks, LeapMaxTicks);
				velocity = new Vector2(dx / t, Math.Max(-LeapMaxUp, (dy - 0.5f * Gravity * t * t) / t));
			}
			MathSafety.Sanitize(ref velocity);
			NPC.velocity = velocity;
			ChangeState((int)Phase.Leap);
		}

		/// <summary>Server: blows up on the first living player it touches.</summary>
		private void CheckTouch() {
			Rectangle box = NPC.Hitbox;
			box.Inflate(TouchMargin, TouchMargin);
			foreach (Player player in Main.ActivePlayers) {
				if (!player.dead && box.Intersects(player.Hitbox)) {
					Detonate();
					return;
				}
			}
		}

		/// <summary>Server: the blast, and the Dinamitrom is gone (no loot: it was spent).</summary>
		private void Detonate() {
			int damage = ExpertStats.HostileProjectile(NPC, BlastDamage);
			if (!SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), NPC.Center, Vector2.Zero, ModContent.ProjectileType<DinamitromBlast>(), damage, BlastKnockback, out _)) {
				return;
			}
			NPC.life = 0;
			NPC.active = false;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
			}
		}

		private void FuseEffects() {
			int face = NPC.direction == 0 ? -1 : NPC.direction;
			Vector2 spark = NPC.Bottom + new Vector2(R.SparkX * -face, R.SparkY);
			bool flaring = CurrentPhase != Phase.Hop;
			if (Main.rand.NextBool(flaring ? 1 : 5) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(spark - new Vector2(2f), 4, 4, DustID.Torch, out Dust d, 0f, -1f)) {
				d.noGravity = true;
				d.velocity = Main.rand.NextVector2Circular(flaring ? 2.5f : 1f, flaring ? 2.5f : 1f);
			}
			Lighting.AddLight(spark, flaring ? 0.8f : 0.4f, flaring ? 0.4f : 0.2f, 0.05f);
			if (CurrentPhase == Phase.Windup && Timer % 6f == 0f) {
				SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = 0.6f, Volume = 0.6f, MaxInstances = 3 }, NPC.Center);   // ticking
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Windup:
					return R.Windup + (int)(Timer / 3f) % R.WindupFrames;
				case Phase.Leap:
					return R.Leap;
			}
			if (!Grounded) {
				return NPC.velocity.Y < 0f ? R.Hop + 1 : R.Hop + 2;
			}
			if (HopTimer < 6f) {
				return R.Hop + 3;                           // just landed
			}
			if (HopTimer > HopInterval - 6) {
				return R.Hop;                               // crouching for the next hop
			}
			return R.Idle + (int)(Timer / 15f) % R.IdleFrames;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 12;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, NPC.life > 0 ? DustID.WoodFurniture : DustID.Smoke, out _);
			}
			if (NPC.life <= 0) {
				SoundEngine.PlaySound(SoundID.Item14 with { Volume = 0.35f, Pitch = 0.4f }, NPC.Center);   // a dud pop, no blast
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
