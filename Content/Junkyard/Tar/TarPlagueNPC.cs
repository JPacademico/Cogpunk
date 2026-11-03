using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// <see cref="TarPlague"/> on enemies (2026-10-30, the tar weapons; user-set "20 damage every 0.5 seconds but keep the
	/// slow"): <see cref="TarPlayer.TickDamage"/> every <see cref="TarPlayer.TickInterval"/> ticks through vanilla's
	/// damage-over-time path (decompiled <c>NPC.UpdateNPC_BuffApplyDOTs</c>: <c>lifeRegen</c> -40 is 20 life a second, and a
	/// <c>damage</c> of 10 takes it off in chunks of 10 every 30 ticks; halved on 2026-11-03, user-set) with the DoT number; the server finishes the NPC and
	/// syncs it), and half speed through <see cref="NPCHaste.ApplySlow"/> (bosses, worms and the like take the damage only).
	/// <para>D2: the buff is synced by vanilla (<c>NPC.AddBuff</c> on the hitting client); the damage and the slow then run the
	/// same on every side. D1: one bool per NPC, set by the buff and reset every tick; no allocation.</para>
	/// </summary>
	public sealed class TarPlagueNPC : GlobalNPC
	{
		/// <summary>lifeRegen is in half-life per second (decompiled: 120 counts a point, one count per tick per unit).</summary>
		public const int LifeRegenLoss = TarPlayer.TickDamage * 60 / TarPlayer.TickInterval * 2;
		public const int SlowRefreshTicks = 2;
		private const int DripOneIn = 8;
		private const float TarTintR = 0.55f, TarTintG = 0.5f, TarTintB = 0.46f;

		/// <summary>Set every tick by <see cref="TarPlague.Update(NPC, ref int)"/>.</summary>
		public bool Plagued;

		public override bool InstancePerEntity => true;

		// Any NPC can be coated (a boss takes the damage, not the slow), so this can't be narrowed by type.
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => true;

		public override void ResetEffects(NPC npc) {
			Plagued = false;
		}

		public override void UpdateLifeRegen(NPC npc, ref int damage) {
			if (!Plagued) {
				return;
			}
			if (npc.lifeRegen > 0) {
				npc.lifeRegen = 0;
			}
			npc.lifeRegen -= LifeRegenLoss;
			if (damage < TarPlayer.TickDamage) {
				damage = TarPlayer.TickDamage;
			}
		}

		public override void DrawEffects(NPC npc, ref Color drawColor) {
			if (!Plagued) {
				return;
			}
			drawColor = new Color((int)(drawColor.R * TarTintR), (int)(drawColor.G * TarTintG), (int)(drawColor.B * TarTintB), drawColor.A);
			if (!Main.gamePaused && Main.rand.NextBool(DripOneIn) && CogpunkClientConfig.RollEffect()) {
				Vector2 at = npc.position + new Vector2(Main.rand.NextFloat(npc.width), Main.rand.NextFloat(npc.height * 0.7f));
				if (SafeSpawn.TryNewDust(at, 2, 2, ModContent.DustType<TarSplash>(), out Dust drip)) {
					drip.velocity = new Vector2(npc.velocity.X * 0.2f, Main.rand.NextFloat(0.5f, 1.5f));
				}
			}
		}
	}
}
