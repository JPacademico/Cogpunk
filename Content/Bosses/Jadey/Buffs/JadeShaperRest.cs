using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Bosses.Jadey.Buffs
{
	/// <summary>
	/// The <see cref="Items.JadeShaperPendant"/>'s recharge (user-set 2026-11-17: "cooldown of 3 minutes"): while it lasts the
	/// pendant saves nobody. A debuff the player can't cancel and the Nurse can't take off; it is saved with the player and
	/// survives death (<c>Main.persistentBuff</c>: vanilla clears every other buff on death, decompiled <c>Player.UpdateDead</c>),
	/// so dying or leaving the world doesn't recharge it early.
	/// </summary>
	public class JadeShaperRest : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.persistentBuff[Type] = true;
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;
		}
	}
}
