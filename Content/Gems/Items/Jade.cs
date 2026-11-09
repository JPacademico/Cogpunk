using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Items
{
	/// <summary>
	/// Jade (Jade), a gem (user-set 2026-11-09: "a new gem that can be mined underground (same behaviour and spawn as other
	/// default gems from terraria ex: amethyst emerald) called jade, and add the default gem crafts for it (gem robe, phase
	/// saber, big gem); chests on coghaven contain some jades and jade golems drop it (1-2, 25% chance)"). Mined from
	/// <see cref="Tiles.JadeTile"/> in the caverns (placed like vanilla's gems: <see cref="Generation.JadeGemPass"/>), found in
	/// Coghaven's chests, dropped by the Jade Golem. Crafts the <see cref="JadeRobe"/>, the <see cref="JadePhaseblade"/> (and
	/// its <see cref="JadePhasesaber"/>) and the <see cref="LargeJade"/>; the user will add jade's own recipes later.
	/// <para>As vanilla's Emerald (decompiled 1.4.4 <c>Item.SetDefaults</c> 179: value 7500, a stack of 9999, drawn at alpha
	/// 50; jade sits at the Emerald's rarity in the world too). Vanilla's gems can also be set on walls and floors as
	/// decorations (the Exposed Gems tile, one style per vanilla gem); jade isn't, for now.</para>
	/// </summary>
	public class Jade : CogpunkItem
	{
		public const int Value = 7500;                    // the Emerald's

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 15;               // vanilla gems'
		}

		public override void SetDefaults() {
			Item.width = 14;
			Item.height = 14;
			Item.maxStack = Item.CommonMaxStack;
			Item.value = Value;
			Item.alpha = 50;                              // vanilla's gems sparkle slightly see-through in the world
		}
	}
}
