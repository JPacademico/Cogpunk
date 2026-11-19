using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Bosses.Jadey.Buffs
{
	/// <summary>
	/// A jade statue (the <see cref="Items.JadeShaperPendant"/>'s save, 2026-11-17): for its
	/// <see cref="Items.JadeShaperPendant.StatueTicks"/> the player can't move or act, takes no damage, and is still knocked back
	/// (<see cref="JadeShaperPlayer"/>). A debuff the player can't cancel and the Nurse can't take off; not saved. D2: added on the
	/// saved player's own client; vanilla syncs buffs, so every client draws the statue.
	/// </summary>
	public class JadeStatue : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;
		}
	}
}
