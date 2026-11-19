using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Pets
{
	/// <summary>
	/// Jade Token (Ficha de Jade) (user-set 2026-11-18: "on the top chest of the main mansion on coghaven add a new pet item that
	/// allways spawn there called "jade token" it should give the player a small jade colored spirit fox ... that emits a bit
	/// of light"): a jade coin with a fox's head on a gilt rim. Summons <see cref="JadeFoxPet"/>; always in the Main Hall's
	/// gallery chest (<see cref="Generation.CoghavenChests"/>). A vanity pet (the fox's light is its own touch, not a light
	/// pet's: my call). Set up like <see cref="Scrap.Pets.Scrappybot"/>.
	/// </summary>
	public class JadeToken : CogpunkItem
	{
		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.DefaultToVanitypet(ModContent.ProjectileType<JadeFoxPet>(), ModContent.BuffType<JadeFoxBuff>());
			Item.width = 28;
			Item.height = 28;
			Item.rare = ItemRarityID.Orange;
			Item.value = Item.sellPrice(gold: 2);
		}

		public override bool? UseItem(Player player) {
			if (player.whoAmI == Main.myPlayer) {
				player.AddBuff(Item.buffType, 3600);
			}
			return true;
		}

		// Vanilla would spawn the pet here with a raw Projectile.NewProjectile; the buff spawns it through SafeSpawn instead (D0).
		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			return false;
		}
	}
}
