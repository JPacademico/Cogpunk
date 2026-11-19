using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ObjectData;

namespace Cogpunk.Content.Bosses.Fungimancer.Tiles
{
	/// <summary>
	/// The rainbow mushroom (user-set 2026-11-19): a glowing mushroom whose cap runs through the rainbow, grown very rarely in a
	/// glowing mushroom's place (<see cref="RainbowMushroomGrowth"/>). It glows in turning colours and drops nothing ("does not
	/// drop"); breaking it wakes the <see cref="Fungimancer"/> there (<see cref="FungimancerSystem.SpawnFrom"/>, the server's).
	/// A swing cuts it, as it does the glowing mushroom it replaced. Art: art/bosses/fungimancer/make_fungimancer_art.py.
	/// D1: the light is arithmetic (no allocation); sparkles only near, throttled. D2: the spawn is the server's.
	/// </summary>
	public class RainbowMushroomTile : CogpunkTile
	{
		public const int Styles = 3;

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileCut[Type] = true;
			Main.tileNoFail[Type] = true;
			Main.tileLighted[Type] = true;
			Main.tileObsidianKill[Type] = true;
			TileObjectData.newTile.CopyFrom(TileObjectData.Style1x1);
			TileObjectData.newTile.AnchorValidTiles = new[] { (int)TileID.MushroomGrass };
			TileObjectData.newTile.StyleHorizontal = true;
			TileObjectData.newTile.RandomStyleRange = Styles;
			TileObjectData.newTile.LavaDeath = true;
			TileObjectData.addTile(Type);
			AddMapEntry(new Color(236, 122, 220), CreateMapEntryName());
			HitSound = SoundID.Grass;
			DustType = DustID.GlowingMushroom;
		}

		public override bool CanDrop(int i, int j) => false;

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			float hue = (Main.GlobalTimeWrappedHourly * 0.25f + (i + j) * 0.07f) % 1f;
			Color c = Main.hslToRgb(hue, 1f, 0.6f);
			r = c.R / 255f * 0.6f;
			g = c.G / 255f * 0.6f;
			b = c.B / 255f * 0.6f;
		}

		public override void NearbyEffects(int i, int j, bool closer) {
			if (Main.dedServ || !closer || !Main.rand.NextBool(40) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			if (SafeSpawn.TryNewDust(new Vector2(i * 16, j * 16), 16, 10, DustID.RainbowMk2, out Dust d)) {
				d.noGravity = true;
				d.velocity = new Vector2(0f, -0.6f);
				d.scale = 0.6f;
				d.color = Main.hslToRgb(Main.rand.NextFloat(), 1f, 0.6f);
			}
		}

		public override void KillTile(int i, int j, ref bool fail, ref bool effectOnly, ref bool noItem) {
			if (fail || effectOnly) {
				return;
			}
			noItem = true;
			FungimancerSystem.Remove(i, j);
			FungimancerSystem.SpawnFrom(i, j);                // the server's (it returns at once on a client)
		}
	}
}
