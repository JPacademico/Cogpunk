using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// Cogpunk's custom ID sets. They are tModLoader named ID sets (key <c>"Cogpunk/&lt;Name&gt;"</c>), so other mods can read
	/// and extend them without referencing Cogpunk, and they resize with the content arrays: tModLoader re-runs this
	/// static constructor during ResizeArrays (<see cref="ReinitializeDuringResizeArraysAttribute"/>).
	/// <para>Cogpunk NPCs add themselves in <c>SetStaticDefaults</c>: <c>CogpunkSets.Mechanical[Type] = true;</c></para>
	/// </summary>
	[ReinitializeDuringResizeArrays]
	public static class CogpunkSets
	{
		/// <summary>
		/// Robots, machines and mechanical constructs, for effects that hurt machines more (the Screwdriver). Vanilla
		/// members: the three mechanical bosses with every part and their Probes, the Martian Madness machines and the
		/// Elf Copter. Multi-part bosses are listed part by part, so no <c>realLife</c> lookup is needed.
		/// </summary>
		public static bool[] Mechanical = NPCID.Sets.Factory.CreateNamedSet("Cogpunk", nameof(Mechanical))
			.Description("Robots, machines and mechanical constructs: effects that hurt machines more treat these NPCs as mechanical.")
			.RegisterBoolSet(false,
				NPCID.TheDestroyer, NPCID.TheDestroyerBody, NPCID.TheDestroyerTail, NPCID.Probe,
				NPCID.Retinazer, NPCID.Spazmatism,
				NPCID.SkeletronPrime, NPCID.PrimeCannon, NPCID.PrimeSaw, NPCID.PrimeVice, NPCID.PrimeLaser,
				NPCID.MartianProbe, NPCID.MartianDrone, NPCID.MartianTurret, NPCID.MartianWalker,
				NPCID.MartianSaucer, NPCID.MartianSaucerCannon, NPCID.MartianSaucerTurret, NPCID.MartianSaucerCore,
				NPCID.ElfCopter);

		/// <summary>
		/// Items that generated Scrappy Trunks can hold as their prize (see <c>Content/Furniture/ScrappyTrunkLoot</c>).
		/// Every Cogpunk trinket or accessory that is neither a boss drop nor Hardmode-only sets this in its
		/// <c>SetStaticDefaults</c>: <c>CogpunkSets.ScrappyTrunkTrinket[Type] = true;</c>
		/// </summary>
		public static bool[] ScrappyTrunkTrinket = ItemID.Sets.Factory.CreateNamedSet("Cogpunk", nameof(ScrappyTrunkTrinket))
			.Description("Pre-Hardmode trinkets and accessories (not boss drops) that can be found in Cogpunk's Scrappy Trunks.")
			.RegisterBoolSet(false);

		/// <summary>
		/// NPCs whose own AI applies <see cref="NPCHaste.FactorOf"/> (top speed, acceleration, animation rate: the haste and,
		/// since 2026-10-30, the Tar Plague's slow), so <see cref="NPCHaste"/> skips its generic extra step for them. Set it in
		/// <c>SetStaticDefaults</c> only if the AI really reads the factor.
		/// </summary>
		public static bool[] SelfHasting = NPCID.Sets.Factory.CreateNamedSet("Cogpunk", nameof(SelfHasting))
			.Description("NPCs that apply Cogpunk's haste and slow (the Annoy-o-tron's alarm, the Tar Plague) in their own AI instead of the generic step.")
			.RegisterBoolSet(false);

		/// <summary>
		/// Mini-bosses: big event or invasion enemies that aren't bosses, for effects that treat bosses and mini-bosses
		/// alike (the Metal Wrench's riposte). Vanilla members: terraria.wiki.gg's mini-boss list (the event bosses except
		/// the Celestial Pillars) with their parts. Cogpunk's own add themselves (the Jaeger). Bosses need no entry: see
		/// <see cref="IsBossOrMiniboss"/>.
		/// </summary>
		public static bool[] Miniboss = NPCID.Sets.Factory.CreateNamedSet("Cogpunk", nameof(Miniboss))
			.Description("Mini-bosses (event and invasion heavyweights that aren't bosses): effects that single out bosses treat these NPCs the same way.")
			.RegisterBoolSet(false,
				NPCID.DD2DarkMageT1, NPCID.DD2DarkMageT3, NPCID.DD2OgreT2, NPCID.DD2OgreT3, NPCID.DD2Betsy,
				NPCID.PirateShip, NPCID.PirateShipCannon, NPCID.MourningWood, NPCID.Pumpking, NPCID.PumpkingBlade,
				NPCID.Everscream, NPCID.SantaNK1, NPCID.IceQueen,
				NPCID.MartianSaucer, NPCID.MartianSaucerCore, NPCID.MartianSaucerCannon, NPCID.MartianSaucerTurret);

		/// <summary>
		/// Projectiles that keep running at full speed while <see cref="SlowMotion"/> holds everything else back (the effect
		/// that started it, so its flash isn't frozen with the world).
		/// </summary>
		public static bool[] IgnoresSlowMotion = ProjectileID.Sets.Factory.CreateNamedSet("Cogpunk", nameof(IgnoresSlowMotion))
			.Description("Projectiles that keep updating at full speed during Cogpunk's slow motion.")
			.RegisterBoolSet(false);

		/// <summary>
		/// Summon projectiles that roll their own critical strikes (<c>Projectile.CritChance</c> in their <c>ModifyHitNPC</c>):
		/// vanilla's summon damage skips the crit roll (<c>SummonDamageClass.UseStandardCritCalcs</c> is false), so Cogpunk's
		/// minions roll it themselves. Effects that let every minion crit (the Bottle of Lost Souls) skip these, so nothing
		/// rolls twice.
		/// </summary>
		public static bool[] RollsOwnCrit = ProjectileID.Sets.Factory.CreateNamedSet("Cogpunk", nameof(RollsOwnCrit))
			.Description("Summon projectiles that already roll Projectile.CritChance themselves; effects that make minions crit skip them.")
			.RegisterBoolSet(false);

		/// <summary>Bounds-checked lookup (D0) of <see cref="RollsOwnCrit"/>.</summary>
		public static bool RollsOwnCritType(int type) {
			return type > ProjectileID.None && type < RollsOwnCrit.Length && RollsOwnCrit[type];
		}

		/// <summary>Bounds-checked lookup (D0): unknown or out-of-range types are simply not mechanical.</summary>
		public static bool IsMechanical(NPC npc) {
			int type = npc.type;
			return type > NPCID.None && type < Mechanical.Length && Mechanical[type];
		}

		/// <summary>A boss (or a part of one: a worm segment or a part sharing its life, or a type vanilla counts as a boss) or
		/// a <see cref="Miniboss"/>. Bounds-checked (D0).</summary>
		public static bool IsBossOrMiniboss(NPC npc) {
			if (npc.boss) {
				return true;
			}
			int type = npc.type;
			if (type > NPCID.None && type < Miniboss.Length && (Miniboss[type] || NPCID.Sets.ShouldBeCountedAsBoss[type])) {
				return true;
			}
			if (type == NPCID.EaterofWorldsBody || type == NPCID.EaterofWorldsTail) {
				return true;                                   // separate NPCs with their own life, only the head is counted
			}
			int head = npc.realLife;
			return head >= 0 && head < Main.maxNPCs && head != npc.whoAmI && Main.npc[head].active && Main.npc[head].boss;
		}

		/// <summary>Bounds-checked lookup (D0) of <see cref="IgnoresSlowMotion"/>.</summary>
		public static bool IgnoresSlowMotionType(int type) {
			return type > ProjectileID.None && type < IgnoresSlowMotion.Length && IgnoresSlowMotion[type];
		}
	}
}
