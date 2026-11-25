using Terraria;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;
using Terraria.UI;

namespace Cogpunk.Content.Equipment
{
	/// <summary>
	/// Cogpunk's own extra accessory slot (user, 2026-11-25: "add a cogpunk stylized aditional accessory slot for players on our
	/// mod. it should be locked for now but in future updates we will add a way to unlock it"): a tModLoader
	/// <c>ModAccessorySlot</c> (functional, vanity and dye, under vanilla's), drawn in brass and rivets
	/// (art/equipment/make_slot_art.py). While locked it shows a padlock, takes no item (<see cref="CanAcceptItem"/>) and gives
	/// nothing (<see cref="IsEnabled"/>); hovering it says so. Unlocking is a saved flag on the character
	/// (<see cref="CogpunkSlotPlayer.Unlocked"/>) for the update that adds a way to earn it.
	/// <para>D2: tModLoader syncs and saves the slot's items itself; the lock is the character's, the same on every side (it can
	/// only be false for now). D0: a locked slot can't hold anything, so nothing can be lost in it.</para>
	/// </summary>
	public sealed class CogpunkAccessorySlot : ModAccessorySlot
	{
		private const string Folder = "Cogpunk/Content/Equipment/";

		private bool Unlocked => Player != null && Player.active && Player.GetModPlayer<CogpunkSlotPlayer>().Unlocked;

		public override bool IsEnabled() => Unlocked;

		/// <summary>Shown even while locked (tModLoader hides a disabled slot unless it holds something).</summary>
		public override bool IsVisibleWhenNotEnabled() => true;

		public override bool CanAcceptItem(Item checkItem, AccessorySlotType context) =>
			Unlocked && base.CanAcceptItem(checkItem, context);

		public override string FunctionalBackgroundTexture => Folder + "CogpunkSlot_Back";
		public override string VanityBackgroundTexture => Folder + "CogpunkSlot_BackVanity";
		public override string DyeBackgroundTexture => Folder + "CogpunkSlot_BackDye";
		public override string FunctionalTexture => Folder + (Unlocked ? "CogpunkSlot_Cog" : "CogpunkSlot_Lock");
		public override string VanityTexture => Folder + (Unlocked ? "CogpunkSlot_Cog" : "CogpunkSlot_Lock");
		public override string DyeTexture => Folder + (Unlocked ? "CogpunkSlot_Cog" : "CogpunkSlot_Lock");

		public override void OnMouseHover(AccessorySlotType context) {
			Main.hoverItemName = Language.GetTextValue(Unlocked ? "Mods.Cogpunk.Equipment.SlotName" : "Mods.Cogpunk.Equipment.SlotLocked");
		}
	}

	/// <summary>Whether the character has unlocked the Cogpunk slot (saved by name; nothing unlocks it yet).</summary>
	public sealed class CogpunkSlotPlayer : ModPlayer
	{
		public bool Unlocked;

		public override void Initialize() {
			Unlocked = false;
		}

		public override void SaveData(TagCompound tag) {
			if (Unlocked) {
				tag["CogpunkSlot"] = true;
			}
		}

		public override void LoadData(TagCompound tag) {
			Unlocked = tag.GetBool("CogpunkSlot");
		}

		public override void CopyClientState(ModPlayer targetCopy) {
			((CogpunkSlotPlayer)targetCopy).Unlocked = Unlocked;
		}
	}
}
