using System;
using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Junkyard.Projectiles;
using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.NPCs
{
	/// <summary>
	/// Living Tar: a slime of the Junkyard's steaming tar, commonest on the tar pool's side of the yard. It hops at its
	/// target exactly like a vanilla slime (<c>aiStyle = 1</c>, <c>AIType</c> Blue Slime: same jump timing) and every time
	/// it lands from a jump it flings a glob of tar (<see cref="TarGlob"/>) in an arc at its target, if it is within
	/// <see cref="ShootRange"/>. Its touch and its globs barely hurt, but they coat the player in tar:
	/// <see cref="TarPlague"/> for <see cref="TarTicks"/> ticks.
	/// <para>Stats (user-set 2026-10-26, Expert values like every Cogpunk number, see <see cref="ExpertStats"/>;
	/// docs/balance/npcs.csv; anchor Lava Slime): 60 life, 2 defense, 5 contact damage, globs 4.
	/// Drops 1-5 Gel and 1-5 <see cref="TarDrop"/>.</para>
	/// <para>D2: vanilla's slime AI runs on every side from the synced <c>ai[]</c>; only the server (or singleplayer)
	/// notices the landing and throws the glob. The landing flag and the throw cooldown live in <c>localAI[2]</c> and
	/// <c>localAI[3]</c>, which the slime AI never touches for a Blue Slime.</para>
	/// </summary>
	public class LivingTar : CogpunkNPC
	{
		public const int TarTicks = 120;                 // 2 s of Tar Plague per hit (user-set)
		public const float ShootRange = 28f * 16f;       // "medium range"
		public const int ShootCooldown = 30;
		public const int Life = 60, ContactDamage = 5, Defense = 2;      // Expert (user-set)
		/// <summary>Glob damage in Expert (Classic half, Master 1.5x: <see cref="ExpertStats.HostileProjectile"/>).</summary>
		public const int GlobDamage = 4;

		private ref float WasAirborne => ref NPC.localAI[3];
		private ref float Cooldown => ref NPC.localAI[2];

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 2;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.OnFire] = true;   // already boiling
		}

		public override void SetDefaults() {
			NPC.width = 24;                                // vanilla slime size
			NPC.height = 18;
			NPC.aiStyle = NPCAIStyleID.Slime;
			AIType = NPCID.BlueSlime;
			AnimationType = NPCID.BlueSlime;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = 0.8f;
			NPC.HitSound = SoundID.NPCHit1;
			NPC.DeathSound = SoundID.NPCDeath1;
			NPC.value = 100f;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				ModContent.GetInstance<JunkyardBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) => JunkyardSpawnRules.SurfaceSpawnWeight(spawnInfo, JunkyardSpawnRules.TarSideWeight(spawnInfo));

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ItemID.Gel, 1, 1, 5));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<TarDrop>(), 1, 1, 5));
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			target.AddBuff(ModContent.BuffType<TarPlague>(), TarTicks);
		}

		// After vanilla's slime AI (aiStyle 1) has moved it this tick.
		public override void PostAI() {
			if (!Main.dedServ && Main.rand.NextBool(40)
				&& SafeSpawn.TryNewDust(NPC.position, NPC.width, 6, DustID.Smoke, out Dust wisp, 0f, -0.8f, 120, new Color(195, 200, 205), 0.8f)) {
				wisp.noGravity = true;                     // steam rising off the tar
			}
			bool airborne = NPC.velocity.Y != 0f;
			if (Cooldown > 0f) {
				Cooldown--;
			}
			if (WasAirborne == 1f && !airborne) {
				Landed();
			}
			WasAirborne = airborne ? 1f : 0f;
		}

		/// <summary>Server: a glob of tar lobbed at the target from the top of the slime, aimed to land on it.</summary>
		private void Landed() {
			if (!Main.dedServ) {
				SplatDust(4);
			}
			if (Main.netMode == NetmodeID.MultiplayerClient || Cooldown > 0f || !NPC.HasValidTarget) {
				return;
			}
			Player target = Main.player[NPC.target];
			if (Vector2.DistanceSquared(target.Center, NPC.Center) > ShootRange * ShootRange
				|| !Collision.CanHitLine(NPC.Top, 1, 1, target.position, target.width, target.height)) {
				return;
			}
			Cooldown = ShootCooldown;
			Vector2 from = NPC.Top + new Vector2(0f, 4f);
			Vector2 velocity = TarGlob.AimAt(from, target.Center);
			int damage = ExpertStats.HostileProjectile(NPC, GlobDamage);
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), from, velocity, ModContent.ProjectileType<TarGlob>(), damage, 0f, out _);
		}

		private void SplatDust(int count) {
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(0f, 4f), NPC.width, 4, ModContent.DustType<TarSplash>(), out Dust d,
					Main.rand.NextFloat(-1.5f, 1.5f), -Main.rand.NextFloat(0.5f, 2f))) {
					d.noGravity = false;
				}
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 4 : 18;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, ModContent.DustType<TarSplash>(), out Dust d, hit.HitDirection * 2f, -2f)) {
					d.velocity *= NPC.life > 0 ? 1f : 1.8f;
				}
			}
			if (NPC.life <= 0) {
				SoundEngine.PlaySound(SoundID.Item34 with { Pitch = 0.4f, Volume = 0.4f }, NPC.Center);   // a last hiss of steam
				for (int i = 0; i < 6; i++) {
					if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.Smoke, out Dust s, 0f, -1.5f, 100, new Color(195, 200, 205), 1.2f)) {
						s.noGravity = true;
					}
				}
			}
		}
	}
}
