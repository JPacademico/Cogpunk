using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// A short movement-speed buff on enemies (+<c>(Factor - 1)</c>, 50%), refreshed by whatever grants it (the
	/// Annoy-o-tron's alarm, user-set 2026-10-27: "increasing their speed by 50%"). NPCs have no speed stat, so:
	/// <list type="bullet">
	/// <item>Cogpunk NPCs that set <see cref="CogpunkSets.SelfHasting"/> read <see cref="FactorOf"/> in their own AI (top
	/// speed, acceleration, animation rate: a walker's root motion stays exact).</item>
	/// <item>Every other enemy gets an extra half step each tick in <c>PostAI</c>, after its AI has chosen its velocity and
	/// before vanilla moves it (decompiled <c>NPC.UpdateNPC_Inner</c>: <c>AI()</c>, then <c>UpdateCollision()</c>), through
	/// vanilla's tile collision (<c>Collision.TileCollision</c>, like vanilla's conveyor-belt nudge): horizontal only for
	/// walkers (no higher jumps or faster falls), both axes for fliers and ghosts. Its velocity is untouched, so its AI is
	/// never confused.</item>
	/// </list>
	/// Not for bosses, town NPCs, critters, projectile NPCs or worm segments. The grant is computed the same way on every
	/// side from synced positions (no packet); the server's positions win as usual (D2). D1: one int per NPC, no allocation.
	/// </summary>
	public sealed class NPCHaste : GlobalNPC
	{
		public const float Factor = 1.5f;

		private int ticks;

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

		public static bool IsHasted(NPC npc) => npc.TryGetGlobalNPC(out NPCHaste haste) && haste.ticks > 0;

		/// <summary><see cref="Factor"/> while hasted, else 1: for <see cref="CogpunkSets.SelfHasting"/> NPCs.</summary>
		public static float FactorOf(NPC npc) => IsHasted(npc) ? Factor : 1f;

		public override void PostAI(NPC npc) {
			if (ticks <= 0) {
				return;
			}
			ticks--;
			if (CogpunkSets.SelfHasting[npc.type]) {
				return;
			}
			float k = Factor - 1f;
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
