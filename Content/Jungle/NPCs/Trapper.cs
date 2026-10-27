using System;
using Cogpunk.Content.Jungle.Projectiles;
using Cogpunk.Content.Mechanist.Weapons;
using Cogpunk.Content.Scrap.Items;
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

namespace Cogpunk.Content.Jungle.NPCs
{
	/// <summary>
	/// Trapper (user-set 2026-10-27): a jungle hunter, half goblin and half cyborg (a brass arm, a lens eye, a piston leg),
	/// with a sack of spike balls. It keeps its distance: closer than <see cref="FleeRange"/> it turns and runs
	/// (<see cref="Phase.Flee"/>) until it is <see cref="SafeRange"/> away; within <see cref="ThrowRange"/> and in sight it
	/// stops, winds up for <see cref="ThrowReleaseTick"/> ticks (the telegraph: arm back, a rattle) and lobs a
	/// <see cref="TrapperSpikeBall"/> that bounces and then lies on the ground for a while, like the Spiky Balls goblins
	/// drop. Out of range it walks after its target.
	/// <para>Stats (user-set 2026-10-27, Expert values like every Cogpunk number, see <see cref="ExpertStats"/>;
	/// docs/balance/npcs.csv; anchor Man Eater): 250 life, 35 contact damage, spike balls 20. Drops 1-10
	/// Spiky Balls, 1-2 Rusted Metal and, 5% of the time, the Mechanist's <see cref="TrapperChain"/>. Spawns in the jungle
	/// (surface and underground), rarely.</para>
	/// <para>D2: <see cref="StateMachineNPC"/> state/timer in <c>ai[0]</c>/<c>ai[1]</c>, <c>ai[2]</c> the throw cooldown
	/// (every side counts it), <c>ai[3]</c> the flee direction. The server picks the target, the state and throws; walking
	/// runs on every side from the synced state (vanilla collision). D1: no allocation; at most <see cref="MaxBallsEach"/>
	/// of its balls in the world (one pass over the projectiles per throw, every 2 s at most). Effects client-only.</para>
	/// </summary>
	public class Trapper : StateMachineNPC
	{
		public enum Phase { Stalk, Flee, Throw }

		public const float FleeRange = 9f * 16f;
		public const float SafeRange = 16f * 16f;
		public const float ThrowRange = 32f * 16f;
		public const float WalkSpeed = 1.4f;
		public const float FleeSpeed = 2.9f;               // a walking player (3 px/tick) only just gains on it
		public const float Accel = 0.12f;
		public const float JumpSpeed = 7.5f;
		public const int ThrowReleaseTick = 30;            // telegraph >= 30 ticks (D3)
		public const int ThrowTicks = 48;
		public const int ThrowCooldown = 120;
		public const int MaxFleeTicks = 240;               // cornered or chased for 4 s: turn and throw anyway
		public const int MaxBallsEach = 6;
		public const int RetargetInterval = 30;
		public const int FrameCount = 12;
		public const int IdleFrame = 0, RunFrame = 2, RunFrames = 6, WindFrame = 8, ReleaseFrame = 10, FollowFrame = 11;
		public const int Life = 250, ContactDamage = 35, Defense = 10;   // Expert (user-set; defense ours)
		/// <summary>Spike ball damage in Expert (Classic half, Master 1.5x: <see cref="ExpertStats.HostileProjectile"/>).</summary>
		public const int BallDamage = 20;
		public const float TrapperChainChance = 0.05f;

		private Phase CurrentPhase => (Phase)State;
		private ref float Cooldown => ref NPC.ai[2];
		private ref float FleeDirection => ref NPC.ai[3];

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = FrameCount;
			CogpunkSets.Mechanical[Type] = true;          // half machine: the Screwdriver bonus applies
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Velocity = 1f });
		}

		public override void SetDefaults() {
			NPC.width = 20;
			NPC.height = 40;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0.35f;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath40;
			NPC.value = Item.buyPrice(silver: 5);
			NPC.aiStyle = -1;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Jungle,
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.UndergroundJungle,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player p = spawnInfo.Player;
			if (!p.ZoneJungle || p.ZoneDungeon || p.ZoneLihzhardTemple || spawnInfo.Water || spawnInfo.Invasion || spawnInfo.PlayerInTown
				|| spawnInfo.PlayerSafe || p.ZoneTowerSolar || p.ZoneTowerVortex || p.ZoneTowerNebula || p.ZoneTowerStardust) {
				return 0f;
			}
			return p.ZoneOverworldHeight ? 0.06f : 0.04f;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ItemID.SpikyBall, 1, 1, 10));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedMetal>(), 1, 1, 2));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<TrapperChain>(), 20));   // 1 in 20 = 5%
		}

		protected override void UpdateState() {
			if (Cooldown > 0f) {
				Cooldown--;
			}
			if (IsAuthority && (Timer % RetargetInterval == 1f || !NPC.HasValidTarget)) {
				int old = NPC.target;
				NPC.TargetClosest(false);
				if (NPC.target != old) {
					NPC.netUpdate = true;
				}
			}
			Player target = NPC.HasValidTarget ? Main.player[NPC.target] : null;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			float distance = target != null ? Vector2.Distance(target.Center, NPC.Center) : float.MaxValue;
			switch (CurrentPhase) {
				case Phase.Flee:
					Walk((int)FleeDirection, FleeSpeed);
					if (IsAuthority && (distance > SafeRange || Timer >= MaxFleeTicks)) {
						ChangeState(Cooldown <= 0f && CanThrowAt(target) ? (int)Phase.Throw : (int)Phase.Stalk);
					}
					break;
				case Phase.Throw:
					NPC.velocity.X *= 0.8f;
					if (target != null) {
						Face(dx);
					}
					if (Timer == ThrowReleaseTick && IsAuthority && target != null) {
						Throw(target);
					}
					if (Timer >= ThrowTicks && IsAuthority) {
						Cooldown = ThrowCooldown;
						ChangeState((int)Phase.Stalk);
					}
					break;
				default:
					if (target == null) {
						Walk(NPC.direction == 0 ? -1 : NPC.direction, WalkSpeed * 0.5f);   // wander
						break;
					}
					if (IsAuthority && distance < FleeRange) {
						FleeDirection = dx >= 0f ? -1f : 1f;
						ChangeState((int)Phase.Flee);
						break;
					}
					if (IsAuthority && distance < ThrowRange && Cooldown <= 0f && CanThrowAt(target)) {
						ChangeState((int)Phase.Throw);
						break;
					}
					Walk(distance > ThrowRange * 0.75f ? Math.Sign(dx) : 0, WalkSpeed);
					if (Math.Abs(NPC.velocity.X) < 0.1f) {
						Face(dx);
					}
					break;
			}
			if (Math.Abs(NPC.velocity.X) > 0.1f && CurrentPhase != Phase.Throw) {
				NPC.direction = NPC.spriteDirection = NPC.velocity.X > 0f ? 1 : -1;
			}
		}

		private void Face(float dx) {
			int dir = dx >= 0f ? 1 : -1;
			NPC.direction = NPC.spriteDirection = dir;
		}

		/// <summary>Accelerates towards <paramref name="dir"/> x <paramref name="speed"/> (0 = stop), steps up single tiles and
		/// jumps when a wall blocks it (vanilla collision; same inputs on every side).</summary>
		private void Walk(int dir, float speed) {
			float want = dir * speed;
			if (NPC.velocity.X < want) {
				NPC.velocity.X = Math.Min(want, NPC.velocity.X + Accel);
			}
			else if (NPC.velocity.X > want) {
				NPC.velocity.X = Math.Max(want, NPC.velocity.X - Accel);
			}
			Collision.StepUp(ref NPC.position, ref NPC.velocity, NPC.width, NPC.height, ref NPC.stepSpeed, ref NPC.gfxOffY);
			if (dir != 0 && NPC.collideX && NPC.velocity.Y == 0f) {
				NPC.velocity.Y = -JumpSpeed;                // a wall: hop it
				NPC.netUpdate = IsAuthority;
			}
		}

		private bool CanThrowAt(Player target) {
			return target != null && Collision.CanHitLine(NPC.Top, 1, 1, target.position, target.width, target.height);
		}

		/// <summary>Server: a lob that lands on the target (the ball's gravity), unless this Trapper already has
		/// <see cref="MaxBallsEach"/> balls out.</summary>
		private void Throw(Player target) {
			int mine = 0;
			int type = ModContent.ProjectileType<TrapperSpikeBall>();
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type == type && (int)p.ai[1] == NPC.whoAmI) {
					mine++;
				}
			}
			if (mine >= MaxBallsEach) {
				return;
			}
			Vector2 hand = NPC.Top + new Vector2(NPC.direction * 6f, 8f);
			Vector2 velocity = TrapperSpikeBall.Lob(hand, target.Center + new Vector2(Main.rand.NextFloat(-24f, 24f), 0f));
			int damage = ExpertStats.HostileProjectile(NPC, BallDamage);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), hand, velocity, type, damage, 0f, out _, ai1: NPC.whoAmI);
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 16;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Iron : DustID.GreenBlood, out _);
			}
		}

		public override void FindFrame(int frameHeight) {
			int frame;
			int t = (int)Timer;
			if (CurrentPhase == Phase.Throw) {
				frame = t < 12 ? WindFrame : (t < ThrowReleaseTick ? WindFrame + 1 : (t < ThrowReleaseTick + 6 ? ReleaseFrame : FollowFrame));
				if (!Main.dedServ && t == 12) {
					SoundEngine.PlaySound(SoundID.Item7 with { Pitch = -0.4f, Volume = 0.6f }, NPC.Center);   // the telegraph: a rattle
				}
				if (!Main.dedServ && t == ThrowReleaseTick) {
					SoundEngine.PlaySound(SoundID.Item1 with { Pitch = -0.2f }, NPC.Center);
				}
			}
			else if (NPC.velocity.Y != 0f) {
				frame = RunFrame + 1;                       // mid-stride in the air
			}
			else if (Math.Abs(NPC.velocity.X) > 0.2f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= 6.0 * RunFrames) {
					NPC.frameCounter -= 6.0 * RunFrames;
				}
				frame = RunFrame + (int)(NPC.frameCounter / 6.0) % RunFrames;
			}
			else {
				frame = IdleFrame + (t / 20) % 2;
			}
			NPC.frame.Y = frame * frameHeight;
		}
	}
}
