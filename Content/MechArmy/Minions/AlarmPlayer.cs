using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Minions
{
	/// <summary>
	/// The Alarm Head's bonus (user-set 2026-10-28): +<see cref="MoveSpeedPerAlarm"/>% movement speed and
	/// +<see cref="AttackSpeedPerAlarm"/>% attack speed (all classes) for each friendly Alarmobô within
	/// <see cref="NPCs.AnnoyOTron.AlarmRange"/> of the player, whoever owns it; several stack.
	/// <para>Every <see cref="AlarmoboMinion"/> calls <see cref="Hear"/> for the local player when it is in range (its AI,
	/// which vanilla runs after the players each tick); the count is read on the next tick in
	/// <see cref="PostUpdateEquips"/>, where speed bonuses belong (before vanilla turns moveSpeed into run speed). The count
	/// is keyed by the tick, so a missed tick simply reads 0 (D0: nothing can pile up).</para>
	/// <para>D2: movement and attack speed are the owning client's business (it moves its own player and times its own
	/// swings), and every client simulates the minions from their synced positions, so nothing is sent. D1: two ints.</para>
	/// </summary>
	public sealed class AlarmPlayer : ModPlayer
	{
		public const int MoveSpeedPerAlarm = 20;       // percent
		public const int AttackSpeedPerAlarm = 10;     // percent

		private uint heardTick;
		private int heardCount;

		/// <summary>Alarmobôs in range as of the last projectile update (0 if none called in the last tick).</summary>
		public int Alarms => Main.GameUpdateCount - heardTick <= 1 ? heardCount : 0;

		/// <summary>An Alarmobô is within range of this player this tick.</summary>
		public void Hear() {
			uint now = Main.GameUpdateCount;
			if (heardTick != now) {
				heardTick = now;
				heardCount = 0;
			}
			heardCount++;
		}

		public override void PostUpdateEquips() {
			int alarms = Alarms;
			if (alarms <= 0) {
				return;
			}
			Player.moveSpeed += alarms * MoveSpeedPerAlarm / 100f;
			Player.GetAttackSpeed(DamageClass.Generic) += alarms * AttackSpeedPerAlarm / 100f;
		}
	}
}
