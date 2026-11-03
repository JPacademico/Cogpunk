using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Junkyard.Weapons
{
	/// <summary>
	/// Metal Wrench (user-set 2026-10-30): a big, slow wrench of polished metal swung like a sword (<see cref="UseTime"/>
	/// ticks a swing). Redrawn 2026-11-03 (user: "a big thick metal wrench the size of a sword like the Blade of Grass"):
	/// a 68x68 open-end wrench, the Blade of Grass's 1.4.4 sprite size (a swing's hitbox is the sprite's frame, decompiled
	/// <c>Player.ItemCheck_GetMeleeHitbox</c>; the item's own 40x40 is only its hitbox on the ground, as the Blade of
	/// Grass's) that deals +<see cref="MechanicalBonus"/>% to mechanical enemies
	/// (<see cref="CogpunkSets.Mechanical"/>, like the Screwdriver).
	/// <list type="bullet">
	/// <item><b>Right click</b>: a parry. For <see cref="ParryTicks"/> ticks the wrench is held up on guard
	/// (<see cref="MetalWrenchGuard"/>); an enemy attack landing in that window (contact or projectile) clangs off it
	/// (<see cref="MetalClash"/>), deals nothing and readies the riposte. Then <see cref="CooldownTicks"/> ticks of cooldown
	/// (<see cref="WrenchParryCooldown"/>).</item>
	/// <item><b>The riposte</b> (<see cref="WrenchRiposteBuff"/>): the next swing deals x<see cref="RiposteMultiplier"/> to
	/// whatever it hits; landed on a boss or a mini-boss (<see cref="CogpunkSets.IsBossOrMiniboss"/>) it clashes and every
	/// entity slows by 80% for half a second (<see cref="SlowMotion"/>, for the effect).</item>
	/// </list>
	/// The rules live in <see cref="MetalWrenchPlayer"/>. Balance: docs/balance/weapons.csv (anchor: Blade of Grass).
	/// </summary>
	public class MetalWrench : CogpunkItem
	{
		public const int UseTime = 30;
		public const int MechanicalBonus = 50;            // percent
		public const int ParryTicks = 60;                 // a 1 s window (user-set)
		public const int CooldownTicks = 180;             // 3 s (user-set), from the end of the guard
		public const float RiposteMultiplier = 2.5f;      // user-set
		public const int RiposteBuffTicks = 18000;        // it waits for the next swing (5 min, then it fades)
		public const int SlowMotionTicks = 30;            // half a second (user-set)
		public const float SlowMotionSpeed = 0.2f;        // "slows 80%" (user-set)

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MechanicalBonus, ParryTicks / 60f, CooldownTicks / 60f, RiposteMultiplier);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 32;
			Item.crit = 2;                                 // + the player's base 4% = 6% (user-set)
			Item.knockBack = 6.5f;
			Item.DamageType = DamageClass.Melee;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.UseSound = SoundID.Item1 with { Pitch = -0.35f };
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.sellPrice(silver: 60);
			Item.rare = ItemRarityID.Orange;
		}

		// The parry isn't an item use (a swing would show): MetalWrenchPlayer starts it on a right click. No swing while
		// on guard.
		public override bool CanUseItem(Player player) => !player.GetModPlayer<MetalWrenchPlayer>().Guarding;

		public override bool? UseItem(Player player) {
			if (player.whoAmI == Main.myPlayer) {
				player.GetModPlayer<MetalWrenchPlayer>().BeginSwing();
			}
			return null;
		}

		public override void ModifyHitNPC(Player player, NPC target, ref NPC.HitModifiers modifiers) {
			if (CogpunkSets.IsMechanical(target)) {
				modifiers.SourceDamage *= 1f + MechanicalBonus / 100f;
			}
			if (player.GetModPlayer<MetalWrenchPlayer>().RiposteSwing) {
				modifiers.SourceDamage *= RiposteMultiplier;
			}
		}

		public override void OnHitNPC(Player player, NPC target, NPC.HitInfo hit, int damageDone) {
			player.GetModPlayer<MetalWrenchPlayer>().OnSwingHit(target);
		}

		// The riposte swing throws brass sparks off the wrench (every client: the buff is synced and stays on until the
		// swing ends).
		public override void MeleeEffects(Player player, Rectangle hitbox) {
			if (Main.dedServ || !player.HasBuff<WrenchRiposteBuff>() || !CogpunkClientConfig.RollEffect() || !Main.rand.NextBool(2)) {
				return;
			}
			if (SafeSpawn.TryNewDust(hitbox.TopLeft(), hitbox.Width, hitbox.Height, Main.rand.NextBool(3) ? DustID.GoldFlame : DustID.Enchanted_Gold,
				out Dust spark, player.velocity.X * 0.2f, -1f)) {
				spark.noGravity = true;
				spark.scale = 1.1f;
			}
			Lighting.AddLight(hitbox.Center.ToVector2(), 0.5f, 0.4f, 0.15f);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<PolishedMetal>(22)
				.AddIngredient<CondensedTar>(4)
				.AddIngredient<RustedCog>(16)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
