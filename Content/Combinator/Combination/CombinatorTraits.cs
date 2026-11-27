using System;
using System.Collections.Generic;
using Cogpunk.Content.BloodMoon.Weapons;
using Cogpunk.Content.Bosses.Jadey.Weapons;
using Cogpunk.Content.Bosses.CursedConductor.Weapons;
using Cogpunk.Content.Bosses.TrashTr0m.Buffs;
using Cogpunk.Content.Bosses.TrashTr0m.Weapons;
using Cogpunk.Content.Desert.Weapons;
using Cogpunk.Content.Gems.Items;
using Cogpunk.Content.Junkyard.Weapons;
using Cogpunk.Content.Mechanist.Weapons;
using Cogpunk.Content.OldBrassTown.Weapons;
using Cogpunk.Content.Research.Items;
using Cogpunk.Content.Research.Weapons;
using Cogpunk.Content.Scrap.Weapons;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>
	/// What a base weapon lends a combination (user, 2026-11-12: "the base slot should define passive effects or bonus
	/// (like area damage, homing, don't consume ammo, or +50% damage on mechs) and range"). No game keeps a weapon's passives
	/// in data: vanilla codes them per item type (decompiled <c>Player.StatusToNPC</c> for melee debuffs,
	/// <c>Player.IsAmmoFreeThisShot</c> for ammo saving) and in each projectile's own code, so they can't be lifted off a weapon
	/// generically. This table names them instead, from those decompiled lines for vanilla and from each Cogpunk weapon's own
	/// constants, as portable <see cref="CombinatorTrait"/>s that <see cref="CombinedWeapon"/> and
	/// <see cref="CombinedProjectile"/> run on whatever the augment attacks with. Every weapon also lends its crit, armor
	/// penetration, auto swing and range (<see cref="CombinationRules"/>).
	/// <para>Future weapons (user, 2026-11-12: "compatibility for all future weapons"), in order: a weapon whose
	/// <c>ModItem</c> implements <see cref="ICombinatorPassives"/> declares its own (any mod's, asked once at load); else the
	/// table below; else what its own projectile tells (vanilla's sets, which modders fill for their projectiles too:
	/// <c>ProjectileID.Sets.CultistIsResistantTo</c> marks homing shots, the Lunatic Cultist resists them;
	/// <c>ProjectileID.Sets.Explosive</c> marks explosive ones). A Cogpunk weapon with no passive is listed in
	/// <see cref="NoPassives"/>; <c>tools/check_combinator.py</c> fails while a new weapon is in neither list nor declares.</para>
	/// <para>D1: one array per type, built once at load; lookups are dictionary reads off the hot path (once per spawn or
	/// hit). D0: <see cref="Unload"/> clears it.</para>
	/// </summary>
	public sealed class CombinatorTraits : ModSystem
	{
		private static readonly Dictionary<int, CombinatorTrait[]> table = new();
		private static readonly CombinatorTrait[] none = Array.Empty<CombinatorTrait>();

		public static void Register(int itemType, params CombinatorTrait[] traits) {
			if (itemType <= ItemID.None || traits == null || traits.Length == 0) {
				return;
			}
			if (table.TryGetValue(itemType, out CombinatorTrait[] old)) {
				CombinatorTrait[] merged = new CombinatorTrait[old.Length + traits.Length];
				old.CopyTo(merged, 0);
				traits.CopyTo(merged, old.Length);
				table[itemType] = merged;
				return;
			}
			table[itemType] = (CombinatorTrait[])traits.Clone();
		}

		/// <summary>The traits a base of <paramref name="itemType"/> lends (an empty array when it has none).</summary>
		public static CombinatorTrait[] Of(int itemType) {
			return table.TryGetValue(itemType, out CombinatorTrait[] t) ? t : none;
		}

		public static bool Has(CombinatorTrait[] traits, TraitKind kind, out CombinatorTrait trait) {
			for (int k = 0; k < traits.Length; k++) {
				if (traits[k].Kind == kind) {
					trait = traits[k];
					return true;
				}
			}
			trait = default;
			return false;
		}

		public override void PostSetupContent() {
			// --- vanilla (decompiled 1.4.4) ---------------------------------------------------------------------------------
			// Player.IsAmmoFreeThisShot: Minishark and Candy Corn Rifle 1 in 3; Megashark, Gatligator, Chain Gun and
			// Celebration Mk2 1 in 2; S.D.M.G., Vortex Beater and Phantasm 2 in 3.
			Register(ItemID.Minishark, Saver(1f / 3f));
			Register(ItemID.CandyCornRifle, Saver(1f / 3f));
			Register(ItemID.Megashark, Saver(0.5f));
			Register(ItemID.Gatligator, Saver(0.5f));
			Register(ItemID.ChainGun, Saver(0.5f));
			Register(ItemID.Celeb2, Saver(0.5f));
			Register(ItemID.SDMG, Saver(2f / 3f));
			Register(ItemID.VortexBeater, Saver(2f / 3f));
			Register(ItemID.Phantasm, Saver(2f / 3f));
			// Player.StatusToNPC: the melee weapons' own debuffs
			Register(ItemID.FieryGreatsword, Debuff(BuffID.OnFire, 180, 0.5f));      // Volcano
			Register(ItemID.BladeofGrass, Debuff(BuffID.Poisoned, 420, 0.25f));
			Register(ItemID.Bladetongue, Debuff(BuffID.Ichor, 450, 1f));             // 5-10 s: the middle
			Register(ItemID.DD2SquireDemonSword, Debuff(BuffID.OnFire3, 300, 0.25f)); // Brand of the Inferno: Hellfire
			Register(ItemID.WaffleIron, Debuff(BuffID.OnFire3, 300, 1f / 3f));
			Register(ItemID.Flymeal, Debuff(BuffID.Stinky, 300, 1f));

			// --- Cogpunk (each weapon's own numbers) ---------------------------------------------------------------------
			Register(ModContent.ItemType<Screwdriver>(), new CombinatorTrait(TraitKind.BonusVsMechanical, 1f + Screwdriver.MechanicalBonus / 100f));
			Register(ModContent.ItemType<MetalWrench>(), new CombinatorTrait(TraitKind.BonusVsMechanical, 1f + MetalWrench.MechanicalBonus / 100f));
			Register(ModContent.ItemType<Macuahuitl>(), new CombinatorTrait(TraitKind.FirstStrike, Macuahuitl.FirstHitMultiplier));
			Register(ModContent.ItemType<Tetanus>(), Debuff(ModContent.BuffType<TetanusDebuff>(), Tetanus.DebuffTicks, 1f));
			Register(ModContent.ItemType<TarShower>(), new CombinatorTrait(TraitKind.TarPlague, d: TarSpray.PlagueTicks));
			Register(ModContent.ItemType<SheriffsRevolver>(), new CombinatorTrait(TraitKind.Homing, 20f * 16f, 0.06f));   // its ricochet seeks enemies
			Register(ModContent.ItemType<BanditsDream>(), new CombinatorTrait(TraitKind.Homing, 20f * 16f, 0.06f));      // the same ricochet (2026-11-19)
			Register(ModContent.ItemType<ScrapLauncher>(), new CombinatorTrait(TraitKind.AreaBurst, 3f * 16f, 0.35f));    // its scrap bursts on impact
			Register(ModContent.ItemType<Scrapmancer>(), new CombinatorTrait(TraitKind.Pierce, d: 2));                     // its wave runs through enemies
			Register(ModContent.ItemType<CursedLantern>(), new CombinatorTrait(TraitKind.Homing, SoulFire.HomingRange, 0.08f));
			Register(ModContent.ItemType<JadeStaff>(), new CombinatorTrait(TraitKind.JadeCurse));
			Register(ModContent.ItemType<TarBoneStaff>(),
				new CombinatorTrait(TraitKind.Homing, 25f * 16f, 0.06f),
				new CombinatorTrait(TraitKind.AreaBurst, 5f * 16f, 0.5f));                                                   // its skull bursts over 5 tiles
			Register(ModContent.ItemType<BarrelGun>(), new CombinatorTrait(TraitKind.Stun, BarrelGunFish.StunChance, d: BarrelGunFish.StunTicks));
			Register(ModContent.ItemType<DiamondCutter>(),
				new CombinatorTrait(TraitKind.ArmorPierce, DiamondCutterBeam.ArmorIgnore),
				new CombinatorTrait(TraitKind.Pierce, d: DiamondCutterBeam.MaxTargets - 1));
			Register(ModContent.ItemType<CogLauncher>(), new CombinatorTrait(TraitKind.Pierce, d: CogLauncherCog.Pierce));
			Register(ModContent.ItemType<Firesaw>(), Debuff(BuffID.OnFire, 180, 0.25f));                                  // its burning blade
			Register(ModContent.ItemType<CogspringSword>(), new CombinatorTrait(TraitKind.FirstStrike, 1.5f));          // 2026-11-19: its charged blow (my call)
			Register(ModContent.ItemType<SmokerBook>(), new CombinatorTrait(TraitKind.Pierce, d: 3));                    // 2026-11-19: its smoke runs through enemies
			Register(ModContent.ItemType<JadeCursedGlaives>(), new CombinatorTrait(TraitKind.JadeCurse));                // 2026-11-17: every slash curses
			Register(ModContent.ItemType<JadeRefractor>(),                                                                // 2026-11-24: the cutter's line, jade
				new CombinatorTrait(TraitKind.ArmorPierce, DiamondCutterBeam.ArmorIgnore),
				new CombinatorTrait(TraitKind.Pierce, d: DiamondCutterBeam.MaxTargets - 1),
				new CombinatorTrait(TraitKind.JadeCurse));
			Register(ModContent.ItemType<Cakti>(), Saver(Cakti.AmmoSaveChance));      // 2026-11-17: the Minishark's saving
			Register(ModContent.ItemType<FireworkCannon>(), new CombinatorTrait(TraitKind.AreaBurst, FireworkRocket.BurstRadius, 0.5f),
				new CombinatorTrait(TraitKind.Stun, 1f / FireworkRocket.StunOneIn, d: FireworkRocket.StunTicks));          // its fireworks burst and stun
			Register(ModContent.ItemType<Sparkler>(), Debuff(BuffID.OnFire, 120, 0.5f));                                    // 0.3.0: its sparks ignite
			Register(ModContent.ItemType<Flintsword>(), Debuff(BuffID.OnFire, 120, 0.5f));                                  // 0.3.0: its flint sparks ignite

			// --- every other weapon, of any mod: its own declaration, else what its projectile tells -------------------------
			var declared = new List<CombinatorTrait>(4);
			for (int type = 1; type < ItemLoader.ItemCount; type++) {
				Item sample = CombinationRules.Sample(type);
				if (sample == null || CombinationRules.Check(sample) != CombinationRefusal.None) {
					continue;
				}
				if (sample.ModItem is ICombinatorPassives passives) {
					declared.Clear();
					try {
						passives.AddCombinatorTraits(declared);
					}
					catch (Exception e) {
						SafeLog.Warn("Combinator.Declare", "Combinator: item {0} failed to declare its passives ({1}).", type, e.Message);
						declared.Clear();
					}
					if (declared.Count > 0) {
						Register(type, declared.ToArray());
						continue;
					}
				}
				if (!table.ContainsKey(type)) {
					Infer(sample);
				}
			}
		}

		/// <summary>The passives a weapon's own projectile tells of (vanilla's sets): homing, an explosion.</summary>
		private static void Infer(Item sample) {
			int shot = sample.shoot;
			if (shot <= ProjectileID.None || shot >= ProjectileLoader.ProjectileCount) {
				return;
			}
			if (ProjectileID.Sets.CultistIsResistantTo[shot]) {
				Register(sample.type, new CombinatorTrait(TraitKind.Homing, InferredHomingRange, InferredHomingTurn));
			}
			if (ProjectileID.Sets.Explosive[shot]) {
				Register(sample.type, new CombinatorTrait(TraitKind.AreaBurst, InferredBurstRadius, InferredBurstShare));
			}
		}

		public const float InferredHomingRange = 25f * 16f, InferredHomingTurn = 0.06f;
		public const float InferredBurstRadius = 3f * 16f, InferredBurstShare = 0.5f;

		/// <summary>Cogpunk weapons with no passive to lend (a decision recorded, for <c>tools/check_combinator.py</c>): they
		/// still lend their crit, armor penetration, auto swing and range.</summary>
		public static readonly string[] NoPassives = {
			nameof(JadePhaseblade), nameof(JadePhasesaber), nameof(ScrappyBow), nameof(ScrappyWand), nameof(TrapperChain),
			nameof(PossessedCog),                          // 2026-11-16: its piercing is its own yoyo's (kept as the augment)
			nameof(JadeShaperWhip),                        // 2026-11-17: its bonus against jade is its own lash's
			nameof(IncenseMace),                           // 2026-11-18: its aura is its own right click's
			nameof(BundleOfWands),                         // 2026-11-18: its five-bolt burst is its own attack (kept as the augment)
			nameof(JadeClaws),                             // 2026-11-24: a digging claw, nothing to lend
			nameof(HandMadeGun),                           // 0.3.0: its bounce and misfire belong to its own shot
			nameof(DrillerExtractor),                      // 0.3.0: a drill, nothing to lend
		};

		public override void Unload() {
			table.Clear();
		}

		private static CombinatorTrait Saver(float chance) => new(TraitKind.AmmoSaver, chance);

		private static CombinatorTrait Debuff(int buff, int ticks, float chance) => new(TraitKind.Debuff, chance, c: buff, d: ticks);
	}
}
