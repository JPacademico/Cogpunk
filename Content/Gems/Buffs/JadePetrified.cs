using Cogpunk.Core.Templates;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Buffs
{
	/// <summary>Turned to jade (<see cref="JadeCurseNPC"/>): frozen, harmless, still hurt and killed.</summary>
	public class JadePetrified : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
		}
	}
}
