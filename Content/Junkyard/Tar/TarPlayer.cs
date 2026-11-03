using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Tar
{
	/// <summary>
	/// The Junkyard's tar hurts: a player whose hitbox is in water inside the Junkyard (all of it is drawn as tar there, see
	/// <see cref="TarWaterStyle"/>) gets <see cref="TarPlague"/>, and the plague deals <see cref="TickDamage"/> every
	/// <see cref="TickInterval"/> ticks, the way vanilla's damage-over-time debuffs do (decompiled
	/// <c>Player.UpdateLifeRegen</c>): life is subtracted on every side with a DoT number, positive regeneration stops, and
	/// only the owner kills the player, which syncs the death and the life total.
	/// <para>D2: the buff is applied by the owning client (player movement and <c>wet</c> are simulated there) and reaches
	/// other clients through vanilla's buff sync; everything else follows from the buff. Lava, honey and shimmer are left
	/// alone. D1: O(1) per tick (a rectangle test and a few flags), allocation-free.</para>
	/// </summary>
	public sealed class TarPlayer : ModPlayer
	{
		public const int TickDamage = 10;              // halved 2026-11-03 (user: "half tar poisoning damage"), was 20
		public const int TickInterval = 30;             // half a second
		public const int LingerTicks = 40;              // a brief dip costs one tick, never two
		private const float TarTintR = 0.48f, TarTintG = 0.45f, TarTintB = 0.42f;
		private const int DripOneIn = 6;

		private static LocalizedText deathMessage;

		/// <summary>Set every tick by <see cref="TarPlague.Update"/>; read by the damage tick and the draw tint.</summary>
		public bool Plagued;

		/// <summary>Extra ticks of Tar Plague this player's hits give enemies (<see cref="TarPlague.InflictOn"/>); gear adds to
		/// it every tick (the Tyrant set: +90) and it resets in <see cref="ResetEffects"/>.</summary>
		public int PlagueBonusTicks;

		private int tickTimer;

		public override void SetStaticDefaults() {
			deathMessage = Mod.GetLocalization("Junkyard.TarDeath");
		}

		public override void Unload() {
			deathMessage = null;
		}

		public override void ResetEffects() {
			Plagued = false;
			PlagueBonusTicks = 0;
		}

		// After the equip updates, so an item's buffImmune[TarPlague] (the future diving gear) is already set and AddBuff
		// refuses the buff. wet is last tick's collision result, like every vanilla wet check at this point.
		public override void PostUpdateMiscEffects() {
			if (Player.whoAmI != Main.myPlayer || Player.dead || Player.ghost) {
				return;
			}
			if (Player.wet && !Player.lavaWet && !Player.honeyWet && !Player.shimmerWet && JunkyardSystem.Contains(Player.Center)) {
				Player.AddBuff(ModContent.BuffType<TarPlague>(), LingerTicks);
			}
		}

		public override void UpdateBadLifeRegen() {
			if (!Plagued || Player.dead) {
				tickTimer = 0;
				return;
			}
			if (Player.lifeRegen > 0) {
				Player.lifeRegen = 0;
			}
			Player.lifeRegenTime = 0;
			if (++tickTimer < TickInterval) {
				return;
			}
			tickTimer = 0;
			Player.statLife -= TickDamage;
			CombatText.NewText(Player.Hitbox, CombatText.LifeRegen, TickDamage, dramatic: false, dot: true);
			if (Player.statLife <= 0 && Player.whoAmI == Main.myPlayer) {
				Player.KillMe(PlayerDeathReason.ByCustomReason(deathMessage.ToNetworkText(Player.name)), 10.0, 0);
			}
		}

		public override void DrawEffects(PlayerDrawSet drawInfo, ref float r, ref float g, ref float b, ref float a, ref bool fullBright) {
			if (!Plagued) {
				return;
			}
			r *= TarTintR;
			g *= TarTintG;
			b *= TarTintB;
			if (drawInfo.shadow == 0f && !Main.gamePaused && Main.rand.NextBool(DripOneIn) && CogpunkClientConfig.RollEffect()) {
				Vector2 at = drawInfo.Position + new Vector2(Main.rand.NextFloat(Player.width), Main.rand.NextFloat(Player.height * 0.7f));
				if (SafeSpawn.TryNewDust(at, 2, 2, ModContent.DustType<TarSplash>(), out Dust drip)) {
					drip.velocity = new Vector2(Player.velocity.X * 0.2f, Main.rand.NextFloat(0.5f, 1.5f));
				}
			}
		}
	}
}
