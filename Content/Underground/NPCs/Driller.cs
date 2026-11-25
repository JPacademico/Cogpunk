using System;
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
using Terraria.GameContent;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Underground.NPCs.DrillerRigData;

namespace Cogpunk.Content.Underground.NPCs
{
	/// <summary>
	/// The Driller (user, 2026-11-25: "a new enemy that can spawn on the underground called "driller" a drill bot that can drill
	/// (phase through blocks like a worm) if it gets stuck while chasing the player, behaving like a worm enemy while driling but
	/// a normal chasing enemy while not driling"): a brass mining bot on a tread with a cone drill.
	/// <list type="bullet">
	/// <item><b>Rolling</b>: it chases like a fighter (vanilla collision, gravity, a hop at walls).</item>
	/// <item><b>Stuck</b> (the server judges): no headway for <see cref="StuckTicks"/> while it wants to move (SKILL §3.4: ticks
	/// of almost no speed, not wall touches), or its target <see cref="FarRows"/> tiles above or below with no line to them for
	/// <see cref="StrandedTicks"/> → it <b>bores in</b> (<see cref="BoreTicks"/>: the drill revs, a shriek, it tips nose
	/// down).</item>
	/// <item><b>Drilling</b>: a worm's head: no gravity, no tile collision, steering towards its target at most
	/// <see cref="DrillTurn"/> radians a tick at <see cref="DrillSpeed"/> (vanilla's worms turn and accelerate the same way), dirt
	/// and grinding while inside rock. It surfaces only where its whole hitbox is in open air (never inside a block), after at
	/// least <see cref="MinDrillTicks"/>, once near its target or in sight of it, or after <see cref="MaxDrillTicks"/> in any
	/// open air; then it falls and rolls again. Nothing is dug out of the world: it phases through.</item>
	/// <item>Mechanical (Hit the Joints, the Screwdriver); immune to poison.</item>
	/// </list>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv): between the cavern's Undead Miner (terraria.wiki.gg 1.4.4 Expert
	/// pre-Hardmode: 140 life, 9 defense, 44 contact) and Hardmode's Digger (400 / 10-30 / 56-90): a pre-Hardmode cavern
	/// machine. Drops (my calls): 3-6 of one base ore it bored through (copper, tin, iron or lead), Rusted Cogs 1-2 half the time.</para>
	/// <para>D2: the server decides when it bores in and surfaces (state in <c>ai[0]</c>, the switches synced); while drilling it
	/// syncs its position and velocity every <see cref="DrillSyncTicks"/> ticks (worms do it often too); every side steers the
	/// same way between syncs. D0: the open-air test is vanilla's bounded <c>Collision.SolidCollision</c> over its hitbox; every
	/// timer capped; never stuck in a block (it can't surface inside one, and drilling has no limit while buried). D1: no
	/// allocation per tick.</para>
	/// </summary>
	public class Driller : GridWalkerNPC
	{
		private enum Phase { Roll, Bore, Drill }

		public const int Life = 240, ContactDamage = 48, Defense = 14;
		public const float KnockbackResist = 0.25f;
		public const float RollSpeed = 2.4f, RollAccel = 0.08f, JumpSpeed = 6.5f;
		public const int StuckTicks = 90, StrandedTicks = 150, FarRows = 8;
		public const int BoreTicks = 24, MinDrillTicks = 40, MaxDrillTicks = 6 * 60, DrillSyncTicks = 12;
		public const float DrillSpeed = 5f, DrillAccel = 0.12f, DrillTurn = 0.06f;
		public const float SurfaceRange = 6f * 16f, SightRange = 18f * 16f;
		public const float SpawnWeight = 0.12f;

		private static Asset<Texture2D> glow, drillSheet, drillGlow;

		private Phase CurrentPhase => (Phase)State;
		private ref float Stuck => ref NPC.ai[2];                      // server: ticks without headway (or stranded)
		private ref float Stranded => ref NPC.ai[3];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => null;
		protected override Asset<Texture2D> NearSheet => null;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Caverns;

		/// <summary>The rig origin from the hitbox's middle (facing left: the drill makes the body box lopsided).</summary>
		public const int RigShift = -(R.BodyLeft + R.BodyRight) / 2;

		protected override Vector2 DrawAnchor => NPC.Bottom + new Vector2(NPC.spriteDirection == 1 ? -RigShift : RigShift, 0f);

		protected override void LoadSheets() {
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
			drillSheet = DepthLayers.RequestOptional(Texture + "_Drill");
			drillGlow = DepthLayers.RequestOptional(Texture + "_DrillGlow");
		}

		public override void Unload() {
			glow = drillSheet = drillGlow = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			CogpunkSets.Mechanical[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		public override void SetDefaults() {
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = R.BodyRight - R.BodyLeft;
			NPC.height = -R.BodyTop;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Item.buyPrice(silver: 4);                     // a little over the Undead Miner's 2.5 silver
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player player = spawnInfo.Player;
			bool underground = player.ZoneDirtLayerHeight || player.ZoneRockLayerHeight;
			return underground && !player.ZoneDungeon && !player.ZoneLihzhardTemple && !player.ZoneGlowshroom && !spawnInfo.PlayerInTown
				&& !spawnInfo.Water ? SpawnWeight : 0f;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(new OneFromRulesRule(1, ItemDropRule.Common(ItemID.CopperOre, 1, 3, 6), ItemDropRule.Common(ItemID.TinOre, 1, 3, 6),
				ItemDropRule.Common(ItemID.IronOre, 1, 3, 6), ItemDropRule.Common(ItemID.LeadOre, 1, 3, 6)));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedCog>(), 2, 1, 2));
		}

		protected override void UpdateState() {
			Retarget();
			Player target = Target;
			switch (CurrentPhase) {
				case Phase.Bore:
					NPC.velocity.X *= 0.85f;
					if (target != null) {
						NPC.direction = NPC.spriteDirection = target.Center.X >= NPC.Center.X ? 1 : -1;
					}
					if (IsAuthority && Timer >= BoreTicks) {
						Vector2 aim = target != null ? (target.Center - NPC.Center).SafeNormalize(Vector2.UnitY) : Vector2.UnitY;
						NPC.velocity = aim * 2f;                        // it noses in towards them
						ChangeState((int)Phase.Drill);
					}
					break;
				case Phase.Drill:
					DrillAt(target);
					break;
				default:
					RollAt(target);
					break;
			}
			NPC.noGravity = NPC.noTileCollide = CurrentPhase == Phase.Drill;
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Rolling: a fighter; the server counts how long it has been stuck or stranded and bores in.</summary>
		private void RollAt(Player target) {
			int dir = target != null ? (target.Center.X >= NPC.Center.X ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			bool wants = target != null && Math.Abs(target.Center.X - NPC.Center.X) > 16f;
			Run(wants ? dir : 0, RollSpeed, RollAccel, JumpSpeed);
			FaceMotion(dir);
			if (!IsAuthority || target == null) {
				return;
			}
			Stuck = wants && Math.Abs(NPC.velocity.X) < 0.3f ? Stuck + 1f : Math.Max(0f, Stuck - 2f);
			bool far = Math.Abs(target.Center.Y - NPC.Center.Y) > FarRows * 16f;
			bool sight = Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height);
			Stranded = far && !sight ? Stranded + 1f : 0f;
			if (Stuck >= StuckTicks || Stranded >= StrandedTicks) {
				Stuck = Stranded = 0f;
				ChangeState((int)Phase.Bore);
			}
		}

		/// <summary>Drilling: a worm's head. It turns its velocity towards the target a little a tick and speeds up to
		/// <see cref="DrillSpeed"/>; the server surfaces it only in open air.</summary>
		private void DrillAt(Player target) {
			Vector2 want = target != null ? (target.Center - NPC.Center).SafeNormalize(Vector2.UnitY) : Vector2.UnitY;
			Vector2 dir = NPC.velocity.SafeNormalize(want);
			float turn = MathHelper.WrapAngle(want.ToRotation() - dir.ToRotation());
			dir = dir.RotatedBy(MathHelper.Clamp(turn, -DrillTurn, DrillTurn));
			float speed = Math.Min(DrillSpeed, NPC.velocity.Length() + DrillAccel);
			NPC.velocity = dir * speed;
			if (Math.Abs(NPC.velocity.X) > 0.1f) {
				NPC.direction = NPC.spriteDirection = Math.Sign(NPC.velocity.X);
			}
			if (!IsAuthority) {
				return;
			}
			if ((int)Timer % DrillSyncTicks == 0) {
				NPC.netUpdate = true;
			}
			if (Timer < MinDrillTicks || Collision.SolidCollision(NPC.position, NPC.width, NPC.height)) {
				return;                                                // still in the rock (it never surfaces inside a block)
			}
			bool near = target != null && Vector2.DistanceSquared(target.Center, NPC.Center) <= SurfaceRange * SurfaceRange;
			bool seen = target != null && Vector2.DistanceSquared(target.Center, NPC.Center) <= SightRange * SightRange
				&& Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height);
			if (near || seen || Timer >= MaxDrillTicks || target == null) {
				NPC.velocity *= 0.5f;
				ChangeState((int)Phase.Roll);
			}
		}

		private void Effects() {
			if (CurrentPhase == Phase.Bore && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Item22 with { Pitch = 0.2f, Volume = 0.6f, MaxInstances = 3 }, NPC.Center);   // the drill revs
			}
			if (CurrentPhase == Phase.Drill) {
				bool buried = Collision.SolidCollision(NPC.position, NPC.width, NPC.height);
				if (buried && (int)Timer % 12 == 0) {
					SoundEngine.PlaySound(SoundID.Item22 with { Pitch = -0.2f, Volume = 0.45f, MaxInstances = 3 }, NPC.Center);
				}
				if (buried && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(NPC.Center - new Vector2(10f), 20, 20, DustID.Dirt, out Dust d)) {
					d.velocity = -NPC.velocity * 0.3f + Main.rand.NextVector2Circular(1.5f, 1.5f);
					d.noGravity = Main.rand.NextBool();
				}
			}
			else if (Main.rand.NextBool(24) && CogpunkClientConfig.RollEffect()) {
				Vector2 stack = DrawAnchor + new Vector2(NPC.spriteDirection == 1 ? -10f : 10f, -26f);
				if (SafeSpawn.TryNewDust(stack - new Vector2(3f), 6, 6, DustID.Smoke, out Dust puff)) {
					puff.velocity = new Vector2(0f, -0.8f);                 // a puff from its stack
					puff.scale = 0.9f;
				}
			}
			Lighting.AddLight(NPC.Center, 0.18f, 0.07f, 0.02f);                // its ember eye
		}

		protected override int PickFrame() {
			int step = CurrentPhase == Phase.Bore ? 3 : Math.Abs(NPC.velocity.X) > 0.2f ? 6 : 14;
			return (int)(Main.GameUpdateCount / (uint)step % (uint)R.Frames);
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			if (CurrentPhase != Phase.Drill || NPC.IsABestiaryIconDummy || drillSheet?.IsLoaded != true) {
				return base.PreDraw(spriteBatch, screenPos, drawColor);
			}
			float angle = NPC.velocity.LengthSquared() > 0.01f ? NPC.velocity.ToRotation() : (NPC.direction == 1 ? 0f : MathHelper.Pi);
			int heading = (int)MathF.Round(angle / MathHelper.TwoPi * R.Headings);
			heading = ((heading % R.Headings) + R.Headings) % R.Headings;
			int spin = (int)(Main.GameUpdateCount / 3u % (uint)R.Spins);
			Rectangle source = new(heading * R.DrillStride, spin * R.DrillStride, R.DrillCell, R.DrillCell);
			Vector2 at = NPC.Center - screenPos - new Vector2(R.DrillCell * 0.5f);
			at = new Vector2(MathF.Round(at.X / 2f) * 2f, MathF.Round(at.Y / 2f) * 2f);
			spriteBatch.Draw(drillSheet.Value, at, source, NPC.GetAlpha(drawColor));
			if (drillGlow?.IsLoaded == true) {
				spriteBatch.Draw(drillGlow.Value, at, source, Color.White * NPC.Opacity);
			}
			return false;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 14;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 2 == 0 ? DustID.Iron : DustID.GoldCoin, out _);
			}
		}
	}
}
