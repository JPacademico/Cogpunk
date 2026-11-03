using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>Minion buff for <see cref="TarSlimeMinion"/>: stays while at least one tar slime is out (ExampleSimpleMinionBuff pattern).</summary>
	public class TarSlimeBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoSave[Type] = true;
			Main.buffNoTimeDisplay[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			if (player.ownedProjectileCounts[ModContent.ProjectileType<TarSlimeMinion>()] > 0) {
				player.buffTime[buffIndex] = 18000;
			}
			else {
				player.DelBuff(buffIndex);
				buffIndex--;
			}
		}
	}
}
