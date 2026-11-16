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
	/// <item><b>A yoyo's reach</b> (2026-11-16, user: "verify if the combinator properly works for yoyo weapons without bugs"):
	/// vanilla reads a yoyo's string length from its projectile's type alone (decompiled <c>Projectile.AI_099_2</c>:
	/// <c>ProjectileID.Sets.YoyosMaximumRange[type]</c>, then the Yoyo String and melee speed), so the base's range never
	/// reached a yoyo product. A yoyo product whose base is a yoyo now flies on the base's string (<see cref="YoyoRange"/>): the
	/// set's entry for the type vanilla reads is swapped in <see cref="PreAI"/> and put back in <see cref="PostAI"/>
	/// (tModLoader runs <c>PostAI</c> after every <c>PreAI</c>, decompiled <c>ProjectileLoader.ProjectileAI</c>; projectiles
	/// update one at a time, so no other yoyo of the type ever sees it).</item>
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
		/// <summary>A yoyo product's string reach from its yoyo base (px; 0: the yoyo's own). From the synced base type.</summary>
		public float YoyoRange;
		private int homingTarget = -1;
		private float savedRange;
		private int swappedType = -1;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(Projectile entity, bool lateInstantiation) => lateInstantiation && !entity.hostile;

		public override void OnSpawn(Projectile projectile, IEntitySource source) {
			Traits = null;
			BaseType = 0;
			Generation = 0;
			YoyoRange = 0f;
			if (projectile.hostile || projectile.type == ModContent.ProjectileType<CombinatorBlast>()) {
				return;
			}
			if (source is EntitySource_ItemUse use && CombinedWeapon.TryGet(use.Item, out CombinedWeapon data) && data.IsProduct) {
				BaseType = data.Base.type;
			}
			else if (source is EntitySource_Parent parent && parent.Entity is Projectile p && p.active
				&& p.TryGetGlobalProjectile(out CombinedProjectile from) && from.BaseType > 0 && from.Generation < MaxGeneration) {
				BaseType = from.BaseType;                         // one level down: a held bow's arrows, the Yoyo Glove's second yoyo
				Generation = from.Generation + 1;
			}
			YoyoRange = BaseType > 0 ? YoyoRangeFor(projectile, BaseType) : 0f;
			Traits = BaseType > 0 ? CombinatorTraits.Of(BaseType) : null;
			if (Traits == null || Traits.Length == 0) {
				Traits = null;
				if (YoyoRange <= 0f) {
					BaseType = 0;                                 // nothing to carry (a yoyo base with no passive still lends its reach)
				}
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
			binaryWriter.Write7BitEncodedInt(Traits != null || YoyoRange > 0f ? BaseType : 0);
		}

		public override void ReceiveExtraAI(Projectile projectile, BitReader bitReader, BinaryReader binaryReader) {
			int type = binaryReader.Read7BitEncodedInt();
			BaseType = type > ItemID.None && type < ItemLoader.ItemCount ? type : 0;
			CombinatorTrait[] traits = BaseType > 0 ? CombinatorTraits.Of(BaseType) : null;
			Traits = traits != null && traits.Length > 0 ? traits : null;
			YoyoRange = BaseType > 0 ? YoyoRangeFor(projectile, BaseType) : 0f;
		}

		/// <summary>The string reach a yoyo projectile takes from its product's base (0 for anything else): only the main
		/// yoyos (vanilla's counterweights run another AI and keep theirs).</summary>
		private static float YoyoRangeFor(Projectile projectile, int baseType) {
			if (projectile.aiStyle != ProjAIStyleID.Yoyo || projectile.counterweight) {
				return 0f;
			}
			return CombinationRules.YoyoRangeOf(baseType);
		}

		/// <summary>The type whose yoyo sets vanilla reads while this projectile's AI runs (a modded projectile may borrow a
		/// vanilla type's AI, decompiled <c>ProjectileLoader.ProjectileAI</c>); -1 when out of the set's range (D0).</summary>
		private static int SetKey(Projectile projectile) {
			int key = projectile.ModProjectile != null && projectile.ModProjectile.AIType > 0 ? projectile.ModProjectile.AIType : projectile.type;
			return key > 0 && key < ProjectileID.Sets.YoyosMaximumRange.Length ? key : -1;
		}

		public override bool PreAI(Projectile projectile) {
			if (YoyoRange > 0f && swappedType < 0) {
				int key = SetKey(projectile);
				if (key >= 0) {
					savedRange = ProjectileID.Sets.YoyosMaximumRange[key];
					ProjectileID.Sets.YoyosMaximumRange[key] = YoyoRange;
					swappedType = key;
				}
			}
			return true;
		}

		public override void PostAI(Projectile projectile) {
			if (swappedType >= 0) {
				ProjectileID.Sets.YoyosMaximumRange[swappedType] = savedRange;   // back before any other projectile updates
				swappedType = -1;
			}
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
