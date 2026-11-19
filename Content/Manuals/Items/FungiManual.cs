using Microsoft.Xna.Framework;
using Terraria.ID;

namespace Cogpunk.Content.Manuals.Items
{
	/// <summary>The Fungi Manual (user-set 2026-11-19: "add a "fungi manual" for the fungimancer to drop"), the Fungimancer's
	/// crafting manual: its first defeat in a world leaves one for every player who fought (<see cref="ManualDrop"/>). See
	/// <see cref="CraftingManual"/>. Art: art/manuals/make_manuals_art.py.</summary>
	public class FungiManual : CraftingManual
	{
		protected override Vector3 GlowLight => new(0.25f, 0.45f, 0.95f);

		protected override int SparkDust => DustID.GlowingMushroom;

		protected override int Rarity => ItemRarityID.Yellow;
	}
}
