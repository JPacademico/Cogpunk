using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor
{
	/// <summary>
	/// How long each player has been alive (user, 2026-11-05: the Conductor's trains target "only players that are on the
	/// fight, so it does not consider a player that is on another area or just respawned"): the boss counts a player as a
	/// fighter only after <see cref="CursedConductor.RespawnGraceTicks"/> alive (<see cref="CursedConductor.IsFighter"/>).
	/// <para>D2: counted on every side from the synced <c>dead</c> flag (vanilla updates every player on the server too),
	/// so the server's choice of target needs no packet. D1: one int.</para>
	/// </summary>
	public sealed class ConductorFightPlayer : ModPlayer
	{
		public const int Cap = 1 << 20;

		public int AliveTicks { get; private set; }

		public override void PostUpdate() {
			AliveTicks = Player.dead ? 0 : (AliveTicks < Cap ? AliveTicks + 1 : Cap);
		}

		public override void OnRespawn() {
			AliveTicks = 0;
		}
	}
}
