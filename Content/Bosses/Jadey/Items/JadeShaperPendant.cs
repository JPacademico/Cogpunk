using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Items
{
	/// <summary>
	/// Jade-shaper Pendant (Pingente da Molda-Jade), Jadey's Expert item, in her treasure bag only (user-set 2026-11-17: "when
	/// the player would take lethal damage it petrifies into jade for 2.5 seconds instead and becomes immune to damage while
	/// petrified (cooldown of 3 minutes) but still takes knockback (to ensure that fights like the wall of flesh still works,
	/// pushing the player so it is never behind the wall of flesh)"): a carved jade panda on a red cord with a gilt clasp.
	/// The save itself is <see cref="JadeShaperPlayer"/>'s: <see cref="StatueTicks"/> ticks as a jade statue
	/// (<see cref="Buffs.JadeStatue"/>), then <see cref="CooldownTicks"/> ticks of <see cref="Buffs.JadeShaperRest"/>.
	/// <para>Balance: docs/balance/accessories.csv (no vanilla accessory cheats death; its price is the 3-minute recharge and
	/// the 2.5 s spent frozen, unable to heal or flee). Art: art/bosses/jadey/make_jadey_loot_art.py.</para>
	/// </summary>
	public class JadeShaperPendant : CogpunkItem
	{
		public const int StatueTicks = 150;                 // user-set: 2.5 s
		public const int CooldownTicks = 3 * 60 * 60;       // user-set: 3 minutes

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(StatueTicks / 60f, CooldownTicks / 3600);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 24;
			Item.height = 32;
			Item.accessory = true;
			Item.expert = true;
			Item.rare = ItemRarityID.Expert;
			Item.value = Item.sellPrice(gold: 3);
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetModPlayer<JadeShaperPlayer>().Pendant = true;
		}
	}
}
