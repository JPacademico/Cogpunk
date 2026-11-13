using System;
using Cogpunk.Content.Mechanist;
using Cogpunk.Core.Safety;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>Why a weapon can't go into the Combinator (the UI says it).</summary>
	public enum CombinationRefusal : byte
	{
		None,
		Empty,
		NotAWeapon,
		Summon,
		AlreadyCombined,
		DifferentClass,
	}

	/// <summary>
	/// The Combinator's rules (user-set 2026-11-12):
	/// <list type="bullet">
	/// <item>two weapons of the same class (melee, ranged, magic, Mechanist, throwing or another mod's class); never summon
	/// weapons; never a weapon that is already a combination (<see cref="Check"/>, <see cref="CanCombine"/>);</item>
	/// <item>the product's damage is half the sum of the two, and the same for the use time, the mana and the steam
	/// (<see cref="ApplyStats"/>), from each weapon's own stats: a reforge on either is ignored (the stats come from
	/// <c>ContentSamples.ItemsByType</c>, the item as <c>SetDefaults</c> makes it);</item>
	/// <item>the augment defines the attack: the product is an item of the augment's own type (so its projectile, animation
	/// and every special code vanilla or a mod keys on that type still run), the base lends its passives
	/// (<see cref="CombinatorTraits"/>), its crit, armor penetration and auto swing, and its range;</item>
	/// <item>the product reforges like any weapon of its class (its type's prefix categories); <see cref="CombinedWeapon"/>
	/// rebuilds the stats from scratch and re-applies the prefix whenever tModLoader rebuilds the item;</item>
	/// <item>the right click is the base's when the base has one (<see cref="CombinedAltPlayer"/>), the augment's otherwise.</item>
	/// </list>
	/// My calls: the use time keeps the augment's shots per use (its useTime : useAnimation ratio, so a burst gun stays a
	/// burst) with the averaged animation (equal to plain averaging for ordinary weapons); knockback is the attack's (the
	/// augment's); crit, armor penetration and auto swing come from the base, as "bonus" stats; projectile range is the
	/// augment's shot speed times the base's over the augment's, clamped to x0.75-x1.33; a swung blade reaches as far as its
	/// combined sprite (<see cref="CombinedWeapon.UseItemHitbox"/>); value is the sum, rarity the higher one.
	/// </summary>
	public static class CombinationRules
	{
		public const float MinRangeRatio = 0.75f, MaxRangeRatio = 1.33f;
		public const int MaxNameLength = 32;

		/// <summary>A weapon the Combinator takes: damage, one to a stack, used, not a tool, ammo, consumable, placeable,
		/// accessory or fishing pole.</summary>
		public static bool IsWeapon(Item item) {
			return item != null && !item.IsAir && item.damage > 0 && item.maxStack == 1 && item.useStyle != ItemUseStyleID.None
				&& !item.accessory && !item.vanity && item.pick == 0 && item.axe == 0 && item.hammer == 0 && item.ammo == AmmoID.None
				&& !item.consumable && item.createTile < TileID.Dirt && item.createWall <= WallID.None && item.fishingPole == 0;
		}

		/// <summary>Whether <paramref name="item"/> may go in a Combinator slot on its own.</summary>
		public static CombinationRefusal Check(Item item) {
			if (item == null || item.IsAir) {
				return CombinationRefusal.Empty;
			}
			if (CombinedWeapon.IsCombined(item) || CombinedWeapon.IsProxy(item)) {
				return CombinationRefusal.AlreadyCombined;
			}
			if (!IsWeapon(item)) {
				return CombinationRefusal.NotAWeapon;
			}
			if (item.DamageType.CountsAsClass(DamageClass.Summon)) {
				return CombinationRefusal.Summon;
			}
			return CombinationRefusal.None;
		}

		/// <summary>Both may go in, and they are of one class.</summary>
		public static CombinationRefusal CanCombine(Item baseItem, Item augment) {
			CombinationRefusal r = Check(baseItem);
			if (r != CombinationRefusal.None) {
				return r;
			}
			r = Check(augment);
			if (r != CombinationRefusal.None) {
				return r;
			}
			return ClassOf(baseItem) == ClassOf(augment) ? CombinationRefusal.None : CombinationRefusal.DifferentClass;
		}

		/// <summary>The class a weapon belongs to for the same-class rule (vanilla's sub-classes count as their class:
		/// MeleeNoSpeed is melee, and so on).</summary>
		public static DamageClass ClassOf(Item item) {
			DamageClass t = item.DamageType;
			if (t.CountsAsClass(DamageClass.Melee)) {
				return DamageClass.Melee;
			}
			if (t.CountsAsClass(DamageClass.Ranged)) {
				return DamageClass.Ranged;
			}
			if (t.CountsAsClass(DamageClass.Magic)) {
				return DamageClass.Magic;
			}
			if (t.CountsAsClass(DamageClass.Throwing)) {
				return DamageClass.Throwing;
			}
			if (t.CountsAsClass<MechanistDamage>()) {
				return ModContent.GetInstance<MechanistDamage>();
			}
			return t;
		}

		/// <summary>The item of <paramref name="type"/> as SetDefaults makes it (no prefix): the stats the rules average.</summary>
		public static Item Sample(int type) {
			return type > ItemID.None && type < ItemLoader.ItemCount && ContentSamples.ItemsByType.TryGetValue(type, out Item item) ? item : null;
		}

		/// <summary>A Mechanist weapon's own steam cost (0 for anything else).</summary>
		public static int SteamOf(Item sample) => sample?.ModItem is MechanistWeapon w ? w.SteamCost : 0;

		/// <summary>Half the sum, rounded half up.</summary>
		public static int Half(int a, int b) => (Math.Max(0, a) + Math.Max(0, b) + 1) / 2;

		/// <summary>The base's range over the augment's: their shot speeds, clamped.</summary>
		public static float RangeRatio(Item augment, Item baseItem) {
			if (augment == null || baseItem == null || augment.shootSpeed <= 0f || baseItem.shootSpeed <= 0f) {
				return 1f;
			}
			return Math.Clamp(baseItem.shootSpeed / augment.shootSpeed, MinRangeRatio, MaxRangeRatio);
		}

		/// <summary>
		/// Writes the combined stats of an augment of <paramref name="augmentType"/> and a base of <paramref name="baseType"/>
		/// onto <paramref name="target"/>, whose own type makes the attack: the product (the augment's type) or, while the
		/// base's right click runs, its stand-in (the base's type, <paramref name="baseFace"/>). Every field a prefix touches
		/// is written, so the caller re-applies the item's prefix afterwards. False (nothing written) when a type is unknown.
		/// </summary>
		public static bool ApplyStats(Item target, int augmentType, int baseType, bool baseFace) {
			Item a = Sample(augmentType), b = Sample(baseType);
			if (target == null || a == null || b == null) {
				return false;
			}
			Item own = baseFace ? b : a;
			target.damage = Half(a.damage, b.damage);
			int animation = Math.Max(2, Half(a.useAnimation, b.useAnimation));
			target.useAnimation = animation;
			target.useTime = Math.Max(1, (int)Math.Round(animation * own.useTime / (float)Math.Max(1, own.useAnimation)));
			target.reuseDelay = own.reuseDelay;
			target.mana = a.mana > 0 || b.mana > 0 ? Half(a.mana, b.mana) : 0;
			target.knockBack = own.knockBack;
			target.crit = b.crit;
			target.ArmorPenetration = Math.Max(a.ArmorPenetration, b.ArmorPenetration);
			target.autoReuse = a.autoReuse || b.autoReuse;
			target.shootSpeed = baseFace ? b.shootSpeed : a.shootSpeed * RangeRatio(a, b);
			target.scale = own.scale;
			target.value = a.value + b.value;
			target.rare = Math.Max(a.rare, b.rare);
			if (target.ModItem is MechanistWeapon weapon) {
				int steam = Half(SteamOf(a), SteamOf(b));
				weapon.CombinedSteamCost = SteamOf(a) > 0 || SteamOf(b) > 0 ? Math.Max(1, steam) : 0;
				weapon.PrefixSteamMultiplier = 1f;
			}
			return true;
		}

		/// <summary>
		/// The product of <paramref name="baseItem"/> and <paramref name="augment"/>, or null when the rules refuse. Both go
		/// inside it whole (prefixes and all) for <see cref="Separate"/>. The product is the augment itself, rebuilt
		/// (<see cref="Rebuild"/>) without its prefix: whatever a weapon keeps in its own <c>ModItem</c> or in another mod's
		/// global (a future weapon's charge or level, an enchantment) stays with the attack it belongs to (2026-11-12, "all
		/// future weapons"); a fresh item of its type when the augment can't be rebuilt.
		/// </summary>
		public static Item Combine(Item baseItem, Item augment) {
			if (CanCombine(baseItem, augment) != CombinationRefusal.None) {
				return null;
			}
			Item product = Rebuild(augment, 0) ?? new Item(augment.type);
			if (!product.TryGetGlobalItem(out CombinedWeapon data)) {
				return null;
			}
			data.SetParts(baseItem.Clone(), augment.Clone(), "");
			data.Recompute(product);
			product.NetStateChanged();                        // D2: a new item even where the slot held one of its type
			return product;
		}

		/// <summary>
		/// Takes a product apart: the base exactly as it went in; the augment with its own prefix back and with whatever its
		/// modded data gathered while it was the product (rebuilt from the product, <see cref="Rebuild"/>), or exactly as it
		/// went in when that fails. The product's own reforge goes with it.
		/// </summary>
		public static bool Separate(Item product, out Item baseItem, out Item augment) {
			baseItem = augment = null;
			if (!CombinedWeapon.TryGet(product, out CombinedWeapon data) || !data.IsProduct) {
				return false;
			}
			baseItem = data.Base.Clone();
			augment = (product.type == data.Augment.type ? Rebuild(product, data.Augment.prefix) : null) ?? data.Augment.Clone();
			baseItem.NetStateChanged();
			augment.NetStateChanged();
			return !baseItem.IsAir && !augment.IsAir;
		}

		/// <summary>
		/// A fresh copy of <paramref name="item"/> as plain weapon with <paramref name="prefix"/>: saved and loaded back the way
		/// tModLoader does it (decompiled <c>ItemIO.Load</c>: <c>SetDefaults</c>, the <c>ModItem</c>'s data, the prefix, every
		/// global's data), so its stats are its type's own and its modded data is kept. Null (logged once) if its data fails
		/// to save or load: the caller falls back to a plain copy.
		/// </summary>
		private static Item Rebuild(Item item, int prefix) {
			try {
				Item copy = item.Clone();
				if (CombinedWeapon.TryGet(copy, out CombinedWeapon d)) {
					d.Clear();                                    // a plain weapon: the combination isn't saved with it
				}
				copy.prefix = prefix;
				copy.stack = 1;
				copy.favorited = false;
				Item back = ItemIO.Load(ItemIO.Save(copy));
				return back != null && !back.IsAir && back.type == item.type ? back : null;
			}
			catch (Exception e) {
				SafeLog.Warn("Combinator.Rebuild", "Combinator: item {0} could not be rebuilt from its data ({1}); a plain copy is used.", item.type, e.Message);
				return null;
			}
		}

		/// <summary>The product's name until the player gives it one: "first half of the augment, second half of the base",
		/// like its sprite. One-word names meet in the middle ("Mega" + "shark"); otherwise the augment's first word and the
		/// base's last ("Night's" + "Grass").</summary>
		public static string DefaultName(int augmentType, int baseType) {
			string a = Lang.GetItemNameValue(augmentType) ?? "", b = Lang.GetItemNameValue(baseType) ?? "";
			if (a.Length == 0 || b.Length == 0) {
				return a.Length > 0 ? a : b;
			}
			string[] aw = a.Split(' ', StringSplitOptions.RemoveEmptyEntries), bw = b.Split(' ', StringSplitOptions.RemoveEmptyEntries);
			if (aw.Length == 0 || bw.Length == 0) {
				return a;
			}
			string name;
			if (aw.Length == 1 && bw.Length == 1) {
				string first = aw[0][..((aw[0].Length + 1) / 2)];
				string second = bw[0][(bw[0].Length / 2)..];
				name = first + second;
			}
			else {
				name = aw[0] + " " + bw[^1];
			}
			return name.Length > MaxNameLength ? name[..MaxNameLength] : name;
		}

		/// <summary>True when the base has its own right-click attack, which the product's right click then runs: vanilla's
		/// alternate use (<c>ItemLoader.AltFunctionUse</c>) or a right-click skill (<see cref="Core.Combat.IRightClickSkill"/>).</summary>
		public static bool BaseHasAltUse(Item baseItem, Player player) {
			if (baseItem == null || baseItem.IsAir) {
				return false;
			}
			return baseItem.ModItem is Core.Combat.IRightClickSkill || ItemLoader.AltFunctionUse(baseItem, player);
		}

		/// <summary>Whose right click <paramref name="item"/> has: its own type, or for a product the base's when the base has
		/// one (else the augment's, the product's own type). The Metal Wrench's parry asks this.</summary>
		public static int RightClickTypeOf(Item item, Player player) {
			if (item == null || item.IsAir) {
				return ItemID.None;
			}
			if (CombinedWeapon.TryGet(item, out CombinedWeapon data)) {
				if (data.IsProduct) {
					return BaseHasAltUse(data.Base, player) ? data.Base.type : item.type;
				}
				if (data.IsStandIn) {
					return item.type;
				}
			}
			return item.type;
		}
	}
}
