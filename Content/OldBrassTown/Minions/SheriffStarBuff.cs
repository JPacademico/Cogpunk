using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Minions
{
	/// <summary>Minion buff for <see cref="SheriffStarMinion"/>: stays while at least one star is out (ExampleSimpleMinionBuff
	/// pattern).</summary>
	public class SheriffStarBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoSave[Type] = true;
			Main.buffNoTimeDisplay[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			if (player.ownedProjectileCounts[ModContent.ProjectileType<SheriffStarMinion>()] > 0) {
				player.buffTime[buffIndex] = 18000;
			}
			else {
				player.DelBuff(buffIndex);
				buffIndex--;
			}
		}
	}
}
