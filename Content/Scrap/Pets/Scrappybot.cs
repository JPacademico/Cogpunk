using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Pets
{
	/// <summary>Ultra rare (1%) Extractinator find from Rusted Scrap: the robot, folded up. Summons <see cref="ScrappybotPet"/>.</summary>
	public class Scrappybot : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToVanitypet(ModContent.ProjectileType<ScrappybotPet>(), ModContent.BuffType<ScrappybotBuff>());
			Item.width = 24;
			Item.height = 26;
			Item.rare = ItemRarityID.Orange;
			Item.value = Item.sellPrice(gold: 2);
		}

		public override bool? UseItem(Player player) {
			if (player.whoAmI == Main.myPlayer) {
				player.AddBuff(Item.buffType, 3600);
			}
			return true;
		}

		// Vanilla would spawn the pet here with a raw Projectile.NewProjectile, which overwrites the oldest
		// projectile when the array is full. The buff spawns it through SafeSpawn instead (D0).
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			return false;
		}
	}
}
