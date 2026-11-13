using System.Collections.Generic;
using Cogpunk.Content.Combinator.Combination;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;
using Terraria.UI;

namespace Cogpunk.Content.Combinator.UI
{
	/// <summary>
	/// The Combinator window's three slots belong to the local player (like vanilla's reforge slot, <c>Main.reforgeItem</c>):
	/// <see cref="BaseSlot"/>, <see cref="AugmentSlot"/> and <see cref="ProductSlot"/>. Whatever is in them goes back to the
	/// inventory when the window closes (<see cref="ReturnAll"/>: <c>Player.GetItem</c>, the rest dropped at their feet), and
	/// is saved with the player meanwhile, so a crash or a quit with a weapon in a slot loses nothing: it is handed back on the
	/// next entry into a world (<see cref="OnEnterWorld"/>). Shift-click moves a weapon from the inventory into the first
	/// free input slot (<see cref="ShiftClickSlot"/>).
	/// <para>D2: client-local (the window is the local player's); the inventory changes sync as any inventory change does.
	/// D0: every slot is never null; load reads keys with defaults.</para>
	/// </summary>
	public sealed class CombinatorPlayer : ModPlayer
	{
		public Item BaseSlot = new();
		public Item AugmentSlot = new();
		public Item ProductSlot = new();

		public override void Initialize() {
			BaseSlot = new Item();
			AugmentSlot = new Item();
			ProductSlot = new Item();
		}

		/// <summary>Hands every slot's item back to the player.</summary>
		public void ReturnAll() {
			Return(ref BaseSlot);
			Return(ref AugmentSlot);
			Return(ref ProductSlot);
		}

		private void Return(ref Item slot) {
			if (slot != null && !slot.IsAir) {
				SafeSpawn.TryGiveToLocalPlayer(Player, slot, "CombinatorReturn");
			}
			slot = new Item();
		}

		public override void OnEnterWorld() {
			if (Player.whoAmI == Main.myPlayer) {
				ReturnAll();                                  // left in the window by a quit or a crash
			}
		}

		public override void SaveData(TagCompound tag) {
			var saved = new List<TagCompound>(3);
			foreach (Item item in new[] { BaseSlot, AugmentSlot, ProductSlot }) {
				if (item != null && !item.IsAir) {
					saved.Add(ItemIO.Save(item));
				}
			}
			if (saved.Count > 0) {
				tag["slots"] = saved;
			}
		}

		public override void LoadData(TagCompound tag) {
			BaseSlot = new Item();
			AugmentSlot = new Item();
			ProductSlot = new Item();
			if (!tag.ContainsKey("slots")) {
				return;
			}
			IList<TagCompound> saved = tag.GetList<TagCompound>("slots");
			Item[] into = new Item[3];
			for (int k = 0; k < saved.Count && k < into.Length; k++) {
				into[k] = ItemIO.Load(saved[k]);
			}
			BaseSlot = into[0] ?? new Item();
			AugmentSlot = into[1] ?? new Item();
			ProductSlot = into[2] ?? new Item();          // all handed back in OnEnterWorld
		}

		/// <summary>Shift-click on an inventory weapon while the window is open: into the first free input slot it fits.</summary>
		public override bool ShiftClickSlot(Item[] inventory, int context, int slot) {
			if (!CombinatorUISystem.IsOpen || context != ItemSlot.Context.InventoryItem || inventory == null || slot < 0 || slot >= inventory.Length) {
				return false;
			}
			Item item = inventory[slot];
			if (item == null || item.IsAir || item.favorited || Player.itemAnimation > 0 || Player.itemTime > 0) {
				return false;
			}
			if (CombinationRules.Check(item) != CombinationRefusal.None) {
				return false;
			}
			if (BaseSlot.IsAir) {
				BaseSlot = item;
			}
			else if (AugmentSlot.IsAir) {
				AugmentSlot = item;
			}
			else {
				return false;
			}
			inventory[slot] = new Item();
			SoundEngine.PlaySound(SoundID.Grab);
			return true;
		}

		/// <summary>The shift-click cursor (vanilla's inventory-to-chest arrow) over a weapon the window would take.</summary>
		public override bool HoverSlot(Item[] inventory, int context, int slot) {
			if (CombinatorUISystem.IsOpen && ItemSlot.ShiftInUse && context == ItemSlot.Context.InventoryItem && inventory != null
				&& slot >= 0 && slot < inventory.Length && !inventory[slot].IsAir && !inventory[slot].favorited
				&& CombinationRules.Check(inventory[slot]) == CombinationRefusal.None && (BaseSlot.IsAir || AugmentSlot.IsAir)) {
				Main.cursorOverride = CursorOverrideID.InventoryToChest;
				return true;
			}
			return false;
		}
	}
}
