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
using Terraria.GameContent.Bestiary;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Jungle.NPCs.RhinoBeetleRigData;

namespace Cogpunk.Content.Jungle.NPCs
{
	/// <summary>
	/// Rhino Beetle, a rare Hardmode jungle enemy (user-set 2026-11-11: "add a new enemy to populate the ruins: rhino beetle
	/// (ensure good sprite and animations)"; moved the same day, second request: "make the rhino beetle have high armor and
	/// knockback; make the rhino a rare enemy of the jungle on hardmode instead of the ruins now"; the behaviour and numbers
	/// are my calls). A giant rhinoceros beetle, its shell marked with a spore-lit glow. It crawls after its target; with the
	/// target roughly level (<see cref="ChargeHeight"/>) and in sight within <see cref="ChargeRange"/> it braces (the
	/// telegraph, <see cref="BraceTicks"/> ticks: the front sinks, the horn levels, the fore legs scrape, it chirps), then
	/// charges straight along that line up to <see cref="ChargeSpeed"/>, never turning (a jump clears it). A ram flicks its
	/// horn up: the player is thrown hard the way it runs (x<see cref="RamKnockback"/> vanilla's knockback) and tossed into the
	/// air (<see cref="TossSpeed"/>, <see cref="RhinoTossPlayer"/>), and it settles; its plain touch shoves too
	/// (x<see cref="ContactKnockback"/>). A charge into a wall at speed leaves it dazed (<see cref="DazedTicks"/>, harmless
	/// meanwhile); overshooting by <see cref="Overshoot"/> makes it skid. When its target is far above it
	/// (<see cref="FlyRise"/>) or it has made no headway for <see cref="StuckTicks"/> ticks (a wall too high to hop), it opens
	/// its shell and flies (up to <see cref="FlyMaxTicks"/>, hovering over the target) and drops back down once over them. The
	/// charge hits for x<see cref="ChargeDamageMultiplier"/> its contact damage. Heavy armour: <see cref="Defense"/> defense,
	/// and it shrugs off most knockback (<see cref="KnockbackResist"/>).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Giant Tortoise, terraria.wiki.gg: Hardmode Jungle
	/// and Underground Jungle, 470 life, 30 defense (60 spinning), 80 contact (160 spinning) in Classic = 940 / 30 / 160 (320)
	/// in Expert, 70% knockback resistance: the jungle's armoured charger): <see cref="Life"/> life, <see cref="Defense"/>
	/// defense, <see cref="CrawlDamage"/> contact and 192 charging. Rare: weight <see cref="SpawnWeight"/> in the jungle's
	/// pool in Hardmode (<see cref="SurfaceWeight"/> on the surface), one at a time (<see cref="SpawnChance"/>). Drops coins
	/// only.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the charge's direction (locked by the server with the
	/// state change), <c>ai[3]</c> the charge's cooldown; the server decides every change (its stuck count and flight cooldown
	/// are server-only); every side runs the movement, gravity and contact damage from the synced state. The toss is applied
	/// by the thrown player's own client, the knockback by vanilla on the same client. D1: no allocation; dust, sound and
	/// light on clients.</para>
	/// </summary>
	public class RhinoBeetle : GridWalkerNPC
	{
		private enum Phase { Crawl, Brace, Charge, Toss, Skid, Dazed, TakeOff, Fly, Land }

		public const int Life = 800, CrawlDamage = 120, Defense = 45;        // Expert (user, 2026-11-11b: "high armor")
		public const float ChargeDamageMultiplier = 1.6f;                     // 192 in Expert
		public const int Width = 52, Height = 32;
		public const float KnockbackResist = 0.1f;                            // heavy: 90% resisted (the Tortoise: 70%)
		/// <summary>Vanilla's knockback on the hit player times this: x2 for a ram (about 20 tiles on flat ground, decompiled
		/// <c>Player.Hurt</c>: velocity = knockback sideways and x7/9 of it upwards), x1.5 for a plain touch (about 11; user,
		/// 2026-11-11b: "high knockback").</summary>
		public const float RamKnockback = 2f, ContactKnockback = 1.5f;
		public const float CrawlSpeed = 1.2f, CrawlAccel = 0.08f, JumpSpeed = 6.5f;
		public const float ChargeSpeed = 7.5f, ChargeAccel = 0.4f;
		public const float ChargeRange = 22f * 16f;
		public const float ChargeHeight = 3f * 16f;
		public const float Overshoot = 5f * 16f;
		public const int BraceTicks = 40;                                      // the telegraph (D3: >= 30 at T0-T4)
		public const int ChargeMaxTicks = 90;
		public const int TossTicks = 24, SkidTicks = 24, DazedTicks = 75;
		public const float WallStunSpeed = 4f;
		public const int ChargeCooldown = 100;
		/// <summary>The rammed player's upward speed, px/tick: about eight tiles at vanilla's player gravity (over the x2
		/// knockback's own 7 px/tick lift).</summary>
		public const float TossSpeed = 10f;
		public const float FlyRise = 6f * 16f, FlyRangeX = 30f * 16f;
		public const int StuckTicks = 50;
		public const float StuckSpeed = 0.3f;                                  // below this it is making no headway
		public const int TakeOffTicks = 16, FlyMaxTicks = 240, LandMaxTicks = 180, FlyCooldown = 300;
		public const float FlySpeed = 3.2f, FlyAccel = 0.12f, FlyHover = 3f * 16f, LiftSpeed = 1.8f;
		public const float DropRangeX = 2f * 16f;
		public const int FlapTicks = 3;                                        // game ticks per wing frame (a 12-tick beat)
		/// <summary>Its weight in a Hardmode jungle spawn pool (vanilla's own pick weighs 1): rare (my call).</summary>
		public const float SpawnWeight = 0.05f;
		public const float SurfaceWeight = 0.07f;                              // the surface jungle, where the tortoises roam too
		/// <summary>Game px of travel per walk / charge frame: the art's own foot step, so a planted foot never slips.</summary>
		public const float WalkAnimDistance = R.WalkStep, ChargeAnimDistance = R.ChargeStep;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "RhinoBeetle_GoreHorn", "RhinoBeetle_GoreShell", "RhinoBeetle_GoreLeg", "RhinoBeetle_GoreLeg" };
		private static readonly SoundStyle Chirp = SoundID.NPCHit31 with { Pitch = 0.6f, Volume = 0.55f, MaxInstances = 3 };
		private static readonly SoundStyle Rush = SoundID.NPCHit31 with { Pitch = -0.45f, Volume = 0.8f, MaxInstances = 2 };
		private static readonly SoundStyle Flick = SoundID.Item1 with { Pitch = -0.5f, Volume = 0.8f, MaxInstances = 2 };
		private static readonly SoundStyle Bonk = SoundID.Dig with { Pitch = -0.3f, Volume = 0.9f, MaxInstances = 2 };
		private static readonly SoundStyle Buzz = SoundID.Item32 with { Pitch = -0.45f, Volume = 0.4f, MaxInstances = 2 };

		// --- what a variant changes (2026-11-16: the Jade Beetle, Jadey's lesser jade copy, overrides these) -----------------
		/// <summary>Expert life, contact damage and defense (<see cref="CogpunkNPC.SetExpertStats"/>).</summary>
		protected virtual int ExpertLife => Life;
		protected virtual int ExpertContact => CrawlDamage;
		protected virtual int ExpertDefense => Defense;
		protected virtual float Resist => KnockbackResist;
		/// <summary>Vanilla's knockback on the hit player times these (the ram, a plain touch), and the toss's upward speed.</summary>
		protected virtual float RamPush => RamKnockback;
		protected virtual float TouchPush => ContactKnockback;
		protected virtual float Toss => TossSpeed;
		protected virtual int CoinValue => Item.buyPrice(silver: 10);
		protected virtual string[] Gores => GoreNames;
		protected virtual int BloodDust => DustID.GreenBlood;

		/// <summary>Anything else a variant's hit does to a player (the hit player's own client and the others, as
		/// <see cref="OnHitPlayer"/>).</summary>
		protected virtual void OnBeetleHit(Player target) {
		}

		private Phase CurrentPhase => (Phase)State;
		private ref float ChargeDir => ref NPC.ai[2];
		private ref float Cooldown => ref NPC.ai[3];
		private float targetX;
		private int stuck, flyCooldown;                                        // server-only

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Jungle;

		/// <summary>The rune on its shell flares while it braces and charges.</summary>
		protected override float GlowStrength => CurrentPhase == Phase.Brace || CurrentPhase == Phase.Charge ? 1f : 0.65f;

		/// <summary>A hover bob in flight: the whole sprite dips two game px on the wings' down-beat (every plane together, so
		/// no plane's pixels change: check_flicker).</summary>
		protected override Vector2 DrawAnchor => Frame == R.Fly + 2 ? NPC.Bottom + new Vector2(0f, 2f) : NPC.Bottom;

		private bool Charging => CurrentPhase == Phase.Charge;

		/// <summary>The charge and the first half of the toss: the horn still hits as hard and tosses (a hit decided on the
		/// player's client can reach it a few ticks after the server's ram already turned the charge into the toss).</summary>
		private bool Ramming => Charging || (CurrentPhase == Phase.Toss && Timer <= TossTicks / 2);
		private bool Airborne => CurrentPhase == Phase.Fly || (CurrentPhase == Phase.TakeOff && Timer > TakeOffTicks / 2);

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			far = near = glow = null;
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(ExpertLife, ExpertContact, ExpertDefense);
			NPC.knockBackResist = Resist;
			NPC.HitSound = SoundID.NPCHit31;                                   // the Antlion Charger's
			NPC.DeathSound = SoundID.NPCDeath34;
			NPC.value = CoinValue;                                             // rare (the Tortoise drops 5 silver): 10 silver
			NPC.aiStyle = -1;
		}

		/// <summary>Rare in a Hardmode jungle, on the ground, one at a time (my calls); never in the temple, the dungeon, water,
		/// towns, invasions or pillar zones.</summary>
		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player p = spawnInfo.Player;
			if (!Main.hardMode || !p.ZoneJungle || p.ZoneDungeon || p.ZoneLihzhardTemple || p.ZoneUnderworldHeight || spawnInfo.Water
				|| spawnInfo.Invasion || spawnInfo.PlayerInTown || spawnInfo.PlayerSafe || p.ZoneTowerSolar || p.ZoneTowerVortex
				|| p.ZoneTowerNebula || p.ZoneTowerStardust || NPC.AnyNPCs(Type)) {
				return 0f;
			}
			return p.ZoneOverworldHeight ? SurfaceWeight : SpawnWeight;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Jungle,
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.UndergroundJungle,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		protected override void UpdateState() {
			if (Cooldown > 0f) {
				Cooldown--;
			}
			if (IsAuthority && flyCooldown > 0) {
				flyCooldown--;
			}
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			// from the synced state, on every side (defDamage holds the mode-scaled contact damage)
			NPC.damage = Ramming ? (int)(NPC.defDamage * ChargeDamageMultiplier) : (CurrentPhase == Phase.Dazed ? 0 : NPC.defDamage);
			NPC.knockBackResist = Ramming ? 0f : Resist;
			NPC.noGravity = Airborne;
			switch (CurrentPhase) {
				case Phase.Brace:
					Run(0, 0f, CrawlAccel * 4f, JumpSpeed);
					NPC.direction = NPC.spriteDirection = dir;
					if (!Main.dedServ) {
						BraceEffects();
					}
					if (IsAuthority && Timer >= BraceTicks) {
						ChargeDir = dir;
						ChangeState((int)Phase.Charge);
					}
					break;
				case Phase.Charge:
					DoCharge(target);
					break;
				case Phase.Toss:
					NPC.velocity.X *= 0.85f;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(Flick, NPC.Center);
					}
					if (IsAuthority && Timer >= TossTicks) {
						Cooldown = ChargeCooldown;
						ChangeState((int)Phase.Crawl);
					}
					break;
				case Phase.Skid:
					NPC.velocity.X *= 0.9f;
					if (!Main.dedServ && Timer % 4f == 0f) {
						SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(0f, 4f), NPC.width, 4, DustID.Stone, out _, -NPC.velocity.X * 0.3f, -1f);
					}
					if (IsAuthority && Timer >= SkidTicks) {
						Cooldown = ChargeCooldown;
						ChangeState((int)Phase.Crawl);
					}
					break;
				case Phase.Dazed:
					NPC.velocity.X *= 0.85f;
					if (!Main.dedServ && Main.rand.NextBool(5) && CogpunkClientConfig.RollEffect()) {
						SafeSpawn.TryNewDust(NPC.Top + new Vector2(-8f, -8f), 16, 8, DustID.Smoke, out _, 0f, -1.2f);
					}
					if (IsAuthority && Timer >= DazedTicks) {
						Cooldown = ChargeCooldown;
						ChangeState((int)Phase.Crawl);
					}
					break;
				case Phase.TakeOff:
					NPC.velocity.X *= 0.85f;
					if (Airborne) {
						NPC.velocity.Y = Math.Max(NPC.velocity.Y - 0.3f, -LiftSpeed);   // lifting off
					}
					if (!Main.dedServ) {
						WingEffects();
					}
					if (IsAuthority && Timer >= TakeOffTicks) {
						ChangeState((int)Phase.Fly);
					}
					break;
				case Phase.Fly:
					DoFly(target, dir);
					break;
				case Phase.Land:
					NPC.velocity.X *= 0.96f;
					FaceMotion(dir);
					if (IsAuthority && ((Grounded && Timer > 2f) || Timer >= LandMaxTicks)) {
						flyCooldown = FlyCooldown;
						ChangeState((int)Phase.Crawl);
					}
					break;
				default:
					Crawl(target, dx, dir);
					break;
			}
		}

		/// <summary>Crawls after the target; the server starts a brace when the target is level and in sight, or a take-off when
		/// the target is far above it or a wall has stopped it a while.</summary>
		private void Crawl(Player target, float dx, int dir) {
			Run(target != null ? dir : 0, CrawlSpeed, CrawlAccel, JumpSpeed);
			FaceMotion(dir);
			if (!IsAuthority || target == null) {
				return;
			}
			// no headway: pressed against a wall it can't hop (Run's hops reset nothing here: they don't move it either)
			stuck = Math.Abs(NPC.velocity.X) < StuckSpeed ? stuck + 1 : 0;
			float dy = target.Bottom.Y - NPC.Bottom.Y;
			if (flyCooldown <= 0 && Grounded && Math.Abs(dx) < FlyRangeX && (dy < -FlyRise || stuck >= StuckTicks)) {
				stuck = 0;
				ChangeState((int)Phase.TakeOff);
				return;
			}
			if (Grounded && Cooldown <= 0f && Math.Abs(dx) < ChargeRange && Math.Abs(dy) < ChargeHeight
				&& Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height)) {
				NPC.direction = NPC.spriteDirection = dir;
				ChangeState((int)Phase.Brace);
			}
		}

		/// <summary>Straight along the locked direction, never turning; a wall at speed dazes it, a ram tosses the player and
		/// ends it, overshooting the target (as it stood when the charge began) by <see cref="Overshoot"/> or running out of
		/// time makes it skid (server).</summary>
		private void DoCharge(Player target) {
			int dir = ChargeDir >= 0f ? 1 : -1;
			if (Timer == 1f) {
				targetX = target != null ? target.Center.X : NPC.Center.X + dir * ChargeRange;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(Rush, NPC.Center);
				}
			}
			Run(dir, ChargeSpeed, ChargeAccel, JumpSpeed * 0.6f);
			NPC.direction = NPC.spriteDirection = dir;
			if (!Main.dedServ && Timer % 3f == 0f) {
				SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(0f, 4f), NPC.width, 4, DustID.Stone, out _, -dir * 2f, -1.2f);
			}
			if (!IsAuthority) {
				return;
			}
			if (NPC.collideX && Math.Abs(NPC.oldVelocity.X) > WallStunSpeed) {
				NPC.velocity.X = -dir * 2f;                                      // bounced off the wall
				ChangeState((int)Phase.Dazed);
				if (!Main.dedServ) {
					BonkEffects(dir);
				}
				return;
			}
			if (RammedSomeone()) {
				ChangeState((int)Phase.Toss);
				return;
			}
			bool past = dir > 0 ? NPC.Center.X > targetX + Overshoot : NPC.Center.X < targetX - Overshoot;
			if (past || Timer >= ChargeMaxTicks) {
				ChangeState((int)Phase.Skid);
			}
		}

		/// <summary>Server: a ram ends the charge (the Mechanical Bull's test: player hitboxes as the server has them, a little
		/// slack, since vanilla decides the contact hit on the hit player's own client).</summary>
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

		/// <summary>Flies towards a point <see cref="FlyHover"/> over the target (tile collision on); the server lands it once it
		/// is over the target, when its time runs out or when the target is gone.</summary>
		private void DoFly(Player target, int dir) {
			Vector2 goal = target != null ? target.Center - new Vector2(0f, FlyHover) : NPC.Center + new Vector2(NPC.direction * 64f, -16f);
			Vector2 to = goal - NPC.Center;
			Vector2 want = to.LengthSquared() > 64f ? to.SafeNormalize(Vector2.Zero) * FlySpeed : Vector2.Zero;
			Vector2 step = want - NPC.velocity;
			if (step.LengthSquared() > FlyAccel * FlyAccel) {
				step = step.SafeNormalize(Vector2.Zero) * FlyAccel;
			}
			NPC.velocity += step;
			FaceMotion(dir);
			if (!Main.dedServ) {
				WingEffects();
			}
			if (!IsAuthority) {
				return;
			}
			bool over = target != null && Math.Abs(target.Center.X - NPC.Center.X) < DropRangeX && NPC.Bottom.Y < target.Top.Y;
			if (target == null || Timer >= FlyMaxTicks || (over && Timer > 30f)) {
				ChangeState((int)Phase.Land);
			}
		}

		/// <summary>Clients: the telegraph's chirps and the fore legs' scraping, keyed to the timer.</summary>
		private void BraceEffects() {
			int face = NPC.direction == 0 ? -1 : NPC.direction;
			if (Timer == 1f || Timer == 18f) {
				SoundEngine.PlaySound(Chirp, NPC.Center);
			}
			if (Timer % 10f == 5f) {
				SafeSpawn.TryNewDust(NPC.Bottom + new Vector2(face * 18f - 6f, -6f), 12, 4, DustID.Stone, out _, -face * 1.5f, -1f);
			}
		}

		/// <summary>Clients: the wings' buzz.</summary>
		private void WingEffects() {
			if (Timer % (FlapTicks * 4f) == 1f) {
				SoundEngine.PlaySound(Buzz, NPC.Center);
			}
		}

		/// <summary>Clients: the horn cracks into the wall.</summary>
		private void BonkEffects(int dir) {
			Vector2 horn = NPC.Bottom + new Vector2(-R.HornTipX * dir, R.HornTipY * 0.5f);
			SoundEngine.PlaySound(Bonk, horn);
			for (int i = 0; i < 6; i++) {
				SafeSpawn.TryNewDust(horn - new Vector2(6f), 12, 12, DustID.Stone, out _, -dir * 1.5f, -1.5f);
			}
		}

		/// <summary>The charge's ram tosses the player up (the thrown player's own client applies it next tick, after vanilla's
		/// knockback: decompiled <c>Player.Hurt</c> runs the NPC's <c>OnHitPlayer</c> through <c>PlayerLoader.OnHurt</c> before
		/// it sets the knockback velocity).</summary>
		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			OnBeetleHit(target);
			if (!Ramming) {
				return;
			}
			if (target.whoAmI == Main.myPlayer) {
				target.GetModPlayer<RhinoTossPlayer>().Toss(Toss);
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(Flick, target.Center);
			}
		}

		/// <summary>Heavy hits: vanilla applies the knockback on the hit player's client (decompiled <c>Player.Hurt</c>); a Cobalt
		/// Shield's <c>noKnockback</c> still cancels it.</summary>
		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			if (Ramming) {
				modifiers.HitDirectionOverride = ChargeDir >= 0f ? 1 : -1;      // thrown the way it runs
				modifiers.Knockback *= RamPush;
			}
			else {
				modifiers.Knockback *= TouchPush;
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Brace:
					return Timer < 8f ? R.Brace : R.Brace + 1 + (int)(Timer / 8f) % 2;
				case Phase.Charge:
					NPC.frameCounter += Math.Abs(NPC.velocity.X);
					if (NPC.frameCounter >= ChargeAnimDistance * R.ChargeFrames) {
						NPC.frameCounter -= ChargeAnimDistance * R.ChargeFrames;
					}
					return R.Charge + (int)(NPC.frameCounter / ChargeAnimDistance) % R.ChargeFrames;
				case Phase.Toss:
					return R.Toss + Math.Min(R.TossFrames - 1, (int)(Timer / (TossTicks / 3f)));
				case Phase.Skid:
					return R.Skid;
				case Phase.Dazed:
					return R.Dazed + (int)(Timer / 6f) % R.DazedFrames;
				case Phase.TakeOff:
					return R.TakeOff + Math.Min(R.TakeOffFrames - 1, (int)(Timer / (TakeOffTicks / 2f)));
				case Phase.Fly:
					return R.Fly + (int)(Timer / FlapTicks) % R.FlyFrames;
				case Phase.Land:
					return Grounded ? R.TakeOff : R.TakeOff + 1;                 // the wings fold as it drops
			}
			if (Math.Abs(NPC.velocity.X) > 0.15f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= WalkAnimDistance * R.WalkFrames) {
					NPC.frameCounter -= WalkAnimDistance * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / WalkAnimDistance) % R.WalkFrames;
			}
			return R.Walk;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 16;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? BloodDust : DustID.Dirt, out _);
			}
			if (NPC.life <= 0) {
				foreach (string name in Gores) {
					if (Mod.TryFind(name, out ModGore gore)) {
						SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.position + new Vector2(Main.rand.Next(NPC.width), Main.rand.Next(NPC.height)),
							NPC.velocity * 0.5f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
					}
				}
			}
		}
	}

	/// <summary>
	/// The Rhino Beetle's toss on the thrown player: an upward speed applied on that player's own client at its next movement
	/// update (after vanilla's knockback has set the hurt velocity), so the player is flung up by the horn; gear that cancels
	/// knockback (the Cobalt Shield's <c>noKnockback</c>) cancels the toss too. The player's own client moves its player and
	/// syncs the result (D2). D1: one float.
	/// </summary>
	public sealed class RhinoTossPlayer : ModPlayer
	{
		private float pending;

		/// <summary>Queues a toss of <paramref name="speed"/> px/tick upward (the strongest queued one wins).</summary>
		public void Toss(float speed) {
			if (speed > pending && float.IsFinite(speed)) {
				pending = speed;
			}
		}

		public override void PreUpdateMovement() {
			if (pending <= 0f) {
				return;
			}
			if (Player.whoAmI == Main.myPlayer && !Player.dead && Player.mount?.Active != true && !Player.noKnockback) {
				Player.velocity.Y = Math.Min(Player.velocity.Y, -pending);
			}
			pending = 0f;
		}

		public override void OnRespawn() {
			pending = 0f;
		}
	}
}
