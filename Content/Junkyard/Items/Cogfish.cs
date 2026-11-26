using Cogpunk.Content.Junkyard.Tar;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Items
{
	/// <summary>
	/// Cogfish (Peixe-engrenagem), user 2026-11-26: "add a new fish that can be fished on the tar pit called "cogfish" it should be
	/// using in crafting for tar imunity potion". A material fish of oily iron with a cog for a dorsal fin, caught in the
	/// Junkyard's tar (<see cref="CogfishCatch"/>); the <see cref="TarImmunityPotion"/>'s key. Art: art/junkyard/make_cogfish_art.py.
	/// </summary>
	public class Cogfish : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;                       // vanilla's fish
		}

		public override void SetDefaults() {
			Item.width = 26;
			Item.height = 26;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Item.sellPrice(silver: 5);
			Item.rare = ItemRarityID.Blue;
		}
	}

	/// <summary>
	/// The Cogfish's catch: a bobber in the Junkyard's tar (its water, inside the Junkyard: the tar pit; not lava, honey or
	/// shimmer) turns half of the common and uncommon catches that aren't crates or a quest fish into a Cogfish (my call: a
	/// staple of the pit, as vanilla's Obsidifish is of lava). D2: the fishing player's own client decides its catch, as vanilla.
	/// </summary>
	public sealed class CogfishCatch : ModPlayer
	{
		public override void CatchFish(FishingAttempt attempt, ref int itemDrop, ref int npcSpawn, ref AdvancedPopupRequest sonar, ref Vector2 sonarPosition) {
			if (attempt.inLava || attempt.inHoney || attempt.crate || npcSpawn > 0 || (attempt.questFish > 0 && itemDrop == attempt.questFish)) {
				return;
			}
			if (!JunkyardSystem.ContainsTile(new Point(attempt.X, attempt.Y))) {
				return;
			}
			if ((attempt.common || attempt.uncommon) && Main.rand.NextBool(2)) {
				itemDrop = ModContent.ItemType<Cogfish>();
			}
		}
	}

	/// <summary>
	/// Tar Immunity Potion (Poção de Imunidade ao Piche): drunk, <see cref="TarImmunity"/> for <see cref="Minutes"/> minutes (my
	/// call: Obsidian Skin's), the Tar Plague can't take hold: the tar pit can be swum. Crafted from Bottled Water, a
	/// <see cref="Cogfish"/> and <see cref="TarDropCost"/> Tar Drops at a placed bottle or an alchemy table (my calls, vanilla's
	/// potion recipe shape: water, a fish, a reagent).
	/// </summary>
	public class TarImmunityPotion : CogpunkItem
	{
		public const int Minutes = 4;
		public const int TarDropCost = 2;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 20;                      // vanilla's potions
		}

		public override void SetDefaults() {
			Item.width = 20;
			Item.height = 28;
			Item.useStyle = ItemUseStyleID.DrinkLiquid;
			Item.useAnimation = 17;
			Item.useTime = 17;
			Item.useTurn = true;
			Item.UseSound = SoundID.Item3;
			Item.maxStack = Item.CommonMaxStack;
			Item.consumable = true;
			Item.rare = ItemRarityID.Blue;
			Item.value = Item.buyPrice(silver: 2);
			Item.buffType = ModContent.BuffType<TarImmunity>();
			Item.buffTime = Minutes * 60 * 60;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.BottledWater)
				.AddIngredient<Cogfish>()
				.AddIngredient<TarDrop>(TarDropCost)
				.AddTile(TileID.Bottles)
				.Register();
		}
	}

	/// <summary>Tar Immunity: the Tar Plague can't take hold (vanilla's immunity: <c>buffImmune</c>, set before the tar's own
	/// check runs, <see cref="TarPlayer"/>); one already on the player goes the same tick (decompiled <c>Player.UpdateEquips</c>
	/// path: vanilla deletes every buff the player is immune to).</summary>
	public class TarImmunity : CogpunkBuff
	{
		public override string Texture => "Cogpunk/Content/Junkyard/Buffs/TarImmunity";

		public override void Update(Player player, ref int buffIndex) {
			player.buffImmune[ModContent.BuffType<TarPlague>()] = true;
		}
	}
}
