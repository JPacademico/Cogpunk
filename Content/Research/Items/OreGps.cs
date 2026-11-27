using System.Collections.Generic;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Items
{
	/// <summary>
	/// Ore GPS (user-set 2026-11-27: "unlocked by 'x-ray' ... a utility item that on use prompts the player to chose a ore or
	/// gem (pre-hardmode ores, and using icons for better visibility) then it points (the arrow pointing that the mysterious
	/// map uses) to the nearest clump of the chosen ore or gem (minimum of 6 blocks of the chosen ore or gem to be considered a
	/// clump to be targeted). it should be crafted using 4 rusted cogs and 2 copper bars"): a pocket brass radar dial.
	/// <para>Using it toggles <see cref="OreGpsUISystem"/> (an icon grid of every pre-Hardmode ore and gem). While in the
	/// player's inventory or hand, <see cref="OreGpsArrowLayer"/> draws the Mysterious Map's compass arrow pointing at the
	/// nearest 6+ block vein (<see cref="OreGpsSystem"/>). Recipe unlocked by <see cref="ResearchNodes.XRay"/>.</para>
	/// </summary>
	public class OreGps : CogpunkItem
	{
		public const int CogCost = 4, BarCost = 2;                // user-set: 4 rusted cogs and 2 copper bars
		public const int MinClumpBlocks = 6;                      // user-set: minimum of 6 blocks

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MinClumpBlocks);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 28;
			Item.height = 28;
			Item.maxStack = 1;
			Item.useStyle = ItemUseStyleID.HoldUp;
			Item.useTime = 18;
			Item.useAnimation = 18;
			Item.UseSound = SoundID.MenuTick;
			Item.rare = ItemRarityID.Blue;
			Item.value = Item.sellPrice(silver: 12);
		}

		public override bool? UseItem(Player player) {
			if (player.whoAmI == Main.myPlayer && player.ItemAnimationJustStarted && !Main.dedServ) {
				OreGpsUISystem.Toggle();
			}
			return true;
		}

		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			if (Main.dedServ || Main.gameMenu || Main.LocalPlayer == null) {
				return;
			}
			OreGpsPlayer gps = Main.LocalPlayer.GetModPlayer<OreGpsPlayer>();
			string status;
			Color color;
			if (gps.SelectedIndex < 0 || gps.SelectedIndex >= OreGpsSystem.Targets.Length) {
				status = Language.GetTextValue("Mods.Cogpunk.Items.OreGps.TrackingNone");
				color = new Color(150, 156, 166);
			}
			else {
				string targetName = Lang.GetItemNameValue(OreGpsSystem.Targets[gps.SelectedIndex].ItemType);
				if (gps.HasTarget) {
					status = Language.GetTextValue("Mods.Cogpunk.Items.OreGps.TrackingFound", targetName);
					color = new Color(140, 228, 88);
				}
				else {
					status = Language.GetTextValue("Mods.Cogpunk.Items.OreGps.TrackingMissing", targetName);
					color = new Color(236, 122, 88);
				}
			}
			tooltips.Add(new TooltipLine(Mod, "OreGpsStatus", status) { OverrideColor = color });
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>(CogCost)
				.AddRecipeGroup(VanillaRecipeGroups.CopperBar, BarCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
