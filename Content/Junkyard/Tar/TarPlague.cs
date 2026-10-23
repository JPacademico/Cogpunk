using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// Tar Plague: the Junkyard's steaming tar eats through you. While it lasts the player loses
	/// <see cref="TarPlayer.TickDamage"/> life every <see cref="TarPlayer.TickInterval"/> ticks (20 every half second,
	/// 40 per second), regenerates nothing and moves at <see cref="MoveSpeedMultiplier"/> speed. Contact with the tar
	/// keeps it at <see cref="TarPlayer.LingerTicks"/>, so it wears off shortly after climbing out.
	/// <para>It is the Junkyard pool's progression barrier: a later item lets players dive by granting immunity the vanilla
	/// way, <c>player.buffImmune[ModContent.BuffType&lt;TarPlague&gt;()] = true</c> in its equip update.</para>
	/// </summary>
	public class TarPlague : CogpunkBuff
	{
		public const float MoveSpeedMultiplier = 0.5f;   // same slow as vanilla's Slow debuff (decompiled Player.Update: moveSpeed /= 2)

		public override void SetStaticDefaults() {
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			Main.pvpBuff[Type] = false;
			BuffID.Sets.NurseCannotRemoveDebuff[Type] = true;   // it comes from the environment and returns at once anyway
			// The duration is only the linger after leaving the tar; Expert/Master stretching it (DebuffTimeMultiplier) would
			// turn a dip into a death sentence, so it stays the same in every mode.
			BuffID.Sets.LongerExpertDebuff[Type] = false;
		}

		public override void Update(Player player, ref int buffIndex) {
			player.GetModPlayer<TarPlayer>().Plagued = true;
			player.moveSpeed *= MoveSpeedMultiplier;
		}
	}
}
