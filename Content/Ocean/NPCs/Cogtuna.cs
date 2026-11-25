using System;
using Cogpunk.Content.Junkyard;
using Cogpunk.Content.Ocean.Items;
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
using R = Cogpunk.Content.Ocean.NPCs.CogtunaRigData;

namespace Cogpunk.Content.Ocean.NPCs
{
	/// <summary>
	/// Cogtuna (named Cogshark until 2026-11-05, when the user renamed it; user-set 2026-11-04: "a new enemy for the default ocean, a steampunk shark with high armor and damage that
	/// only spawns in the water; 10% to drop the Shark Eye"): a riveted iron shark with a brass belly. In water it cruises
	/// back and forth until a player is in the water within <see cref="DetectRange"/> and in sight, then stalks them, and
	/// every <see cref="LungeCooldown"/> ticks, closer than <see cref="LungeRange"/>, it pulls back and gapes (the
	/// telegraph, <see cref="WindupTicks"/> ticks, its throat's furnace glowing), then lunges along the locked line at
	/// <see cref="LungeSpeed"/> for <see cref="LungeTicks"/> ticks with its jaws snapping, and coasts to a stop. It never
	/// leaves the water on its own: it stays under the surface (a player out of the water is only stalked from below); thrown
	/// out, it flops and falls until it is wet again.
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Shark, decompiled 1.4.4 NPC 65: 300 life, 2 defense,
	/// 40 contact in Classic = 600 / 2 / 80 in Expert, value 400): <see cref="Life"/> life, <see cref="Defense"/> defense (the
	/// user's "high armor"), <see cref="ContactDamage"/> contact (the user's "high damage"). Spawns in the water of the
	/// vanilla ocean only (the Junkyard replaces the left one; <see cref="SpawnWeight"/>). Drops the Shark's coins, 1 in
	/// <see cref="SharkEyeOdds"/> the <see cref="SharkEye"/> (user-set 10%), a Shark Fin 1 in <see cref="FinOdds"/> and 1-3
	/// Rusted Cogs.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the lunge's heading (radians, locked by the server
	/// with the state change), <c>ai[3]</c> the lunge cooldown (every side counts it); the server targets and decides; every
	/// side steers from the synced state and the target's synced position. D0: the surface test goes through
	/// <see cref="TileSafety"/>; no spawns. D1: no allocation; bubbles and sounds on clients, throttled.</para>
	/// </summary>
	[LegacyName("Cogshark")]                           // renamed 2026-11-05 (user): old worlds keep its banner and kills
	public class Cogtuna : GridWalkerNPC
	{
		private enum Phase { Cruise, Stalk, Windup, Lunge, Recover, Beached }

		public const int Life = 400, ContactDamage = 90, Defense = 24;     // Expert
		public const int Width = 88, Height = 30;
		public const float KnockbackResist = 0.4f;
		public const float CruiseSpeed = 1.6f, StalkSpeed = 4.2f, Accel = 0.12f;
		public const float DetectRange = 40f * 16f;
		public const float LungeRange = 14f * 16f;
		public const int WindupTicks = 30;                                  // D3: >= 30 at T0-T4
		public const int LungeTicks = 26;
		public const float LungeSpeed = 11f;
		public const float PullBack = 1.2f;                                 // px/tick it backs off while gaping
		public const int RecoverTicks = 40;
		public const int LungeCooldown = 90;
		public const int CruiseTurnTicks = 300;
		public const float Gravity = 0.3f, MaxFall = 10f;
		public const float FlopSpeed = 4.5f;
		public const int FlopTicks = 40;
		public const float SwimAnimDistance = 6f;                           // px of travel per swim frame
		public const float TiltSpeed = 1.6f;                                // |vy| past this shows a tilted frame
		public const float SpawnWeight = 0.1f;
		public const int SharkEyeOdds = 10;                                 // 10% (user-set)
		public const int FinOdds = 2;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "Cogtuna_GoreHead", "Cogtuna_GoreFin", "Cogtuna_GoreTail" };

		private Phase CurrentPhase => (Phase)State;
		private ref float Heading => ref NPC.ai[2];
		private ref float Cooldown => ref NPC.ai[3];
		private float swimCounter;

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Ocean;

		/// <summary>A fish has no feet: the cells' origin sits <see cref="R.CenterY"/> under its centre.</summary>
		protected override Vector2 DrawAnchor => NPC.Center + new Vector2(0f, R.CenterY);

		/// <summary>The furnace in its throat glows while it gapes; the eye always.</summary>
		protected override float GlowStrength => 1f;

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
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.noGravity = true;                           // it swims; out of water its own gravity applies
			NPC.waterMovementSpeed = 1f;                    // its speeds are its real speeds (vanilla halves wet NPCs: decompiled Collision_MoveWhileWet)
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 400f;                               // the Shark's (decompiled NPC.SetDefaults, type 65)
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			if (!spawnInfo.Water || !spawnInfo.Player.ZoneBeach || spawnInfo.PlayerInTown
				|| JunkyardSystem.ContainsTile(new Point(spawnInfo.SpawnTileX, spawnInfo.SpawnTileY))) {
				return 0f;
			}
			return SpawnWeight;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<SharkEye>(), SharkEyeOdds));
			npcLoot.Add(ItemDropRule.Common(ItemID.SharkFin, FinOdds));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedCog>(), 1, 1, 3));
		}

		protected override void UpdateState() {
			if (Cooldown > 0f) {
				Cooldown--;
			}
			Retarget();
			bool wet = NPC.wet;
			if (!wet) {
				Beach();
				return;
			}
			if (CurrentPhase == Phase.Beached && IsAuthority) {
				ChangeState((int)Phase.Cruise);             // back in the water
			}
			Player target = Target;
			bool hunting = target != null && target.wet && !target.dead
				&& Vector2.DistanceSquared(target.Center, NPC.Center) < DetectRange * DetectRange;
			switch (CurrentPhase) {
				case Phase.Stalk:
					DoStalk(target, hunting);
					break;
				case Phase.Windup:
					DoWindup(target);
					break;
				case Phase.Lunge:
					DoLunge();
					break;
				case Phase.Recover:
					NPC.velocity *= 0.95f;
					if (IsAuthority && Timer >= RecoverTicks) {
						Cooldown = LungeCooldown;
						ChangeState((int)(hunting ? Phase.Stalk : Phase.Cruise));
					}
					break;
				default:
					DoCruise(target, hunting);
					break;
			}
			StayUnder();
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Patrols back and forth at <see cref="CruiseSpeed"/>, turning at walls or every
		/// <see cref="CruiseTurnTicks"/>; starts stalking a player in the water and in sight.</summary>
		private void DoCruise(Player target, bool hunting) {
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			if (IsAuthority && (NPC.collideX || Timer >= CruiseTurnTicks)) {
				NPC.direction = -dir;
				ChangeState((int)Phase.Cruise);
				dir = -dir;
			}
			Steer(new Vector2(dir * CruiseSpeed, (float)Math.Sin(Timer * 0.04f) * 0.4f), Accel * 0.5f);
			NPC.spriteDirection = NPC.direction = dir;
			if (IsAuthority && hunting && Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height)) {
				ChangeState((int)Phase.Stalk);
			}
		}

		/// <summary>Swims at the target; the server starts the lunge when it is close, in line and the cooldown is over.</summary>
		private void DoStalk(Player target, bool hunting) {
			if (!hunting) {
				if (IsAuthority) {
					ChangeState((int)Phase.Cruise);
				}
				return;
			}
			Vector2 to = target.Center - NPC.Center;
			Steer(to.SafeNormalize(Vector2.UnitX * NPC.direction) * StalkSpeed, Accel);
			FaceMotion(to.X >= 0f ? 1 : -1);
			if (IsAuthority && Cooldown <= 0f && to.LengthSquared() < LungeRange * LungeRange
				&& Collision.CanHitLine(NPC.position, NPC.width, NPC.height, target.position, target.width, target.height)) {
				ChangeState((int)Phase.Windup);
				Heading = to.ToRotation();                  // locked as the telegraph starts (synced with the change)
			}
		}

		/// <summary>The telegraph: it backs off along its heading and gapes; the heading follows the target until the last
		/// third, then the server keeps it.</summary>
		private void DoWindup(Player target) {
			Vector2 heading = Heading.ToRotationVector2();
			NPC.velocity = Vector2.Lerp(NPC.velocity, -heading * PullBack, 0.2f);
			NPC.direction = NPC.spriteDirection = heading.X >= 0f ? 1 : -1;
			if (Timer == 1f && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item13 with { Pitch = -0.6f, Volume = 0.7f, MaxInstances = 3 }, NPC.Center);   // a gurgle of steam
			}
			if (IsAuthority && target != null && Timer < WindupTicks * 2 / 3) {
				float aim = (target.Center - NPC.Center).ToRotation();
				if (Math.Abs(MathHelper.WrapAngle(aim - Heading)) > 0.05f) {
					Heading = aim;
					NPC.netUpdate = true;
				}
			}
			if (IsAuthority && Timer >= WindupTicks) {
				ChangeState((int)Phase.Lunge);
			}
		}

		private void DoLunge() {
			Vector2 heading = Heading.ToRotationVector2();
			NPC.velocity = heading * LungeSpeed;
			NPC.direction = NPC.spriteDirection = heading.X >= 0f ? 1 : -1;
			if (Timer == 1f && !Main.dedServ) {
				SoundEngine.PlaySound(SoundID.NPCHit4 with { Pitch = -0.4f, Volume = 0.8f, MaxInstances = 3 }, NPC.Center);   // the jaws
				SoundEngine.PlaySound(SoundID.Splash with { Pitch = -0.2f, Volume = 0.6f, MaxInstances = 3 }, NPC.Center);
			}
			if (IsAuthority && (Timer >= LungeTicks || (Timer > 4f && (NPC.collideX || NPC.collideY)))) {
				ChangeState((int)Phase.Recover);
			}
		}

		/// <summary>Out of the water: gravity, a flop every <see cref="FlopTicks"/> ticks on the ground (the server rolls the
		/// side and syncs it), until it is wet again.</summary>
		private void Beach() {
			if (IsAuthority && CurrentPhase != Phase.Beached) {
				ChangeState((int)Phase.Beached);
			}
			NPC.velocity.Y = Math.Min(NPC.velocity.Y + Gravity, MaxFall);
			bool grounded = NPC.collideY && NPC.oldVelocity.Y >= 0f;   // last tick's fall was stopped (decompiled UpdateCollision)
			if (grounded) {
				NPC.velocity.X *= 0.85f;                    // on the ground: friction
			}
			if (IsAuthority && grounded && Timer >= FlopTicks) {
				int side = Main.rand.NextBool() ? 1 : -1;
				Player target = Target;
				if (target != null && Main.rand.NextBool(3)) {
					side = target.Center.X >= NPC.Center.X ? 1 : -1;
				}
				NPC.velocity = new Vector2(side * 2f, -FlopSpeed);
				NPC.direction = NPC.spriteDirection = side;
				ChangeState((int)Phase.Beached);
			}
		}

		/// <summary>Accelerates the velocity towards <paramref name="want"/>.</summary>
		private void Steer(Vector2 want, float accel) {
			NPC.velocity = Vector2.Lerp(NPC.velocity, want, accel);
		}

		/// <summary>Never breaks the surface: with open air at the top of its hitbox it can't rise (D0: the tile through
		/// <see cref="TileSafety"/>).</summary>
		private void StayUnder() {
			int x = (int)(NPC.Center.X / 16f);
			int y = (int)((NPC.position.Y - 2f) / 16f);
			bool water = TileSafety.TryGetTile(x, y, out Tile tile) && tile.LiquidAmount > 0 && tile.LiquidType == LiquidID.Water;
			if (!water && NPC.velocity.Y < 0.5f) {
				NPC.velocity.Y = 0.5f;
			}
		}

		private void Effects() {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			Vector2 origin = DrawAnchor;
			if (Main.rand.NextBool(CurrentPhase == Phase.Lunge ? 2 : 14)
				&& SafeSpawn.TryNewDust(origin + new Vector2(R.VentX * -dir, R.VentY) - new Vector2(3f), 6, 6, DustID.BreatheBubble, out Dust vent)) {
				vent.velocity = new Vector2(Main.rand.NextFloat(-0.3f, 0.3f), -1.2f);
				vent.noGravity = true;
			}
			if (CurrentPhase == Phase.Windup && Main.rand.NextBool(3)
				&& SafeSpawn.TryNewDust(origin + new Vector2(R.MouthX * -dir, R.MouthY) - new Vector2(4f), 8, 8, DustID.BreatheBubble, out Dust mouth)) {
				mouth.velocity = new Vector2(dir * 0.8f, -0.6f);
				mouth.noGravity = true;
			}
			if (CurrentPhase == Phase.Windup || CurrentPhase == Phase.Lunge) {
				Lighting.AddLight(origin + new Vector2(R.MouthX * -dir * 0.7f, R.MouthY), 0.5f, 0.22f, 0.05f);
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Windup:
					return R.Lunge;
				case Phase.Lunge:
					return R.Lunge + 1 + (int)(Timer / 4f) % 2;
				case Phase.Beached:
					return R.Beached + (NPC.velocity.Y < 0f ? 1 : 0);
			}
			float speed = NPC.velocity.Length();
			swimCounter += Math.Max(0.5f, speed);
			if (swimCounter >= SwimAnimDistance * R.SwimFrames) {
				swimCounter -= SwimAnimDistance * R.SwimFrames;
			}
			int beat = (int)(swimCounter / SwimAnimDistance);
			// the art is turned, never the sprite (D4): nose up when rising, down when diving (vy and the facing both count)
			if (NPC.velocity.Y < -TiltSpeed) {
				return R.Rise + beat % R.RiseFrames;
			}
			if (NPC.velocity.Y > TiltSpeed) {
				return R.Dive + beat % R.DiveFrames;
			}
			return R.Swim + beat % R.SwimFrames;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 16;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Gold : DustID.Iron, out _);
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
