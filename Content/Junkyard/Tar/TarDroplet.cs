using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// A drop of tar hanging from a ceiling over the Junkyard tar, then falling and splashing. Behaves exactly like vanilla's
	/// water drip (ExampleMod 1.4.4 <c>ExampleDroplet</c>): 15 frames of 18x20, 0-4 forming, 5-9 falling, 10-14 splash.
	/// </summary>
	public class TarDroplet : ModGore
	{
		public override void SetStaticDefaults() {
			ChildSafety.SafeGore[Type] = true;
			GoreID.Sets.LiquidDroplet[Type] = true;
			UpdateType = GoreID.WaterDrip;
		}
	}
}
