using Microsoft.Xna.Framework;
using Terraria.ID;

namespace Cogpunk.Content.Manuals.Items
{
	/// <summary>The Scrap Manual (user-set 2026-11-17), Trash-Tr0m's crafting manual: its first defeat in a world leaves one for every
	/// player who fought (<see cref="ManualDrop"/>). See <see cref="CraftingManual"/>. Art: art/manuals/make_manuals_art.py.</summary>
	public class ScrapManual : CraftingManual
	{
		protected override Vector3 GlowLight => new(0.85f, 0.50f, 0.25f);

		protected override int SparkDust => DustID.CopperCoin;

		protected override int Rarity => ItemRarityID.Green;
	}
}
