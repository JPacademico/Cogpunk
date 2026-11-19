using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Buffs
{
	/// <summary>
	/// Tetanus, on enemies (from the <see cref="Weapons.Tetanus"/> lance) and, since 2026-11-18, on players (user: "make so
	/// every mech enemy from the mech invasion, westworld and junkyard apply tetanus debuff on the player": their touch,
	/// <see cref="TetanusContactNPC"/>): whoever has it takes <see cref="DamageTakenPercent"/>% more damage from every source
	/// while it lasts. Applied with <c>AddBuff</c> on the side that lands the hit; vanilla syncs both kinds of buff (ExampleMod
	/// 1.4.4 <c>ExampleDefenseDebuff</c>). The multiplier: <see cref="TetanusGlobalNPC"/> and <see cref="TetanusPlayer"/>; rust
	/// flakes drip off whoever has it (clients only). The <see cref="Items.TetanusShot"/> makes a player immune.
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

		public override void Update(Player player, ref int buffIndex) {
			if (!Main.dedServ && Main.rand.NextBool(8) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(player.position, player.width, player.height, DustID.Copper, out Dust d, 0f, 1f, 0, default, 0.7f)) {
				d.velocity *= 0.3f;
			}
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

	/// <summary>+<see cref="TetanusDebuff.DamageTakenPercent"/>% damage taken by a player with Tetanus (2026-11-18).</summary>
	public sealed class TetanusPlayer : ModPlayer
	{
		public override void ModifyHurt(ref Player.HurtModifiers modifiers) {
			if (Player.HasBuff<TetanusDebuff>()) {
				modifiers.FinalDamage *= TetanusDebuff.DamageTakenMultiplier;
			}
		}
	}

	/// <summary>
	/// The machines that give Tetanus on touch (user, 2026-11-18: "every mech enemy from the mech invasion, westworld and
	/// junkyard"): the Mech Army's robots (Annoy-o-Tron, Boombot, the Jaeger, the Mech Walker, the Rogue Mice Bot), Westworld's
	/// (the Brass Bandit, the Dinamitrom, the Mechanical Bull, the Sheriff) and the Junkyard's (the Rust Collector and Trash-Tr0m).
	/// Their contact hit gives the player <see cref="TouchTicks"/> ticks of Tetanus (my call: 4 s, Expert's like every number of
	/// ours; modded debuffs aren't lengthened by the mode). D2: <c>OnHitPlayer</c> runs on the hurt player's client, which owns
	/// its buffs (vanilla syncs them). D1: only those types (<see cref="AppliesToEntity"/>).
	/// </summary>
	public sealed class TetanusContactNPC : GlobalNPC
	{
		public const int TouchTicks = 240;
		private static bool[] gives;

		public override void SetStaticDefaults() {
			gives = new bool[NPCLoader.NPCCount];
			int[] types = {
				ModContent.NPCType<MechArmy.NPCs.AnnoyOTron>(), ModContent.NPCType<MechArmy.NPCs.Boombot>(), ModContent.NPCType<MechArmy.NPCs.Jaeger>(),
				ModContent.NPCType<MechArmy.NPCs.MechWalker>(), ModContent.NPCType<MechArmy.NPCs.RogueMiceBot>(),
				ModContent.NPCType<OldBrassTown.NPCs.BrassBandit>(), ModContent.NPCType<OldBrassTown.NPCs.Dinamitrom>(),
				ModContent.NPCType<OldBrassTown.NPCs.MechanicalBull>(), ModContent.NPCType<OldBrassTown.NPCs.Sheriff>(),
				ModContent.NPCType<Junkyard.NPCs.RustCollector>(), ModContent.NPCType<TrashTr0m>(),
			};
			foreach (int t in types) {
				if (t > 0 && t < gives.Length) {
					gives[t] = true;
				}
			}
		}

		public override void Unload() {
			gives = null;
		}

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			return lateInstantiation && gives != null && entity.type > 0 && entity.type < gives.Length && gives[entity.type];
		}

		public override void OnHitPlayer(NPC npc, Player target, Player.HurtInfo hurtInfo) {
			if (target.whoAmI == Main.myPlayer) {
				target.AddBuff(ModContent.BuffType<TetanusDebuff>(), TouchTicks);
			}
		}
	}
}
