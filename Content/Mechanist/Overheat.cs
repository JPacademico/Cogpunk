using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// Overheat (user-set 2026-10-27): firing a Mechanist weapon without enough steam vents the boiler. No item can be used
	/// (vanilla's Cursed lock, <c>player.noItems</c>) and the player can't stop moving (<see cref="SteamPlayer.SetControls"/>)
	/// until the steam tank has refilled completely. The buff only mirrors <see cref="SteamPlayer.Overheated"/>: the owner
	/// clears it the tick the tank is full, so its long timer never runs out on its own. It shows to every client (vanilla
	/// syncs player buffs), which draws the steam hissing out of the player.
	/// </summary>
	public class Overheat : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			Main.buffNoTimeDisplay[Type] = true;            // it lasts until the tank is full, not for a time
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			SteamPlayer steam = player.GetModPlayer<SteamPlayer>();
			if (player.whoAmI == Main.myPlayer && !steam.Overheated) {
				player.DelBuff(buffIndex);                     // stale copy (the state is the owner's): drop it
				buffIndex--;
				return;
			}
			player.noItems = true;
			steam.OverheatEffects();
		}
	}
}
