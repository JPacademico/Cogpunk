using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Terraria.ID;

namespace Cogpunk.Content.MechArmy.NPCs
{
	/// <summary>
	/// Base for the Mech Army's small ground machines (Rogue Mice-bot, Boombot, Annoy-o-tron): a <see cref="GridWalkerNPC"/>
	/// (three grid planes, ground running, server targeting) that is a machine (<see cref="CogpunkSets.Mechanical"/>,
	/// immune to poison and confusion) and reads <see cref="NPCHaste"/> itself (<see cref="CogpunkSets.SelfHasting"/>): the
	/// Annoy-o-tron's alarm raises its top speed and acceleration by half. Cell sizes come from <see cref="MechArmyRigData"/>.
	/// </summary>
	public abstract class MechWalker : GridWalkerNPC
	{
		protected override int CellPadding => MechArmyRigData.CellPadding;

		protected float Haste => NPCHaste.FactorOf(NPC);

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			CogpunkSets.Mechanical[Type] = true;
			CogpunkSets.SelfHasting[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // machines
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
			// Vanilla skips all mode scaling for an NPC with no contact damage (decompiled NPC.ScaleStats: returns when
			// damage == 0 unless NeedsExpertScaling), so the Boombot and the Annoy-o-tron (contact 0) kept their Classic life
			// in Expert and Master until 2026-11-04; this lets SetExpertStats land on their Expert life.
			NPCID.Sets.NeedsExpertScaling[Type] = true;
		}
	}
}
