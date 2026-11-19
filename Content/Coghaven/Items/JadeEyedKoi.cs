using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Coghaven.Items
{
	/// <summary>
	/// Jade-eyed Koi (Carpa de Olhos de Jade), a treasure (user-set 2026-11-17: "inside the chest that jadey guards there should
	/// be basic sky loot and a jade-eyed koi a valuable item that can be sold for 2 platinum coins"): a koi cast in gold with
	/// jade eyes and crimson lacquer patches, one in each world's Jade Vault (<see cref="Generation.CoghavenChests"/>). Worth
	/// <c>sellPrice(platinum: 2)</c> at any merchant; nothing else (a valuable, like vanilla's gems).
	/// Art: art/coghaven/make_koi_art.py.
	/// </summary>
	public class JadeEyedKoi : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 24;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(platinum: 2);      // user-set
			Item.rare = ItemRarityID.Yellow;
		}
	}
}
