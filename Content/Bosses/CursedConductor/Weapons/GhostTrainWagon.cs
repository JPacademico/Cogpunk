using System;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Weapons
{
	/// <summary>
	/// A wagon of the <see cref="CursedTrainWhistle"/>'s ghost train (one minion slot, one per blow after the first): a little
	/// ghost passenger car hitched behind the <see cref="GhostTrainEngine"/>, which places it on its path every tick (its
	/// <c>ai[1]</c> names the engine, <c>ai[0]</c> is its ticket: its place in the train). It hits whatever it passes
	/// through, once a run (<see cref="GhostTrainEngine.HitCooldown"/>-tick immunity of its own: user, 2026-11-09, "dealing
	/// damage for every wagon that hits"), only while the engine is charging, each hit on an enemy <see cref="GhostTrainEngine.FalloffPerHit"/>
	/// times the segment's before it on that enemy that run (<see cref="GhostTrainEngine.NextHitScale"/>). Without its engine
	/// it lets go (the owner removes it).
	/// <para>D2: placed on every client by every client's engine; hits are the owner's. D1: no allocation.</para>
	/// </summary>
	public class GhostTrainWagon : CogpunkProjectile
	{
		private static Asset<Texture2D> glow;

		/// <summary>Its place behind the engine (1 = the first car), set by the engine.</summary>
		public int Rank;

		/// <summary>When the engine last placed it.</summary>
		public uint PlacedTick;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = 1;
			ProjectileID.Sets.MinionSacrificable[Type] = true;
			ProjectileID.Sets.CultistIsResistantTo[Type] = true;
			CogpunkSets.RollsOwnCrit[Type] = true;
			if (!Main.dedServ) {
				glow = DepthLayers.RequestOptional(Texture + "_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 24;
			Projectile.height = 24;
			Projectile.friendly = true;
			Projectile.minion = true;
			Projectile.minionSlots = GhostTrainEngine.MinionSlots;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = GhostTrainEngine.HitCooldown;
		}

		public override bool? CanCutTiles() => false;

		public override bool MinionContactDamage() => true;

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			if (owner.active && !owner.dead && owner.HasBuff(ModContent.BuffType<GhostTrainBuff>())) {
				Projectile.timeLeft = 2;
			}
			int engine = Projectile.GetByUUID(Projectile.owner, Projectile.ai[1]);
			if (engine < 0 || Main.projectile[engine].type != ModContent.ProjectileType<GhostTrainEngine>()) {
				Engine = null;
				if (Projectile.owner == Main.myPlayer) {
					Projectile.Kill();                           // its engine is gone (dismissed, sacrificed, or never came)
				}
				return;
			}
			Projectile.velocity = Vector2.Zero;                   // the engine sets its place
			Engine = Main.projectile[engine].ModProjectile as GhostTrainEngine;
		}

		/// <summary>Its engine, found again every tick (null while it has none).</summary>
		public GhostTrainEngine Engine { get; private set; }

		/// <summary>Hurts only once the engine has placed it (a wagon just hitched sits on the engine for a tick), and only while
		/// the engine is charging (never on the way home).</summary>
		public override bool? CanDamage() => Rank > 0 && Engine != null && Engine.Projectile.active && Engine.Hurting ? null : false;

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			Vector2 u = new Vector2(MathF.Cos(Projectile.rotation), MathF.Sin(Projectile.rotation)) * (GhostTrainEngine.CarLength * 0.5f - GhostTrainEngine.CarRadius);
			return SwingPose.CapsuleHitsRect(Projectile.Center - u, Projectile.Center + u, GhostTrainEngine.CarRadius, targetHitbox);
		}

		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (Main.rand.Next(100) < Projectile.CritChance) {
				modifiers.SetCrit();                              // summon damage skips vanilla's crit roll (the owner's roll)
			}
			if (Engine != null) {
				modifiers.SourceDamage *= Engine.NextHitScale(target.whoAmI);   // 12% less than the segment before, same run
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			if (Rank <= 0) {
				return false;
			}
			Vector2 heading = new(MathF.Cos(Projectile.rotation), MathF.Sin(Projectile.rotation));
			GhostTrainEngine.DrawSegment(TextureAssets.Projectile[Type].Value, glow?.IsLoaded == true ? glow.Value : null, GhostTrainArt.CarCell,
				Projectile.Center, heading);
			return false;
		}
	}
}
