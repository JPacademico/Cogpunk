using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// The Metal Wrench's parry is cooling down (<see cref="WrenchParry.CooldownTicks"/> ticks from the end of a guard,
	/// user-set 3 s): <see cref="MetalWrenchPlayer"/> won't start a guard while it lasts. A debuff the player can't cancel,
	/// shown with its time like vanilla's Potion Sickness.
	/// </summary>
	public class WrenchParryCooldown : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;
			BuffID.Sets.LongerExpertDebuff[Type] = false;
		}

		public override void ModifyBuffText(ref string buffName, ref string tip, ref int rare) {
			tip = Description.Format(WrenchParry.CooldownTicks / 60f);
		}
	}
}
