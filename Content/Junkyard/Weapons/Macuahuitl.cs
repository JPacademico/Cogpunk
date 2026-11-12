using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// Macuahuitl, an obsidian-edged wooden war club (user-set 2026-11-11, with a reference image: "a new melee weapon crafted
	/// using 20 wood + 8 obsidian + 3 condensed tar; it should cause 23 damage and deal double damage on the first hit against
	/// an enemy (4x if it crits), same range as the metal wrench but attacks faster and 12% base crit chance; it should also be
	/// a material for a future melee weapon"; the name is mine, the real weapon its picture shows). Swung like a sword:
	/// <see cref="Damage"/> a hit, <see cref="UseTime"/> ticks a swing (the Metal Wrench's 30, faster), the Metal Wrench's
	/// 68x68 sprite (a swing reaches as far as its sprite's frame, decompiled <c>Player.ItemCheck_GetMeleeHitbox</c>), crit
	/// <see cref="CritBonus"/> over the player's base 4% (12%).
	/// <para><b>The first cut</b>: the first time the wearer's club strikes an enemy it deals x<see cref="FirstHitMultiplier"/>
	/// (a crit doubles that again: x4), with a crack of obsidian; every later hit on that enemy is plain. Kept per enemy
	/// (the root of a worm's or a boss's linked parts) on the striker's own client (<see cref="MacuahuitlStruck"/>), which is
	/// where vanilla works out a player's melee hits (D2). The future weapon it is a material for will list it in its recipe
	/// (tModLoader marks recipe ingredients as materials itself).</para>
	/// <para>Balance: docs/balance/weapons.csv (anchor the Blade of Grass). Recipe at an anvil (my call). Art:
	/// art/junkyard/make_macuahuitl_art.py.</para>
	/// </summary>
	public class Macuahuitl : CogpunkItem
	{
		public const int Damage = 23;                            // user-set
		public const int CritBonus = 8;                          // user-set: 12% with the player's own 4% (D3 rule 9)
		public const int UseTime = 25;                           // my call: faster than the Metal Wrench's 30; 61.8 effective DPS, +10%
		public const float Knockback = 5f;
		public const float FirstHitMultiplier = 2f;              // user-set: x2 on the first hit (x4 with a crit)
		public const int WoodCost = 20, ObsidianCost = 8, TarCost = 3;   // user-set

		private static readonly SoundStyle CrackSound = SoundID.Item70 with { Pitch = 0.4f, Volume = 0.6f, PitchVariance = 0.15f };

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs((int)FirstHitMultiplier, (int)(FirstHitMultiplier * 2));

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = CritBonus;
			Item.knockBack = Knockback;
			Item.DamageType = DamageClass.Melee;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.UseSound = SoundID.Item1;
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.sellPrice(silver: 40);
			Item.rare = ItemRarityID.Green;
		}

		public override void ModifyHitNPC(Player player, NPC target, ref NPC.HitModifiers modifiers) {
			if (!MacuahuitlStruck.Struck(target)) {
				modifiers.SourceDamage *= FirstHitMultiplier;    // a crit doubles the result again: x4
			}
		}

		public override void OnHitNPC(Player player, NPC target, NPC.HitInfo hit, int damageDone) {
			if (MacuahuitlStruck.Mark(target) && !Main.dedServ) {
				SoundEngine.PlaySound(CrackSound, target.Center);
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 8; i++) {                // obsidian chips off the first cut
						if (SafeSpawn.TryNewDust(target.Center - new Vector2(10f), 20, 20, DustID.Obsidian, out Dust chip)) {
							chip.velocity = Main.rand.NextVector2Circular(3f, 3f) - Vector2.UnitY;
							chip.scale = 1.1f;
						}
					}
				}
			}
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddRecipeGroup(RecipeGroupID.Wood, WoodCost)
				.AddIngredient(ItemID.Obsidian, ObsidianCost)
				.AddIngredient<CondensedTar>(TarCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}

	/// <summary>
	/// Which enemies this client's player has already cut with the <see cref="Macuahuitl"/>: a flag per NPC (the root of
	/// linked parts), only ever set by the local player's hits (vanilla works out a player's melee hits on that player's
	/// client, so each client keeps its own player's: two club-wielders each get their own first cut). A new NPC in the slot
	/// gets new globals (decompiled <c>NPCLoader.SetDefaults</c> re-creates them through
	/// <c>GlobalLoaderUtils.SetDefaults</c>), so the flag never outlives its enemy. D1: one bool per hostile NPC; town NPCs
	/// and other friendly NPCs (which a club can't hit) carry none, and an NPC without the flag gets no bonus.
	/// </summary>
	public sealed class MacuahuitlStruck : GlobalNPC
	{
		public override bool InstancePerEntity => true;

		// Decided after SetDefaults, when friendly is known.
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => lateInstantiation && !entity.friendly;

		private bool struck;

		/// <summary>The NPC whose flag counts: the root of a worm's or a boss's parts.</summary>
		private static NPC Root(NPC npc) {
			int root = npc.realLife;
			return root >= 0 && root < Main.maxNPCs && Main.npc[root].active ? Main.npc[root] : npc;
		}

		/// <summary>True if this client's player has already cut <paramref name="npc"/> with the club (or the NPC isn't
		/// tracked, which means no bonus).</summary>
		public static bool Struck(NPC npc) => !Root(npc).TryGetGlobalNPC(out MacuahuitlStruck g) || g.struck;

		/// <summary>Marks <paramref name="npc"/> cut; true if this was the first time.</summary>
		public static bool Mark(NPC npc) {
			if (!Root(npc).TryGetGlobalNPC(out MacuahuitlStruck g) || g.struck) {
				return false;
			}
			g.struck = true;
			return true;
		}
	}
}
