using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>
	/// A Combinator product (user-set 2026-11-12). The product is an item of the <b>augment's own type</b> carrying this
	/// global: the base weapon and the augment exactly as they went in (prefixes and modded data kept, for taking it apart),
	/// and the name the player gave it. Being the augment's type is what makes "the augment defines the projectile and the
	/// attack animation" hold for every weapon: vanilla keys hundreds of special shots on the item's type (decompiled
	/// <c>Player.ItemCheck_Shoot</c>: shotguns, bows, the 1.4 sword slashes...) and a mod weapon's hooks live on its
	/// <c>ModItem</c>, and both still run. The base adds its passives (<see cref="CombinatorTraits"/>, run here for the
	/// product's own hits and by <see cref="CombinedProjectile"/> for its projectiles), its bonus stats and its range
	/// (<see cref="CombinationRules.ApplyStats"/>), and its right click (<see cref="CombinedAltPlayer"/>, which also uses this
	/// global to mark the stand-in it swaps in for that click). The look is drawn in CombinedWeapon.Draw.cs.
	/// <para>Rebuilt, never trusted: tModLoader rebuilds an item from scratch to save, load, sync and reforge it (decompiled
	/// <c>ItemIO.Load</c>/<c>Receive</c>: <c>SetDefaults</c>, then <c>Prefix</c>, then the globals' data; <c>Item.ResetPrefix</c>
	/// round-trips the item through <c>ItemIO.Send</c>/<c>Receive</c>), so <see cref="Recompute"/> writes every combined stat
	/// from the two weapons' own samples and re-applies the item's prefix once, whenever the data arrives. A reforge then
	/// rolls a prefix on top of the combined stats, like on any weapon of the augment's class.</para>
	/// <para>Guards (D0, no weapon lost): <see cref="Clone"/> deep-copies the parts (vanilla clones items freely); research
	/// is refused (it would consume the item); in shimmer the product never transforms (its shimmer timer is held at 0); a
	/// product crafted with as the augment's type gives the base back (<see cref="OnCreated"/>); save and load catch a broken
	/// tag and keep the item as a plain weapon rather than fail. D2: <see cref="NetSend"/> carries both parts and the name
	/// with the item, wherever vanilla syncs it (inventories, chests, the world).</para>
	/// </summary>
	public sealed partial class CombinedWeapon : GlobalItem
	{
		/// <summary>The base weapon as it went in (null when the item isn't a combination).</summary>
		public Item Base { get; private set; }

		/// <summary>The augment as it went in (its prefix and data kept; the product itself is a fresh item of its type).</summary>
		public Item Augment { get; private set; }

		/// <summary>The player's name for it ("" for the default, <see cref="CombinationRules.DefaultName"/>).</summary>
		public string CustomName { get; private set; } = "";

		/// <summary>A stand-in of the base's type during the base's right click (<see cref="CombinedAltPlayer"/>): the type of
		/// the augment it was combined with (synced, for the look) and, on the owner only, the product it stands in for.</summary>
		public int ProxyAugmentType { get; private set; }
		public Item ProxyOf { get; private set; }

		public bool IsProduct => Base != null && !Base.IsAir && Augment != null && !Augment.IsAir;
		public bool IsStandIn => ProxyAugmentType > ItemID.None;

		public override bool InstancePerEntity => true;

		// Weapons only (decided after SetDefaults): everything the Combinator can take or make.
		public override bool AppliesToEntity(Item entity, bool lateInstantiation) {
			return lateInstantiation && entity.damage > 0 && entity.maxStack == 1 && !entity.accessory;
		}

		public static bool TryGet(Item item, out CombinedWeapon data) {
			data = null;
			return item != null && !item.IsAir && item.TryGetGlobalItem(out data);
		}

		public static bool IsCombined(Item item) => TryGet(item, out CombinedWeapon d) && d.IsProduct;

		public static bool IsProxy(Item item) => TryGet(item, out CombinedWeapon d) && d.IsStandIn;

		internal void SetParts(Item baseItem, Item augment, string name) {
			Base = baseItem;
			Augment = augment;
			CustomName = Clean(name);
			ProxyAugmentType = ItemID.None;
			ProxyOf = null;
		}

		/// <summary>Makes this a plain weapon's data again (no parts, no name, no stand-in).</summary>
		internal void Clear() => SetParts(null, null, "");

		internal void MakeStandIn(int augmentType, Item product) {
			Base = Augment = null;
			CustomName = "";
			ProxyAugmentType = augmentType;
			ProxyOf = product;
		}

		/// <summary>Renames the product (the Combinator's name box): trimmed, at most
		/// <see cref="CombinationRules.MaxNameLength"/> characters, control characters dropped.</summary>
		public void Rename(Item item, string name) {
			CustomName = Clean(name);
			ApplyName(item);
			item.NetStateChanged();                            // D2: the name travels with the item's next sync
		}

		private static string Clean(string name) {
			if (string.IsNullOrWhiteSpace(name)) {
				return "";
			}
			StringBuilder sb = new(Math.Min(name.Length, CombinationRules.MaxNameLength));
			foreach (char c in name) {
				if (!char.IsControl(c) && sb.Length < CombinationRules.MaxNameLength) {
					sb.Append(c);
				}
			}
			return sb.ToString().Trim();
		}

		/// <summary>The traits this product's base lends (empty for anything else).</summary>
		public CombinatorTrait[] Traits => IsProduct ? CombinatorTraits.Of(Base.type) : Array.Empty<CombinatorTrait>();

		/// <summary>
		/// Writes the combined stats onto <paramref name="item"/> and re-applies its prefix once (every field a prefix touches is
		/// written first, value and rarity included, so nothing compounds). Called on combining, and whenever tModLoader
		/// rebuilds the item (load, net receive, reforge), after it has applied the prefix to the plain stats.
		/// </summary>
		public void Recompute(Item item) {
			int prefix = item.prefix;
			bool ok;
			if (IsProduct) {
				ok = CombinationRules.ApplyStats(item, item.type, Base.type, baseFace: false);
			}
			else if (IsStandIn) {
				ok = CombinationRules.ApplyStats(item, ProxyAugmentType, item.type, baseFace: true);
			}
			else {
				return;
			}
			if (!ok) {
				return;
			}
			item.prefix = 0;
			if (prefix > 0) {
				item.Prefix(prefix);                        // vanilla's own multipliers, value and rarity, once
			}
			ApplyName(item);
		}

		private void ApplyName(Item item) {
			if (IsProduct) {
				item.SetNameOverride(CustomName.Length > 0 ? CustomName : CombinationRules.DefaultName(item.type, Base.type));
			}
			else if (IsStandIn && ProxyOf != null && TryGet(ProxyOf, out CombinedWeapon product)) {
				item.SetNameOverride(product.CustomName.Length > 0 ? product.CustomName : CombinationRules.DefaultName(ProxyAugmentType, item.type));
			}
		}

		public override GlobalItem Clone(Item from, Item to) {
			CombinedWeapon clone = (CombinedWeapon)base.Clone(from, to);
			clone.Base = Base?.Clone();
			clone.Augment = Augment?.Clone();
			return clone;                                   // ProxyOf stays a reference: the one product the stand-in returns to
		}

		// --- save, load, sync ---------------------------------------------------------------------------------------------

		public override void SaveData(Item item, TagCompound tag) {
			if (IsProduct) {
				tag["base"] = ItemIO.Save(Base);
				tag["augment"] = ItemIO.Save(Augment);
				if (CustomName.Length > 0) {
					tag["name"] = CustomName;
				}
			}
			else if (IsStandIn && ProxyOf != null) {
				tag["standInFor"] = ItemIO.Save(ProxyOf);     // never expected (the swap undoes itself before a save), but kept whole
			}
		}

		public override void LoadData(Item item, TagCompound tag) {
			try {
				if (tag.ContainsKey("base") && tag.ContainsKey("augment")) {
					Item b = ItemIO.Load(tag.GetCompound("base"));
					Item a = ItemIO.Load(tag.GetCompound("augment"));
					if (b != null && !b.IsAir && a != null && !a.IsAir) {
						SetParts(b, a, tag.GetString("name"));
						Recompute(item);
					}
				}
				else if (tag.ContainsKey("standInFor")) {
					Item product = ItemIO.Load(tag.GetCompound("standInFor"));
					if (product != null && !product.IsAir) {
						MakeStandIn(product.type, product);    // CombinedAltPlayer swaps it back on the first update
						CombinedAltPlayer.LoadedStandIn = true;
					}
				}
			}
			catch (Exception e) {
				SafeLog.Warn("Combinator.LoadFailed", "Combinator: a combined weapon's data could not be read ({0}); kept as a plain weapon.", e.Message);
				SetParts(null, null, "");
			}
		}

		public override void NetSend(Item item, BinaryWriter writer) {
			byte flags = (byte)((IsProduct ? 1 : 0) | (IsStandIn ? 2 : 0));
			writer.Write(flags);
			if (IsProduct) {
				ItemIO.Send(Base, writer, writeStack: true);
				ItemIO.Send(Augment, writer, writeStack: true);
				writer.Write(CustomName);
			}
			else if (IsStandIn) {
				writer.Write7BitEncodedInt(ProxyAugmentType);
			}
		}

		public override void NetReceive(Item item, BinaryReader reader) {
			byte flags = reader.ReadByte();
			if ((flags & 1) != 0) {
				Item b = ItemIO.Receive(reader, readStack: true);
				Item a = ItemIO.Receive(reader, readStack: true);
				string name = reader.ReadString();
				SetParts(b, a, name);
				Recompute(item);
			}
			else if ((flags & 2) != 0) {
				int aug = reader.Read7BitEncodedInt();
				Item kept = ProxyOf;                           // a local stand-in keeps its product reference
				MakeStandIn(aug > ItemID.None && aug < ItemLoader.ItemCount ? aug : ItemID.None, kept);
				Recompute(item);
			}
			else {
				SetParts(null, null, "");
			}
		}

		// --- tooltips -------------------------------------------------------------------------------------------------------

		public override void ModifyTooltips(Item item, List<TooltipLine> tooltips) {
			if (!IsProduct && !IsStandIn) {
				return;
			}
			int augType = IsProduct ? item.type : ProxyAugmentType;
			int baseType = IsProduct ? Base.type : item.type;
			tooltips.Add(new TooltipLine(Mod, "CombinedOf", Language.GetTextValue("Mods.Cogpunk.Combinator.TooltipParts",
				Lang.GetItemNameValue(augType), Lang.GetItemNameValue(baseType))) { OverrideColor = new Color(223, 185, 78) });
			CombinatorTrait[] traits = CombinatorTraits.Of(baseType);
			for (int k = 0; k < traits.Length; k++) {
				tooltips.Add(new TooltipLine(Mod, "CombinedTrait" + k, TraitText(traits[k])) { OverrideColor = new Color(140, 201, 176) });
			}
			if (IsProduct && CombinationRules.BaseHasAltUse(Base, Main.LocalPlayer)) {
				tooltips.Add(new TooltipLine(Mod, "CombinedAlt", Language.GetTextValue("Mods.Cogpunk.Combinator.TooltipAlt", Lang.GetItemNameValue(baseType))));
			}
		}

		/// <summary>A trait in words (Mods.Cogpunk.Combinator.Trait.*).</summary>
		public static string TraitText(CombinatorTrait t) {
			string key = "Mods.Cogpunk.Combinator.Trait." + t.Kind;
			return t.Kind switch {
				TraitKind.Homing => Language.GetTextValue(key, (int)Math.Round(t.A / 16f)),
				TraitKind.AreaBurst => Language.GetTextValue(key, (int)Math.Round(t.B * 100f), (int)Math.Round(t.A / 16f)),
				TraitKind.AmmoSaver => Language.GetTextValue(key, (int)Math.Round(t.A * 100f)),
				TraitKind.BonusVsMechanical => Language.GetTextValue(key, (int)Math.Round((t.A - 1f) * 100f)),
				TraitKind.Debuff => Language.GetTextValue(key, (int)Math.Round(t.A * 100f), t.C > 0 && t.C < BuffLoader.BuffCount ? Lang.GetBuffName(t.C) : "?", t.D / 60f),
				TraitKind.TarPlague => Language.GetTextValue(key, t.D / 60f),
				TraitKind.Stun => Language.GetTextValue(key, (int)Math.Round(t.A * 100f), t.D / 60f),
				TraitKind.FirstStrike => Language.GetTextValue(key, t.A),
				TraitKind.Pierce => Language.GetTextValue(key, t.D),
				TraitKind.ArmorPierce => Language.GetTextValue(key, (int)Math.Round(t.A * 100f)),
				_ => Language.GetTextValue(key),
			};
		}

		// --- guards ---------------------------------------------------------------------------------------------------------

		/// <summary>Research would consume the item, and the base with it.</summary>
		public override bool CanResearch(Item item) => !IsProduct && !IsStandIn;

		/// <summary>In the world: a product never shimmers into something else (vanilla transforms at 0.9 of its timer,
		/// decompiled <c>Item.Shimmering</c>); a stand-in that ever lands here turns back into its product.</summary>
		public override void Update(Item item, ref float gravity, ref float maxFallSpeed) {
			if (IsProduct) {
				item.shimmerTime = 0f;
				return;
			}
			if (IsStandIn && Main.netMode != NetmodeID.MultiplayerClient) {
				CombinedAltPlayer.RestoreWorldItem(item, ProxyOf);
			}
		}
	}
}

namespace Cogpunk.Content.Combinator.Combination
{
	/// <summary>
	/// A recipe that eats a Combinator product as its augment's type (vanilla counts and consumes ingredients by type,
	/// decompiled <c>Recipe.Create</c>/<c>ConsumeForCraft</c>) gives the base inside back to the crafter: it isn't what the
	/// recipe asked for. tModLoader hands the consumed clones to <c>OnCreated</c> (<c>RecipeItemCreationContext</c>), on the
	/// crafting client. Every item can be crafted, so this global applies to all and keeps no state.
	/// </summary>
	public sealed class CombinatorCraftRefund : GlobalItem
	{
		public override void OnCreated(Item item, ItemCreationContext context) {
			if (context is not RecipeItemCreationContext recipe || recipe.ConsumedItems == null) {
				return;
			}
			Player player = Main.LocalPlayer;
			foreach (Item used in recipe.ConsumedItems) {
				if (CombinedWeapon.TryGet(used, out CombinedWeapon data) && data.IsProduct) {
					SafeSpawn.TryGiveToLocalPlayer(player, data.Base, "CombinatorRefund");
				}
			}
		}
	}
}
