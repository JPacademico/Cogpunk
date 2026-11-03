using System;
using Cogpunk.Content.MechArmy.Armor;
using Cogpunk.Content.MechArmy.Items;
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
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.MechArmy.MechArmyRigData;

namespace Cogpunk.Content.MechArmy.NPCs
{
	/// <summary>
	/// Jaeger (named "Yager" until 2026-10-28, user), the Mech Army's miniboss (user-set 2026-10-27): a jaeger-style war machine about six times the player's
	/// height (302 px; the player's sprite is about 50), that only joins once the invasion is half done
	/// (<see cref="MechArmyInvasion.JaegerFrom"/>). It walks slowly and relentlessly at its target and hurts by contact:
	/// <see cref="ContactDamage"/> in Expert with a very heavy knockback (<see cref="KnockbackStrength"/>, vanilla's contact
	/// knockback is 4.5) and thick armour (<see cref="Defense"/>, no knockback taken).
	/// <list type="bullet">
	/// <item><b>Walk</b>: a 24-frame cycle (<see cref="R.JaegerWalkFrames"/>), <see cref="TicksPerFrame"/> ticks a frame. Root
	/// motion (art direction 2026-10-26): it moves only on frame changes, by exactly <see cref="R.JaegerStep"/> px, the
	/// distance the planted foot slides back in the art, so its feet never slip: 0.75 px/tick (a walking player runs 3).
	/// Heel strikes thud and shake the ground a little.</item>
	/// <item><b>Turn</b>: a target more than <see cref="TurnHysteresis"/> px behind it makes it stop and turn
	/// (<see cref="TurnTicks"/>), so it never jitters back and forth.</item>
	/// <item><b>Obstacles</b>: when <see cref="HopAfterSteps"/> steps in a row hit a wall, it hops (<see cref="HopSpeed"/>,
	/// about 6 tiles); after <see cref="GiveUpSteps"/> blocked steps it turns back.</item>
	/// <item><b>Hitboxes follow the art</b> (boss-fight rule, applied to the miniboss): contact, melee swings and
	/// projectiles only meet the silhouette strips of the current frame (<see cref="R.JaegerHit"/>).</item>
	/// <item>The Annoy-o-tron's alarm speeds up its whole cycle by half (<see cref="NPCHaste"/>), so the root motion stays
	/// exact.</item>
	/// </list>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor Dark Mage T1, the pre-Hardmode invasion miniboss: 1600
	/// life / 18 defense / 80 contact in Expert): <see cref="Life"/> life, <see cref="Defense"/> defense, 100 contact
	/// (user-set). Counts 10 kills (<see cref="MechArmyInvasion.JaegerKillValue"/>). Drops (user, 2026-10-28): the Goblin
	/// Summoner's coins (value 5000), 1-2 Rusted Metal, one Jaeger armor piece 1 time in <see cref="ArmorPieceOdds"/>
	/// (<see cref="JaegerHelmet"/>, <see cref="JaegerChestplate"/> or <see cref="JaegerGreaves"/>) and the
	/// <see cref="CogpunkerManual"/> 1 time in <see cref="ManualOdds"/>.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the walk phase (ticks into the cycle, advanced by
	/// the haste factor), <c>ai[3]</c> the facing it turns to; the server targets and decides; every side walks and draws
	/// from the synced values (<see cref="ResolveFrame"/>). Spawned by the natural spawn pool, only where its whole body
	/// fits (<see cref="SpawnNPC"/>). D1: no allocation; effects client-side.</para>
	/// </summary>
	[LegacyName("Yager")]
	public class Jaeger : StateMachineNPC
	{
		private enum Phase { Walk, Turn, Hop, Idle }

		public const int Life = 1800, ContactDamage = 100, Defense = 24;
		public const float KnockbackStrength = 13f;
		public const float VanillaKnockback = 4.5f;
		public const int TicksPerFrame = 8;
		public const int CycleTicks = TicksPerFrame * R.JaegerWalkFrames;
		public const float TurnHysteresis = 6f * 16f;
		public const int TurnTicks = 30;
		public const float HopSpeed = 8.5f;
		public const float HopDrift = 2.2f;
		public const int HopAfterSteps = 2, GiveUpSteps = 12;
		public const int RetargetInterval = 60;
		public const float MaxParallax = 4f;
		public const int Width = 136, Height = -R.JaegerTop;
		public const int SpawnSearchColumns = 16, SpawnSearchRows = 8;
		public const int ArmorPieceOdds = 4, ManualOdds = 4;     // 25% each (user-set)

		private static Asset<Texture2D>[] bodyPages, glowPages, nearPages, farPages;

		private Phase CurrentPhase => (Phase)State;
		private ref float WalkPhase => ref NPC.ai[2];
		private ref float TurnTo => ref NPC.ai[3];
		private ref float BlockedSteps => ref NPC.localAI[0];
		private ref float LastStepTick => ref NPC.localAI[1];
		private ref float StepPending => ref NPC.localAI[2];

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 1;
			CogpunkSets.Mechanical[Type] = true;
			CogpunkSets.SelfHasting[Type] = true;
			CogpunkSets.Miniboss[Type] = true;           // the Mech Army's heavyweight (the Metal Wrench's riposte treats it as one)
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() {
				Scale = 0.35f,
				PortraitScale = 0.5f,
				PortraitPositionYOverride = 40f,
				Velocity = 1f,
			});
			if (!Main.dedServ) {
				const string path = "Cogpunk/Content/MechArmy/NPCs/Jaeger";
				bodyPages = DepthLayers.RequestPages(path, R.JaegerBodyPages);
				glowPages = DepthLayers.RequestPages(path + "_Glow", R.JaegerGlowPages);
				nearPages = DepthLayers.RequestPages(path + "_Near", R.JaegerNearPages);
				farPages = DepthLayers.RequestPages(path + "_Far", R.JaegerFarPages);
			}
		}

		public override void Unload() {
			bodyPages = glowPages = nearPages = farPages = null;
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0f;
			NPC.HitSound = SoundID.NPCHit4 with { Pitch = -0.5f };
			NPC.DeathSound = SoundID.NPCDeath14 with { Pitch = -0.4f };
			NPC.value = Item.buyPrice(silver: 50);           // 5000: the Goblin Summoner's (decompiled NPC.SetDefaults, type 471)
			NPC.npcSlots = 5f;
			NPC.aiStyle = -1;
			NPC.rarity = 2;                                  // the Lifeform Analyzer calls it out
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedMetal>(), 1, 1, 2));
			npcLoot.Add(ItemDropRule.OneFromOptions(ArmorPieceOdds, ModContent.ItemType<JaegerHelmet>(),
				ModContent.ItemType<JaegerChestplate>(), ModContent.ItemType<JaegerGreaves>()));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<CogpunkerManual>(), ManualOdds));
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Surface,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		// ------------------------------------------------------------------------------------------------------------
		// AI (every side; decisions on the server)
		// ------------------------------------------------------------------------------------------------------------

		protected override void UpdateState() {
			if (IsAuthority && (Timer % RetargetInterval == 1f || !NPC.HasValidTarget)) {
				int old = NPC.target;
				NPC.TargetClosest(false);
				if (NPC.target != old) {
					NPC.netUpdate = true;
				}
			}
			Player target = NPC.HasValidTarget ? Main.player[NPC.target] : null;
			if (NPC.direction == 0) {
				NPC.direction = -1;
			}
			NPC.spriteDirection = NPC.direction;
			switch (CurrentPhase) {
				case Phase.Turn:
					NPC.velocity.X = 0f;
					if (Timer == TurnTicks / 2 && TurnTo != 0f) {
						NPC.direction = NPC.spriteDirection = (int)TurnTo;
					}
					if (Timer >= TurnTicks && IsAuthority) {
						ChangeState((int)Phase.Walk);
					}
					break;
				case Phase.Hop:
					NPC.velocity.X = NPC.direction * HopDrift * NPCHaste.FactorOf(NPC);
					if (IsAuthority && ((Timer > 8f && NPC.velocity.Y == 0f) || Timer >= 180f)) {
						ChangeState((int)Phase.Walk);
					}
					if (Timer > 8f && NPC.velocity.Y == 0f && !Main.dedServ) {
						Footfall(1.6f);
					}
					break;
				case Phase.Idle:
					NPC.velocity.X = 0f;
					if (IsAuthority && target != null) {
						ChangeState((int)Phase.Walk);
					}
					break;
				default:
					Walk(target);
					break;
			}
			if (!Main.dedServ) {
				ReactorLight();
			}
		}

		/// <summary>Clients: the chest reactor lights its surroundings (ember).</summary>
		private void ReactorLight() {
			int r = ResolveFrame() * 2;
			if (r + 1 >= R.JaegerReactor.Length) {
				return;
			}
			float pulse = 0.8f + 0.2f * MathF.Sin(Main.GlobalTimeWrappedHourly * 3f);
			float rx = NPC.spriteDirection == 1 ? -R.JaegerReactor[r] : R.JaegerReactor[r];
			Lighting.AddLight(RigOrigin + new Vector2(rx, R.JaegerReactor[r + 1]), 0.9f * pulse, 0.45f * pulse, 0.12f);
		}

		private void Walk(Player target) {
			if (IsAuthority && target == null) {
				ChangeState((int)Phase.Idle);
				return;
			}
			if (IsAuthority && target != null && Math.Sign(target.Center.X - NPC.Center.X) == -NPC.direction
				&& Math.Abs(target.Center.X - NPC.Center.X) > TurnHysteresis) {
				TurnTo = -NPC.direction;
				ChangeState((int)Phase.Turn);
				return;
			}
			// The step taken last tick (root motion moves it only on frame changes): did a wall stop it?
			if (StepPending != 0f) {
				StepPending = 0f;
				BlockedSteps = NPC.collideX && NPC.velocity.Y == 0f ? BlockedSteps + 1f : 0f;
				if (IsAuthority && BlockedSteps >= GiveUpSteps) {
					BlockedSteps = 0f;
					TurnTo = -NPC.direction;
					ChangeState((int)Phase.Turn);
					return;
				}
				if (IsAuthority && BlockedSteps >= HopAfterSteps && (BlockedSteps - HopAfterSteps) % 4f == 0f) {
					NPC.velocity.Y = -HopSpeed;
					ChangeState((int)Phase.Hop);
					return;
				}
			}
			int before = (int)(WalkPhase / TicksPerFrame);
			WalkPhase += NPCHaste.FactorOf(NPC);
			if (WalkPhase >= CycleTicks) {
				WalkPhase -= CycleTicks;
			}
			int after = (int)(WalkPhase / TicksPerFrame);
			if (after != before) {
				// Root motion: on a frame change the body moves exactly as far as the planted foot slides back.
				NPC.velocity.X = NPC.direction * R.JaegerStep;
				StepPending = 1f;
				if (!Main.dedServ && R.JaegerFootfall[after % R.JaegerWalkFrames] != 0) {
					Footfall(1f);
				}
			}
			else {
				NPC.velocity.X = 0f;
			}
		}

		/// <summary>The frame for the synced state: walking frames from the phase, the idle cycle otherwise.</summary>
		private int ResolveFrame() {
			switch (CurrentPhase) {
				case Phase.Walk:
					return R.JaegerWalk + Math.Clamp((int)(WalkPhase / TicksPerFrame), 0, R.JaegerWalkFrames - 1);
				case Phase.Hop:
					return R.JaegerWalk + R.JaegerWalkFrames / 4;
				default:
					return R.JaegerIdle + (int)(Timer / 16f) % R.JaegerIdleFrames;
			}
		}

		/// <summary>The ground point under the pelvis (the rig origin).</summary>
		private Vector2 RigOrigin => NPC.Bottom;

		/// <summary>Clients: a heel strike. Dust at the feet, a thud, and a small shake for players nearby.</summary>
		private void Footfall(float strength) {
			if (LastStepTick == Main.GameUpdateCount) {
				return;
			}
			LastStepTick = Main.GameUpdateCount;
			SoundEngine.PlaySound(SoundID.Item14 with { Volume = 0.3f * strength, Pitch = -0.9f, MaxInstances = 2 }, NPC.Bottom);
			for (int i = 0; i < 6; i++) {
				if (SafeSpawn.TryNewDust(NPC.BottomLeft + new Vector2(0f, -6f), NPC.width, 6, DustID.Smoke, out Dust d, 0f, 0f, 0, default, 1.2f)) {
					d.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), Main.rand.NextFloat(-1.2f, 0f));
				}
			}
			if ((CogpunkClientConfig.Instance?.ScreenShake ?? true) && Vector2.DistanceSquared(Main.LocalPlayer.Center, NPC.Bottom) < 900f * 900f) {
				Main.instance.CameraModifiers.Add(new PunchCameraModifier(NPC.Bottom, Vector2.UnitY, 1.6f * strength, 10f, 8, 900f, "Cogpunk:JaegerStep"));
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Contact: heavy knockback; hitboxes that follow the art
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>Runs on the hit player's client (vanilla checks NPC contact there); knockback immunity still applies.</summary>
		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			modifiers.Knockback *= KnockbackStrength / VanillaKnockback;
			modifiers.HitDirectionOverride = target.Center.X >= NPC.Center.X ? 1 : -1;
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item52 with { Pitch = -0.8f, Volume = 0.8f }, target.Center);
			}
		}

		private Rectangle Strip(int frame, int k) {
			int i = (frame * R.JaegerStrips + k) * 4;
			if (i < 0 || i + 3 >= R.JaegerHit.Length) {
				return Rectangle.Empty;
			}
			int x0 = R.JaegerHit[i], y0 = R.JaegerHit[i + 1], x1 = R.JaegerHit[i + 2], y1 = R.JaegerHit[i + 3];
			if (x1 <= x0 || y1 <= y0) {
				return Rectangle.Empty;
			}
			Vector2 origin = RigOrigin;
			int left = NPC.spriteDirection == 1 ? (int)origin.X - x1 : (int)origin.X + x0;   // mirrored when facing right
			return new Rectangle(left, (int)origin.Y + y0, x1 - x0, y1 - y0);
		}

		/// <summary>True if <paramref name="box"/> meets the current frame's silhouette; <paramref name="hit"/> is the strip.</summary>
		public bool TouchesSilhouette(Rectangle box, out Rectangle hit) {
			int frame = ResolveFrame();
			for (int k = 0; k < R.JaegerStrips; k++) {
				hit = Strip(frame, k);
				if (hit.Intersects(box)) {
					return true;
				}
			}
			hit = Rectangle.Empty;
			return false;
		}

		public override bool ModifyCollisionData(Rectangle victimHitbox, ref int immunityCooldownSlot, ref MultipliableFloat damageMultiplier, ref Rectangle npcHitbox) {
			npcHitbox = TouchesSilhouette(victimHitbox, out Rectangle hit) ? hit : Rectangle.Empty;   // empty never intersects
			return false;
		}

		public override bool? CanCollideWithPlayerMeleeAttack(Player player, Item item, Rectangle meleeAttackHitbox) {
			return TouchesSilhouette(meleeAttackHitbox, out _) ? null : false;
		}

		public override bool? CanBeHitByProjectile(Projectile projectile) {
			Rectangle box = projectile.Hitbox;
			if (!box.Intersects(NPC.Hitbox)) {
				return null;                                 // custom-shaped collision (beams, whips): its own code decides
			}
			return TouchesSilhouette(box, out _) ? null : false;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Spawning: only where the whole body fits
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>
		/// Natural spawn (decompiled <c>NPCLoader.SpawnNPC</c>: the pool chose this type on the ground tile
		/// (<paramref name="tileX"/>, <paramref name="tileY"/>)). Its 9 x 19-tile body would be stuck in any overhang, so it
		/// spawns on the nearest column (up to <see cref="SpawnSearchColumns"/> tiles to either side, the ground up to
		/// <see cref="SpawnSearchRows"/> tiles up or down) where the ground is solid and the whole box is clear; nowhere, no
		/// spawn (index <c>Main.maxNPCs</c>, the dummy slot vanilla also returns when full, D0). Bounded loops, every tile
		/// through <see cref="TileSafety"/>.
		/// </summary>
		public override int SpawnNPC(int tileX, int tileY) {
			int halfW = (Width / 16 + 1) / 2;
			int tall = Height / 16 + 1;
			for (int k = 0; k <= SpawnSearchColumns * 2; k++) {
				int x = tileX + (k % 2 == 0 ? k / 2 : -(k / 2 + 1));
				for (int dy = -SpawnSearchRows; dy <= SpawnSearchRows; dy++) {
					int ground = tileY + dy;
					if (!Solid(x, ground) || Solid(x, ground - 1) || !Clear(x - halfW, x + halfW, ground - tall, ground - 1)) {
						continue;
					}
					return SafeSpawn.TryNewNPC(Terraria.Entity.GetSource_NaturalSpawn(), x * 16 + 8, ground * 16, Type, out NPC npc) ? npc.whoAmI : Main.maxNPCs;
				}
			}
			return Main.maxNPCs;
		}

		private static bool Solid(int x, int y) {
			return TileSafety.TryGetTile(x, y, out Tile tile) && tile.HasTile && !tile.IsActuated && Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType];
		}

		private static bool Clear(int x0, int x1, int y0, int y1) {
			for (int x = x0; x <= x1; x++) {
				for (int y = y0; y <= y1; y++) {
					if (!TileSafety.InWorld(x, y) || Solid(x, y)) {
						return false;
					}
				}
			}
			return true;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Death and drawing (clients)
		// ------------------------------------------------------------------------------------------------------------

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 4 : 40;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, NPC.life > 0 ? DustID.Iron : (i % 2 == 0 ? DustID.Smoke : DustID.Torch), out Dust d)) {
					d.velocity *= NPC.life > 0 ? 1f : 3f;
				}
			}
			if (NPC.life <= 0) {
				SoundEngine.PlaySound(SoundID.Item14 with { Volume = 1f, Pitch = -0.4f }, NPC.Center);
				MechArmyGores.Spawn(NPC, "Jaeger_GoreHead", "Jaeger_GorePauldron", "Jaeger_GoreFist");
				MechArmyGores.Spawn(NPC, "Jaeger_GoreBoot", "Jaeger_GorePlate", "Jaeger_GoreFist");
			}
		}

		public override void FindFrame(int frameHeight) {
			NPC.frame = new Rectangle(0, 0, R.JaegerBoundsWidth, R.JaegerBoundsHeight);   // the bestiary sizes its box from this
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			bool dummy = NPC.IsABestiaryIconDummy;
			float scale = dummy ? NPC.scale : 1f;
			int frame = dummy ? R.JaegerIdle : ResolveFrame();
			Vector2 anchor = RigOrigin - screenPos + new Vector2(0f, NPC.gfxOffY);
			anchor = new Vector2(MathF.Round(anchor.X), MathF.Round(anchor.Y));
			bool flip = NPC.spriteDirection == 1;
			Color light = NPC.GetAlpha(drawColor);
			// Feet planted on the ground line: the planes slide against each other horizontally only.
			Vector2 farShift = dummy ? Vector2.Zero : new Vector2(DepthLayers.Shift(anchor, DepthLayers.Far, MaxParallax).X, 0f);
			Vector2 nearShift = dummy ? Vector2.Zero : new Vector2(DepthLayers.Shift(anchor, DepthLayers.Near, MaxParallax).X, 0f);
			DepthLayers.DrawFrame(spriteBatch, farPages, R.JaegerFarFrames, frame, anchor + farShift, 0, DepthLayers.Tint(light, DepthLayers.Far), flip, scale);
			DepthLayers.DrawFrame(spriteBatch, bodyPages, R.JaegerBodyFrames, frame, anchor, 0, light, flip, scale);
			float pulse = 0.8f + 0.2f * MathF.Sin(Main.GlobalTimeWrappedHourly * 3f);
			DepthLayers.DrawFrame(spriteBatch, glowPages, R.JaegerGlowFrames, frame, anchor, 0, Color.White * pulse * NPC.Opacity, flip, scale);
			DepthLayers.DrawFrame(spriteBatch, nearPages, R.JaegerNearFrames, frame, anchor + nearShift, 0, light, flip, scale);
			return false;
		}
	}
}
