using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// Short movement-speed changes on enemies, refreshed by whatever grants them: a haste (x<see cref="Factor"/>, the
	/// Annoy-o-tron's alarm, user-set 2026-10-27: "increasing their speed by 50%") and a slow (x<see cref="SlowFactor"/>,
	/// the Tar Plague, 2026-10-30: "keep the slow"); both at once multiply. NPCs have no speed stat, so:
	/// <list type="bullet">
	/// <item>Cogpunk NPCs that set <see cref="CogpunkSets.SelfHasting"/> read <see cref="FactorOf"/> in their own AI (top
	/// speed, acceleration, animation rate: a walker's root motion stays exact).</item>
	/// <item>Every other enemy gets the difference as an extra part of a step each tick in <c>PostAI</c> (half a step more
	/// when hasted, half a step back when slowed), after its AI has chosen its velocity and before vanilla moves it
	/// (decompiled <c>NPC.UpdateNPC_Inner</c>: <c>AI()</c>, then <c>UpdateCollision()</c>), through vanilla's tile collision
	/// (<c>Collision.TileCollision</c>, like vanilla's conveyor-belt nudge): horizontal only for walkers (no higher jumps or
	/// faster falls), both axes for fliers and ghosts. Its velocity is untouched, so its AI is never confused.</item>
	/// </list>
	/// Not for bosses, town NPCs, critters, projectile NPCs or worm segments (the slow also skips worm heads and NPCs counted
	/// as bosses: their AI times its moves). The grant is computed the same way on every side from synced state (positions,
	/// buffs; no packet); the server's positions win as usual (D2). D1: two ints per NPC, no allocation.
	/// </summary>
	public sealed class NPCHaste : GlobalNPC
	{
		public const float Factor = 1.5f;
		public const float SlowFactor = 0.5f;

		private int ticks;
		private int slowTicks;

		public override bool InstancePerEntity => true;

		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) {
			return lateInstantiation && !entity.friendly && !entity.townNPC && !entity.boss && entity.lifeMax > 5 && !entity.immortal
				&& !NPCID.Sets.ProjectileNPC[entity.type] && !NPCID.Sets.CountsAsCritter[entity.type];
		}

		/// <summary>Hastes <paramref name="npc"/> for at least <paramref name="duration"/> ticks; false if it can't be hasted.</summary>
		public static bool Apply(NPC npc, int duration) {
			if ((npc.realLife >= 0 && npc.realLife != npc.whoAmI) || !npc.TryGetGlobalNPC(out NPCHaste haste)) {
				return false;
			}
			if (haste.ticks < duration) {
				haste.ticks = duration;
			}
			return true;
		}

		/// <summary>Slows <paramref name="npc"/> for at least <paramref name="duration"/> ticks; false if it can't be slowed.</summary>
		public static bool ApplySlow(NPC npc, int duration) {
			if ((npc.realLife >= 0 && npc.realLife != npc.whoAmI) || npc.aiStyle == NPCAIStyleID.Worm
				|| (npc.type > NPCID.None && npc.type < NPCID.Sets.ShouldBeCountedAsBoss.Length && NPCID.Sets.ShouldBeCountedAsBoss[npc.type])
				|| !npc.TryGetGlobalNPC(out NPCHaste haste)) {
				return false;
			}
			if (haste.slowTicks < duration) {
				haste.slowTicks = duration;
			}
			return true;
		}

		public static bool IsHasted(NPC npc) => npc.TryGetGlobalNPC(out NPCHaste haste) && haste.ticks > 0;

		public static bool IsSlowed(NPC npc) => npc.TryGetGlobalNPC(out NPCHaste haste) && haste.slowTicks > 0;

		/// <summary>The speed multiplier now (<see cref="Factor"/> hasted, <see cref="SlowFactor"/> slowed, both multiply; 1
		/// otherwise): for <see cref="CogpunkSets.SelfHasting"/> NPCs.</summary>
		public static float FactorOf(NPC npc) {
			if (!npc.TryGetGlobalNPC(out NPCHaste haste)) {
				return 1f;
			}
			return haste.Current;
		}

		private float Current => (ticks > 0 ? Factor : 1f) * (slowTicks > 0 ? SlowFactor : 1f);

		public override void PostAI(NPC npc) {
			if (ticks <= 0 && slowTicks <= 0) {
				return;
			}
			float k = Current - 1f;
			if (ticks > 0) {
				ticks--;
			}
			if (slowTicks > 0) {
				slowTicks--;
			}
			if (CogpunkSets.SelfHasting[npc.type] || k == 0f) {
				return;
			}
			Vector2 extra = npc.noGravity ? npc.velocity * k : new Vector2(npc.velocity.X * k, 0f);
			if (extra == Vector2.Zero || !MathSafety.IsFinite(extra)) {
				return;
			}
			if (!npc.noTileCollide) {
				bool fall = npc.velocity.Y > 0f;
				extra = Collision.TileCollision(npc.position, extra, npc.width, npc.height, fall, fall);
			}
			npc.position += extra;
		}

		public override void DrawEffects(NPC npc, ref Color drawColor) {
			if (ticks <= 0) {
				return;
			}
			// A red pulse in step with the alarm light: who is hasted reads at a glance (hostile ember red, D3).
			float pulse = 0.5f + 0.5f * (float)System.Math.Sin(Main.GlobalTimeWrappedHourly * 12f);
			drawColor = Color.Lerp(drawColor, new Color(236, 113, 40, drawColor.A), 0.18f + 0.17f * pulse);
		}
	}
}
