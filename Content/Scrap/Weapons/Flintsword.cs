using System;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Combat;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.Weapons
{
	/// <summary>
	/// Flintsword (user-set 2026-11-27: "a melee weapon that creates spark projectiles when hitting enemies. it should be as
	/// strong as a platinum sword. crafted using 2 rusted cogs and 4 iron/lead bars"): an iron broadsword fitted with a
	/// cog-driven flint striker at the guard. Every enemy hit scrapes a live spark (<c>ProjectileID.WandOfSparkingSpark</c>)
	/// off the edge.
	/// <para>Follows Cogpunk's directional melee rule (<see cref="DirectionalSwing"/>) and phantom slash trail rule
	/// (<see cref="FlintswordTrailLayer"/>). D3: 14 blade + 5 spark every 20 ticks = 59.3 eff DPS against the Platinum
	/// Broadsword's 58.7 (+1.0%; docs/balance/weapons.csv). D2: the striker's own client spawns the spark on hit.</para>
	/// </summary>
	public class Flintsword : CogpunkItem
	{
		public const int Damage = 14;
		public const int UseTime = 20;
		public const float Knockback = 5.5f;
		public const float SparkDamageShare = 0.36f;              // 14 x 0.36 = 5 base spark damage, scaling with melee bonuses
		public const int CogCost = 2, BarCost = 4;                // user-set

		// Measured along the 52x52 sprite's diagonal from its bottom-left corner (game px at scale 1):
		public const float GripFromCorner = 10f, BladeFrom = 18f, BladeTo = 70f, BladeRadius = 8f;

		private static readonly SoundStyle SparkSound = SoundID.Item8 with { Pitch = 0.45f, Volume = 0.55f, MaxInstances = 4 };

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.knockBack = Knockback;
			Item.DamageType = DamageClass.Melee;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.UseSound = SoundID.Item1;
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.sellPrice(silver: 14);
			Item.rare = ItemRarityID.White;
		}

		public override void UseStyle(Player player, Rectangle heldItemFrame) {
			float aim = DirectionalSwing.Aim(player);
			DirectionalSwing.PoseHeld(player, DirectionalSwing.VanillaArc(DirectionalSwing.Done(player)) + aim, GripFromCorner,
				player.GetAdjustedItemScale(Item));
			DirectionalSwing.Note(player);
		}

		public override void UseItemHitbox(Player player, ref Rectangle hitbox, ref bool noHitbox) {
			float scale = player.GetAdjustedItemScale(Item);
			if (DirectionalSwing.HeldBladeBounds(player, BladeFrom * scale, BladeTo * scale, BladeRadius * scale, out Rectangle bounds)) {
				hitbox = bounds;
			}
			else {
				noHitbox = true;
			}
		}

		public override bool? CanMeleeAttackCollideWithNPC(Rectangle meleeAttackHitbox, Player player, NPC target) {
			float scale = player.GetAdjustedItemScale(Item);
			return DirectionalSwing.HeldBladeSweepHits(player, BladeFrom * scale, BladeTo * scale, BladeRadius * scale, target.Hitbox);
		}

		public override void OnHitNPC(Player player, NPC target, NPC.HitInfo hit, int damageDone) {
			if (target == null || target.friendly || target.CountsAsACritter) {
				return;
			}
			if (player.whoAmI == Main.myPlayer) {
				int sparkDamage = Math.Max(1, (int)MathF.Round(hit.SourceDamage * SparkDamageShare));
				Vector2 spawn = Vector2.Lerp(player.MountedCenter, target.Center, 0.65f);
				Vector2 vel = new(player.direction * Main.rand.NextFloat(5.5f, 7.5f), Main.rand.NextFloat(-3.2f, -1.4f));
				if (SafeSpawn.TryNewProjectile(player.GetSource_OnHit(target), spawn, vel, ProjectileID.WandOfSparkingSpark,
						sparkDamage, Knockback * 0.4f, out Projectile proj, player.whoAmI)) {
					proj.DamageType = DamageClass.Melee;
					proj.usesLocalNPCImmunity = true;
					proj.localNPCHitCooldown = 20;
				}
			}
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SparkSound, target.Center);
				if (CogpunkClientConfig.RollEffect()) {
					for (int i = 0; i < 5; i++) {
						if (SafeSpawn.TryNewDust(target.Center - new Vector2(8f), 16, 16, DustID.Torch, out Dust d)) {
							d.velocity = Main.rand.NextVector2Circular(3f, 3f) - Vector2.UnitY * 1.2f;
							d.noGravity = true;
							d.scale = 1.15f;
						}
					}
				}
			}
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddIngredient<RustedCog>(CogCost)
				.AddRecipeGroup(RecipeGroupID.IronBar, BarCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}

	/// <summary>
	/// Flintsword's warm flint-spark phantom slash crescent (user rule, 0.2.2: every melee swing gets a phantom slash trail),
	/// pivoting at <c>itemLocation</c> along the directional swing's recent <c>itemRotation</c> history.
	/// </summary>
	public sealed class FlintswordTrailLayer : PlayerDrawLayer
	{
		public const int TrailFrames = 8;
		public const float TrailStep = 12f * MathHelper.Pi / 180f;
		public const int TrailTicks = 6;
		public const float TrailMin = 0.15f;
		public const float TrailFull = 0.9f;
		public const float TrailOpacity = 0.55f;
		public const int Gap = 2;
		public const int TrailW = 96, TrailH = 88, TrailPivotX = 12, TrailPivotY = 84;

		private static Asset<Texture2D> trail;
		private static int swordType = -1;

		public override void Load() {
			trail = DepthLayers.RequestOptional("Cogpunk/Content/Scrap/Weapons/FlintswordTrail");
		}

		public override void Unload() {
			trail = null;
			swordType = -1;
		}

		public override Position GetDefaultPosition() => new BeforeParent(PlayerDrawLayers.HeldItem);

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo) {
			if (swordType < 0) {
				swordType = ModContent.ItemType<Flintsword>();
			}
			Player player = drawInfo.drawPlayer;
			return drawInfo.shadow == 0f && player.itemAnimation > 0 && player.HeldItem.type == swordType && !player.dead && !player.frozen
				&& !player.pulley && player.HeldItem.useStyle == ItemUseStyleID.Swing;
		}

		protected override void Draw(ref PlayerDrawSet drawInfo) {
			if (trail?.IsLoaded != true) {
				return;
			}
			Player player = drawInfo.drawPlayer;
			int back = Math.Min(TrailTicks, DirectionalSwing.Noted(player) - 1);
			if (back < 1) {
				return;
			}
			Vector2 now = SwingPose.HeldBladeDirection(player, player.itemRotation);
			Vector2 then = SwingPose.HeldBladeDirection(player, DirectionalSwing.Rotation(player, back, player.itemRotation));
			float sweep = MathF.Atan2(then.X * now.Y - then.Y * now.X, Vector2.Dot(then, now));
			float span = MathF.Abs(sweep);
			if (!float.IsFinite(span) || span < TrailMin) {
				return;
			}
			int frame = Math.Clamp((int)(span / TrailStep + 0.5f), 1, TrailFrames) - 1;
			Rectangle source = new(0, frame * (TrailH + Gap), TrailW, TrailH);
			if (source.Bottom > trail.Value.Height) {
				return;
			}
			bool clockwise = sweep > 0f;
			Vector2 origin = new(TrailPivotX, clockwise ? TrailPivotY : TrailH - TrailPivotY);
			float opacity = TrailOpacity * MathHelper.Clamp(span / TrailFull, 0.35f, 1f);
			Color color = new Color(255, 255, 255, 0) * opacity;
			Vector2 location = drawInfo.Position + (player.itemLocation - player.position);
			Vector2 at = new((int)(location.X - Main.screenPosition.X), (int)(location.Y - Main.screenPosition.Y));
			drawInfo.DrawDataCache.Add(new DrawData(trail.Value, at, source, color, MathF.Atan2(now.Y, now.X),
				origin, player.GetAdjustedItemScale(player.HeldItem), clockwise ? SpriteEffects.None : SpriteEffects.FlipVertically));
		}
	}
}
