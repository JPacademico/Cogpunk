using Microsoft.Xna.Framework;
using Terraria.ID;

namespace Cogpunk.Content.Manuals.Items
{
	/// <summary>The Sticky Pages (user-set 2026-11-17), the Tar Tyrant's crafting manual: its first defeat in a world leaves one for every
	/// player who fought (<see cref="ManualDrop"/>). See <see cref="CraftingManual"/>. Art: art/manuals/make_manuals_art.py.</summary>
	public class StickyPages : CraftingManual
	{
		protected override Vector3 GlowLight => new(0.80f, 0.55f, 0.30f);

		protected override int SparkDust => DustID.AmberBolt;

		protected override int Rarity => ItemRarityID.Orange;
	}
}
