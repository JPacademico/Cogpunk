using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Furniture
{
	/// <summary>
	/// Buff stations last until death (user, 2026-11-12: "rework terraria buff stations so on our mod the buff they give
	/// lasts until the player dies instead of the basic 10 minutes"). Vanilla's stations (decompiled
	/// <c>Player.TileInteractionsUse</c>): the Crystal Ball (Clairvoyance), Bewitching Table (Bewitched), Sharpening Station
	/// (Sharpened), Ammo Box (Ammo Box) and War Table (War Table) give 108000 ticks (30 minutes, not 10), the Slice of Cake
	/// Sugar Rush for 7200 (2 minutes); Cogpunk's <see cref="Mechanist.Stations.SteamInjection"/> joins them.
	/// <para>How: vanilla's own <c>BuffID.Sets.TimeLeftDoesNotDecrease</c> (decompiled <c>Player.UpdateBuffs</c>: the local
	/// player's buff time only counts down when it is false), plus <c>Main.buffNoTimeDisplay</c> so the icon shows no clock.
	/// Death ends them: vanilla clears every buff that isn't <c>Main.persistentBuff</c> when a player dies (decompiled
	/// <c>Player.UpdateDead</c>), and none of these is. A station clicked again just refreshes the buff (vanilla
	/// <c>AddBuff</c>). Saved with the player as before, so a buff still running when they log out is there when they come
	/// back, until they die. Right-clicking the icon still cancels it, as for any buff.</para>
	/// <para>Checked: nothing else in vanilla gives these six buffs (each comes from its station's tile only), so no timed
	/// source turns permanent by accident. D2: buff time only ever counted down on the owner (that same line), and the buff
	/// list syncs as before. D0: set once at load from fixed ids; vanilla's arrays get their old values back in
	/// <see cref="Unload"/>.</para>
	/// </summary>
	public sealed class BuffStationRules : ModSystem
	{
		/// <summary>Vanilla's station buffs (BuffID 29, 150, 159, 93, 348, 192).</summary>
		public static readonly int[] VanillaStationBuffs = {
			BuffID.Clairvoyance, BuffID.Bewitched, BuffID.Sharpened, BuffID.AmmoBox, BuffID.WarTable, BuffID.SugarRush,
		};

		private static readonly bool[] savedNoDecrease = new bool[VanillaStationBuffs.Length];
		private static readonly bool[] savedNoTime = new bool[VanillaStationBuffs.Length];
		private static bool applied;

		public override void PostSetupContent() {
			for (int k = 0; k < VanillaStationBuffs.Length; k++) {
				int type = VanillaStationBuffs[k];
				savedNoDecrease[k] = BuffID.Sets.TimeLeftDoesNotDecrease[type];
				savedNoTime[k] = Main.buffNoTimeDisplay[type];
				MakeUntilDeath(type);
			}
			applied = true;
		}

		public override void Unload() {
			if (!applied) {
				return;
			}
			for (int k = 0; k < VanillaStationBuffs.Length; k++) {
				int type = VanillaStationBuffs[k];
				if (type < BuffID.Sets.TimeLeftDoesNotDecrease.Length) {
					BuffID.Sets.TimeLeftDoesNotDecrease[type] = savedNoDecrease[k];
				}
				if (type < Main.buffNoTimeDisplay.Length) {
					Main.buffNoTimeDisplay[type] = savedNoTime[k];
				}
			}
			applied = false;
		}

		/// <summary>A buff that never counts down and shows no clock: it lasts until the player dies.</summary>
		public static void MakeUntilDeath(int type) {
			if (type <= 0 || type >= BuffID.Sets.TimeLeftDoesNotDecrease.Length || type >= Main.buffNoTimeDisplay.Length) {
				return;
			}
			BuffID.Sets.TimeLeftDoesNotDecrease[type] = true;
			Main.buffNoTimeDisplay[type] = true;
		}
	}
}
