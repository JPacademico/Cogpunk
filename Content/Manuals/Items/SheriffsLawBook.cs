using Microsoft.Xna.Framework;
using Terraria.ID;

namespace Cogpunk.Content.Manuals.Items
{
	/// <summary>The Sheriff's Law Book (user-set 2026-11-17), the Cursed Conductor's crafting manual: its first defeat in a world leaves one for every
	/// player who fought (<see cref="ManualDrop"/>). See <see cref="CraftingManual"/>. Art: art/manuals/make_manuals_art.py.</summary>
	public class SheriffsLawBook : CraftingManual
	{
		protected override Vector3 GlowLight => new(0.95f, 0.78f, 0.35f);

		protected override int SparkDust => DustID.GoldFlame;

		protected override int Rarity => ItemRarityID.Orange;
	}
}
