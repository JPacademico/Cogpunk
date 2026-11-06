using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Core.Systems
{
	/// <summary>
	/// Recipe groups for vanilla ore-bar pairs that vanilla doesn't provide (it only has IronBar: use RecipeGroupID.IronBar).
	/// Each group is registered under the first item's internal name, as ExampleMod recommends, so every mod
	/// that defines the same group merges into one instead of creating duplicates.
	/// Use in recipes: <c>.AddRecipeGroup(VanillaRecipeGroups.CopperBar)</c>.
	/// </summary>
	public sealed class VanillaRecipeGroups : ModSystem
	{
		/// <summary>Copper Bar or Tin Bar.</summary>
		public const string CopperBar = nameof(ItemID.CopperBar);

		/// <summary>Gold Bar or Platinum Bar.</summary>
		public const string GoldBar = nameof(ItemID.GoldBar);
		/// <summary>The Musket or The Undertaker (the evil biomes' twin guns: a Crimson world has no Musket).</summary>
		public const string Musket = nameof(ItemID.Musket);

		public override void AddRecipeGroups() {
			// "LegacyMisc.37" is the game's own localized word for "Any".
			RecipeGroup.RegisterGroup(CopperBar, new RecipeGroup(
				() => $"{Language.GetTextValue("LegacyMisc.37")} {Lang.GetItemNameValue(ItemID.CopperBar)}",
				ItemID.CopperBar, ItemID.TinBar));
			RecipeGroup.RegisterGroup(GoldBar, new RecipeGroup(
				() => $"{Language.GetTextValue("LegacyMisc.37")} {Lang.GetItemNameValue(ItemID.GoldBar)}",
				ItemID.GoldBar, ItemID.PlatinumBar));
			RecipeGroup.RegisterGroup(Musket, new RecipeGroup(
				() => $"{Language.GetTextValue("LegacyMisc.37")} {Lang.GetItemNameValue(ItemID.Musket)}",
				ItemID.Musket, ItemID.TheUndertaker));
		}
	}
}
