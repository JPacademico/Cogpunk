using Cogpunk.Content.Bosses.TrashTr0m.Buffs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Underground.Items
{
	/// <summary>
	/// The <see cref="RustedNail"/>'s thorns: when an enemy's touch lands on the wearer, it takes
	/// <see cref="RustedNail.ThornDamage"/> (no class, no variation: <c>Player.ApplyDamageToNPC</c>, the call vanilla's own
	/// thorns use, which also syncs the strike) and then gets Tetanus, so the thorn itself deals the plain 30.
	/// <para>D2: vanilla resolves an enemy's touch on the touched player's client, which runs <c>OnHitByNPC</c>; the strike
	/// and the buff are sent from there, as vanilla's thorns are. D0: no projectile, no loop; a dead or untouchable enemy is
	/// skipped. D1: one bool, reset every tick.</para>
	/// </summary>
	public sealed class RustedNailPlayer : ModPlayer
	{
		private const int RustFlakes = 5;

		/// <summary>Set by the accessory every tick.</summary>
		public bool Nail;

		public override void ResetEffects() {
			Nail = false;
		}

		public override void OnHitByNPC(NPC npc, Player.HurtInfo hurtInfo) {
			if (!Nail || Player.whoAmI != Main.myPlayer || !npc.active || npc.dontTakeDamage || npc.friendly || npc.immortal) {
				return;
			}
			int away = npc.Center.X < Player.Center.X ? -1 : 1;
			Player.ApplyDamageToNPC(npc, RustedNail.ThornDamage, RustedNail.ThornKnockback, away);
			if (npc.active) {
				npc.AddBuff(ModContent.BuffType<TetanusDebuff>(), RustedNail.TetanusTicks);
			}
			if (!Main.dedServ && CogpunkClientConfig.RollEffect()) {
				for (int i = 0; i < RustFlakes; i++) {                 // rust flakes off the nail
					SafeSpawn.TryNewDust(npc.position, npc.width, npc.height, DustID.Copper, out _, away * 1.5f, -1f, 0, default, 0.9f);
				}
			}
		}
	}
}
