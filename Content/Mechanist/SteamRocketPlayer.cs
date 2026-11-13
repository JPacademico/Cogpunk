using System;
using System.Collections.Generic;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// Rocket Boots run on steam (user, 2026-11-12: "rework the terraria rocket boots so on our mod it uses steam (2 steam
	/// every 0.1 seconds)"). Only vanilla's Rocket Boots item (<see cref="ItemID.RocketBoots"/>, the only accessory that sets
	/// <c>Player.rocketBoots = 1</c>, decompiled <c>Player.ApplyEquipFunctional</c>); its upgrades (Spectre, Fairy,
	/// Lightning, Frostspark, Terraspark Boots, Hellfire Treads: 2-5) fly as in vanilla. Vanilla's last-equipped rocket boots
	/// win, so a pair of upgrades worn after them takes over.
	/// <para>The tank is the fuel and the limit: vanilla's rocket timer (<c>rocketTime</c>, 7 bursts of 10 ticks, about
	/// 1.2 s; decompiled <c>Player.Update</c>) is kept full while the tank can pay the next <see cref="WindowTicks"/>, and
	/// emptied when it can't, so the boots fly exactly as long as the steam lasts. Every <see cref="WindowTicks"/> ticks of
	/// thrust (0.1 s) cost <see cref="SteamPerWindow"/> steam (<see cref="SteamPlayer.TrySpendFlat"/>: not a weapon, so no
	/// cost multiplier; like an attack it holds the refill, so the tank refills only after landing). An empty tank (or none:
	/// a player's base capacity is 0) means no rocket, with the "No steam tank!" hint when there is no tank at all.</para>
	/// <para>With wings, vanilla adds the boots' remaining bursts to the wings' time once in the air (6 ticks a burst, above
	/// <c>wingTimeMax</c>). That extra flight is the boots' too: while the wings fly on it, the same
	/// <see cref="SteamPerWindow"/> a <see cref="WindowTicks"/>, and it is cut off when the tank runs dry.</para>
	/// <para>Order (decompiled <c>Player.Update</c>): <see cref="PostUpdateRunSpeeds"/> runs just before vanilla's jump,
	/// wing and rocket code, <see cref="PreUpdateMovement"/> just after it. D2: the owner's tank and controls; other clients
	/// see the flight through the synced position, and vanilla's rocket visuals follow <c>rocketFrame</c> as before. D1: a
	/// few field reads a tick. D0: no spawns, no loops.</para>
	/// </summary>
	public sealed class SteamRocketPlayer : ModPlayer
	{
		public const int SteamPerWindow = 2;               // user-set: 2 steam...
		public const int WindowTicks = 6;                  // ...every 0.1 s of thrust
		private const int SteamRocketBoots = 1;            // Player.rocketBoots for the Rocket Boots item (vanilla)

		private int windowLeft;                            // ticks of thrust already paid for
		private float lastWingTime;

		/// <summary>The Rocket Boots are the player's rocket boots this tick (and nothing replaced them).</summary>
		public bool SteamFuelled => Player.rocketBoots == SteamRocketBoots;

		public override void UpdateDead() {
			windowLeft = 0;
		}

		/// <summary>Before vanilla's flight code: the rocket timer follows the tank (no wings), so a burst only starts when
		/// the next window can be paid.</summary>
		public override void PostUpdateRunSpeeds() {
			if (Player.whoAmI != Main.myPlayer || !SteamFuelled || Player.wingsLogic > 0) {
				return;
			}
			SteamPlayer steam = Player.GetModPlayer<SteamPlayer>();
			bool fuelled = windowLeft > 0 || steam.Steam >= SteamPerWindow;
			Player.rocketTime = fuelled ? Player.rocketTimeMax : 0;
			// vanilla's own test for a rocket attempt (decompiled Player.Update), so a plain jump never shows the hint
			bool attempt = Player.controlJump && Player.canRocket && Player.rocketRelease && Player.rocketDelay == 0
				&& !Player.AnyExtraJumpUsable();
			if (!fuelled && attempt && steam.SteamMax < SteamPerWindow) {
				steam.NoteNoTank();                        // no tank at all: the hint, at most once a second
			}
		}

		/// <summary>After vanilla's flight code: pay for the thrust that just happened.</summary>
		public override void PreUpdateMovement() {
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			if (!SteamFuelled) {
				windowLeft = 0;
				lastWingTime = Player.wingTime;
				return;
			}
			SteamPlayer steam = Player.GetModPlayer<SteamPlayer>();
			if (Player.wingsLogic > 0) {
				// flying on the boots' extra wing time (above the wings' own maximum) burns steam the same way
				bool onBoots = lastWingTime > Player.wingTimeMax && Player.wingTime < lastWingTime;
				if (onBoots && !Pay(steam)) {
					Player.wingTime = Math.Min(Player.wingTime, Player.wingTimeMax);
				}
				lastWingTime = Player.wingTime;
				return;
			}
			lastWingTime = Player.wingTime;
			if (!Player.rocketFrame) {
				if (Player.velocity.Y == 0f) {
					windowLeft = 0;                        // landed: a new flight starts a new window
				}
				return;
			}
			if (!Pay(steam)) {
				Player.rocketDelay = 0;                    // out of steam mid-burst: the thrust stops next tick
				Player.rocketTime = 0;
			}
		}

		/// <summary>A tick of rocket flight: the first tick of each window pays <see cref="SteamPerWindow"/>. False when the
		/// tank can't (nothing taken).</summary>
		private bool Pay(SteamPlayer steam) {
			if (windowLeft <= 0) {
				if (!steam.TrySpendFlat(SteamPerWindow)) {
					return false;
				}
				windowLeft = WindowTicks;
			}
			windowLeft--;
			return true;
		}
	}

	/// <summary>The Rocket Boots' tooltip says they burn steam (<see cref="SteamRocketPlayer"/>).</summary>
	public sealed class SteamRocketBootsTooltip : GlobalItem
	{
		private static LocalizedText line;

		public override bool AppliesToEntity(Item entity, bool lateInstantiation) => entity.type == ItemID.RocketBoots;

		public override void SetStaticDefaults() {
			line = Mod.GetLocalization("Mechanist.RocketBootsSteam");
		}

		public override void Unload() {
			line = null;
		}

		public override void ModifyTooltips(Item item, List<TooltipLine> tooltips) {
			if (line == null) {
				return;
			}
			float seconds = SteamRocketPlayer.WindowTicks / 60f;
			tooltips.Add(new TooltipLine(Mod, "SteamFuel", line.Format(SteamRocketPlayer.SteamPerWindow, seconds)));
		}
	}
}
