using System;
using Cogpunk.Content.Rain.Projectiles;
using Cogpunk.Content.Scrap.Items;
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
using R = Cogpunk.Content.Rain.NPCs.SplasherRigData;

namespace Cogpunk.Content.Rain.NPCs
{
	/// <summary>
	/// Splasher (user-set 2026-11-03: "a new enemy that spawns in the rain: a robot with an umbrella on the head that shoots
	/// with a water gun, mid range"): a squat iron walker with an umbrella bolted to its head and a pump-action water gun.
	/// It walks towards its target until it is within <see cref="StandRange"/> (it keeps its distance: a mid-range shooter),
	/// and every <see cref="ShotCooldown"/> ticks, with the target in sight within <see cref="ShootRange"/>, it raises the gun
	/// and pumps it (the telegraph, <see cref="AimTicks"/> ticks, a gurgle), then fires <see cref="BurstShots"/> globs of
	/// water (<see cref="SplasherWater"/>), one every <see cref="BurstInterval"/> ticks, lobbed to land on the target.
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Raincoat Zombie, the rain's walker, decompiled 1.4.4
	/// NPC 223: 50 life, 8 defense, 16 contact in Classic = 100 / 8 / 32 in Expert): <see cref="Life"/> life,
	/// <see cref="Defense"/> defense, <see cref="ContactDamage"/> contact (it fights at range), water
	/// <see cref="WaterDamage"/>. Spawns on the surface in the rain, day and night (<see cref="SpawnWeight"/>), not in the
	/// snow (it snows there) or in towns. Drops the Raincoat Zombie's coins, 1-2 Rusted Cogs and, 1 in
	/// <see cref="UmbrellaOdds"/>, vanilla's Umbrella (the one it wore).</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the shot cooldown (every side counts it); the server
	/// targets, decides and fires (hostile projectiles through <see cref="SafeSpawn"/>, damage through
	/// <see cref="ExpertStats.HostileProjectile"/>). D1: no allocation; sounds and dust on clients.</para>
	/// </summary>
	public class Splasher : GridWalkerNPC
	{
		private enum Phase { Walk, Aim, Shoot }

		public const int Life = 120, ContactDamage = 20, Defense = 10;   // Expert
		public const int WaterDamage = 24;                               // Expert, per glob
		public const int Width = 24, Height = 44;
		public const float KnockbackResist = 0.45f;                      // the Raincoat Zombie's
		public const float WalkSpeed = 1.2f, WalkAccel = 0.08f, JumpSpeed = 6.5f;
		public const float StandRange = 12f * 16f, ShootRange = 22f * 16f;
		public const int ShotCooldown = 120;
		public const int AimTicks = 30;
		public const int BurstShots = 4, BurstInterval = 7;
		public const int ShootTicks = BurstShots * BurstInterval + 12;
		public const float ShotSpread = 0.06f;                           // radians each way
		public const float WalkAnimDistance = 3f;                        // px of travel per walk frame (WalkStep)
		public const float SpawnWeight = 0.12f;
		public const int UmbrellaOdds = 25;

		private static Asset<Texture2D> far, near, glow;
		private static readonly string[] GoreNames = { "Splasher_GoreUmbrella", "Splasher_GoreHead", "Splasher_GoreGun" };

		private Phase CurrentPhase => (Phase)State;
		private ref float Cooldown => ref NPC.ai[2];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;
		// the surface, with vanilla's rain overlay on it (as its rain enemies show)
		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Surface,
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Events.Rain,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

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
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 70f;                                // the Raincoat Zombie's (decompiled NPC.SetDefaults, type 223)
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player player = spawnInfo.Player;
			return Main.raining && player.ZoneOverworldHeight && !player.ZoneSnow && !spawnInfo.PlayerInTown && !spawnInfo.Water
				? SpawnWeight : 0f;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedCog>(), 1, 1, 2));
			npcLoot.Add(ItemDropRule.Common(ItemID.Umbrella, UmbrellaOdds));
		}

		protected override void UpdateState() {
			if (Cooldown > 0f) {
				Cooldown--;
			}
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.Aim:
					Run(0, 0f, WalkAccel * 2f, JumpSpeed);
					NPC.direction = NPC.spriteDirection = dir;
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(SoundID.Item85 with { Pitch = -0.3f, Volume = 0.6f, MaxInstances = 3 }, NPC.Center);   // the pump's gurgle
					}
					if (IsAuthority && Timer >= AimTicks) {
						ChangeState((int)Phase.Shoot);
					}
					break;
				case Phase.Shoot:
					Run(0, 0f, WalkAccel * 2f, JumpSpeed);
					NPC.direction = NPC.spriteDirection = dir;
					if ((Timer - 1f) % BurstInterval == 0f && Timer <= BurstShots * BurstInterval) {
						Fire(target);
					}
					if (IsAuthority && Timer >= ShootTicks) {
						Cooldown = ShotCooldown;
						ChangeState((int)Phase.Walk);
					}
					break;
				default:
					float adx = Math.Abs(dx);
					bool close = target != null && adx < StandRange;
					Run(target != null && !close ? dir : 0, WalkSpeed, WalkAccel, JumpSpeed);
					FaceMotion(dir);
					if (close) {
						NPC.direction = NPC.spriteDirection = dir;
					}
					if (IsAuthority && target != null && Cooldown <= 0f && Grounded && adx < ShootRange && Math.Abs(target.Center.Y - NPC.Center.Y) < 12f * 16f
						&& Collision.CanHitLine(Muzzle(dir), 1, 1, target.position, target.width, target.height)) {
						ChangeState((int)Phase.Aim);
					}
					break;
			}
		}

		/// <summary>The nozzle in world space (rig data, mirrored when it faces right).</summary>
		private Vector2 Muzzle(int dir) => NPC.Bottom + new Vector2(R.MuzzleX * -dir, R.MuzzleY);

		/// <summary>One glob of the burst: sound and spray on every side, the projectile from the server, lobbed to land on
		/// the target (<see cref="SplasherWater.AimAt"/>), a little spread so a burst fans out.</summary>
		private void Fire(Player target) {
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			Vector2 from = Muzzle(dir);
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item13 with { Pitch = 0.2f, Volume = 0.55f, MaxInstances = 4 }, from);
				for (int i = 0; i < 3; i++) {
					SafeSpawn.TryNewDust(from - new Vector2(4f), 8, 8, DustID.Water, out _, dir * 2f, -0.5f);
				}
			}
			if (!IsAuthority || target == null) {
				return;
			}
			Vector2 velocity = SplasherWater.AimAt(from, target.Center).RotatedBy(Main.rand.NextFloat(-ShotSpread, ShotSpread));
			int damage = ExpertStats.HostileProjectile(NPC, WaterDamage);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, velocity, ModContent.ProjectileType<SplasherWater>(), damage, 1f, out _);
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Aim:
					return R.Aim + (int)(Timer / 8f) % 2;
				case Phase.Shoot:
					int sinceShot = (int)(Timer - 1f) % BurstInterval;
					return Timer <= BurstShots * BurstInterval + 1 && sinceShot < 3 ? R.Shoot : R.Shoot + 1;
			}
			if (!Grounded) {
				return R.Walk + 1;
			}
			if (Math.Abs(NPC.velocity.X) > 0.15f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= WalkAnimDistance * R.WalkFrames) {
					NPC.frameCounter -= WalkAnimDistance * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / WalkAnimDistance) % R.WalkFrames;
			}
			return R.Idle + (int)(Timer / 24f) % 2;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 12;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 2 == 0 ? DustID.Water : DustID.Iron, out _);
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
