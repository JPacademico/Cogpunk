using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Mechanist
{
	/// <summary>
	/// The Mechanist's Steam (user-set 2026-10-27): what mana is to a mage. Mechanist weapons spend it
	/// (<see cref="MechanistWeapon"/>); it refills only after the player has gone <see cref="RegenDelayTicks"/> (1.5 s)
	/// without a Mechanist attack, then by <see cref="BaseRegenAmount"/> every <see cref="RegenIntervalTicks"/> (10 per
	/// 0.5 s; gear raises <see cref="SteamRegen"/>). Trying to fire without enough of it <b>overheats</b> the player
	/// (<see cref="Overheat"/>): no items, and they can't stop moving, until the tank has refilled completely.
	/// <para>Capacity: <see cref="BaseSteamMax"/> (0: a player has no tank of their own) + <see cref="SteamMaxBonus"/>
	/// (Mechanist armor and steam containers add to it every tick, like <c>statManaMax2</c>) + <see cref="SteamMaxInnate"/>
	/// (permanent upgrades: the Cogpunker Manual's +20, 2026-10-28; it alone doesn't keep the gauge up). Costs are scaled by
	/// <see cref="SteamCostMultiplier"/> (the Polished set: -10%). Tuned 2026-10-27 (user): refill doubled, delay 2 s ->
	/// 1.5 s, base capacity 100 -> 0.</para>
	/// <para>Steam as mana (the Serene Tear, 2026-10-29): with <see cref="SteamAsMana"/> a mana cost the tank can cover is
	/// paid in steam instead (<see cref="ModifyManaCost"/> zeroes it, <see cref="OnConsumeMana"/> takes the steam), and mana
	/// pays once the steam runs short; <see cref="OverheatImmune"/> turns an overheat into a plain refusal to fire;
	/// <see cref="SteamRegenMultiplier"/> scales the refill (the fraction carries over to the next refill).</para>
	/// <para>Steam-costing skills of other classes (user, 2026-11-04: the Metal Wrench's parry, the Tar-Shower's charge;
	/// <see cref="ISteamSkill"/>) pay through <see cref="TryPayAttack"/>, by the same rules as a Mechanist weapon.
	/// <see cref="SteamForUse"/> tells what a use takes from the tank (a Mechanist weapon, a spell the steam pays for, a
	/// skill), which is what the Spring Gloves count.</para>
	/// <para>D2: Steam is the owning client's (like the local mana counter, nobody else can see it); only the owner spends,
	/// refills and overheats. The overheat shows to everyone through its buff, which vanilla syncs. D1: integer counters,
	/// no allocation; effects client-only.</para>
	/// </summary>
	public sealed class SteamPlayer : ModPlayer
	{
		public const int BaseSteamMax = 0;               // only gear grants a tank (user-set)
		public const int RegenDelayTicks = 90;           // 1.5 s without attacking
		public const int RegenIntervalTicks = 30;        // then a refill every 0.5 s...
		public const int BaseRegenAmount = 10;           // ...of 10 steam
		public const int NoTankHintTicks = 60;           // the "no tank" hint repeats at most once a second
		public const int OverheatBuffTicks = 60 * 60 * 10;   // the buff only mirrors the state: cleared when the tank is full
		public const int GaugeLingerTicks = 180;         // the gauge stays up this long after the last reason to show it
		public const int ManaPerSteam = 2;               // the Serene Tear's fallback: mana at half the efficiency (user, 2026-11-12)

		/// <summary>Steam in the tank (owner only).</summary>
		public int Steam = BaseSteamMax;

		/// <summary>Capacity this tick: <see cref="BaseSteamMax"/> + <see cref="SteamMaxBonus"/> + <see cref="SteamMaxInnate"/>.</summary>
		public int SteamMax = BaseSteamMax;

		/// <summary>Added to the capacity by gear; reset every tick.</summary>
		public int SteamMaxBonus;

		/// <summary>Added to the capacity by permanent upgrades (re-added every tick in PostUpdateEquips); reset every tick.</summary>
		public int SteamMaxInnate;

		/// <summary>Steam refilled per <see cref="RegenIntervalTicks"/>; reset to <see cref="BaseRegenAmount"/> every tick.</summary>
		public int SteamRegen = BaseRegenAmount;

		/// <summary>Multiplies every steam cost; reset to 1 every tick.</summary>
		public float SteamCostMultiplier = 1f;

		/// <summary>Multiplies the steam each refill adds; reset to 1 every tick (the Serene Tear: +0.15).</summary>
		public float SteamRegenMultiplier = 1f;

		/// <summary>Mana costs are paid from the steam tank first (the Serene Tear); reset every tick.</summary>
		public bool SteamAsMana;

		/// <summary>Never overheats: a Mechanist weapon without enough steam just doesn't fire (the Serene Tear); reset every tick.</summary>
		public bool OverheatImmune;

		/// <summary>Overheated: set when a Mechanist weapon is used without enough steam, cleared when the tank is full.</summary>
		public bool Overheated { get; private set; }

		private int sinceAttack = RegenDelayTicks;
		private int regenTimer;
		private int gaugeTimer;
		private int noTankHintTimer;
		private float regenCarry;
		private bool measuringMana;
		private int paidItemType = -1;                 // the last mana payment (OnConsumeMana): which item, and the steam it took
		private int paidSteam;
		private bool lastPaidWithMana;                 // the last steam cost (Spend) was paid in mana (the Serene Tear's fallback)
		private static LocalizedText noTankText;

		/// <summary>The gauge is shown while steam matters: a Mechanist weapon in hand, Mechanist gear on, a tank that isn't
		/// full, an overheat, and for <see cref="GaugeLingerTicks"/> after.</summary>
		public bool ShowGauge => gaugeTimer > 0;

		/// <summary>0..1 how far the regen delay has run (the gauge's valve turns while waiting).</summary>
		public float RegenWait => MathHelper.Clamp(sinceAttack / (float)RegenDelayTicks, 0f, 1f);

		public override void SetStaticDefaults() {
			noTankText = Mod.GetLocalization("Mechanist.NoTank");
		}

		public override void Unload() {
			noTankText = null;
		}

		public override void Initialize() {
			Steam = BaseSteamMax;
			SteamMax = BaseSteamMax;
			Overheated = false;
		}

		public override void ResetEffects() {
			SteamMaxBonus = 0;
			SteamMaxInnate = 0;
			SteamRegen = BaseRegenAmount;
			SteamCostMultiplier = 1f;
			SteamRegenMultiplier = 1f;
			SteamAsMana = false;
			OverheatImmune = false;
		}

		public override void UpdateDead() {
			ResetEffects();
			Overheated = false;
		}

		public override void OnRespawn() {
			Steam = Math.Max(BaseSteamMax, SteamMax);   // capped to the real capacity on the next update
			Overheated = false;
			sinceAttack = RegenDelayTicks;
		}

		/// <summary>The cost of a Mechanist attack after <see cref="SteamCostMultiplier"/> (never negative; 1 minimum when
		/// the base cost is above 0, so gear can't make a weapon free by rounding).</summary>
		public int GetCost(int baseCost) {
			if (baseCost <= 0) {
				return 0;
			}
			float scaled = baseCost * Math.Max(0f, SteamCostMultiplier);
			return Math.Max(1, (int)Math.Round(scaled));
		}

		/// <summary>Owner: a Mechanist attack happened (or was attempted): the refill waits another <see cref="RegenDelayTicks"/>.
		/// With <see cref="SteamAsMana"/> (the Serene Tear) mana's own refill waits too (user, 2026-11-12: "steam and mana can't
		/// regen while any is being consumed"; vanilla's delay, decompiled <c>Player.ItemCheck_ApplyManaRegenDelay</c>).</summary>
		public void NoteAttack() {
			sinceAttack = 0;
			regenTimer = 0;
			gaugeTimer = GaugeLingerTicks;
			if (SteamAsMana) {
				HoldManaRegen();
			}
		}

		/// <summary>Owner: vanilla's mana refill starts its wait again, as a mana cost does.</summary>
		private void HoldManaRegen() {
			Player.manaRegenDelay = Math.Max(Player.manaRegenDelay, (int)Player.maxRegenDelay);
		}

		/// <summary>The mana a steam cost takes when the Serene Tear pays it in mana: <see cref="ManaPerSteam"/> a steam
		/// (user, 2026-11-12: "half the efficiency ... double the cost conversion"); vanilla's mana cost multiplier applies on
		/// top in <c>Player.CheckMana</c>.</summary>
		public static int ManaFor(int steamCost) => Math.Max(0, steamCost) * ManaPerSteam;

		/// <summary>Whether mana alone covers <paramref name="steamCost"/> right now (no potion drunk: a plain comparison
		/// with vanilla's <c>CheckMana</c> rounding, safe to ask from tooltips and damage hooks).</summary>
		private bool ManaCovers(int steamCost) {
			return steamCost > 0 && Player.statMana >= (int)(ManaFor(steamCost) * Player.manaCost);
		}

		/// <summary>Owner: pays for a Mechanist attack, in steam when the tank holds it; otherwise, with
		/// <see cref="SteamAsMana"/> (the Serene Tear), in mana at <see cref="ManaPerSteam"/> a steam (user, 2026-11-12:
		/// "steam consuming weapons can also use mana at half the efficiency after steam ends"). Never goes below zero. The
		/// payment's kind is remembered for <see cref="SteamForUse"/>.</summary>
		public void Spend(int baseCost) {
			int cost = GetCost(baseCost);
			lastPaidWithMana = false;
			if (Steam >= cost) {
				Steam -= cost;
			}
			else if (SteamAsMana && cost > 0 && Player.CheckMana(ManaFor(cost), pay: true, blockQuickMana: true)) {
				lastPaidWithMana = true;                   // CanPayAttack checked (and drank a potion if it had to)
			}
			else {
				Steam = 0;
			}
			NoteAttack();
			if (lastPaidWithMana) {
				HoldManaRegen();                           // CheckMana(int) doesn't start vanilla's wait itself
			}
		}

		/// <summary>Owner: whether an attack costing <paramref name="baseCost"/> (before the multiplier) can be paid now, by a
		/// Mechanist weapon's rules. With <see cref="SteamAsMana"/> (the Serene Tear) a cost the tank can't cover is paid in
		/// mana instead, <see cref="ManaPerSteam"/> a steam, when there is enough (vanilla's <c>CheckMana</c>, which drinks a
		/// mana potion through the Mana Flower like any spell). A refusal does what it does for a Mechanist weapon: nothing
		/// while overheated; the "No steam tank!" hint when the whole tank is smaller than the cost (no refill could ever
		/// pay); an overheat (or, with <see cref="OverheatImmune"/>, a plain refusal) when the tank is merely short.</summary>
		public bool CanPayAttack(int baseCost) {
			if (Overheated) {
				return false;
			}
			int cost = GetCost(baseCost);
			if (Steam >= cost) {
				return true;                               // Steam never exceeds SteamMax, so the tank holds the cost too
			}
			if (SteamAsMana && cost > 0 && Player.CheckMana(ManaFor(cost), pay: false)) {
				return true;
			}
			if (SteamMax < cost) {
				NoteNoTank();
				return false;
			}
			TriggerOverheat();
			return false;
		}

		/// <summary>Owner: pays a steam-costing attack that isn't a Mechanist weapon's item use (a weapon skill,
		/// <see cref="ISteamSkill"/>) if <see cref="CanPayAttack"/> allows it. <paramref name="paid"/> is the steam taken
		/// (after the multiplier), which the skill's payoff hands to the Spring Gloves.</summary>
		public bool TryPayAttack(int baseCost, out int paid) {
			paid = 0;
			if (!CanPayAttack(baseCost)) {
				return false;
			}
			paid = GetCost(baseCost);
			Spend(baseCost);
			return true;
		}

		/// <summary>Owner: the steam the use of <paramref name="item"/> that is starting or under way takes from the tank (what
		/// the Spring Gloves count): a steam skill's cost during the skill (<see cref="ISteamSkill.SteamForUse"/>), a
		/// Mechanist weapon's cost, or, with <see cref="SteamAsMana"/>, the mana cost the steam pays. Summoning items count
		/// nothing: the steam pays for the summon, not for the minion's attacks (vanilla recomputes a minion's damage from the
		/// class bonus alone, never from the weapon's). Read from <c>ModifyWeaponDamage</c>, which vanilla calls before it pays
		/// for a use (decompiled <c>Player.ItemCheck_Inner</c>: <c>GetWeaponDamage</c> first, then <c>ItemCheck_CheckCanUse</c>
		/// and its <c>ItemCheck_PayMana</c>), so a use about to start counts what the tank would pay, and later ticks of the
		/// same use count what it did pay. D1: field reads and one <c>GetManaCost</c>.</summary>
		public int SteamForUse(Item item) {
			if (item == null || item.IsAir) {
				return 0;
			}
			if (item.ModItem is ISteamSkill skill) {
				int s = skill.SteamForUse(Player);
				if (s > 0) {
					return HalvedIfMana(s);
				}
			}
			if (item.ModItem is MechanistWeapon weapon) {
				return HalvedIfMana(GetCost(weapon.ItemSteamCost(Player)));
			}
			if (!SteamAsMana || item.mana <= 0 || item.DamageType.CountsAsClass(DamageClass.Summon)) {
				return 0;
			}
			if (Player.ItemAnimationActive && item.type == paidItemType) {
				return paidSteam;                          // the use under way: what it paid
			}
			int cost = ManaCostWithoutSteam(item);
			return cost > 0 && Steam >= cost ? cost : 0;  // about to start (or a tooltip): what the tank would pay
		}

		/// <summary>A steam-paid use's steam for the bonuses that count it (the Spring Gloves), halved when the Serene Tear pays
		/// it in mana (user, 2026-11-12: "half the bonus if there's bonus applied"): the use under way by how it was paid
		/// (<see cref="Spend"/>), a use about to start by how it would be. D1: field reads.</summary>
		private int HalvedIfMana(int steam) {
			if (!SteamAsMana || steam <= 0) {
				return steam;
			}
			bool viaMana = Player.ItemAnimationActive ? lastPaidWithMana : Steam < steam && ManaCovers(steam);
			return viaMana ? steam / 2 : steam;
		}

		/// <summary>Owner: pays a flat <paramref name="amount"/> (no cost multiplier: not a weapon) if the tank holds it; false
		/// (nothing spent) otherwise. Like an attack, it restarts the refill delay.</summary>
		public bool TrySpendFlat(int amount) {
			if (amount < 0 || Steam < amount) {
				return false;
			}
			Steam -= amount;
			NoteAttack();
			return true;
		}

		/// <summary>Owner: fired without enough steam. Items lock and the player can't stop until the tank is full again.</summary>
		public void TriggerOverheat() {
			if (OverheatImmune) {
				gaugeTimer = GaugeLingerTicks;             // no vent and no extra wait: it fires again once the refill covers it
				return;
			}
			NoteAttack();
			if (Overheated) {
				return;
			}
			Overheated = true;
			Player.AddBuff(ModContent.BuffType<Overheat>(), OverheatBuffTicks);
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item34 with { Pitch = -0.3f, Volume = 0.8f }, Player.Center);   // the release valve
				SoundEngine.PlaySound(SoundID.NPCHit53 with { Pitch = 0.4f, Volume = 0.5f }, Player.Center);
				for (int i = 0; i < 16; i++) {
					if (SafeSpawn.TryNewDust(Player.position, Player.width, Player.height / 2, DustID.Smoke, out Dust d, 0f, -2f, 80,
						new Color(238, 241, 243), 1.4f)) {
						d.velocity = Main.rand.NextVector2CircularEdge(3f, 2f) - new Vector2(0f, 1.5f);
						d.noGravity = true;
					}
				}
			}
		}

		/// <summary>Owner: tried to fire a weapon that costs more than the whole tank holds (no Mechanist gear yet).
		/// Nothing fires and nothing overheats (a refill could never pay for it); a hint shows, at most once a second.</summary>
		public void NoteNoTank() {
			gaugeTimer = GaugeLingerTicks;
			if (noTankHintTimer > 0 || Main.dedServ) {
				return;
			}
			noTankHintTimer = NoTankHintTicks;
			SoundEngine.PlaySound(SoundID.MenuTick with { Pitch = -0.6f }, Player.Center);   // a dry click: nothing to vent
			if (noTankText != null) {
				CombatText.NewText(Player.getRect(), new Color(195, 200, 205), noTankText.Value);
			}
		}

		private void EndOverheat() {
			Overheated = false;
			int index = Player.FindBuffIndex(ModContent.BuffType<Overheat>());
			if (index >= 0) {
				Player.DelBuff(index);
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.MaxMana with { Pitch = -0.5f }, Player.Center);
			}
		}

		public override void PostUpdateMiscEffects() {
			SteamMax = Math.Max(0, BaseSteamMax + SteamMaxBonus + SteamMaxInnate);
			if (Player.whoAmI != Main.myPlayer) {
				return;                                    // only the owner tracks its tank (D2)
			}
			if (noTankHintTimer > 0) {
				noTankHintTimer--;
			}
			if (Player.creativeGodMode) {
				Steam = SteamMax;                          // Journey god mode: infinite steam, like infinite mana
			}
			Steam = Math.Clamp(Steam, 0, SteamMax);
			if (Player.ItemAnimationActive && Player.HeldItem.ModItem is MechanistWeapon) {
				sinceAttack = 0;                           // still swinging/firing: no refill yet
			}
			if (sinceAttack < RegenDelayTicks) {
				sinceAttack++;
				regenTimer = 0;
			}
			else if (Steam < SteamMax) {
				if (++regenTimer >= RegenIntervalTicks) {
					regenTimer = 0;
					float amount = Math.Max(0, SteamRegen) * Math.Max(0f, SteamRegenMultiplier) + regenCarry;
					int whole = (int)amount;
					regenCarry = amount - whole;
					Steam = Math.Min(SteamMax, Steam + whole);
				}
			}
			else {
				regenTimer = 0;
			}
			if (Overheated && (Steam >= SteamMax || OverheatImmune)) {
				EndOverheat();
			}
			bool relevant = Overheated || Steam < SteamMax || SteamMaxBonus != 0 || SteamCostMultiplier != 1f
				|| Player.HeldItem.ModItem is MechanistWeapon || (SteamMax > 0 && Player.HeldItem.ModItem is ISteamSkill);
			gaugeTimer = relevant ? GaugeLingerTicks : Math.Max(0, gaugeTimer - 1);
		}

		/// <summary>The mana cost of <paramref name="item"/> as if steam paid nothing (every other reduction applied).</summary>
		private int ManaCostWithoutSteam(Item item) {
			measuringMana = true;
			int cost = Player.GetManaCost(item);
			measuringMana = false;
			return cost;
		}

		/// <summary>Owner, with <see cref="SteamAsMana"/>: a mana cost the steam tank holds costs no mana (decompiled
		/// <c>Player.GetManaCost</c>: <c>(int)(item.mana * reduce * mult)</c>; <c>Player.CheckMana</c> then pays 0 and calls
		/// <see cref="OnConsumeMana"/>, which takes the steam). A cost the tank can't cover is left alone: mana pays it.</summary>
		public override void ModifyManaCost(Item item, ref float reduce, ref float mult) {
			if (!SteamAsMana || measuringMana || Player.whoAmI != Main.myPlayer) {
				return;
			}
			int cost = ManaCostWithoutSteam(item);
			if (cost > 0 && Steam >= cost) {
				mult = 0f;
			}
		}

		/// <summary>Owner: a use whose mana cost the steam covered (0 mana paid): one steam per point of mana. Like an
		/// attack, it restarts the refill delay. Every payment is recorded (which item, the steam it took: 0 when mana paid),
		/// so <see cref="SteamForUse"/> knows what the use under way paid.</summary>
		public override void OnConsumeMana(Item item, int manaConsumed) {
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			paidItemType = item?.type ?? -1;
			paidSteam = 0;
			if (!SteamAsMana || item == null) {
				return;
			}
			if (manaConsumed > 0) {
				NoteAttack();                              // mana paid the spell: the steam waits too (user, 2026-11-12)
				return;
			}
			int cost = ManaCostWithoutSteam(item);
			if (cost > 0 && TrySpendFlat(cost)) {         // NoteAttack (through TrySpendFlat) holds mana's refill too
				paidSteam = cost;
			}
		}

		/// <summary>Overheated: the player can't stop. With no direction held they keep running the way they face; they can
		/// still turn by holding the other way. Owner only (SetControls runs for the local player, decompiled Player.Update).</summary>
		public override void SetControls() {
			if (!Overheated || Player.whoAmI != Main.myPlayer || Player.dead) {
				return;
			}
			if (!Player.controlLeft && !Player.controlRight) {
				if (Player.direction < 0) {
					Player.controlLeft = true;
				}
				else {
					Player.controlRight = true;
				}
			}
		}

		/// <summary>Client effects while overheated (every client sees the buff): steam hissing out of the player.</summary>
		internal void OverheatEffects() {
			if (Main.dedServ || !Main.rand.NextBool(3) || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			if (SafeSpawn.TryNewDust(Player.position + new Vector2(0f, 6f), Player.width, 12, DustID.Smoke, out Dust d, 0f, -1.5f, 100,
				new Color(238, 241, 243), 1.1f)) {
				d.velocity.X = -Player.velocity.X * 0.2f + Main.rand.NextFloat(-0.6f, 0.6f);
				d.noGravity = true;
			}
		}
	}
}
