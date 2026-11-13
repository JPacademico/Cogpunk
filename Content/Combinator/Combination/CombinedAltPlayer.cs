using Cogpunk.Core.Safety;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>
	/// A combination's right click is its base's when the base has one (user-set 2026-11-12: "the right mouse attack should be
	/// taken from the base but if the base does not have a right mouse attack it should take from the augment"). The product is
	/// the augment's type, so its own right click is the augment's (vanilla's alternate use runs on the held item's type and
	/// <c>ModItem</c>); for the base's, the owner swaps a <b>stand-in</b> into the held slot for exactly that use: an item of
	/// the base's own type carrying the combined stats (<see cref="CombinationRules.ApplyStats"/> with the base's attack) and
	/// marked with the product it stands for. Vanilla then runs the base's own alternate use, its projectile, animation and
	/// every hook keyed on its type, and the product goes back in the slot the tick the use is over. A right-click skill that
	/// isn't an item use (the Metal Wrench's parry) needs no swap: its own code accepts a product whose base it is
	/// (<see cref="Core.Combat.RightClickOwner"/>).
	/// <para>When: just before the item check (<see cref="PreItemCheck"/>), on the same right click vanilla would start an
	/// alternate use with (decompiled <c>Player.ItemCheck_ManageRightClickFeatures</c>: right held, left released, no tile or
	/// NPC interaction, not over the UI), with nothing in use; back in <see cref="PostItemCheck"/> once nothing is in use and
	/// nothing is channelled. A use the base refuses (no rounds, no steam) swaps back the same tick.</para>
	/// <para>No weapon can be lost or doubled (D0): the stand-in is favorited (vanilla never throws, sells or quick-stacks a
	/// favorited item); the product goes back before a death drops the inventory (<see cref="PreKill"/>) and before the player
	/// is saved (<see cref="PreSavePlayer"/>); if the stand-in ever left the slot it is found and replaced, or made air and the
	/// product given back; a stand-in found anywhere else (a save from a crash, the world) turns back into its product or
	/// disappears (it is only ever a copy). D2: the owner's inventory; vanilla syncs the slot both ways like any swap, and
	/// other clients draw the base's use with the combined look (the stand-in's synced augment type).</para>
	/// </summary>
	public sealed class CombinedAltPlayer : ModPlayer
	{
		public const int ScanInterval = 60;

		private Item product;
		private Item standIn;
		private int slot = -1;
		internal static bool LoadedStandIn;                 // a stand-in came out of a save: scan for it now

		public bool Swapped => standIn != null;

		public override bool PreItemCheck() {
			if (Player.whoAmI != Main.myPlayer || Swapped) {
				return true;
			}
			bool rightClick = Player.controlUseTile && !Player.tileInteractionHappened && Player.releaseUseItem && !Player.controlUseItem
				&& !Player.mouseInterface && !Main.HoveringOverAnNPC && !Main.SmartInteractShowingGenuine;
			if (!rightClick || Player.itemAnimation > 0 || Player.itemTime > 0 || Player.noItems || Player.CCed || Player.dead) {
				return true;
			}
			int s = Player.selectedItem;
			if (s < 0 || s >= 58) {
				return true;                                  // 58 is the item on the mouse: left alone
			}
			Item held = Player.inventory[s];
			if (!CombinedWeapon.TryGet(held, out CombinedWeapon data) || !data.IsProduct
				|| data.Base.ModItem is Core.Combat.IRightClickSkill || !ItemLoader.AltFunctionUse(data.Base, Player)) {
				return true;
			}
			Item proxy = data.Base.Clone();                   // the base as it went in: its own modded data runs its right click
			proxy.prefix = 0;                                 // the base's reforge is ignored (the product's goes on below)
			if (!proxy.TryGetGlobalItem(out CombinedWeapon standInData)) {
				return true;
			}
			standInData.MakeStandIn(held.type, held);
			standInData.Recompute(proxy);
			if (held.prefix > 0 && proxy.CanApplyPrefix(held.prefix)) {
				proxy.Prefix(held.prefix);                    // the product's own reforge, where the base's type can take it
			}
			proxy.favorited = true;
			MarkReplaced(proxy, held);
			product = held;
			standIn = proxy;
			slot = s;
			Player.inventory[s] = proxy;
			return true;
		}

		/// <summary>
		/// D2: vanilla resyncs a slot only when its item's type, stack, prefix or <c>NetStateVersion</c> differs from what it
		/// last sent (decompiled <c>Main.TrySyncingMyPlayer</c>, <c>Item.IsNetStateDifferent</c>). A product and its stand-in
		/// can share all three (a weapon combined with its own kind), so the item taking the slot gets a version of its own.
		/// </summary>
		internal static void MarkReplaced(Item now, Item was) {
			if (now != null && was != null && now.NetStateVersion == was.NetStateVersion) {
				now.NetStateChanged();
			}
		}

		public override void PostItemCheck() {
			if (Player.whoAmI != Main.myPlayer || !Swapped) {
				return;
			}
			if (Player.ItemAnimationActive || Player.itemTime > 0 || Player.channel) {
				return;                                       // the base's right click is still going
			}
			SwapBack();
		}

		/// <summary>Puts the product back where the stand-in is (normally the held slot).</summary>
		public void SwapBack() {
			if (!Swapped) {
				return;
			}
			Item p = product, s = standIn;
			int at = slot;
			product = standIn = null;
			slot = -1;
			if (p == null || p.IsAir) {
				return;
			}
			MarkReplaced(p, s);
			if (at >= 0 && at < Player.inventory.Length && ReferenceEquals(Player.inventory[at], s)) {
				Player.inventory[at] = p;
				return;
			}
			for (int k = 0; k < Player.inventory.Length; k++) {
				if (ReferenceEquals(Player.inventory[k], s)) {
					Player.inventory[k] = p;
					return;
				}
			}
			if (ReferenceEquals(Main.mouseItem, s)) {
				Main.mouseItem = p;
				return;
			}
			s?.TurnToAir();                                   // wherever it went, it is only a copy
			SafeSpawn.TryGiveToLocalPlayer(Player, p, "CombinatorReturn");
		}

		/// <summary>The world-item guard (<see cref="CombinedWeapon.Update"/>) took this stand-in back: forget it.</summary>
		internal void Forget(Item item) {
			if (ReferenceEquals(item, standIn)) {
				product = standIn = null;
				slot = -1;
			}
		}

		public override bool PreKill(double damage, int hitDirection, bool pvp, ref bool playSound, ref bool genDust, ref PlayerDeathReason damageSource) {
			if (Player.whoAmI == Main.myPlayer) {
				SwapBack();
			}
			return true;
		}

		public override void PreSavePlayer() {
			SwapBack();
		}

		public override void OnEnterWorld() {
			LoadedStandIn = true;
		}

		/// <summary>Every <see cref="ScanInterval"/> ticks (and after a load), any stand-in that isn't the one in use turns back
		/// into its product, or into air when it has none. 59 slots and the mouse; no allocation.</summary>
		public override void PostUpdate() {
			if (Player.whoAmI != Main.myPlayer || (!LoadedStandIn && Main.GameUpdateCount % ScanInterval != 0)) {
				return;
			}
			LoadedStandIn = false;
			for (int k = 0; k < Player.inventory.Length; k++) {
				Item it = Player.inventory[k];
				if (!ReferenceEquals(it, standIn) && CombinedWeapon.TryGet(it, out CombinedWeapon d) && d.IsStandIn) {
					Item back = d.ProxyOf != null && !d.ProxyOf.IsAir ? d.ProxyOf : new Item();
					MarkReplaced(back, it);
					Player.inventory[k] = back;
				}
			}
			if (!ReferenceEquals(Main.mouseItem, standIn) && CombinedWeapon.TryGet(Main.mouseItem, out CombinedWeapon m) && m.IsStandIn) {
				Item back = m.ProxyOf != null && !m.ProxyOf.IsAir ? m.ProxyOf : new Item();
				MarkReplaced(back, Main.mouseItem);
				Main.mouseItem = back;
			}
		}

		/// <summary>Server or singleplayer: a stand-in lying in the world. In singleplayer its product is known: it takes the
		/// stand-in's place (and the owner forgets the swap); anywhere else it disappears (the owner keeps the product).</summary>
		internal static void RestoreWorldItem(Item item, Item productOf) {
			int i = item.whoAmI;
			if (i < 0 || i >= Main.maxItems || !ReferenceEquals(Main.item[i], item)) {
				return;
			}
			if (Main.netMode == NetmodeID.SinglePlayer && productOf != null && !productOf.IsAir) {
				Main.LocalPlayer.GetModPlayer<CombinedAltPlayer>().Forget(item);
				Item p = productOf;
				p.position = item.position;
				p.velocity = item.velocity;
				p.whoAmI = i;
				p.active = true;
				p.favorited = false;
				Main.item[i] = p;
				return;
			}
			item.TurnToAir();
			item.active = false;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncItem, number: i);
			}
		}
	}
}
