using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Junkyard.Items
{
	/// <summary>Condensed Tar (user-set 2026-10-30): <see cref="TarDropsPerBrick"/> Tar Drops boiled down at a Solidifier into
	/// one hard, glossy brick. A material: with Polished Metal it will make weapons (the user names them in a later update).
	/// Art: art/junkyard/make_junkyard_loot.py.</summary>
	public class CondensedTar : CogpunkItem
	{
		public const int TarDropsPerBrick = 4;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 25;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 22;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(copper: 10 * TarDropsPerBrick);   // what its Tar Drops sell for
			Item.rare = ItemRarityID.Blue;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<TarDrop>(TarDropsPerBrick)
				.AddTile(TileID.Solidifier)
				.Register();
		}
	}
}
