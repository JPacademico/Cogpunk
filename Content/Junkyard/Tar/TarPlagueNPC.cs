using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// <see cref="TarPlague"/> on enemies (2026-10-30, the tar weapons): vanilla's damage-over-time path (decompiled
	/// <c>NPC.UpdateNPC_BuffApplyDOTs</c>: <c>lifeRegen</c> is in half-life a second, 120 counts a point; the server finishes the
	/// NPC and syncs it) and half speed through <see cref="NPCHaste.ApplySlow"/> (bosses, worms and the like take the damage
	/// only).
	/// <list type="bullet">
	/// <item>The damage (user, 2026-11-24: "decrease a bit tar poisoning so its only 20% stronger than default poison. but keep
	/// the slow effect"; it was 20 a second since 2026-11-03): vanilla's Poisoned takes 12 <c>lifeRegen</c> from an NPC, 6 life a
	/// second; the tar takes <see cref="LifeRegenLossFifths"/> fifths, 14.4 on average (15 two ticks in five, 14 the other
	/// three: a whole number every tick), 7.2 life a second, poison's +20%, shown in chunks of <see cref="DamageChunk"/>.</item>
	/// <item>Fire (same day: "If a tar poisoned enemy takes fire burning damage it should increase the on fire damage in 2x while
	/// it is tar poisoned"): On Fire! and Hellfire burn twice as hard on a tarred enemy (the hook runs after vanilla's own burns,
	/// so their loss is taken once more: 8 and 30 <c>lifeRegen</c>, decompiled). Other burns (Cursed Inferno, Shadowflame,
	/// Frostburn) are left as they are: my reading of "on fire damage".</item>
	/// </list>
	/// The players' tar in the Junkyard pool is unchanged (<see cref="TarPlayer"/>: 20 a second, the pool's barrier that the
	/// Missing Bones mount opens): my reading of the request, which spoke of enemies.
	/// <para>D2: the buff is synced by vanilla (<c>NPC.AddBuff</c> on the hitting client); the damage, the fire and the slow then
	/// run the same on every side (the fifths follow <c>Main.GameUpdateCount</c>). D1: one bool per NPC, set by the buff and
	/// reset every tick; no allocation.</para>
	/// </summary>
	public sealed class TarPlagueNPC : GlobalNPC
	{
		/// <summary>Vanilla's Poisoned on an NPC: <c>lifeRegen</c> -12 (6 life a second, decompiled).</summary>
		public const int PoisonLifeRegen = 12;
		/// <summary>The tar's loss in fifths of a <c>lifeRegen</c> point: poison's 12 x 1.2 = 14.4 = 72 fifths.</summary>
		public const int LifeRegenLossFifths = PoisonLifeRegen * 6;
		public const int DamageChunk = 2;
		/// <summary>On Fire! and Hellfire's own losses (decompiled), taken once more on a tarred enemy (x2).</summary>
		public const int OnFireLifeRegen = 8, HellfireLifeRegen = 30;
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
			// 72 fifths: 15 on two ticks of every five, 14 on the other three (14.4 a tick on average: 7.2 life a second)
			int loss = LifeRegenLossFifths / 5 + (Main.GameUpdateCount % 5 < (uint)(LifeRegenLossFifths % 5) ? 1 : 0);
			npc.lifeRegen -= loss;
			if (npc.onFire) {
				npc.lifeRegen -= OnFireLifeRegen;                 // x2: vanilla's own burn taken again
			}
			if (npc.onFire3) {
				npc.lifeRegen -= HellfireLifeRegen;
			}
			if (damage < DamageChunk) {
				damage = DamageChunk;
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
