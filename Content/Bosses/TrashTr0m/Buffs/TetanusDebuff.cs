using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Buffs
{
	/// <summary>
	/// Tetanus (NPC debuff, from the <see cref="Weapons.Tetanus"/> lance): the target takes
	/// <see cref="DamageTakenPercent"/>% more damage from every source while it lasts (2 s per hit). Applied with
	/// <c>NPC.AddBuff</c> on the attacking client; vanilla syncs NPC buffs (ExampleMod 1.4.4 <c>ExampleDefenseDebuff</c>).
	/// The multiplier is applied by <see cref="TetanusGlobalNPC"/>; rust flakes drip off the target (clients only).
	/// </summary>
	public class TetanusDebuff : CogpunkBuff
	{
		public const int DamageTakenPercent = 10;
		public const float DamageTakenMultiplier = 1f + DamageTakenPercent / 100f;

		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.pvpBuff[Type] = false;
			Main.buffNoSave[Type] = true;
		}

		public override void Update(NPC npc, ref int buffIndex) {
			if (!Main.dedServ && Main.rand.NextBool(6) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(npc.position, npc.width, npc.height, DustID.Copper, out Dust d, 0f, 1f, 0, default, 0.8f)) {
				d.velocity *= 0.3f;
			}
		}
	}

	/// <summary>
	/// +10% damage taken under <see cref="TetanusDebuff"/> (ExampleMod 1.4.4 <c>DamageModificationGlobalNPC</c>). Runs per
	/// hit, not per tick (D1), on the side that computes the hit; <c>HasBuff</c> is a scan of at most the NPC's 20 buff
	/// slots, so no per-entity state is needed.
	/// </summary>
	public sealed class TetanusGlobalNPC : GlobalNPC
	{
		// Any NPC can be hit by the lance, so this can't be narrowed by type; it holds no per-entity data.
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => true;

		public override void ModifyIncomingHit(NPC npc, ref NPC.HitModifiers modifiers) {
			if (npc.HasBuff<TetanusDebuff>()) {
				modifiers.FinalDamage *= TetanusDebuff.DamageTakenMultiplier;
			}
		}
	}
}
