using System;
using System.Collections.Generic;
using Cogpunk.Content.Mechanist;
using Cogpunk.Content.OldBrassTown.Weapons;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Weapons
{
	/// <summary>
	/// Bandit's Dream (Sonho do Bandido), the Sheriff's Revolver with a sabre's blade along its barrel (user-set 2026-11-19: "a
	/// old west revolver with a sharp blade atatched ... it should have the same 6 bulets then reload mechanic that the sherif
	/// revolver has (and the ricochet bulets) but on the right click it performs a quick slash attack on front (molten sword
	/// range) that deals 6x the weapon damage and destroy enemy projectiles, costing 10 steam and can be performed mid
	/// reload"). Its recipe is locked until the "Bring a Knife to a Gunfight" node (the Sheriff's Law Book reveals it).
	/// <list type="bullet">
	/// <item><b>Left click</b>: the revolver's own: <see cref="SheriffsBullet"/> (bullets for ammo, the bullet's damage added;
	/// ricochets off walls only, 2026-11-19), six rounds then a 1.5 s reload. The cylinder is the player's
	/// (<see cref="SheriffsRevolverPlayer"/>), shared with the Sheriff's Revolver.</item>
	/// <item><b>Right click</b>: a quick slash in front (<see cref="BanditsSlash"/>: the Volcano's reach, the molten sword's),
	/// <see cref="SlashMultiplier"/>x the gun's damage, cutting enemy projectiles out of the air, for <see cref="SlashSteamCost"/>
	/// steam (a steam skill, <see cref="ISteamSkill"/>). Not an item use (<see cref="BanditsDreamPlayer"/> starts it): it
	/// needs no bullet and works while the cylinder reloads.</item>
	/// </list>
	/// D2: the owner shoots and slashes; the slash is a player projectile, so the server runs it too and destroys hostile
	/// projectiles where it is authoritative. Balance: docs/balance/weapons.csv.
	/// </summary>
	public class BanditsDream : CogpunkItem, ISteamSkill
	{
		public const int Damage = 34, UseTime = 23;                 // my call (the revolver: 26), see the CSV
		public const int SlashSteamCost = 10;                       // user-set
		public const float SlashMultiplier = 6f;                    // user-set: "6x the weapon damage"
		public const float AimSpread = 1f, ShotSpeed = 16f, MuzzleDistance = 44f;   // the muzzle: 44 px from the hand (the sprite)
		public const int TarCost = 8, BarCost = 10;                 // my call: the user named the parts, not the counts

		public int SkillSteamCost => SlashSteamCost;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(SheriffsRevolverPlayer.Chambers, SheriffsRevolverPlayer.ReloadTicks / 60f,
			(int)SlashMultiplier, SlashSteamCost);

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.crit = 2;                                          // the revolver's 6%
			Item.knockBack = 4f;
			Item.DamageType = DamageClass.Ranged;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<SheriffsBullet>();
			Item.shootSpeed = ShotSpeed;
			Item.useAmmo = AmmoID.Bullet;
			Item.UseSound = SoundID.Item41 with { Pitch = -0.2f };
			Item.width = 80;                                        // the sprite: 40 x 15 at 1x
			Item.height = 30;
			Item.value = Item.sellPrice(gold: 6);
			Item.rare = ItemRarityID.LightRed;
		}

		public override bool CanUseItem(Player player) {
			SheriffsRevolverPlayer cylinder = player.GetModPlayer<SheriffsRevolverPlayer>();
			return !cylinder.Reloading && cylinder.Rounds > 0 && player.GetModPlayer<BanditsDreamPlayer>().SlashTicks <= 0;
		}

		public override Vector2? HoldoutOffset() => new Vector2(-4f, 0f);  // the hand on the frame over the grip

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			SheriffsRevolverPlayer cylinder = player.GetModPlayer<SheriffsRevolverPlayer>();
			if (cylinder.Rounds <= 0) {
				return false;
			}
			type = ModContent.ProjectileType<SheriffsBullet>();
			Vector2 direction = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 muzzle = direction * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
			velocity = velocity.RotatedBy(Main.rand.NextFloat(-1f, 1f) * MathHelper.ToRadians(AimSpread));
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI);
			cylinder.Fired();
			return false;
		}

		public override void ModifyTooltips(List<TooltipLine> tooltips) {
			SteamSkillTooltip.AddNoTankLine(Mod, tooltips, SlashSteamCost);
			SheriffsRevolverPlayer cylinder = Main.LocalPlayer.GetModPlayer<SheriffsRevolverPlayer>();
			int index = tooltips.FindIndex(static line => line.Mod == "Terraria" && line.Name == "Knockback");
			TooltipLine rounds = new(Mod, "Rounds", Language.GetTextValue("Mods.Cogpunk.Items.SheriffsRevolver.Rounds", cylinder.Rounds, SheriffsRevolverPlayer.Chambers));
			if (index >= 0) {
				tooltips.Insert(index + 1, rounds);
			}
			else {
				tooltips.Add(rounds);
			}
		}

		public override void AddRecipes() {
			CreateRecipe().AddIngredient<SheriffsRevolver>().AddIngredient<Junkyard.Items.CondensedTar>(TarCost)
				.AddRecipeGroup(VanillaRecipeGroups.GoldBar, BarCost).AddTile(TileID.Anvils).Register();
		}
	}

	/// <summary>
	/// The Bandit's Dream's right click (the Metal Wrench's pattern: caught just before the item check, where vanilla takes its
	/// own right clicks, so it is no item use and needs no bullet): pays <see cref="BanditsDream.SlashSteamCost"/> steam and
	/// throws the <see cref="BanditsSlash"/> at the cursor, <see cref="BanditsDream.SlashMultiplier"/>x the gun's damage.
	/// D2: the owner's; the slash projectile carries the aim (ai[0]) to everyone.
	/// </summary>
	public sealed class BanditsDreamPlayer : ModPlayer
	{
		/// <summary>Owner: ticks until the next slash may start (the slash and a short pause; no shots meanwhile).</summary>
		public int SlashTicks;
		public const int PauseTicks = 6;

		public override void PostUpdate() {
			if (SlashTicks > 0) {
				SlashTicks--;
			}
		}

		public override bool PreItemCheck() {
			if (Player.whoAmI != Main.myPlayer || SlashTicks > 0 || Player.HeldItem?.type != ModContent.ItemType<BanditsDream>()) {
				return true;
			}
			bool rightClick = Player.controlUseTile && Main.mouseRightRelease && !Player.tileInteractionHappened && Player.releaseUseItem
				&& !Player.controlUseItem && !Player.mouseInterface && !Main.HoveringOverAnNPC && !Main.SmartInteractShowingGenuine;
			if (!rightClick || Player.itemAnimation > 0 || Player.CCed || Player.noItems || Player.dead) {
				return true;
			}
			Main.mouseRightRelease = false;
			if (!Player.GetModPlayer<SteamPlayer>().TryPayAttack(BanditsDream.SlashSteamCost, out _)) {
				return true;                                // no tank (a hint) or too little steam (an overheat)
			}
			Vector2 aim = (Main.MouseWorld - Player.MountedCenter).SafeNormalize(Vector2.UnitX * Player.direction);
			Player.direction = aim.X >= 0f ? 1 : -1;
			int damage = (int)Math.Round(Player.GetWeaponDamage(Player.HeldItem) * BanditsDream.SlashMultiplier);
			float knockback = Player.GetWeaponKnockback(Player.HeldItem) * 1.5f;
			if (SafeSpawn.TryNewProjectile(Player.GetSource_ItemUse(Player.HeldItem), Player.MountedCenter, aim, ModContent.ProjectileType<BanditsSlash>(),
				damage, knockback, out _, Player.whoAmI, aim.ToRotation(), Player.direction)) {
				SlashTicks = BanditsSlash.Ticks + PauseTicks;
				SoundEngine.PlaySound(SoundID.Item71 with { Pitch = 0.2f, Volume = 0.8f }, Player.Center);
			}
			return true;
		}
	}

	/// <summary>
	/// The Bandit's Dream's slash: the whole weapon swept through <see cref="Arc"/> radians round the aim in
	/// <see cref="Ticks"/> ticks (quick), blade first, out to <see cref="Reach"/> px (the Volcano's: its 54 px sprite held at
	/// arm's length). Each enemy is hit once; every hostile projectile its blade crosses is destroyed (the server's copy of
	/// this player projectile does it, authoritative in multiplayer; the owner's copy too, so it shows at once). Huge ones
	/// (beams over <see cref="MaxCutSize"/> px) are left alone. D0: owner and indices checked; finite life.
	/// </summary>
	public class BanditsSlash : CogpunkProjectile
	{
		public const int Ticks = 12;
		public const float Arc = 2.4f, Reach = 80f, BladeWidth = 16f, MaxCutSize = 64f;
		/// <summary>The sprite's hand hold (2x px) and how far its blade's tip sits above the line from there (radians): the
		/// drawing turns by it so the drawn tip lies on the cutting line.</summary>
		public const float GripX = 8f, GripY = 17f, TipTilt = 0.22f;

		private float Aim => Projectile.ai[0];
		private int Side => Projectile.ai[1] < 0f ? -1 : 1;

		public override string Texture => "Cogpunk/Content/Research/Weapons/BanditsDream";

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ownerHitCheck = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
			Projectile.timeLeft = Ticks;
			Projectile.aiStyle = -1;
			Projectile.hide = true;
		}

		/// <summary>The blade's angle now: from behind the aim to past it, over the facing side.</summary>
		private float BladeAngle() {
			float progress = 1f - Projectile.timeLeft / (float)Ticks;
			return Aim - Side * Arc * 0.5f + Side * Arc * progress;
		}

		public override void AI() {
			if (Projectile.owner < 0 || Projectile.owner >= Main.maxPlayers || !Main.player[Projectile.owner].active || Main.player[Projectile.owner].dead) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[Projectile.owner];
			Projectile.Center = owner.MountedCenter;
			float angle = BladeAngle();
			Projectile.rotation = angle;
			owner.heldProj = Projectile.whoAmI;
			owner.SetCompositeArmFront(true, Player.CompositeArmStretchAmount.Full, angle - MathHelper.PiOver2);
			Vector2 tip = Projectile.Center + angle.ToRotationVector2() * Reach;
			if (Main.netMode != NetmodeID.MultiplayerClient || Projectile.owner == Main.myPlayer) {
				foreach (Projectile p in Main.ActiveProjectiles) {
					if (!p.hostile || p.friendly || p.damage <= 0 || p.width > MaxCutSize || p.height > MaxCutSize) {
						continue;
					}
					float point = 0f;
					if (Collision.CheckAABBvLineCollision(p.position, p.Size, Projectile.Center, tip, BladeWidth, ref point)) {
						p.Kill();
						if (!Main.dedServ) {
							SoundEngine.PlaySound(SoundID.Item10 with { Pitch = 0.8f, Volume = 0.5f, MaxInstances = 3 }, p.Center);
						}
					}
				}
			}
			if (!Main.dedServ && Main.rand.NextBool(2)) {
				Vector2 at = Projectile.Center + angle.ToRotationVector2() * Main.rand.NextFloat(Reach * 0.5f, Reach);
				if (SafeSpawn.TryNewDust(at - new Vector2(2f), 4, 4, DustID.GoldFlame, out Dust d)) {
					d.noGravity = true;
					d.velocity = (angle + Side * MathHelper.PiOver2).ToRotationVector2() * 2f;
					d.scale = 0.9f;
				}
			}
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			float point = 0f;
			Vector2 tip = Projectile.Center + BladeAngle().ToRotationVector2() * Reach;
			return Collision.CheckAABBvLineCollision(targetHitbox.TopLeft(), targetHitbox.Size(), Projectile.Center, tip, BladeWidth, ref point);
		}

		// The weapon itself, turned along the blade (held items turn in vanilla), its grip at the hand. Drawn once, by the
		// owner's held-projectile layer (heldProj; hide keeps vanilla's projectile pass from drawing it a second time).
		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			float angle = BladeAngle();
			bool left = Math.Cos(angle) < 0;
			SpriteEffects fx = left ? SpriteEffects.FlipVertically : SpriteEffects.None;
			Vector2 origin = new(GripX, left ? texture.Height - GripY : GripY);
			float rotation = angle + (left ? -TipTilt : TipTilt);
			Main.EntitySpriteDraw(texture, Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY), null, lightColor, rotation, origin, 1f, fx);
			return false;
		}
	}
}
