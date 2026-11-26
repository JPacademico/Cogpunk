using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Mechanist.Accessories
{
	/// <summary>
	/// Glass Container (user-set 2026-10-27): a small glass steam tank with iron caps, worn as an accessory: +10 steam
	/// capacity. Found in 10% of plain Wooden Chests (<see cref="Generation.GlassContainerPass"/>); upgraded at the Rust
	/// Polisher into the <see cref="BrassContainer"/>.
	/// <para>Not a Scrappy Trunk trinket (SKILL §3.3) on purpose: while it is the only trinket, every trunk would hold
	/// one, far above the user's 10%.</para>
	/// </summary>
	public class GlassContainer : SteamContainer
	{
		public const int Capacity = 15;                // 10, +5 (user, 2026-11-26: "increase amount of max steam that all max steam increasing itens give in 5 points")
		public const int ChestChance = 10;               // percent of plain Wooden Chests

		public override int SteamCapacity => Capacity;

		public override void SetDefaults() {
			Item.width = 20;
			Item.height = 28;
			Item.accessory = true;
			Item.value = Item.sellPrice(silver: 20);
			Item.rare = ItemRarityID.Blue;
		}
	}
}
