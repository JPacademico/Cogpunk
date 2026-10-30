using Cogpunk.Core.Safety;
using Terraria;
using Terraria.GameContent.Events;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Events
{
	/// <summary>
	/// Runs every <see cref="CogpunkInvasion"/> on the server (or in singleplayer), around vanilla's own invasion code
	/// (decompiled <c>Main.DoUpdateInWorld</c>: <c>UpdateTime</c> -> <c>PostUpdateTime</c> -> <c>WorldGen.UpdateWorld</c> ->
	/// <c>UpdateInvasion</c> -> <c>PostUpdateInvasions</c>, server and singleplayer only from <c>UpdateInvasion</c> on).
	/// <list type="bullet">
	/// <item><b>The dawn roll</b> (<see cref="PostUpdateTime"/>): vanilla rolls its goblin and pirate invasions inside
	/// <c>UpdateTime_StartDay</c>, skipped when lunar events or lanterns are up (<c>ShouldNormalEventsBeAbleToStart</c>),
	/// when an Eclipse starts that morning, or during the Old One's Army. A dawn is seen here as night -> day since the last
	/// tick, so it also catches Journey's time skip (<c>Main.SkipToTime</c>). Each invasion rolls its
	/// <see cref="CogpunkInvasion.NaturalChanceDenominator"/>; one that wins <b>takes priority</b> over vanilla (user,
	/// 2026-10-27: "prioritize Mech army"): a vanilla invasion vanilla started that same dawn is cancelled.</item>
	/// <item><b>Cancelling</b> clears vanilla's <c>invasionType</c>/<c>Size</c> before vanilla's <c>UpdateInvasion</c>
	/// runs, so its first warning (sent from there) is never shown; the world data is resent so clients agree. The same
	/// happens to any vanilla invasion that starts while ours runs (a Martian Probe that escapes; the invasion items are
	/// refused by <see cref="InvasionItemGuard"/>).</item>
	/// <item><b>Update</b> (<see cref="PostUpdateInvasions"/>): each invasion's approach, warnings and end.</item>
	/// </list>
	/// D1: a few field reads per tick; the roll happens once a day.
	/// </summary>
	public sealed class InvasionDirector : ModSystem
	{
		private static bool lastDayTime;
		private static int lastVanillaType;
		private static bool tracking;

		public override void OnWorldLoad() {
			Track();
		}

		public override void OnWorldUnload() {
			tracking = false;
		}

		private static void Track() {
			lastDayTime = Main.dayTime;
			lastVanillaType = Main.invasionType;
			tracking = true;
		}

		public override void PostUpdateTime() {
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}
			if (!tracking) {
				Track();
				return;
			}
			bool dawn = !lastDayTime && Main.dayTime;
			bool vanillaStarted = lastVanillaType == 0 && Main.invasionType != 0;
			if (CogpunkInvasion.AnyActive) {
				if (vanillaStarted) {
					CancelVanilla();
				}
			}
			else if (dawn && lastVanillaType == 0) {
				RollDawn(vanillaStarted);
			}
			lastDayTime = Main.dayTime;
		}

		public override void PostUpdateInvasions() {
			var all = CogpunkInvasion.All;
			for (int i = 0; i < all.Count; i++) {
				all[i].UpdateServer();
			}
			lastDayTime = Main.dayTime;
			lastVanillaType = Main.invasionType;
		}

		private static void RollDawn(bool vanillaStarted) {
			if (Main.ShouldNormalEventsBeAbleToStart() || Main.eclipse || DD2Event.Ongoing || Main.snowMoon || Main.pumpkinMoon) {
				return;
			}
			var all = CogpunkInvasion.All;
			for (int i = 0; i < all.Count; i++) {
				CogpunkInvasion invasion = all[i];
				int chance = invasion.NaturalChanceDenominator;
				if (!invasion.CanHappen || chance <= 0 || Main.rand.Next(chance) != 0) {
					continue;
				}
				if (vanillaStarted) {
					CancelVanilla();
				}
				if (invasion.TryStart()) {
					return;
				}
			}
		}

		/// <summary>Stops a vanilla invasion that has just started, before vanilla's <c>UpdateInvasion</c> announces it.</summary>
		private static void CancelVanilla() {
			SafeLog.Info("Invasion.CancelVanilla", "Cancelled a vanilla invasion that started during or with a Cogpunk invasion (one invasion at a time).");
			Main.invasionType = 0;
			Main.invasionSize = 0;
			Main.invasionSizeStart = 0;
			Main.invasionWarn = 0;
			lastVanillaType = 0;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.WorldData);
			}
		}
	}
}
