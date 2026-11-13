using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>
	/// Koi (Carpa Koi), a fish caught only in Coghaven's pond (user, 2026-11-12; <see cref="KoiFishing"/>). A material like
	/// vanilla's fish (decompiled <c>Item.SetDefaults</c> 2290-2321: common max stack, a sell value by rarity), anchored on
	/// the Damselfish it replaces there (vanilla's uncommon sky catch, 2304: 30 silver, Blue); a step rarer (Green) since
	/// one pond in the world holds it. Cooks into Cooked Fish at a Cooking Pot, as vanilla's fish do.
	/// </summary>
	public class Koi : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;                // vanilla's fish
		}

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 24;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(silver: 30);
			Item.rare = ItemRarityID.Green;
		}

		public override void ModifyResearchSorting(ref ContentSamples.CreativeHelper.ItemGroup itemGroup) {
			itemGroup = ContentSamples.CreativeHelper.ItemGroup.Fish;
		}

		public override void AddRecipes() {
			Recipe.Create(ItemID.CookedFish)
				.AddIngredient(Type)
				.AddTile(TileID.CookingPots)
				.Register();
		}
	}
}
