using Cogpunk.Core.Templates;
using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Buffs
{
	/// <summary>Freshly freed from jade: the curse can't take hold again yet (<see cref="JadeCurseNPC.WardTicks"/>).</summary>
	public class JadeWard : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
		}
	}
}
