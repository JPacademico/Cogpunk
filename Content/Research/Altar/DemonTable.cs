using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ObjectData;

namespace Cogpunk.Content.Research.Altar
{
	/// <summary>
	/// The Demon Table (user, 2026-11-25: "be able to craft a demon table (demon/crimson altar crafting station but without
	/// spreading corruption or scarying npcs) so the player does not need to allways go to the corruption or crimsom biome to
	/// craft something"): a placeable altar to carry home. Its tile counts as a Demon/Crimson Altar for every recipe that needs
	/// one (<see cref="DemonTableTile"/>). Its recipe is unlocked by the research node Unholy Carpentry (a voodoo doll's price,
	/// shown once a Shadow Orb or Crimson Heart has been smashed in the world). Recipe (my call): 15 Ebonstone or Crimstone, 8
	/// Demonite or Crimtane Bars and 5 Rotten Chunks or Vertebrae, at an altar: the evil biome's own stuff, so the trip there is
	/// made once.
	/// </summary>
	public class DemonTable : CogpunkItem
	{
		public const int StoneCost = 15, BarCost = 8, ChunkCost = 5;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<DemonTableTile>());
			Item.width = 40;
			Item.height = 24;
			Item.value = Item.buyPrice(gold: 1);
			Item.rare = ItemRarityID.Blue;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddRecipeGroup(AltarRecipes.EvilStone, StoneCost)
				.AddRecipeGroup(AltarRecipes.EvilBar, BarCost)
				.AddRecipeGroup(AltarRecipes.EvilChunk, ChunkCost)
				.AddTile(TileID.DemonAltar)
				.Register();
		}
	}

	/// <summary>
	/// The Demon Table placed: a 3 x 2 table that counts as a Demon/Crimson Altar for crafting (<c>AdjTiles</c>: vanilla's tile 26,
	/// the same tile for both altars), and as a table for housing. It is none of the evil biome's blocks (no <c>TileID.Sets</c>
	/// corruption or crimson entry, no biome tile count), so it never spreads and never makes townsfolk unhappy; it can't be
	/// smashed like an altar (it is mined like any furniture: no Hardmode ores, no wraiths). A faint ember glow
	/// from its sigil (client-side lighting).
	/// </summary>
	public class DemonTableTile : CogpunkTile
	{
		public const int Width = 3, Height = 2;

		public override void SetStaticDefaults() {
			Main.tileFrameImportant[Type] = true;
			Main.tileNoAttach[Type] = true;
			Main.tileLavaDeath[Type] = false;
			Main.tileLighted[Type] = true;
			Main.tileTable[Type] = true;
			Main.tileSolidTop[Type] = true;
			TileID.Sets.DisableSmartCursor[Type] = true;
			TileID.Sets.IgnoredByNpcStepUp[Type] = true;
			AddToArray(ref TileID.Sets.RoomNeeds.CountsAsTable);
			AdjTiles = new int[] { TileID.DemonAltar };
			DustType = DustID.Demonite;

			TileObjectData.newTile.CopyFrom(TileObjectData.Style3x2);
			TileObjectData.newTile.CoordinateHeights = new[] { 16, 18 };
			TileObjectData.addTile(Type);

			AddMapEntry(new Color(104, 52, 96), CreateMapEntryName());
		}

		public override void NumDust(int i, int j, bool fail, ref int num) {
			num = fail ? 1 : 3;
		}

		public override void ModifyLight(int i, int j, ref float r, ref float g, ref float b) {
			Tile tile = Main.tile[i, j];
			if (tile.TileFrameY == 0 && tile.TileFrameX % 54 == 18) {      // the top middle tile: the sigil's glow
				float pulse = 0.85f + 0.15f * (float)System.Math.Sin(Main.GlobalTimeWrappedHourly * 2.2f);
				r = 0.32f * pulse;
				g = 0.08f * pulse;
				b = 0.22f * pulse;
			}
		}
	}
}
