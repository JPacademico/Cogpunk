using Microsoft.Xna.Framework;
using Terraria.ID;

namespace Cogpunk.Content.Manuals.Items
{
	/// <summary>The Jade-shaper Manual (user-set 2026-11-17), Jadey's crafting manual: its first defeat in a world leaves one for every
	/// player who fought (<see cref="ManualDrop"/>). See <see cref="CraftingManual"/>. Art: art/manuals/make_manuals_art.py.</summary>
	public class JadeShaperManual : CraftingManual
	{
		protected override Vector3 GlowLight => new(0.30f, 0.85f, 0.55f);

		protected override int SparkDust => DustID.GemEmerald;

		protected override int Rarity => ItemRarityID.Orange;
	}
}
