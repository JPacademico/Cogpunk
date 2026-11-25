using System;
using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Summons
{
	/// <summary>
	/// The Jade Coin (user, 2026-11-24: "a new summon weapon called "jade coin" using a platinum coin + 8 jades. it should
	/// summon a jade bat and if used again instead off summoning another bat it should evolve the bat into a jade beetle and
	/// then into a jade golem and then into a jade loong (like defalult terraria cloud hard mode loong, but smaller and jade
	/// colored), each version stronger than the previous (like default terraria ghost abigail flower summon does). since the
	/// loong is the final form after that any more uses (if teh player still has summon slots) summons another bat that can
	/// be evolved just like the other one"), crafted once the research node Jade Menagerie is unlocked (Jadey's manual).
	/// <para>Built as vanilla's Abigail's Flower (decompiled 1.4.4: every use makes an invisible counter, projectile 970, that
	/// takes the minion slot, and one visible Abigail, 963, with no slot of her own, grows with the counters): every use makes
	/// a <see cref="JadeCoinCounter"/> (one slot); the visible <see cref="JadeSpirit"/>s take none, and spirit k shows
	/// counters 4k+1 .. 4k+4 as a bat, a beetle, a golem, a loong (<see cref="JadeSpirit.FormOf"/>): the fifth use starts a
	/// second bat. Freeing a slot (vanilla sacrifices the oldest counter when another minion needs it) takes the youngest
	/// spirit a form back.</para>
	/// <para>Balance (D3, docs/balance/weapons.csv; anchor the Imp Staff, T4: Jadey's tier): every form is worth its slots
	/// (<see cref="JadeSpirit.FormDamage"/>, <see cref="JadeSpirit.FormCooldown"/>), so N slots match N imps whatever the
	/// mix, and each form hits harder than the one before. Summon crits are rolled by the spirits (D3 rule 9), and the crit
	/// line is added back here.</para>
	/// <para>D2: the owner's client uses it and spawns (owner-only player projectiles); every client derives the forms from
	/// the owner's counters. D0: spawns through SafeSpawn; spirits capped at <see cref="JadeSpirit.MaxSpirits"/>.</para>
	/// </summary>
	public class JadeCoin : CogpunkItem
	{
		public const int Damage = 10, UseTime = 36, ManaCost = 10;

		public override void SetStaticDefaults() {
			ItemID.Sets.GamepadWholeScreenUseRange[Type] = true;
			ItemID.Sets.LockOnIgnoresCollision[Type] = true;
			ItemID.Sets.StaffMinionSlotsRequired[Type] = JadeCoinCounter.MinionSlots;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.knockBack = 2f;
			Item.mana = ManaCost;
			Item.DamageType = DamageClass.Summon;
			Item.useStyle = ItemUseStyleID.HoldUp;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.UseSound = SoundID.Item44;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.buffType = ModContent.BuffType<JadeCoinBuff>();
			Item.shoot = ModContent.ProjectileType<JadeCoinCounter>();
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.buyPrice(platinum: 1);          // it is a platinum coin (sells for a fifth, as every item)
			Item.rare = ItemRarityID.Orange;
		}

		public override void ModifyShootStats(Player player, ref Vector2 position, ref Vector2 velocity, ref int type, ref int damage, ref float knockback) {
			position = player.Center;                         // the counter rides on its owner
			velocity = Vector2.Zero;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			player.AddBuff(Item.buffType, 2);
			int counters = player.ownedProjectileCounts[type];
			if (SafeSpawn.TryNewProjectile(source, position, Vector2.Zero, type, damage, knockback, out Projectile counter, player.whoAmI)) {
				counter.originalDamage = Item.damage;
				JadeSpirit.EnsureSpirits(player, source, counters + 1, Item.damage);
			}
			return false;
		}

		// Summon damage hides vanilla's crit line (SummonDamageClass), but the spirits crit: shown as vanilla words it
		// (Lang.tip[41]), after the damage line, as the Mice-bot does.
		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Damage");
			if (index < 0) {
				return;
			}
			int crit = Main.LocalPlayer.GetWeaponCrit(Item);
			tooltips.Insert(index + 1, new TooltipLine(Mod, "CritChance", crit + Lang.tip[41].Value));
		}

		/// <summary>Research-locked (Jade Menagerie): <see cref="ResearchRecipes"/> hides it until the node is unlocked.</summary>
		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.PlatinumCoin)
				.AddIngredient<Gems.Items.Jade>(8)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}

	/// <summary>The Jade Coin's buff: kept while any counter lives (as every minion buff).</summary>
	public class JadeCoinBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoSave[Type] = true;
			Main.buffNoTimeDisplay[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			if (player.ownedProjectileCounts[ModContent.ProjectileType<JadeCoinCounter>()] > 0) {
				player.buffTime[buffIndex] = 18000;
			}
			else {
				player.DelBuff(buffIndex);
				buffIndex--;
			}
		}
	}

	/// <summary>
	/// One use of the Jade Coin: an invisible counter on its owner that holds one minion slot (vanilla's Abigail counter,
	/// decompiled 1.4.4 type 970: hidden, no damage, sacrificed first when a new minion needs room). The spirits read how
	/// many there are.
	/// </summary>
	public class JadeCoinCounter : CogpunkProjectile
	{
		public const float MinionSlots = 1f;

		public override string Texture => "Cogpunk/Content/Research/Summons/JadeCoin";

		public override void SetStaticDefaults() {
			Main.projPet[Type] = true;                        // vanilla frees slots only from "pet" minions
			ProjectileID.Sets.MinionSacrificable[Type] = true;
		}

		public override void SetDefaults() {
			Projectile.width = 10;
			Projectile.height = 10;
			Projectile.friendly = false;
			Projectile.minion = true;
			Projectile.minionSlots = MinionSlots;
			Projectile.DamageType = DamageClass.Summon;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.hide = true;
			Projectile.timeLeft = 60;
		}

		public override bool? CanCutTiles() => false;

		public override bool? CanDamage() => false;

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			int buff = ModContent.BuffType<JadeCoinBuff>();
			if (!owner.active || owner.dead) {
				owner.ClearBuff(buff);
				return;
			}
			if (owner.HasBuff(buff)) {
				Projectile.timeLeft = 2;
			}
			Projectile.Center = owner.Center;
			Projectile.velocity = Vector2.Zero;
		}

		public override bool PreDraw(ref Color lightColor) => false;
	}

	/// <summary>
	/// The owner's counters, for the spirits: how strong the coin that made them was (the highest <c>originalDamage</c>, as
	/// vanilla keeps <c>highestAbigailCounterOriginalDamage</c>), counted once a tick per player that has any; and, on the
	/// owner's client, a spirit that went missing (a counter with no spirit to show it) is called back every
	/// <see cref="RefillTicks"/> ticks.
	/// </summary>
	public class JadeCoinPlayer : ModPlayer
	{
		public const int RefillTicks = 30;

		/// <summary>The strongest counter's base damage (0 with none).</summary>
		public int CounterDamage { get; private set; }

		private int refill;

		public override void PostUpdate() {
			int type = ModContent.ProjectileType<JadeCoinCounter>();
			int counters = Player.ownedProjectileCounts[type];
			if (counters <= 0) {
				CounterDamage = 0;
				return;
			}
			int best = 0;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.owner == Player.whoAmI && p.type == type && p.originalDamage > best) {
					best = p.originalDamage;
				}
			}
			CounterDamage = best > 0 ? best : JadeCoin.Damage;
			if (Player.whoAmI == Main.myPlayer && ++refill >= RefillTicks) {
				refill = 0;
				JadeSpirit.EnsureSpirits(Player, Player.GetSource_Misc("JadeCoin"), counters, -1);
			}
		}
	}
}
