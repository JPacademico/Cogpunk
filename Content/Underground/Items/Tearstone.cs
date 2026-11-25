using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Underground.Items
{
	/// <summary>
	/// The Tearstone (user, 2026-11-25: "a small chance to drop a accessory called "tearstone" that gives 10 defense when the
	/// player is at full hp"): a ring set with a tear of the Crystal Lizards' crystal; +<see cref="FullHealthDefense"/> defense
	/// while its wearer's life is full. A pre-Hardmode trinket that isn't a boss drop, so Scrappy Trunks can hold it (D3 note in
	/// the cogpunk-dev skill §3.3). Judged in <see cref="TearstonePlayer.PostUpdateEquips"/>, after every piece of gear has
	/// added its life, so another accessory's +life can't make "full" wrong for a tick.
	/// </summary>
	public class Tearstone : CogpunkItem
	{
		public const int FullHealthDefense = 10;                        // user-set

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(FullHealthDefense);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
			CogpunkSets.ScrappyTrunkTrinket[Type] = true;
		}

		public override void SetDefaults() {
			Item.width = 32;
			Item.height = 32;
			Item.accessory = true;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Green;
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetModPlayer<TearstonePlayer>().Wearing = true;
		}
	}

	/// <summary>The Tearstone's bonus, judged after all equipment has updated (every side: the wearer's synced life and gear).</summary>
	public sealed class TearstonePlayer : ModPlayer
	{
		public bool Wearing;

		public override void ResetEffects() {
			Wearing = false;
		}

		public override void PostUpdateEquips() {
			if (Wearing && Player.statLife >= Player.statLifeMax2) {
				Player.statDefense += Tearstone.FullHealthDefense;
			}
		}
	}
}
