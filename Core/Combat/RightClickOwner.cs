using System;
using Terraria;

namespace Cogpunk.Core.Combat
{
	/// <summary>
	/// Which weapon's right click a held item has. Plain items answer for themselves; a Combinator product (2026-11-12)
	/// answers with its base's type when the base has a right click, else its own. Content/Combinator installs the resolver at
	/// load, so a skill like the Metal Wrench's parry asks here without depending on that slice. D1: one delegate call.
	/// </summary>
	public static class RightClickOwner
	{
		/// <summary>Set by the Combinator's system in <c>Load</c>, cleared in <c>Unload</c>.</summary>
		public static Func<Item, Player, int> Resolver;

		public static int TypeOf(Item item, Player player) {
			if (item == null || item.IsAir) {
				return 0;
			}
			return Resolver?.Invoke(item, player) ?? item.type;
		}
	}
}
