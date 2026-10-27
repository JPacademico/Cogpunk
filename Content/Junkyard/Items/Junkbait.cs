using Cogpunk.Content.Bosses.TrashTr0m;
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
	/// Junkbait: a ball of scrap glazed in grease, with a Scrappybot rattling inside as the bait. Summons Trash-Tr0m, the
	/// Junkyard's boss: usable inside the Junkyard while it isn't alive, it makes it claw its way out of the ground in front
	/// of the player (<see cref="TrashTr0mSummon.RequestFromBait"/>; set up like ExampleMod 1.4.4's
	/// <c>MinionBossSummonItem</c>: the owner asks, the server spawns). <see cref="CanUseItem"/> refuses a use that could
	/// not summon, so the bait is never wasted.
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

		public override bool CanUseItem(Player player) {
			return TrashTr0mSummon.CanUseBait(player);
		}

		public override bool? UseItem(Player player) {
			TrashTr0mSummon.RequestFromBait(player);       // owner only; the server validates and spawns
			return true;
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
