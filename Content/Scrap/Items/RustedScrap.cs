using Cogpunk.Content.Scrap.Pets;
using Cogpunk.Content.Scrap.Tiles;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Items
{
	/// <summary>Placeable block of compacted junk. Its main use is the Extractinator.</summary>
	public class RustedScrap : CogpunkItem
	{
		// Extractinator table (out of 100): 1 Scrappybot, 33 Rusted Metal, 66 Rusted Cog. Materials drop in random
		// stacks of MinStack-MaxStack (average 2.5); the pet always drops alone.
		public const int PetChance = 1;
		public const int MetalChance = 33;
		public const int MinStack = 1;
		public const int MaxStack = 4;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 100;
			ItemID.Sets.ExtractinatorMode[Type] = Type;
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<RustedScrapTile>());
			Item.width = 16;
			Item.height = 16;
			Item.value = Item.sellPrice(copper: 5);
		}

		// Runs on the client using the Extractinator, after vanilla rolled its own result; vanilla then spawns
		// and syncs the item (decompiled Player.ExtractinatorUse / DropItemFromExtractinator).
		public override void ExtractinatorUse(int extractinatorBlockType, ref int resultType, ref int resultStack) {
			int roll = Main.rand.Next(100);
			if (roll < PetChance) {
				resultType = ModContent.ItemType<Scrappybot>();
				resultStack = 1;
				return;
			}
			resultType = roll < PetChance + MetalChance ? ModContent.ItemType<RustedMetal>() : ModContent.ItemType<RustedCog>();
			resultStack = Main.rand.Next(MinStack, MaxStack + 1);   // Next(min, max) excludes max: 1-4
		}
	}
}
