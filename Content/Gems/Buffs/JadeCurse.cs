using Cogpunk.Core.Templates;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Buffs
{
	/// <summary>The jade curse's stacks on an enemy (<see cref="JadeCurseNPC"/>): slower attacks, then petrification.</summary>
	public class JadeCurse : CogpunkBuff
	{
		public override LocalizedText Description => base.Description.WithFormatArgs((int)(JadeCurseNPC.SlowPerStack * 100f), JadeCurseNPC.Stacks);

		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
		}
	}
}
