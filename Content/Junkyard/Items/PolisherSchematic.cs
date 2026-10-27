using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Junkyard.Items
{
	/// <summary>
	/// Polisher Schematic: a grease-stained blueprint found in the Junkyard Cache. The <see cref="RustPolisher"/> recipe
	/// needs it at an anvil but never uses it up (a blueprint, not a part), so one schematic builds a polisher for everyone.
	/// </summary>
	public class PolisherSchematic : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 32;
			Item.height = 28;
			Item.maxStack = 1;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Green;
		}
	}
}
