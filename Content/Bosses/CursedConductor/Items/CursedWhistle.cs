using Cogpunk.Content.OldBrassTown;
using Cogpunk.Content.OldBrassTown.Items;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Items
{
	/// <summary>
	/// The Cursed Whistle (user-set 2026-11-04: "a Broken Whistle along with 10 brass bars on a demonic altar crafts a cursed
	/// whistle that can be used in the Old Brass Town biome to summon the Cursed Conductor"): blown inside the town, it calls
	/// him (ExampleMod 1.4.4's <c>MinionBossSummonItem</c>: <c>NPC.SpawnOnPlayer</c> in singleplayer, a
	/// <c>SpawnBossUseLicenseStartEvent</c> message from a multiplayer client, which the server answers with the same call).
	/// Used up, like vanilla's summons; once he is beaten Friendobô sells it (every boss's summon is in his shop), so the fight
	/// can be had again. Recipe: a Demon or a Crimson Altar (vanilla's one tile, 26).
	/// Art: art/oldbrasstown/make_revolver_art.py.
	/// </summary>
	public class CursedWhistle : CogpunkItem
	{
		public const int BrassBars = 10;                    // user-set

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;
			ItemID.Sets.SortingPriorityBossSpawns[Type] = 12;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.maxStack = 20;
			Item.value = Item.sellPrice(silver: 50);
			Item.rare = ItemRarityID.Orange;
			Item.useAnimation = 45;
			Item.useTime = 45;
			Item.useStyle = ItemUseStyleID.HoldUp;
			Item.consumable = true;
		}

		public override void ModifyResearchSorting(ref ContentSamples.CreativeHelper.ItemGroup itemGroup) {
			itemGroup = ContentSamples.CreativeHelper.ItemGroup.BossSpawners;
		}

		/// <summary>Only inside Old Brass Town, and only while he isn't already here (the server's own check for the spawn
		/// message is <c>!NPC.AnyNPCs</c> too).</summary>
		public override bool CanUseItem(Player player) {
			return OldBrassTownSystem.Contains(player.Center) && !NPC.AnyNPCs(ModContent.NPCType<CursedConductor>());
		}

		public override bool? UseItem(Player player) {
			if (player.whoAmI == Main.myPlayer) {
				SoundEngine.PlaySound(SoundID.DD2_WyvernScream with { Pitch = 0.6f, Volume = 0.7f }, player.Center);   // a whistle in the dark
				int type = ModContent.NPCType<CursedConductor>();
				if (Main.netMode != NetmodeID.MultiplayerClient) {
					NPC.SpawnOnPlayer(player.whoAmI, type);
				}
				else {
					NetMessage.SendData(MessageID.SpawnBossUseLicenseStartEvent, number: player.whoAmI, number2: type);
				}
			}
			return true;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<BrokenWhistle>()
				.AddIngredient<TarnishedBrassBar>(BrassBars)
				.AddTile(TileID.DemonAltar)
				.Register();
		}
	}
}
