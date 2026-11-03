using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// Tar Plague ("tar poisoning"): the Junkyard's steaming tar eats through you. While it lasts the player loses
	/// <see cref="TarPlayer.TickDamage"/> life every <see cref="TarPlayer.TickInterval"/> ticks (10 every half second,
	/// 20 per second; halved from 20 on 2026-11-03, user-set), regenerates nothing and moves at <see cref="MoveSpeedMultiplier"/> speed. Contact with the tar
	/// keeps it at <see cref="TarPlayer.LingerTicks"/>, so it wears off shortly after climbing out.
	/// <para>It is the Junkyard pool's progression barrier: a later item lets players dive by granting immunity the vanilla
	/// way, <c>player.buffImmune[ModContent.BuffType&lt;TarPlague&gt;()] = true</c> in its equip update.</para>
	/// <para>Enemies get it too (2026-10-30: the tar weapons, user-set "20 damage every 0.5 seconds but keep the slow"):
	/// the same tick and half speed, applied by <see cref="TarPlagueNPC"/>. Player weapons coat enemies through
	/// <see cref="InflictOn"/>, which adds the wearer's <see cref="TarPlayer.PlagueBonusTicks"/> (the Tyrant set's +1.5 s,
	/// 2026-11-03).</para>
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

		/// <summary>A player's weapon coats <paramref name="target"/> for <paramref name="ticks"/> plus the player's
		/// <see cref="TarPlayer.PlagueBonusTicks"/>. Called on the owner's client from a hit (vanilla syncs the NPC buff from
		/// <c>NPC.AddBuff</c> there); the bonus field is set the same way on every side, so a stray call elsewhere agrees.</summary>
		public static void InflictOn(NPC target, Player source, int ticks) {
			if (source != null && source.active) {
				ticks += source.GetModPlayer<TarPlayer>().PlagueBonusTicks;
			}
			target.AddBuff(ModContent.BuffType<TarPlague>(), ticks);
		}

		public override void Update(NPC npc, ref int buffIndex) {
			if (npc.TryGetGlobalNPC(out TarPlagueNPC plague)) {
				plague.Plagued = true;
			}
			NPCHaste.ApplySlow(npc, TarPlagueNPC.SlowRefreshTicks);   // refused for bosses and the like: they take the damage only
		}
	}
}
