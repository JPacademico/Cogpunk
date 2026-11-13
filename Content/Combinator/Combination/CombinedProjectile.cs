using System;
using System.IO;
using Cogpunk.Core.Combat;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>
	/// A combination's projectiles carry its base's traits (<see cref="CombinatorTraits"/>). They are told apart at spawn by
	/// where they come from (tModLoader's entity sources): one fired by an item use whose item is a product, or (one level
	/// down, <see cref="MaxGeneration"/>) one fired by such a projectile, for weapons that shoot through a held projectile
	/// (bows like the Phantasm, channelled guns). Nothing else ever gets them, so a trait's own effects (the burst) never
	/// carry traits again.
	/// <list type="bullet">
	/// <item><b>Homing</b> (<see cref="TraitKind.Homing"/>): a free-flying shot turns towards the closest enemy it may chase
	/// within range (vanilla's <c>CanBeChasedBy</c>), re-picked every <see cref="RetargetTicks"/> ticks, at its own speed.
	/// Projectiles that a weapon steers itself (held, spear, yoyo, flail, boomerang, drill, whip, sword-slash and minion
	/// styles, and anything that hits only in reach of its owner) are left alone.</item>
	/// <item><b>Pierce</b>: +N to the projectile's penetration at spawn (only ones that already die on a hit).</item>
	/// <item>The hit traits through <see cref="TraitEffects"/>.</item>
	/// </list>
	/// D2: the spawn source is known only where the projectile is made (the owner), so the base's type rides the projectile's
	/// sync (<see cref="SendExtraAI"/>, part of vanilla's message 27) and every side runs the same homing from synced NPC
	/// positions; the owner sends a <c>netUpdate</c> when its target changes. D1: the trait array is shared (one reference a
	/// projectile); the target search is one pass over active NPCs every few ticks, no allocation.
	/// </summary>
	public sealed class CombinedProjectile : GlobalProjectile
	{
		public const int MaxGeneration = 1;
		public const int RetargetTicks = 6;

		public CombinatorTrait[] Traits;
		public int BaseType;                                      // the base whose traits these are (synced)
		public int Generation;
		private int homingTarget = -1;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(Projectile entity, bool lateInstantiation) => lateInstantiation && !entity.hostile;

		public override void OnSpawn(Projectile projectile, IEntitySource source) {
			Traits = null;
			BaseType = 0;
			Generation = 0;
			if (projectile.hostile || projectile.type == ModContent.ProjectileType<CombinatorBlast>()) {
				return;
			}
			if (source is EntitySource_ItemUse use && CombinedWeapon.TryGet(use.Item, out CombinedWeapon data) && data.IsProduct) {
				BaseType = data.Base.type;
			}
			else if (source is EntitySource_Parent parent && parent.Entity is Projectile p && p.active
				&& p.TryGetGlobalProjectile(out CombinedProjectile from) && from.Traits != null && from.Generation < MaxGeneration) {
				BaseType = from.BaseType;
				Generation = from.Generation + 1;
			}
			Traits = BaseType > 0 ? CombinatorTraits.Of(BaseType) : null;
			if (Traits == null || Traits.Length == 0) {
				Traits = null;
				BaseType = 0;
				return;
			}
			if (CombinatorTraits.Has(Traits, TraitKind.Pierce, out CombinatorTrait pierce) && projectile.penetrate > 0) {
				projectile.penetrate += Math.Max(0, pierce.D);
				if (!projectile.usesLocalNPCImmunity && !projectile.usesIDStaticNPCImmunity) {
					projectile.usesLocalNPCImmunity = true;          // each enemy once a pierce, not the global 10-tick lock
					projectile.localNPCHitCooldown = -1;
				}
			}
		}

		public override void SendExtraAI(Projectile projectile, BitWriter bitWriter, BinaryWriter binaryWriter) {
			binaryWriter.Write7BitEncodedInt(Traits != null ? BaseType : 0);
		}

		public override void ReceiveExtraAI(Projectile projectile, BitReader bitReader, BinaryReader binaryReader) {
			int type = binaryReader.Read7BitEncodedInt();
			BaseType = type > ItemID.None && type < ItemLoader.ItemCount ? type : 0;
			CombinatorTrait[] traits = BaseType > 0 ? CombinatorTraits.Of(BaseType) : null;
			Traits = traits != null && traits.Length > 0 ? traits : null;
		}

		public override void PostAI(Projectile projectile) {
			if (Traits == null || !CombinatorTraits.Has(Traits, TraitKind.Homing, out CombinatorTrait homing) || !Steerable(projectile)) {
				return;
			}
			float range = homing.A;
			if (homingTarget < 0 || (projectile.timeLeft + projectile.whoAmI) % RetargetTicks == 0 || !Chaseable(homingTarget, projectile, range)) {
				int old = homingTarget;
				homingTarget = Closest(projectile, range);
				if (old != homingTarget && projectile.owner == Main.myPlayer) {
					projectile.netUpdate = true;
				}
			}
			if (homingTarget < 0) {
				return;
			}
			float speed = projectile.velocity.Length();
			Vector2 want = (Main.npc[homingTarget].Center - projectile.Center).SafeNormalize(Vector2.Zero) * speed;
			Vector2 v = Vector2.Lerp(projectile.velocity, want, Math.Clamp(homing.B, 0.01f, 0.5f));
			if (v.LengthSquared() > 0.0001f) {
				projectile.velocity = Vector2.Normalize(v) * speed;
			}
		}

		/// <summary>A free-flying friendly shot whose own AI doesn't steer it.</summary>
		private static bool Steerable(Projectile p) {
			if (!p.friendly || p.hostile || p.damage <= 0 || p.minion || p.sentry || p.ownerHitCheck || Main.projPet[p.type]
				|| ProjectileID.Sets.IsAWhip[p.type] || p.velocity.LengthSquared() < 1f) {
				return false;
			}
			switch (p.aiStyle) {
				case ProjAIStyleID.Boomerang:
				case ProjAIStyleID.Hook:
				case ProjAIStyleID.Flail:
				case ProjAIStyleID.Spear:
				case ProjAIStyleID.Drill:
				case ProjAIStyleID.HeldProjectile:
				case ProjAIStyleID.Yoyo:
				case ProjAIStyleID.ShortSword:
				case ProjAIStyleID.Whip:
				case ProjAIStyleID.NightsEdge:
					return false;
			}
			return true;
		}

		private static bool Chaseable(int index, Projectile p, float range) {
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC n = Main.npc[index];
			return n.active && n.CanBeChasedBy(p) && Vector2.DistanceSquared(n.Center, p.Center) <= range * range;
		}

		private static int Closest(Projectile p, float range) {
			int best = -1;
			float bestD = range * range;
			foreach (NPC n in Main.ActiveNPCs) {
				if (!n.CanBeChasedBy(p)) {
					continue;
				}
				float d = Vector2.DistanceSquared(n.Center, p.Center);
				if (d < bestD) {
					bestD = d;
					best = n.whoAmI;
				}
			}
			return best;
		}

		public override void ModifyHitNPC(Projectile projectile, NPC target, ref NPC.HitModifiers modifiers) {
			if (Traits != null) {
				TraitEffects.ModifyHit(Traits, target, ref modifiers);
			}
		}

		public override void OnHitNPC(Projectile projectile, NPC target, NPC.HitInfo hit, int damageDone) {
			if (Traits == null || projectile.owner < 0 || projectile.owner >= Main.maxPlayers) {
				return;
			}
			TraitEffects.OnHit(Traits, target, Main.player[projectile.owner], damageDone, target.Center, projectile.DamageType);
		}
	}
}
