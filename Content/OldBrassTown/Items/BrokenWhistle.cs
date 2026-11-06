using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.OldBrassTown.Items
{
	/// <summary>
	/// The Broken Whistle (user-set 2026-11-04): a train conductor's brass whistle, cracked, found in the locked
	/// <see cref="Tiles.BrassStrongboxTile"/> in Old Brass Town's bank vault. A material: with 10 Tarnished Brass Bars at a
	/// Demon or Crimson Altar it becomes the <see cref="Bosses.CursedConductor.Items.CursedWhistle"/> that calls the Cursed
	/// Conductor. Art: art/oldbrasstown/make_revolver_art.py.
	/// </summary>
	public class BrokenWhistle : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Orange;
		}
	}
}
