using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Buffs
{
	/// <summary>
	/// The <see cref="Weapons.IncenseMace"/>'s blessing (user-set 2026-11-18: "+10% damage and attackspeed for 35 seconds"):
	/// <see cref="Weapons.IncenseMace.DamageBonus"/> damage and <see cref="Weapons.IncenseMace.SpeedBonus"/> attack speed, every
	/// class. Set by each player's own client (<see cref="Weapons.IncenseAura"/>). A wisp of incense now and then (clients).
	/// </summary>
	public class IncenseBlessing : CogpunkBuff
	{
		public override LocalizedText Description => base.Description.WithFormatArgs((int)System.Math.Round(Weapons.IncenseMace.DamageBonus * 100f),
			(int)System.Math.Round(Weapons.IncenseMace.SpeedBonus * 100f));

		public override void Update(Player player, ref int buffIndex) {
			player.GetDamage(DamageClass.Generic) += Weapons.IncenseMace.DamageBonus;
			player.GetAttackSpeed(DamageClass.Generic) += Weapons.IncenseMace.SpeedBonus;
			if (!Main.dedServ && Main.rand.NextBool(40) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(player.position + new Vector2(0f, 10f), player.width, player.height - 10, DustID.Smoke, out Dust d, 0f, -0.5f,
					140, new Color(214, 206, 236))) {
				d.noGravity = true;
				d.scale = 0.7f;
			}
		}
	}
}
