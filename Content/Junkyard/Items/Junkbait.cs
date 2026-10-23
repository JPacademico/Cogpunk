using Cogpunk.Content.Scrap.Items;
using Cogpunk.Content.Scrap.Pets;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Items
{
	/// <summary>
	/// Junkbait: a ball of scrap glazed in grease, with a Scrappybot rattling inside as the bait. The summon item of the
	/// Junkyard's boss, which isn't in the mod yet: until it is, <see cref="CanUseItem"/> refuses every use, so the item is
	/// never consumed for nothing. It already sorts, researches and is set up (hold-up use, consumable, stack of 20) like a
	/// boss summon (ExampleMod 1.4.4 <c>MinionBossSummonItem</c>), so the boss only has to add <c>UseItem</c>.
	/// <para>Recipe (anvil): <see cref="Scrappybot"/> + <see cref="ScrapCost"/> <see cref="RustedScrap"/> +
	/// <see cref="BarCost"/> Copper (or Tin) Bars.</para>
	/// </summary>
	public class Junkbait : CogpunkItem
	{
		public const int ScrapCost = 10;
		public const int BarCost = 10;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;
			ItemID.Sets.SortingPriorityBossSpawns[Type] = 3;   // early boss: with Worm Food and Bloody Spine
		}

		public override void SetDefaults() {
			Item.width = 32;
			Item.height = 32;
			Item.maxStack = 20;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Blue;
			Item.useAnimation = 30;
			Item.useTime = 30;
			Item.useStyle = ItemUseStyleID.HoldUp;
			Item.consumable = true;
		}

		public override void ModifyResearchSorting(ref ContentSamples.CreativeHelper.ItemGroup itemGroup) {
			itemGroup = ContentSamples.CreativeHelper.ItemGroup.BossSpawners;
		}

		// No boss to summon yet: refusing the use keeps the item from being consumed.
		public override bool CanUseItem(Player player) {
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<Scrappybot>()
				.AddIngredient<RustedScrap>(ScrapCost)
				.AddRecipeGroup(VanillaRecipeGroups.CopperBar, BarCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
