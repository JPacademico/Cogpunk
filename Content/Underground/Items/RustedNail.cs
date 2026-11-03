using Cogpunk.Content.Bosses.TrashTr0m.Buffs;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Underground.Items
{
	/// <summary>
	/// Rusted Nail (user-set 2026-11-03): an accessory found in underground chests (<see cref="Generation.RustedNailPass"/>,
	/// <see cref="ChestChance"/>% of the underground Wooden and Gold Chests). An enemy that touches the wearer takes
	/// <see cref="ThornDamage"/> damage, like a thorns effect, and gets Tetanus for <see cref="TetanusTicks"/> ticks
	/// (+<see cref="TetanusDebuff.DamageTakenPercent"/>% damage taken, the Tetanus lance's debuff). It is vanilla's Cactus
	/// armor thorns made an accessory: a flat 30 in Expert (decompiled 1.4.4 <c>Player.Update</c> NPC collision:
	/// <c>cactusThorns</c> deal 15 / 30 / 45 by mode through <c>ApplyDamageToNPC</c>, knockback 10, before the hit lands).
	/// The rules live in <see cref="RustedNailPlayer"/>. Not a Scrappy Trunk trinket: it has its own chest rate (SKILL §3.3).
	/// Balance: docs/balance/accessories.csv.
	/// </summary>
	public class RustedNail : CogpunkItem
	{
		public const int ThornDamage = 30;              // user-set; player-side, not mode-scaled (D3 rule 0)
		public const float ThornKnockback = 10f;        // vanilla's thorns
		public const int TetanusTicks = 180;            // 3 s a touch
		public const int ChestChance = 10;              // percent of the underground Wooden and Gold Chests

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(ThornDamage, TetanusDebuff.DamageTakenPercent, TetanusTicks / 60f);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 32;
			Item.height = 32;
			Item.accessory = true;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Green;
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetModPlayer<RustedNailPlayer>().Nail = true;
		}
	}
}
