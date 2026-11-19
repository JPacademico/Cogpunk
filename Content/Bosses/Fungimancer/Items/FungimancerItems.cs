using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Fungimancer.Items
{
	/// <summary>
	/// The Fungimancer's treasure bag (Expert and Master only, D3 rule 0: <c>ItemDropRule.BossBag</c>). Its contents (my calls,
	/// a placeholder until the user designs the Fungimancer's loot): glowing mushrooms, mushroom grass seeds and its coins; the
	/// Fungi Manual comes apart from it (<see cref="Manuals.ManualDrop"/>, one per player on the first defeat).
	/// </summary>
	public class FungimancerBag : CogpunkItem
	{
		public const int MinMushrooms = 25, MaxMushrooms = 40, MinSeeds = 5, MaxSeeds = 10;

		public override void SetStaticDefaults() {
			ItemID.Sets.BossBag[Type] = true;
			Item.ResearchUnlockCount = 3;
		}

		public override void SetDefaults() {
			Item.maxStack = Item.CommonMaxStack;
			Item.consumable = true;
			Item.width = 32;
			Item.height = 32;
			Item.rare = ItemRarityID.Purple;
			Item.expert = true;
		}

		public override bool CanRightClick() => true;

		public override void ModifyItemLoot(ItemLoot itemLoot) {
			AddContents(itemLoot);
			itemLoot.Add(ItemDropRule.CoinsBasedOnNPCValue(ModContent.NPCType<Fungimancer>()));
		}

		/// <summary>The bag's contents (also the Classic drop, under a NotExpert rule).</summary>
		public static void AddContents(ILoot loot) {
			loot.Add(ItemDropRule.Common(ItemID.GlowingMushroom, 1, MinMushrooms, MaxMushrooms));
			loot.Add(ItemDropRule.Common(ItemID.MushroomGrassSeeds, 1, MinSeeds, MaxSeeds));
		}

		public static void AddContents(LeadingConditionRule classic) {
			classic.OnSuccess(ItemDropRule.Common(ItemID.GlowingMushroom, 1, MinMushrooms, MaxMushrooms));
			classic.OnSuccess(ItemDropRule.Common(ItemID.MushroomGrassSeeds, 1, MinSeeds, MaxSeeds));
		}
	}

	/// <summary>
	/// Rainbow Mushroom (Cogumelo Arco-íris), the Fungimancer's summon (the boss rule, user 2026-11-17: the Friendo-bot sells
	/// every boss's summon once it has been defeated): eaten in the glowing mushroom biome, it calls the Fungimancer (vanilla's
	/// boss call: <c>NPC.SpawnOnPlayer</c>, or the server's license message from a client). Used up. Never dropped by the tile.
	/// </summary>
	public class RainbowMushroom : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;
			ItemID.Sets.SortingPriorityBossSpawns[Type] = 12;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.maxStack = 20;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Yellow;
			Item.useAnimation = 30;
			Item.useTime = 30;
			Item.useStyle = ItemUseStyleID.HoldUp;
			Item.consumable = true;
		}

		public override void ModifyResearchSorting(ref ContentSamples.CreativeHelper.ItemGroup itemGroup) {
			itemGroup = ContentSamples.CreativeHelper.ItemGroup.BossSpawners;
		}

		public override bool CanUseItem(Player player) => player.ZoneGlowshroom && !NPC.AnyNPCs(ModContent.NPCType<Fungimancer>());

		public override bool? UseItem(Player player) {
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item2 with { Pitch = 0.2f }, player.Center);
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 12; i++) {
						if (SafeSpawn.TryNewDust(player.Top, 0, 0, DustID.RainbowMk2, out Dust d)) {
							d.velocity = Main.rand.NextVector2Circular(2f, 2f) - Vector2.UnitY;
							d.noGravity = true;
							d.color = Main.hslToRgb(Main.rand.NextFloat(), 1f, 0.6f);
						}
					}
				}
			}
			if (player.whoAmI == Main.myPlayer) {
				int type = ModContent.NPCType<Fungimancer>();
				if (Main.netMode != NetmodeID.MultiplayerClient) {
					NPC.SpawnOnPlayer(player.whoAmI, type);
				}
				else {
					NetMessage.SendData(MessageID.SpawnBossUseLicenseStartEvent, number: player.whoAmI, number2: type);
				}
			}
			return true;
		}
	}
}
