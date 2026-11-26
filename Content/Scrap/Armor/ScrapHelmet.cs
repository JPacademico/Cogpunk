using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Armor
{
	/// <summary>
	/// Scrap armor head: Metal Detector ore detection while worn. Also owns the set bonus: 12% movement speed and, while
	/// moving, a bouncing cog lobbed every 0.75 s at the nearest enemy, or behind the player when none is near
	/// (<see cref="ScrapArmorPlayer"/>).
	/// Balance: docs/balance/armor.csv and weapons.csv. The brass cogs on all three pieces spin through
	/// <see cref="AnimatedEquip"/> (art: art/scrap/make_scrap_armor.py).
	/// </summary>
	[AutoloadEquip(EquipType.Head)]
	public class ScrapHelmet : CogpunkItem
	{
		public const int CogFrames = 4;             // = COG_FRAMES in art/scrap/make_scrap_armor.py
		public const int CogTicksPerFrame = 6;      // one tooth step every 0.1 s
		public const int MoveSpeedBonus = 12;       // percent

		public static LocalizedText SetBonusText { get; private set; }

		public override void Load() {
			AnimatedEquip.Register(this, EquipType.Head, CogFrames, CogTicksPerFrame);
		}

		public override void Unload() {
			SetBonusText = null;
		}

		public override void SetStaticDefaults() {
			SetBonusText = this.GetLocalization("SetBonus").WithFormatArgs(MoveSpeedBonus, ScrapArmorPlayer.CogInterval / 60f,
				ScrapArmorPlayer.CogDamage);
		}

		public override void SetDefaults() {
			Item.width = 26;
			Item.height = 24;
			Item.value = Item.sellPrice(silver: 30);
			Item.rare = ItemRarityID.White;
			Item.defense = 5;
		}

		// Info flags must be set here, not in UpdateEquip: Main.RefreshInfoAccs clears and rescans them while the
		// inventory is open, and it only calls this hook (decompiled Player.RefreshInfoAccsFromItemType). The hook also
		// runs for items lying in the inventory, so only the copy worn in the head slot counts.
		public override void UpdateInfoAccessory(Player player) {
			if (player.armor[0].type == Type) {
				player.accOreFinder = true;             // Metal Detector: shows the most valuable ore nearby
			}
		}

		public override bool IsArmorSet(Item head, Item body, Item legs) {
			return body.type == ModContent.ItemType<ScrapBreastplate>() && legs.type == ModContent.ItemType<ScrapLeggings>();
		}

		public override void UpdateArmorSet(Player player) {
			player.setBonus = SetBonusText.Value;
			player.moveSpeed += MoveSpeedBonus / 100f;
			player.GetModPlayer<ScrapArmorPlayer>().CogVolley = true;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>(6)                           // 5 -> 6, x1.2 (user, 2026-11-26)
				.AddRecipeGroup(VanillaRecipeGroups.GoldBar, 4)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
