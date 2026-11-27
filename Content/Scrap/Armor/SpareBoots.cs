using System;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Armor
{
	/// <summary>
	/// Spare Boots (user-set 2026-11-27: "spare boots crafted using wood greaves + 3 rusted cogs. it should give 12% move
	/// speed"): Wooden Greaves fitted with cog-jointed ankle plates.
	/// </summary>
	[AutoloadEquip(EquipType.Legs)]
	public class SpareBoots : CogpunkItem
	{
		public const int Defense = 3;
		public const int MoveSpeedBonus = 12;         // user-set: +12% movement speed
		public const int CogCost = 3;                 // user-set

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(MoveSpeedBonus);

		public override void Load() {
			AnimatedEquip.Register(this, EquipType.Legs, SpareHelmet.CogFrames, SpareHelmet.CogTicksPerFrame);
		}

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.width = 22;
			Item.height = 18;
			Item.value = Item.sellPrice(silver: 5);
			Item.rare = ItemRarityID.White;
			Item.defense = Defense;
		}

		public override void UpdateEquip(Player player) {
			player.moveSpeed += MoveSpeedBonus / 100f;
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient(ItemID.WoodGreaves)
				.AddIngredient<RustedCog>(CogCost)
				.AddTile(TileID.WorkBenches)
				.Register();
		}
	}

	/// <summary>
	/// Spare armor's set bonus (user-set 2026-11-27: "the full set bonus should be that when taking damage it releases damaging
	/// spark"): on taking damage, the hurt player's client fans <see cref="SparkCount"/> Wand of Sparking sparks upward and
	/// outward at <see cref="SparkDamage"/> generic damage. Guarded by a short cooldown (D0) and owner-only projectile spawning (D2).
	/// </summary>
	public sealed class SpareArmorPlayer : ModPlayer
	{
		public const int SparkCount = 5;
		public const int SparkDamage = 15;
		public const float SparkKnockback = 1.5f;
		public const int SparkCooldownTicks = 15;

		public bool SparkOnHurt;
		private int cooldown;

		public override void ResetEffects() {
			SparkOnHurt = false;
			if (cooldown > 0) {
				cooldown--;
			}
		}

		public override void OnHurt(Player.HurtInfo info) {
			if (!SparkOnHurt || cooldown > 0 || Player.dead) {
				return;
			}
			cooldown = SparkCooldownTicks;
			if (Player.whoAmI == Main.myPlayer) {
				int damage = Math.Max(1, (int)Player.GetTotalDamage(DamageClass.Generic).ApplyTo(SparkDamage));
				var source = Player.GetSource_Misc("SetBonus_SpareArmor");
				for (int i = 0; i < SparkCount; i++) {
					float t = SparkCount > 1 ? i / (float)(SparkCount - 1) : 0.5f;
					float angle = MathHelper.Lerp(-MathHelper.Pi * 0.82f, -MathHelper.Pi * 0.18f, t) + Main.rand.NextFloat(-0.08f, 0.08f);
					Vector2 vel = angle.ToRotationVector2() * Main.rand.NextFloat(6f, 8f);
					if (SafeSpawn.TryNewProjectile(source, Player.MountedCenter, vel, ProjectileID.WandOfSparkingSpark, damage,
							SparkKnockback, out Projectile proj, Player.whoAmI)) {
						proj.DamageType = DamageClass.Generic;
						proj.usesLocalNPCImmunity = true;
						proj.localNPCHitCooldown = 20;
					}
				}
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item8 with { Pitch = 0.35f, Volume = 0.65f }, Player.Center);
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 8; i++) {
						if (SafeSpawn.TryNewDust(Player.position, Player.width, Player.height, DustID.Torch, out Dust d)) {
							d.velocity = Main.rand.NextVector2Circular(3.5f, 3.5f) - Vector2.UnitY;
							d.noGravity = true;
							d.scale = 1.2f;
						}
					}
				}
			}
		}
	}
}
