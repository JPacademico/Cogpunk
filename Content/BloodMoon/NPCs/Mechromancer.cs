using System;
using Cogpunk.Content.BloodMoon.Projectiles;
using Cogpunk.Content.BloodMoon.Weapons;
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
using Terraria.DataStructures;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.BloodMoon.NPCs.MechromancerRigData;

namespace Cogpunk.Content.BloodMoon.NPCs
{
	/// <summary>
	/// Mechromancer (Mecromante), a Blood Moon mini-boss (user-set 2026-11-12: "a robot with a brass skull soul flame head that
	/// summon cogsqueletons and shoots soul fire cogs"; redrawn 2026-11-16 after the user's reference painting: "rework its
	/// design based on the image example"): a robot necromancer in a deep oak hood with ivory ram horns, a brass skull for a
	/// face with soul-fire eyes, a gilt-trimmed robe open over a crimson under-robe where soul runes burn, bell sleeves over
	/// brass claws full of soul fire, and mechanical eyes floating round it (<see cref="EyeCount"/>, drawn orbiting its hood,
	/// their pupils on its target); it floats (art/bloodmoon/make_mechromancer_art.py; v1 in art/bloodmoon/previous/).
	/// <list type="number">
	/// <item><b>Float</b>: it drifts (<see cref="FloatSpeed"/>, through walls) to a point beside its target, <see cref="KeepX"/>
	/// to the side it is on and <see cref="KeepY"/> above, facing it, bobbing.</item>
	/// <item><b>Cast</b> (every <see cref="CastCooldown"/> ticks of floating, the target within <see cref="SpellRange"/> and in
	/// sight of its claw): the telegraph, <see cref="CastTelegraph"/> ticks (D3 T3: at least 30): its near claw rises and its
	/// soul fire swells, its eyes blaze, its floating eyes flare, a rising chant; then it thrusts the claw at the target and a
	/// volley of <see cref="Volley"/> <see cref="SoulFireCog"/>s leaves the fire at where the target is, <see cref="CogSpread"/>
	/// apart, at <see cref="CogSpeed"/>.</item>
	/// <item><b>Summon</b> (every <see cref="SummonCooldown"/> ticks, fewer than <see cref="MaxMinions"/> of its own risen
	/// and rising): both arms rise, fire in both claws, its floating eyes whirl; at once <see cref="MinionsPerSummon"/>
	/// soul-fire rings (<see cref="MechromancerGrave"/>) burn into the ground beside the target, the telegraph
	/// (<see cref="SummonTelegraph"/> ticks); its arms sweep down and a zombie climbs out of each (user, 2026-11-16: "the
	/// mechromancer should summon regular zombies instead of cogskeletons": vanilla's Zombie, its thrall through
	/// <see cref="MechromancerThrall"/>; the Cogsqueleton is gone).</item>
	/// <item><b>Leave</b> at dawn, or with no target for <see cref="LostTargetTicks"/> ticks: it rises and fades away, and its
	/// zombies fall back into the dirt (they follow their master).</item>
	/// </list>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; T3, after Skeletron): anchor the Dark Mage, the Old One's Army's
	/// pre-Hardmode caster mini-boss (decompiled 1.4.4: 800 life, 18 defense, 40 contact in Classic = 1600 / 18 / 80 in
	/// Expert) and the Blood Moon's own fished mini-boss, the Zombie Merman (400 / 20 / 40 Classic): <see cref="Life"/> life
	/// (under the Dark Mage: its dead fight for it), <see cref="Defense"/> defense, knockback immune,
	/// <see cref="ContactDamage"/> contact (a caster, not a brawler), cogs <see cref="CogDamage"/> each. Drops 6-12 Bone, its
	/// coins and 1 time in <see cref="PossessedCogOdds"/> the <see cref="PossessedCog"/> (user, 2026-11-16: "a chance to drop
	/// 'possessed cog'"; the odds are my call: twice the 1 in 8 of the fished Blood Moon mini-bosses' weapons, terraria.wiki.gg,
	/// as it comes alone and rarely). A mini-boss (<see cref="CogpunkSets.Miniboss"/>) and a machine
	/// (<see cref="CogpunkSets.Mechanical"/>).</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the ticks since its last cast, <c>ai[3]</c> since its last
	/// summon (every side counts; the server's values ride each sync); the server targets, decides, fires and marks the
	/// graves; the drift runs on every side from synced positions; the floating eyes are drawing only (their orbit from the
	/// game clock, their gaze from the synced target). D0: spawns through <see cref="SafeSpawn"/>, the graves and zombies
	/// capped (<see cref="MaxMinions"/>), the ground search bounded and bounds-checked (<see cref="TileSafety"/>). D1: no
	/// allocation; sounds, light and dust on clients; the eyes are <see cref="EyeCount"/> unrotated draws a frame (D4).</para>
	/// </summary>
	public class Mechromancer : GridWalkerNPC
	{
		private enum Phase { Float, Cast, Summon, Leave }

		public const int Life = 1500, ContactDamage = 50, Defense = 18;     // Expert
		public const int CogDamage = 44;                                   // Expert, each
		public const int Volley = 3;
		public const float CogSpeed = 7.5f, CogSpread = 0.17f;              // ~10 degrees between cogs
		public const int CastTelegraph = 40;                                // D3: >= 30 at T0-T4
		public const int CastTicks = CastTelegraph + 30;
		public const int CastCooldown = 150;                                // 2.5 s of floating between spells
		public const int SummonTelegraph = 50;
		public const int SummonTicks = SummonTelegraph + 30;
		public const int SummonCooldown = 480;                              // 8 s
		public const int MinionsPerSummon = 2, MaxMinions = 4;
		public const float FloatSpeed = 1.6f, FloatAccel = 0.05f;
		public const float KeepX = 13f * 16f, KeepY = 5f * 16f;
		public const float SpellRange = 40f * 16f;
		public const int GraveOffsetTiles = 6, GraveJitterTiles = 2, GroundSearchTiles = 16;
		public const int LostTargetTicks = 180;
		public const int LeaveFadeTicks = 60;
		public const float SpawnWeight = 0.04f;
		public const int BoneMin = 6, BoneMax = 12;
		public const int PossessedCogOdds = 4;                             // 25% (my call; see the summary)
		// the floating eyes (drawing only): how many, their orbit round the hood (game px), a lap's length, their bob
		public const int EyeCount = 5;
		public const float EyeOrbitX = 34f, EyeOrbitY = 10f;
		public const int EyeLapTicks = 300, SummonEyeLapTicks = 90;

		private static Asset<Texture2D> far, near, glow, eye, eyeGlow;
		private static readonly string[] GoreNames = { "Mechromancer_GoreSkull", "Mechromancer_GoreHorn", "Mechromancer_GoreClaw" };

		private Phase CurrentPhase => (Phase)State;
		private ref float SinceCast => ref NPC.ai[2];
		private ref float SinceSummon => ref NPC.ai[3];
		private int lostTarget;

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Events.BloodMoon;

		/// <summary>The bob of the float (whole px: 0 or 2, D4 rule 17), drawing only.</summary>
		protected override Vector2 DrawAnchor {
			get {
				float bob = (Main.GameUpdateCount / 20 + NPC.whoAmI) % 2 * 2f;
				return NPC.Bottom - new Vector2(0f, bob);
			}
		}

		protected override float GlowStrength => CurrentPhase == Phase.Leave ? Math.Max(0f, 1f - Timer / LeaveFadeTicks) : 1f;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
			eye = DepthLayers.RequestOptional(Texture + "_Eye");
			eyeGlow = DepthLayers.RequestOptional(Texture + "_EyeGlow");
		}

		public override void Unload() {
			far = near = glow = eye = eyeGlow = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			CogpunkSets.Mechanical[Type] = true;
			CogpunkSets.Miniboss[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Surface,
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Events.BloodMoon,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		public override void SetDefaults() {
			NPC.width = 40;                                  // the robe, the hood and the skull (D4: matched to the 2026-11-16 art;
			NPC.height = 92;                                 // the horns, the sleeves and the floating eyes are not body)
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0f;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath52;
			NPC.value = Item.buyPrice(gold: 1);
			NPC.rarity = 2;                                  // the Lifeform Analyzer calls it out
			NPC.aiStyle = -1;
		}

		/// <summary>The Blood Moon on the surface at night, after Skeletron (T3), one at a time.</summary>
		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			if (!Main.bloodMoon || Main.dayTime || !NPC.downedBoss3 || spawnInfo.Invasion || spawnInfo.PlayerSafe || spawnInfo.Water
				|| !spawnInfo.Player.ZoneOverworldHeight || NPC.AnyNPCs(Type)) {
				return 0f;
			}
			return SpawnWeight;
		}

		public override void OnSpawn(IEntitySource source) {
			if (IsAuthority) {
				SinceCast = CastCooldown / 2f;
				SinceSummon = SummonCooldown - 90f;              // its first spell is soon a summon: what it is known for
				NPC.netUpdate = true;
			}
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ItemID.Bone, 1, BoneMin, BoneMax));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<PossessedCog>(), PossessedCogOdds));
		}

		protected override void UpdateState() {
			if (CurrentPhase != Phase.Leave) {
				Retarget();
			}
			Player target = Target;
			int dir = target != null ? (target.Center.X >= NPC.Center.X ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			SinceCast++;
			SinceSummon++;
			if (IsAuthority && CurrentPhase != Phase.Leave) {
				lostTarget = target == null ? lostTarget + 1 : 0;
				if (Main.dayTime || lostTarget >= LostTargetTicks) {
					ChangeState((int)Phase.Leave);
				}
			}
			NPC.damage = CurrentPhase == Phase.Leave ? 0 : NPC.defDamage;
			switch (CurrentPhase) {
				case Phase.Cast:
					NPC.velocity *= 0.9f;
					NPC.direction = NPC.spriteDirection = dir;
					if (Timer == CastTelegraph && IsAuthority) {
						Fire(target);
					}
					if (IsAuthority && Timer >= CastTicks) {
						SinceCast = 0f;
						ChangeState((int)Phase.Float);
					}
					break;
				case Phase.Summon:
					NPC.velocity *= 0.9f;
					NPC.direction = NPC.spriteDirection = dir;
					if (Timer == 1f && IsAuthority) {
						MarkGraves(target);
					}
					if (IsAuthority && Timer >= SummonTicks) {
						SinceSummon = 0f;
						ChangeState((int)Phase.Float);
					}
					break;
				case Phase.Leave:
					NPC.velocity.X *= 0.95f;
					NPC.velocity.Y = Math.Max(NPC.velocity.Y - 0.08f, -3f);
					NPC.alpha = Math.Min(255, (int)(Timer * 255f / LeaveFadeTicks));
					if (IsAuthority && Timer >= LeaveFadeTicks) {
						NPC.active = false;
						if (Main.netMode == NetmodeID.Server) {
							NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
						}
					}
					break;
				default:
					Drift(target);
					NPC.direction = NPC.spriteDirection = dir;
					if (IsAuthority && target != null && Vector2.DistanceSquared(target.Center, NPC.Center) < SpellRange * SpellRange) {
						if (SinceSummon >= SummonCooldown && Timer % 30f == 0f && OwnMinions() < MaxMinions) {
							ChangeState((int)Phase.Summon);
						}
						else if (SinceCast >= CastCooldown && Collision.CanHitLine(FirePoint(R.Cast + ReleaseFrame), 1, 1, target.position, target.width, target.height)) {
							ChangeState((int)Phase.Cast);
						}
					}
					break;
			}
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Every side: eases towards its spot beside the target (the side it is on), slowly, through walls.</summary>
		private void Drift(Player target) {
			if (target == null) {
				NPC.velocity *= 0.95f;
				return;
			}
			float side = NPC.Center.X < target.Center.X ? -1f : 1f;
			Vector2 goal = target.Center + new Vector2(side * KeepX, -KeepY);
			Vector2 to = goal - NPC.Center;
			Vector2 want = to.LengthSquared() > 64f ? to.SafeNormalize(Vector2.Zero) * FloatSpeed : Vector2.Zero;
			NPC.velocity = Vector2.Lerp(NPC.velocity, want, FloatAccel * 4f);
			if (NPC.velocity.LengthSquared() > FloatSpeed * FloatSpeed) {
				NPC.velocity = NPC.velocity.SafeNormalize(Vector2.Zero) * FloatSpeed;
			}
			if (IsAuthority && Timer % 45f == 0f) {
				NPC.netUpdate = true;                             // a gentle correction for clients' drift
			}
		}

		/// <summary>The Cast frame the volley leaves in: the thrust (Cast4).</summary>
		private const int ReleaseFrame = 4;

		/// <summary>The near claw's soul fire in <paramref name="frame"/> (world space; the art faces left).</summary>
		private Vector2 FirePoint(int frame) {
			int k = Math.Clamp(frame, 0, R.FireX.Length - 1);
			return NPC.Bottom + new Vector2(R.FireX[k] * -NPC.direction, R.FireY[k]);
		}

		/// <summary>Server: the volley, from the claw's fire at where the target is now.</summary>
		private void Fire(Player target) {
			if (target == null) {
				return;
			}
			Vector2 from = FirePoint(R.Cast + ReleaseFrame);
			Vector2 aim = (target.Center - from).SafeNormalize(new Vector2(NPC.direction, 0f));
			int damage = ExpertStats.HostileProjectile(NPC, CogDamage);
			int type = ModContent.ProjectileType<SoulFireCog>();
			for (int k = 0; k < Volley; k++) {
				Vector2 v = aim.RotatedBy((k - (Volley - 1) / 2f) * CogSpread) * CogSpeed;
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, v, type, damage, 2f, out _, Main.myPlayer);
			}
		}

		/// <summary>Server: how many of its own zombies are up or rising (a fixed scan: 200 NPCs, 1000 projectiles).</summary>
		private int OwnMinions() {
			int count = 0, grave = ModContent.ProjectileType<MechromancerGrave>();
			foreach (NPC n in Main.ActiveNPCs) {
				if (n.type == NPCID.Zombie && n.TryGetGlobalNPC(out MechromancerThrall thrall) && thrall.Master == NPC.whoAmI) {
					count++;
				}
			}
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == grave && (int)p.ai[0] == NPC.whoAmI) {
					count++;
				}
			}
			return count;
		}

		/// <summary>Server: burns up to <see cref="MinionsPerSummon"/> graves into the ground either side of the target (the
		/// telegraph); each raises a zombie when it burns out (<see cref="MechromancerGrave"/>).</summary>
		private void MarkGraves(Player target) {
			if (target == null) {
				return;
			}
			int room = Math.Min(MinionsPerSummon, MaxMinions - OwnMinions());
			int type = ModContent.ProjectileType<MechromancerGrave>();
			for (int k = 0; k < room; k++) {
				int side = k % 2 == 0 ? -1 : 1;
				int tx = (int)(target.Center.X / 16f) + side * GraveOffsetTiles + Main.rand.Next(-GraveJitterTiles, GraveJitterTiles + 1);
				if (!FindGround(tx, (int)(target.Bottom.Y / 16f) - GroundSearchTiles / 2, out int groundY)) {
					continue;
				}
				Vector2 at = new(tx * 16f + 8f, groundY * 16f - MechromancerGrave.Height / 2f);
				SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), at, Vector2.Zero, type, 0, 0f, out _, Main.myPlayer, NPC.whoAmI);
			}
		}

		/// <summary>The first solid floor at or below (<paramref name="x"/>, <paramref name="startY"/>) with three tiles of air
		/// over it, within <see cref="GroundSearchTiles"/> (bounds-checked); <paramref name="groundY"/> is the floor's tile row.</summary>
		private static bool FindGround(int x, int startY, out int groundY) {
			groundY = 0;
			for (int y = startY; y < startY + GroundSearchTiles; y++) {
				if (!TileSafety.TryGetTile(x, y, out Tile floor, 10) || !floor.HasTile || !Main.tileSolid[floor.TileType] || floor.IsActuated) {
					continue;
				}
				bool open = true;
				for (int up = 1; up <= 3 && open; up++) {
					if (!TileSafety.TryGetTile(x, y - up, out Tile air, 10) || (air.HasTile && Main.tileSolid[air.TileType] && !air.IsActuated)) {
						open = false;
					}
				}
				if (open) {
					groundY = y;
					return true;
				}
			}
			return false;
		}

		/// <summary>Clients: the soul fire's light, the telegraphs' sounds and sparks, the volley's crack, the summon's slam.</summary>
		private void Effects() {
			Vector2 head = NPC.Bottom + new Vector2(R.HeadX * -NPC.direction, R.HeadY);
			Lighting.AddLight(head, 0.12f, 0.42f, 0.32f);
			switch (CurrentPhase) {
				case Phase.Cast:
					if (Timer == 1f) {
						SoundEngine.PlaySound(SoundID.Item8 with { Pitch = -0.5f, Volume = 0.8f }, NPC.Center);
					}
					if (Timer == CastTelegraph) {
						SoundEngine.PlaySound(SoundID.Item20 with { Pitch = -0.2f }, NPC.Center);
					}
					if (Timer < CastTelegraph && Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()) {
						Vector2 at = FirePoint(R.Cast + 2);
						Lighting.AddLight(at, 0.15f, 0.6f, 0.45f);
						if (SafeSpawn.TryNewDust(at - new Vector2(6f), 12, 12, DustID.CursedTorch, out Dust d)) {
							d.noGravity = true;
							d.velocity = Main.rand.NextVector2Circular(1.5f, 1.5f) - Vector2.UnitY;
						}
					}
					break;
				case Phase.Summon:
					if (Timer == 1f) {
						SoundEngine.PlaySound(SoundID.Item44 with { Pitch = -0.6f }, NPC.Center);
						SoundEngine.PlaySound(SoundID.Zombie53 with { Pitch = -0.4f, Volume = 0.7f }, NPC.Center);
					}
					if (Timer == SummonTelegraph) {
						SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f, Volume = 0.6f }, NPC.Bottom);
					}
					if (Timer < SummonTelegraph && Main.rand.NextBool(2) && CogpunkClientConfig.RollEffect()
						&& SafeSpawn.TryNewDust(head - new Vector2(8f, 8f), 16, 12, DustID.CursedTorch, out Dust f)) {
						f.noGravity = true;
						f.velocity = new Vector2(Main.rand.NextFloat(-0.6f, 0.6f), Main.rand.NextFloat(-2.6f, -1.2f));
					}
					break;
				default:
					if (CurrentPhase == Phase.Float && Main.rand.NextBool(8) && CogpunkClientConfig.RollEffect()
						&& SafeSpawn.TryNewDust(head - new Vector2(6f, 6f), 12, 8, DustID.CursedTorch, out Dust w)) {
						w.noGravity = true;
						w.velocity = new Vector2(Main.rand.NextFloat(-0.3f, 0.3f), Main.rand.NextFloat(-1.6f, -0.6f));
					}
					break;
			}
		}

		/// <summary>The frame: the float's 6-frame loop (8 ticks each); the cast raises the claw over two in-betweens (8 ticks
		/// each), holds it flaring in two flickers to the end of the telegraph, thrusts as the volley leaves and follows through;
		/// the summon raises both arms over two in-betweens, holds them high flickering to the end of its telegraph, sweeps them
		/// down as the dead rise and settles. Visual only, from the synced state and timer.</summary>
		protected override int PickFrame() {
			int t = (int)Timer;
			switch (CurrentPhase) {
				case Phase.Cast:
					if (t < 8) {
						return R.Cast;
					}
					if (t < 16) {
						return R.Cast + 1;
					}
					if (t < CastTelegraph) {
						return R.Cast + 2 + (t / 6) % 2;
					}
					return R.Cast + (t < CastTelegraph + 12 ? ReleaseFrame : 5);
				case Phase.Summon:
					if (t < 10) {
						return R.Summon;
					}
					if (t < 20) {
						return R.Summon + 1;
					}
					if (t < SummonTelegraph) {
						return R.Summon + 2 + (t / 6) % 2;
					}
					return R.Summon + (t < SummonTelegraph + 14 ? 4 : 5);
				default:
					return R.Float + (int)((Main.GameUpdateCount / 8 + (uint)NPC.whoAmI) % R.FloatFrames);
			}
		}

		// --- the floating eyes (drawing only) -------------------------------------------------------------------------------

		/// <summary>The back half of the eyes' orbit, behind the robe; then the body (the base); the front half goes on top.</summary>
		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			if (!NPC.IsABestiaryIconDummy) {
				DrawEyes(spriteBatch, screenPos, drawColor, front: false);
			}
			return base.PreDraw(spriteBatch, screenPos, drawColor);
		}

		protected override void DrawExtras(SpriteBatch spriteBatch, Vector2 anchor, Color light, bool flip, float scale, bool dummy) {
			if (!dummy) {
				DrawEyes(spriteBatch, Main.screenPosition, light, front: true);
			}
		}

		/// <summary>The eyes' orbit angle now: a slow lap while floating, a whirl while summoning (the game clock: visual only).</summary>
		private float OrbitAngle(int k) {
			float lap = CurrentPhase == Phase.Summon ? SummonEyeLapTicks : EyeLapTicks;
			float t = Main.GameUpdateCount + NPC.whoAmI * 37f;
			return t / lap * MathHelper.TwoPi + k * MathHelper.TwoPi / EyeCount;
		}

		/// <summary>
		/// The floating eyes on one half of their orbit round the hood (an ellipse, <see cref="EyeOrbitX"/> x
		/// <see cref="EyeOrbitY"/> game px): those on its far side are drawn behind the body and a step darker, the rest in
		/// front. Each bobs by whole pixels (0 or 2) on its own beat, sits on the 2 px grid, and looks at the target (the pupil
		/// frame towards it, one of nine); their irises glow, brighter while it casts and summons. D1/D4: nothing allocated,
		/// nothing rotated.
		/// </summary>
		private void DrawEyes(SpriteBatch spriteBatch, Vector2 screenPos, Color light, bool front) {
			if (eye?.IsLoaded != true || eye.Value.Height < R.EyeFrames * R.EyeCell || NPC.Opacity <= 0f) {
				return;
			}
			int dir = NPC.spriteDirection == 1 ? 1 : -1;
			Vector2 head = DrawAnchor + new Vector2(R.HeadX * -dir, R.HeadY);
			Player target = Target;
			float flare = CurrentPhase == Phase.Cast && Timer < CastTelegraph + 12 ? 1f : CurrentPhase == Phase.Summon ? 0.9f : 0.55f;
			for (int k = 0; k < EyeCount; k++) {
				float a = OrbitAngle(k);
				float depth = MathF.Sin(a);
				if ((depth > 0f) != front) {
					continue;
				}
				int bob = ((int)(Main.GameUpdateCount / 14) + k) % 2 * 2;
				Vector2 world = head + new Vector2(MathF.Cos(a) * EyeOrbitX, depth * EyeOrbitY + bob);
				int frame = 0;
				if (target != null) {
					Vector2 look = target.Center - world;
					if (look.LengthSquared() > 64f) {
						int octant = (int)MathF.Round(MathF.Atan2(look.Y, look.X) / MathHelper.PiOver4);
						frame = 1 + ((octant % 8) + 8) % 8;
					}
				}
				Vector2 at = world - screenPos - new Vector2(R.EyeCell * 0.5f);
				at = new Vector2(DepthLayers.Snap(at.X), DepthLayers.Snap(at.Y));
				Rectangle source = new(0, frame * (R.EyeCell + 2), R.EyeCell, R.EyeCell);
				Color tint = front ? light : DepthLayers.Tint(light, DepthLayers.Far);
				spriteBatch.Draw(eye.Value, at, source, tint * NPC.Opacity);
				if (eyeGlow?.IsLoaded == true && eyeGlow.Value.Height >= source.Bottom) {
					spriteBatch.Draw(eyeGlow.Value, at, source, new Color(255, 255, 255, 0) * (flare * NPC.Opacity * (front ? 1f : 0.6f)));
				}
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 24;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.CursedTorch : DustID.Copper, out _);
			}
			if (NPC.life > 0) {
				return;
			}
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center + new Vector2(0f, -24f + i * 18f), Main.rand.NextVector2Circular(3f, 3f),
						gore.Type, out _);
				}
			}
		}
	}
}
