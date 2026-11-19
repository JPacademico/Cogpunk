using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;

namespace Cogpunk.Content.Research.Items
{
	/// <summary>
	/// Ancient Research Book (Livro de Pesquisa Antigo) (user-set 2026-11-18: "every player should start with a "Ancient research
	/// book" a material (ar example on the promt image) that can be used with wood and clay to craft a "ancient reasearch
	/// table""): a gilt-bound tome of red leather, a jade eye on its cover, blue gems and pearls round it, bones in its corners,
	/// a chain hanging off it, violet pages and a ribbon. Every new character has one (<see cref="ResearchPlayer"/>; older ones
	/// get theirs the first time they enter a world). Art: art/research/make_research_art.py.
	/// </summary>
	public class AncientResearchBook : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 28;
			Item.maxStack = 1;
			Item.rare = ItemRarityID.Green;
			Item.value = 0;
		}
	}
}
