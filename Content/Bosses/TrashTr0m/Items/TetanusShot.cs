using Cogpunk.Content.Bosses.TrashTr0m.Buffs;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Items
{
	/// <summary>
	/// Tetanus Shot (Vacina Antitetânica) (user-set 2026-11-18: "Verify if there's already an accessory that gives tetanus
	/// immunity, if there's not add it being the "tetanus shot" that can be unlocked on a node named "causes autism" costing one
	/// knowledge point and being crafted using glass + rusted metal"; there was none): an accessory, a glass syringe of green
	/// serum with a brass plunger; it makes its wearer immune to <see cref="TetanusDebuff"/> (which the machines of the Mech Army,
	/// Westworld and the Junkyard give on touch since 2026-11-18). Recipe (the amounts and the station are my calls):
	/// <see cref="GlassCost"/> Glass and <see cref="MetalCost"/> Rusted Metal at a Work Bench, locked until the research node
	/// "Causes Autism" (<see cref="Research.ResearchNodes.CausesAutism"/>, <see cref="Research.ResearchRecipes"/>).
	/// Art: art/research/make_research_art.py.
	/// </summary>
	public class TetanusShot : CogpunkItem
	{
		public const int GlassCost = 8, MetalCost = 5;    // Rusted Metal 4 -> 5, x1.2 rounded (user, 2026-11-26: "increase the amount of rusted cog and rusted metal used in any craft that uses them for 20% (rounded)")

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 24;
			Item.height = 24;
			Item.accessory = true;
			Item.rare = ItemRarityID.Blue;
			Item.value = Item.sellPrice(silver: 40);
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			int tetanus = ModContent.BuffType<TetanusDebuff>();
			if (tetanus > 0 && tetanus < player.buffImmune.Length) {
				player.buffImmune[tetanus] = true;
			}
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.Glass, GlassCost)
				.AddIngredient<RustedMetal>(MetalCost)
				.AddTile(TileID.WorkBenches)
				.Register();
		}
	}
}
