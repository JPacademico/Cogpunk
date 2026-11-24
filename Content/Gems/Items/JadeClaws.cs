using Cogpunk.Core.Templates;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Items
{
	/// <summary>
	/// Jade Claws (Garras de Jade), a claw that digs and fights (user, 2026-11-24: "a new weapon/mining tool called "jade claws"
	/// that can be found on hardmode fishing boxes, it has to be weaker than shroomite diggin claw but a powerfull pre-plantera
	/// claw melee weapon/digging tool", with a design image: a gauntlet of plum lacquer and gold scrollwork, leather straps, and
	/// four long jade crystal claws). Swung fast like the Shroomite Digging Claw.
	/// <para>Balance (D3; docs/balance/weapons.csv; T5, Hardmode crates are open from the Wall of Flesh on): just under the
	/// Shroomite Digging Claw (decompiled 1.4.4 <c>Item.SetDefaults</c> 2176: 45 damage, 12 animation / 4 use, 200% pick, 125% axe,
	/// knockback 6): <see cref="Damage"/> every <see cref="SwingTicks"/> ticks (208 eff DPS against its 234, -11%),
	/// <see cref="Pick"/>% pick (the Titanium Pickaxe's: everything before Chlorophyte), <see cref="Axe"/> x5 = 110% axe (the
	/// Pickaxe Axe's), a swing every <see cref="UseTime"/> ticks when digging (between the Shroomite Claw's 4 and the pickaxes'
	/// 7). Found in every Hardmode crate, 1 in <see cref="CrateOdds"/> (<see cref="JadeClawsCrates"/>; the rate is my call).
	/// It lends nothing to the Combinator (a tool: <c>CombinatorTraits.NoPassives</c>). Art: art/gems/make_jade_claws_art.py.</para>
	/// </summary>
	public class JadeClaws : CogpunkItem
	{
		public const int Damage = 40, SwingTicks = 12, UseTime = 5, Pick = 190, Axe = 22;
		public const float Knockback = 5.5f;
		public const int CrateOdds = 25;

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.DamageType = DamageClass.Melee;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useAnimation = SwingTicks;
			Item.useTime = UseTime;
			Item.knockBack = Knockback;
			Item.pick = Pick;
			Item.axe = Axe;
			Item.useTurn = true;
			Item.autoReuse = true;
			Item.UseSound = SoundID.Item1;
			Item.width = 20;                                 // the hitbox of a claw (the Shroomite Digging Claw's 20 x 12)
			Item.height = 12;
			Item.value = Item.sellPrice(gold: 4);
			Item.rare = ItemRarityID.Pink;
		}
	}

	/// <summary>The Jade Claws in the Hardmode crates (every biome's Hardmode twin and the Wooden, Iron and Golden ones), 1 in
	/// <see cref="JadeClaws.CrateOdds"/> beside the crate's own loot (vanilla opens crates through the item loot database).</summary>
	public sealed class JadeClawsCrates : GlobalItem
	{
		public override bool AppliesToEntity(Item entity, bool lateInstantiation) => IsHardmodeCrate(entity.type);

		public static bool IsHardmodeCrate(int type) => type == ItemID.WoodenCrateHard || type == ItemID.IronCrateHard
			|| type == ItemID.GoldenCrateHard || type == ItemID.CorruptFishingCrateHard || type == ItemID.CrimsonFishingCrateHard
			|| type == ItemID.DungeonFishingCrateHard || type == ItemID.FloatingIslandFishingCrateHard || type == ItemID.HallowedFishingCrateHard
			|| type == ItemID.JungleFishingCrateHard || type == ItemID.FrozenCrateHard || type == ItemID.OasisCrateHard
			|| type == ItemID.LavaCrateHard || type == ItemID.OceanCrateHard;

		public override void ModifyItemLoot(Item item, ItemLoot itemLoot) {
			itemLoot.Add(ItemDropRule.Common(ModContent.ItemType<JadeClaws>(), JadeClaws.CrateOdds));
		}
	}
}
