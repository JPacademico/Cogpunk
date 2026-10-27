using Cogpunk.Core.Templates;
using Terraria;
using Terraria.Localization;

namespace Cogpunk.Content.Mechanist.Accessories
{
	/// <summary>
	/// Base for the steam containers: accessories that are a Mechanist's steam tank (<see cref="SteamPlayer"/>'s capacity
	/// starts at 0, user-set 2026-10-27). Each adds <see cref="SteamCapacity"/> to the tank. Only one container can be worn
	/// at a time: an upgrade replaces the tank, it doesn't add a second one (vanilla checks both items through
	/// <c>CanAccessoryBeEquippedWith</c>, decompiled <c>ItemLoader</c>).
	/// </summary>
	public abstract class SteamContainer : CogpunkItem
	{
		/// <summary>Steam capacity added while worn.</summary>
		public abstract int SteamCapacity { get; }

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SteamCapacity);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetModPlayer<SteamPlayer>().SteamMaxBonus += SteamCapacity;
		}

		public override bool CanAccessoryBeEquippedWith(Item equippedItem, Item incomingItem, Player player) {
			return !(equippedItem.ModItem is SteamContainer && incomingItem.ModItem is SteamContainer);
		}
	}
}
