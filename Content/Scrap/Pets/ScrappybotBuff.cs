using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Pets
{
	public class ScrappybotBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoTimeDisplay[Type] = true;
			Main.vanityPet[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			player.buffTime[buffIndex] = 18000;

			// Same rule as vanilla's BuffHandle_SpawnPetIfNeeded, but through SafeSpawn. If the projectile array
			// is nearly full the spawn is refused and simply retried next tick.
			int petType = ModContent.ProjectileType<ScrappybotPet>();
			if (player.whoAmI == Main.myPlayer && player.ownedProjectileCounts[petType] <= 0) {
				SafeSpawn.TryNewProjectile(player.GetSource_Buff(buffIndex), player.Center, Vector2.Zero, petType, 0, 0f, out _, player.whoAmI);
			}
		}
	}
}
