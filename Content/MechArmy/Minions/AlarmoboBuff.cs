using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.MechArmy.Minions
{
	/// <summary>Minion buff for <see cref="AlarmoboMinion"/>: stays while at least one is out (ExampleSimpleMinionBuff
	/// pattern). Its tooltip shows the bonus the owner gets right now from every Alarmobô in range (<see cref="AlarmPlayer"/>).</summary>
	public class AlarmoboBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoSave[Type] = true;
			Main.buffNoTimeDisplay[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			if (player.ownedProjectileCounts[ModContent.ProjectileType<AlarmoboMinion>()] > 0) {
				player.buffTime[buffIndex] = 18000;
			}
			else {
				player.DelBuff(buffIndex);
				buffIndex--;
			}
		}

		public override void ModifyBuffText(ref string buffName, ref string tip, ref int rare) {
			int alarms = Main.LocalPlayer.GetModPlayer<AlarmPlayer>().Alarms;
			tip = Description.Format(alarms, alarms * AlarmPlayer.MoveSpeedPerAlarm, alarms * AlarmPlayer.AttackSpeedPerAlarm);
		}
	}
}
