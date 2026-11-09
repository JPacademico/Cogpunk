using Cogpunk.Core.Templates;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Items
{
	/// <summary>
	/// Bottle of Lost Souls (Garrafa de Almas Perdidas), the Cursed Conductor's Expert item (user-set 2026-11-06: "the cursed
	/// conductor bag should always drop an accessory called bottle of lost souls that enables summon minions crit and gives
	/// +8% crit chance to minions"), always in his treasure bag (<see cref="CursedConductorLoot"/>).
	/// <list type="bullet">
	/// <item>Minions and sentries can land critical strikes (<see cref="LostSoulsPlayer"/>): vanilla's summon damage never
	/// rolls one (<c>SummonDamageClass.UseStandardCritCalcs</c> is false), so the owner's client rolls their
	/// <c>Projectile.CritChance</c> on every hit. tModLoader keeps that current for minions and sentries (the player's 4% base
	/// plus every summon and generic bonus, decompiled <c>Projectile.Update</c>); their shots carry their parent's. Whips are
	/// not minions and keep vanilla's rule.</item>
	/// <item>+<see cref="SummonCrit"/>% summon critical strike chance.</item>
	/// </list>
	/// Animated in the inventory and the world like vanilla's souls (<c>ItemID.Sets.AnimatesAsSoul</c>): two souls circle in
	/// the mist, <see cref="FrameTicks"/> ticks a frame. Art: art/bosses/cursedconductor/make_lost_souls_art.py. Balance:
	/// docs/balance/accessories.csv.
	/// </summary>
	public class BottleOfLostSouls : CogpunkItem
	{
		public const int SummonCrit = 8;                // percent, user-set
		public const int Frames = 4, FrameTicks = 6;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SummonCrit);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
			Main.RegisterItemAnimation(Type, new DrawAnimationVertical(FrameTicks, Frames));
			ItemID.Sets.AnimatesAsSoul[Type] = true;
		}

		public override void SetDefaults() {
			Item.width = 36;
			Item.height = 34;
			Item.accessory = true;
			Item.expert = true;
			Item.rare = ItemRarityID.LightRed;          // fought at the Wall of Flesh's tier
			Item.value = Item.sellPrice(gold: 3);
		}

		public override void UpdateAccessory(Player player, bool hideVisual) {
			player.GetModPlayer<LostSoulsPlayer>().MinionCrits = true;
			player.GetCritChance(DamageClass.Summon) += SummonCrit;
		}
	}
}
