using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Items
{
	/// <summary>
	/// Jade Incense (Incenso de Jade), Jadey's summon (user, 2026-11-17: "add a boss summon for friendo-bot to sell after
	/// defeating Jadey. Make this a rule for every boss that we add"): a stick of jade-green incense in a little gilt burner.
	/// Burnt inside a Jade Vault's hall it calls her back for another fight (<see cref="JadeySummon.RequestByItem"/>: the vault
	/// she guards is her arena, so the incense works only there); used up, like vanilla's summons. The Friendo-bot sells it
	/// once she has been defeated (<see cref="Town.Friendobo.AddShops"/>), at its own value; it has no recipe (my call: the
	/// vault itself calls her the first time).
	/// <para>D2: the use plays on every client; only the user's own client asks (a packet the server validates, as the vault's
	/// touch does). D0: the vault search is bounded (<see cref="JadeySummon.FindVault"/>). Art: art/bosses/jadey/make_jadey_loot_art.py.</para>
	/// </summary>
	public class JadeIncense : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 3;
			ItemID.Sets.SortingPriorityBossSpawns[Type] = 12;
		}

		public override void SetDefaults() {
			Item.width = 24;
			Item.height = 32;
			Item.maxStack = 20;
			Item.value = Item.sellPrice(silver: 60);
			Item.rare = ItemRarityID.Orange;
			Item.useAnimation = 45;
			Item.useTime = 45;
			Item.useStyle = ItemUseStyleID.HoldUp;
			Item.consumable = true;
		}

		public override void ModifyResearchSorting(ref ContentSamples.CreativeHelper.ItemGroup itemGroup) {
			itemGroup = ContentSamples.CreativeHelper.ItemGroup.BossSpawners;
		}

		/// <summary>Only in a vault's hall, and only while she isn't here.</summary>
		public override bool CanUseItem(Player player) {
			return !NPC.AnyNPCs(ModContent.NPCType<Jadey>()) && JadeySummon.FindVault(player, out _, out _);
		}

		public override bool? UseItem(Player player) {
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item20 with { Pitch = -0.3f, Volume = 0.7f }, player.Center);
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 12; i++) {
						if (SafeSpawn.TryNewDust(player.Top + new Vector2(player.direction * 6f, -6f), 0, 0, DustID.GemEmerald, out Dust d)) {
							d.velocity = new Vector2(Main.rand.NextFloat(-0.6f, 0.6f), -Main.rand.NextFloat(1f, 2.5f));
							d.noGravity = true;
						}
					}
				}
			}
			if (player.whoAmI == Main.myPlayer && JadeySummon.FindVault(player, out int left, out int top)) {
				JadeySummon.RequestByItem(player, left, top);
			}
			return true;
		}
	}
}
