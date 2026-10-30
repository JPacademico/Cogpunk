using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Armor
{
	/// <summary>Tyrant Sandals (user-set 2026-10-29): <see cref="Defense"/> defense, +<see cref="SpeedBonus"/>% movement speed
	/// and +10% jump height, both doubled while the wearer is out of steam (<see cref="TyrantArmorPlayer.OutOfSteam"/>).
	/// The jump: vanilla holds <c>jumpSpeed</c> (5.01 px/tick, + <c>jumpSpeedBoost</c>) for 15 ticks and then lets gravity
	/// (0.4) stop it, a 98 px (6.1 tile) jump (decompiled <c>Player.UpdateJumpHeight</c> / <c>JumpMovement</c>);
	/// <see cref="JumpSpeedBoost"/> raises it 10%, <see cref="DryJumpSpeedBoost"/> 20% (replayed tick by tick). Set bonus:
	/// <see cref="TyrantSkull"/>.
	/// <para>Berserker look (user, 2026-10-30: "the pants only an underwear and sandals"): a tar loincloth on a belt of
	/// vertebrae and bone-soled sandals; the legs between are the wearer's own skin (vanilla draws it under leg armor:
	/// <c>ArmorIDs.Legs.Sets.HidesBottomSkin</c> is false by default).</para></summary>
	[AutoloadEquip(EquipType.Legs)]
	public class TyrantSandals : CogpunkItem
	{
		public const int Defense = 5;
		public const int SpeedBonus = 10;               // percent; twice that out of steam
		public const float JumpSpeedBoost = 0.36f, DryJumpSpeedBoost = 0.70f;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SpeedBonus);

		public override void SetDefaults() {
			Item.width = 30;
			Item.height = 20;
			Item.value = Item.sellPrice(gold: 1, silver: 20);
			Item.rare = ItemRarityID.Orange;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			bool dry = TyrantArmorPlayer.OutOfSteam(player);
			player.moveSpeed += SpeedBonus * (dry ? 2 : 1) / 100f;
			player.jumpSpeedBoost += dry ? DryJumpSpeedBoost : JumpSpeedBoost;
		}
	}
}
