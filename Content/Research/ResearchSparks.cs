using System;
using Cogpunk.Content.Scrap.Weapons;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// The 0.4.0 secret spark research chain (user-set 2026-11-27: "add a new secret node chain that reveals after the player
	/// kills something with a spark projectile: 1 - 'sparkling!' that increases chance for sparks to set the enemy on fire. 2 -
	/// 'better sparks' that increase spark lifetime/range (so it takes 1 more seconds to vanish). 3 - 'induced combustion' that
	/// makes so enemies burst sparks when killed (2-4 sparks arround it at random). Each node should cost a reseach point"):
	/// <list type="bullet">
	/// <item><see cref="IsSpark"/> covers vanilla's spark projectiles (<c>WandOfSparkingSpark</c>, <c>Spark</c>,
	/// <c>WandOfFrostingFrost</c>) and Cogpunk's <see cref="ScrappyWandBolt"/>.</item>
	/// <item><b>Better Sparks</b>: decompiled 1.4.4 <c>Projectile.AI</c> ignores <c>timeLeft</c> on vanilla sparks and kills them
	/// at <c>ai[0] &gt;= 60f</c> (invisible while <c>ai[0] &lt;= 3f</c>). Once <c>ai[0] &gt;= 4f</c>, holding <c>ai[0]</c> back 30
	/// ticks in straight flight and 30 ticks across the arc adds an exact +60 ticks (+1.0 s) of lifetime and extends forward
	/// reach without losing dust visibility.</item>
	/// <item><b>Induced Combustion</b>: marks its burst sparks with <see cref="InducedCombustionTag"/> in <c>ai[2]</c> (synced,
	/// unused by vanilla <c>WandOfSparkingSpark</c>) so a combustion spark kill never triggers another combustion burst (D0 rule 4:
	/// no infinite feedback loops).</item>
	/// </list>
	/// </summary>
	public static class ResearchSparks
	{
		public const float InducedCombustionTag = 77f;

		private static int scrappyBoltType = -1;

		public static bool IsSpark(int projType) {
			if (projType == ProjectileID.WandOfSparkingSpark || projType == ProjectileID.Spark
				|| projType == ProjectileID.WandOfFrostingFrost) {
				return true;
			}
			if (scrappyBoltType < 0 && ProjectileLoader.ProjectileCount > ProjectileID.Count) {
				scrappyBoltType = ModContent.ProjectileType<ScrappyWandBolt>();
			}
			return scrappyBoltType > 0 && projType == scrappyBoltType;
		}

		public static void ClearCache() {
			scrappyBoltType = -1;
		}

		/// <summary>Owner's client: spawns 2-4 non-chaining sparks around an enemy just killed by <paramref name="player"/>.</summary>
		public static void BurstOnKill(Player player, NPC target, Projectile killingProj, int damageDone) {
			if (player == null || player.whoAmI != Main.myPlayer || target == null || damageDone <= 0
				|| !player.GetModPlayer<ResearchPlayer>().Has(ResearchNodes.InducedCombustion)) {
				return;
			}
			if (killingProj != null && IsSpark(killingProj.type)
				&& Math.Abs(killingProj.ai[2] - InducedCombustionTag) < 0.01f) {
				return;                                              // D0 rule 4: burst sparks never chain-burst
			}
			NPC root = target.realLife >= 0 && target.realLife < Main.maxNPCs && Main.npc[target.realLife].active
				? Main.npc[target.realLife]
				: target;
			if (root.life > 0 || root.life + damageDone <= 0 || root.SpawnedFromStatue || root.friendly
				|| root.lifeMax <= 5 || root.CountsAsACritter || root.immortal) {
				return;
			}
			int count = Main.rand.Next(ResearchNodes.CombustionMinSparks, ResearchNodes.CombustionMaxSparks + 1);
			int damage = Math.Max(1, (int)player.GetTotalDamage(DamageClass.Generic).ApplyTo(ResearchNodes.CombustionSparkDamage));
			float baseAngle = Main.rand.NextFloat(MathHelper.TwoPi);
			var source = player.GetSource_OnHit(target);
			for (int i = 0; i < count; i++) {
				float angle = baseAngle + MathHelper.TwoPi * i / count + Main.rand.NextFloat(-0.32f, 0.32f);
				Vector2 vel = angle.ToRotationVector2() * Main.rand.NextFloat(4.8f, 7.2f) + new Vector2(0f, -1.2f);
				if (SafeSpawn.TryNewProjectile(source, target.Center, vel, ProjectileID.WandOfSparkingSpark, damage, 1.5f,
						out Projectile spark, player.whoAmI, 0f, 0f, InducedCombustionTag)) {
					spark.DamageType = DamageClass.Generic;
					spark.usesLocalNPCImmunity = true;
					spark.localNPCHitCooldown = 20;
				}
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item8 with { Pitch = 0.4f, Volume = 0.55f, MaxInstances = 4 }, target.Center);
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 6; i++) {
						if (SafeSpawn.TryNewDust(target.Center - new Vector2(8f), 16, 16, DustID.Torch, out Dust d)) {
							d.velocity = Main.rand.NextVector2Circular(3.2f, 3.2f) - Vector2.UnitY * 0.8f;
							d.noGravity = true;
							d.scale = 1.15f;
						}
					}
				}
			}
		}
	}

	/// <summary>Narrow <see cref="GlobalProjectile"/> applied strictly to spark projectiles (<see cref="ResearchSparks.IsSpark"/>)
	/// for <b>Sparkling!</b> and <b>Better Sparks</b> (D1: zero overhead on all other projectiles).</summary>
	public sealed class ResearchSparkGlobalProjectile : GlobalProjectile
	{
		private byte extraTicks;
		private bool halfStep;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(Projectile entity, bool lateInstantiation) =>
			lateInstantiation && ResearchSparks.IsSpark(entity.type);

		public override void PostAI(Projectile projectile) {
			if (!projectile.friendly || projectile.hostile || projectile.owner < 0 || projectile.owner >= Main.maxPlayers) {
				return;
			}
			Player owner = Main.player[projectile.owner];
			if (owner == null || !owner.active || !owner.GetModPlayer<ResearchPlayer>().Has(ResearchNodes.BetterSparks)) {
				return;
			}
			if (projectile.type == ModContent.ProjectileType<ScrappyWandBolt>()) {
				if (extraTicks == 0) {
					extraTicks = 1;
					projectile.timeLeft += ResearchNodes.BetterSparksExtraTicks * (projectile.extraUpdates + 1);
				}
				return;
			}
			if (projectile.ai[0] < 4f || extraTicks >= ResearchNodes.BetterSparksExtraTicks) {
				return;
			}
			int straightTicks = ResearchNodes.BetterSparksExtraTicks / 2;
			if (extraTicks < straightTicks) {
				projectile.ai[0] -= 1f;                              // straight flight before heavy drop (+range)
				extraTicks++;
			}
			else {
				halfStep = !halfStep;
				if (halfStep) {
					projectile.ai[0] -= 1f;                          // stretched arc (+lifetime, +60 ticks total = +1.0 s)
					extraTicks++;
				}
			}
		}

		public override void OnHitNPC(Projectile projectile, NPC target, NPC.HitInfo hit, int damageDone) {
			if (!projectile.friendly || projectile.hostile || projectile.owner < 0 || projectile.owner >= Main.maxPlayers
				|| target == null || !target.active) {
				return;
			}
			Player owner = Main.player[projectile.owner];
			if (owner == null || !owner.active || !owner.GetModPlayer<ResearchPlayer>().Has(ResearchNodes.Sparkling)) {
				return;
			}
			if (Main.rand.NextFloat() < ResearchNodes.SparklingIgniteChance) {
				int buff = projectile.type == ProjectileID.WandOfFrostingFrost
					? (Main.remixWorld ? BuffID.Frostburn2 : BuffID.Frostburn)
					: (Main.remixWorld ? BuffID.OnFire3 : BuffID.OnFire);
				target.AddBuff(buff, ResearchNodes.SparklingFireTicks);
			}
		}
	}
}
