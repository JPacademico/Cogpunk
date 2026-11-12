using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.OldBrassTown.Accessories
{
	/// <summary>
	/// The <see cref="RedCloth"/>'s recharge: while it lasts (<see cref="RedCloth.RechargeTicks"/>, from the last dodge) the
	/// cloth dodges nothing. A debuff the Nurse can't take off and the player can't cancel; not saved (a recharge cut short by
	/// leaving the world is harmless). D2: the dodging player adds it on their own client; vanilla syncs buffs.
	/// </summary>
	public class RedClothCooldown : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;
		}
	}
}
