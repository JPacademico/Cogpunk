using System.Collections.Generic;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.Weapons
{
	/// <summary>
	/// Cursed Train Whistle (Apito do Trem Amaldiçoado), a summon weapon in the Cursed Conductor's weapon pool (user-set
	/// 2026-11-09: "a new weapon to the cursed conductor weapon pool called cursed whistle: summon weapon that summons a train
	/// minion (smaller than the boss train so it's not too visually aggressive), but only the head of the train, and using it
	/// to summon more adds wagons to the train instead of summoning more (like the stardust dragon default terraria summon);
	/// this summon should float around the player and attack the enemies by passing through enemies, dealing damage for every
	/// wagon that hits"). <b>Named "Cursed Train Whistle"</b> because the item that summons him is already the Cursed Whistle
	/// (<see cref="Items.CursedWhistle"/>): my call, flagged to the user.
	/// <para>The first blow calls the <see cref="GhostTrainEngine"/> (one minion slot); every further blow hitches a
	/// <see cref="GhostTrainWagon"/> behind the last (one slot each, at most <see cref="GhostTrainEngine.MaxWagons"/>), as the
	/// Stardust Dragon Staff adds body segments (decompiled 1.4.4 <c>Player.ItemCheck_Shoot</c>, item 3531). At full slots
	/// vanilla frees the oldest sacrificable minion first (<c>Player.FreeUpPetsAndMinions</c>): a wagon or another minion,
	/// never the engine (<c>ProjectileID.Sets.MinionCannotBeFreed</c>), so the train keeps its length.</para>
	/// <para>Balance (docs/balance/weapons.csv; T5 like the Conductor's other drops, anchor the Spider Staff: decompiled
	/// 1.4.4 item 2551, 26 damage, use time 36, 10 mana, a spider per slot hitting at most every 15 ticks): every segment hits
	/// for <see cref="Damage"/> once a pass (<see cref="GhostTrainEngine.HitCooldown"/>-tick immunity each), a pass about
	/// every <see cref="GhostTrainEngine.PassTicks"/> ticks on a single target; segments crit at the player's summon crit
	/// (rolled in <c>ModifyHitNPC</c>, as the other Cogpunk minions). Art: art/bosses/cursedconductor/make_train_whistle_art.py.</para>
	/// </summary>
	public class CursedTrainWhistle : CogpunkItem
	{
		public const int Damage = 57, Mana = 10, UseTime = 36;            // per segment a pass (docs/balance/weapons.csv)
		public const float Knockback = 2f;

		public override void SetStaticDefaults() {
			ItemID.Sets.GamepadWholeScreenUseRange[Type] = true;
			ItemID.Sets.LockOnIgnoresCollision[Type] = true;
			ItemID.Sets.StaffMinionSlotsRequired[Type] = 1f;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.knockBack = Knockback;
			Item.mana = Mana;
			Item.DamageType = DamageClass.Summon;
			Item.useStyle = ItemUseStyleID.HoldUp;           // the whistle lifted to the lips
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.UseSound = SoundID.DD2_WyvernScream with { Pitch = 0.9f, Volume = 0.45f };
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.buffType = ModContent.BuffType<GhostTrainBuff>();
			Item.shoot = ModContent.ProjectileType<GhostTrainEngine>();
			Item.width = 28;
			Item.height = 32;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.LightRed;               // the Cursed Lantern's (the Wall of Flesh's drops' rarity)
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			player.AddBuff(Item.buffType, 2);
			Projectile engine = GhostTrainEngine.FindOwned(player);
			if (engine == null) {
				Vector2 at = player.Center + new Vector2(0f, -GhostTrainEngine.OrbitHeight);
				if (SafeSpawn.TryNewProjectile(source, at, new Vector2(player.direction * GhostTrainEngine.IdleSpeed, 0f), type, damage, knockback,
					out Projectile head, player.whoAmI)) {
					head.originalDamage = Item.damage;
				}
				return false;
			}
			if (engine.ModProjectile is not GhostTrainEngine train || train.WagonCount >= GhostTrainEngine.MaxWagons) {
				return false;                                  // a full train: the blow is spent, nothing hitches on
			}
			float ticket = engine.ai[1];
			engine.ai[1] = ticket + 1f;
			engine.netUpdate = true;
			if (SafeSpawn.TryNewProjectile(source, engine.Center, Vector2.Zero, ModContent.ProjectileType<GhostTrainWagon>(), damage, knockback,
				out Projectile wagon, player.whoAmI, ticket, engine.projUUID)) {
				wagon.originalDamage = Item.damage;
				SoundEngine.PlaySound(SoundID.Item37 with { Pitch = -0.3f, Volume = 0.6f }, engine.Center);   // the coupling clanks
			}
			return false;
		}

		// Summon damage hides the vanilla crit line (SummonDamageClass.ShowStatTooltipLine), but the train does crit.
		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Damage");
			if (index < 0) {
				return;
			}
			int crit = Main.LocalPlayer.GetWeaponCrit(Item);
			tooltips.Insert(index + 1, new TooltipLine(Mod, "CritChance", crit + Lang.tip[41].Value));
		}
	}

	/// <summary>The ghost train's minion buff: stays while its engine runs (ExampleSimpleMinionBuff pattern).</summary>
	public class GhostTrainBuff : CogpunkBuff
	{
		public override void SetStaticDefaults() {
			Main.buffNoSave[Type] = true;
			Main.buffNoTimeDisplay[Type] = true;
		}

		public override void Update(Player player, ref int buffIndex) {
			if (player.ownedProjectileCounts[ModContent.ProjectileType<GhostTrainEngine>()] > 0) {
				player.buffTime[buffIndex] = 18000;
			}
			else {
				player.DelBuff(buffIndex);
				buffIndex--;
			}
		}
	}
}
