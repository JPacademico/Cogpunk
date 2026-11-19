using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;

namespace Cogpunk.Content.Bosses.Jadey.Buffs
{
	/// <summary>
	/// The <see cref="Weapons.IncenseMace"/>'s censer rekindling (user-set 2026-11-18: "30 seconds cooldown"): its right click
	/// waits for this to end. A debuff the player can't cancel and the Nurse can't take off; saved with the player and kept
	/// through death (<c>Main.persistentBuff</c>), so dying doesn't relight the censer early.
	/// </summary>
	public class IncenseBurntOut : CogpunkBuff
	{
		public override LocalizedText Description => base.Description.WithFormatArgs(Weapons.IncenseMace.CooldownTicks / 60);

		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.persistentBuff[Type] = true;
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;
		}
	}
}
