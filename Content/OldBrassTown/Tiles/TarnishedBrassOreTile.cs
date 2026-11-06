using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Tiles
{
	/// <summary>
	/// Tarnished Brass Ore (2026-11-03): brass nuggets ringed with verdigris, in veins through Old Brass Town's sandstone.
	/// Needs a Nightmare or Deathbringer Pickaxe (<see cref="PickaxePower"/>; user, 2026-11-05: "only mined with a demonite
	/// pickaxe": the Nightmare Pickaxe's 65%, the Deathbringer's 70%, decompiled Item.SetDefaults 103 and 798) and ignores explosives like other
	/// gated ores. Ore set (Metal Detector, spelunker glow) like ExampleMod 1.4.4's <c>ExampleOre</c>.
	/// </summary>
	public class TarnishedBrassOreTile : CogpunkTile
	{
		public const int PickaxePower = 65;            // user-set 2026-11-05: the Nightmare Pickaxe's power (Deathbringer 70%)

		public override void SetStaticDefaults() {
			TileID.Sets.GeneralPlacementTiles[Type] = false;   // later world-gen features (micro biomes, other mods) keep off the town
			TileID.Sets.Ore[Type] = true;
			Main.tileSpelunker[Type] = true;
			Main.tileOreFinderPriority[Type] = 420;     // between gold (400) and platinum (450)
			Main.tileShine2[Type] = true;
			Main.tileShine[Type] = 975;
			Main.tileSolid[Type] = true;
			Main.tileBlockLight[Type] = true;
			MinPick = PickaxePower;
			MineResist = 2f;
			DustType = DustID.Gold;
			HitSound = SoundID.Tink;
			AddMapEntry(new Color(214, 170, 72), CreateMapEntryName());
			RegisterItemDrop(ModContent.ItemType<Items.TarnishedBrassOre>());
		}

		public override bool CanExplode(int i, int j) => false;
	}
}
