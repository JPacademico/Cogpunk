using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// Steaming Tar: how water looks while the local player is in the Junkyard (<see cref="JunkyardBiome.WaterStyle"/>).
	/// <para>The Calamity approach (its Sulphurous Sea: <c>SulphurousSeaBiome.WaterStyle</c> = <c>SulphuricWater</c>, and
	/// <c>CalamityPlayerLifeRegen</c> hurts players who are under water in the biome): the liquid stays vanilla water,
	/// with water physics, flow and buckets, and the biome swaps how it is drawn and what it does. tModLoader 1.4.4 has no
	/// custom liquids (every liquid array is sized <c>LiquidID.Count</c> = 4), so this is the only liquid that needs no
	/// IL edit. The damage is <see cref="TarPlague"/>, applied by <see cref="TarPlayer"/>; the steam is
	/// <see cref="TarSteamSystem"/>.</para>
	/// <para>Translucency is vanilla's: water draws at <c>LiquidRenderer.DEFAULT_OPACITY[0]</c> = 0.6 (decompiled
	/// <c>DrawNormalLiquids</c>), so the opaque near-black textures read as see-through tar (D4 rule 9: no
	/// semi-transparent pixels). Texture layout (decompiled <c>LiquidRenderer</c>, <c>TileDrawing.DrawPartialLiquid</c>,
	/// <c>WaterfallManager</c>, matching ExampleMod's sizes): water 48x1360 (16 animation frames of 80 px plus the calm
	/// surface strip at y = 1280), <c>_Block</c> 306x16, <c>_Slope</c> 72x16, waterfall 512x40 (16 frames of 32 px).</para>
	/// Client only: tModLoader autoloads water styles on clients only (<c>[Autoload(Side = ModSide.Client)]</c>).
	/// </summary>
	public class TarWaterStyle : ModWaterStyle
	{
		public override int ChooseWaterfallStyle() => ModContent.GetInstance<TarWaterfallStyle>().Slot;

		public override int GetSplashDust() => ModContent.DustType<TarSplash>();

		public override int GetDropletGore() => ModContent.GoreType<TarDroplet>();

		// The tiles seen through the tar are darkened and warmed, as if seen through dirty brown glass.
		public override void LightColorMultiplier(ref float r, ref float g, ref float b) {
			r = 0.62f;
			g = 0.56f;
			b = 0.5f;
		}

		public override Color BiomeHairColor() => new(46, 50, 59);   // Iron 1
	}

	/// <summary>Waterfalls of tar (a pour off a ledge in the Junkyard): same dark ramp as <see cref="TarWaterStyle"/>.</summary>
	public class TarWaterfallStyle : ModWaterfallStyle
	{
	}
}
