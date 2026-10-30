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
		/// NPCs whose own AI applies <see cref="NPCHaste.FactorOf"/> (top speed, acceleration, animation rate), so
		/// <see cref="NPCHaste"/> skips its generic extra step for them. Set it in <c>SetStaticDefaults</c> only if the AI
		/// really reads the factor.
		/// </summary>
		public static bool[] SelfHasting = NPCID.Sets.Factory.CreateNamedSet("Cogpunk", nameof(SelfHasting))
			.Description("NPCs that apply Cogpunk's haste (the Annoy-o-tron's alarm) in their own AI instead of the generic extra step.")
			.RegisterBoolSet(false);

		/// <summary>Bounds-checked lookup (D0): unknown or out-of-range types are simply not mechanical.</summary>
		public static bool IsMechanical(NPC npc) {
			int type = npc.type;
			return type > NPCID.None && type < Mechanical.Length && Mechanical[type];
		}
	}
}
