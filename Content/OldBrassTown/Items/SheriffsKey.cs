using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>
	/// The Sheriff's Key (user-set 2026-11-04): found in Old Brass Town's single buried cache, it opens the locked
	/// <see cref="Tiles.BrassStrongboxTile"/> in the bank vault and is used up (ExampleMod 1.4.4's <c>ExampleChestKey</c>:
	/// a clone of the Golden Key's defaults).
	/// </summary>
	public class SheriffsKey : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.CloneDefaults(ItemID.GoldenKey);
		}
	}
}
