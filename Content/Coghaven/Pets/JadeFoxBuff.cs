using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;

namespace Cogpunk.Content.Coghaven.Pets
{
	/// <summary>The <see cref="JadeToken"/>'s pet buff: keeps the <see cref="JadeFoxPet"/> out (vanilla's pet rule, through
	/// SafeSpawn, as <see cref="Scrap.Pets.ScrappybotBuff"/>).</summary>
	public class JadeFoxBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoTimeDisplay[Type] = true;
			Main.vanityPet[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			player.buffTime[buffIndex] = 18000;
			int petType = ModContent.ProjectileType<JadeFoxPet>();
			if (player.whoAmI == Main.myPlayer && player.ownedProjectileCounts[petType] <= 0) {
				SafeSpawn.TryNewProjectile(player.GetSource_Buff(buffIndex), player.Center, Vector2.Zero, petType, 0, 0f, out _, player.whoAmI);
			}
		}
	}
}
