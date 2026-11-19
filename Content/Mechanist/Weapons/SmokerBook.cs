using System;
using System.Collections.Generic;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.WorldGeneration;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.IO;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.WorldBuilding;

namespace Cogpunk.Content.Mechanist.Weapons
{
	/// <summary>
	/// Smoker Book (Livro Fumegante), a Mechanist tome found in the Underworld's Shadow Chests (user-set 2026-11-19: "a weapon
	/// that shoots mid range big area (10% smaller than player in high) quick smoke trail that pieces and does damage to
	/// everything onthe way, costs 8 steam"). Each use sends a <see cref="SmokerSmoke"/> rushing out <see cref="RangeTiles"/>
	/// tiles: a band of soot <see cref="SmokerSmoke.BandHeight"/> px tall (the player is 42) that hits every enemy it passes
	/// once, then hangs in the air and thins away.
	/// <para>Balance: docs/balance/weapons.csv (anchor the Flamelash, a Shadow Chest weapon: decompiled Item 113, 35 damage,
	/// use time 22). Art: art/mechanist/make_smoker_book_art.py. Loot: <see cref="SmokerBookPass"/>.</para>
	/// </summary>
	public class SmokerBook : MechanistWeapon
	{
		public const int Damage = 36, UseTime = 26;               // my call: 86.4 a target (-13% on the Flamelash), every enemy in line
		public const int Steam = 8;                               // user-set
		public const float Speed = 20f;                           // px a tick: "quick"
		public const int RangeTiles = 22;                         // "mid range" (my call): the smoke runs RangeTiles x 16 px
		public const float MuzzleDistance = 18f;

		public override int SteamCost => Steam;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs(RangeTiles);

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.DamageType = ModContent.GetInstance<MechanistDamage>();
			Item.knockBack = 3f;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<SmokerSmoke>();
			Item.shootSpeed = Speed;
			Item.UseSound = SoundID.Item34 with { Pitch = -0.6f, Volume = 0.7f };
			Item.width = 28;
			Item.height = 34;
			Item.value = Item.sellPrice(gold: 2);
			Item.rare = ItemRarityID.Orange;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			Vector2 direction = velocity.SafeNormalize(Vector2.UnitX * player.direction);
			Vector2 muzzle = direction * MuzzleDistance;
			if (Collision.CanHit(position, 0, 0, position + muzzle, 0, 0)) {
				position += muzzle;
			}
			SafeSpawn.TryNewProjectile(source, position, direction * Speed, type, damage, knockback, out _, player.whoAmI);
			return false;
		}
	}

	/// <summary>
	/// The Smoker Book's smoke: an unseen front rushing out at <see cref="SmokerBook.Speed"/> px a tick for
	/// <see cref="MoveTicks"/> ticks (or until it meets a wall), every enemy within <see cref="BandHeight"/> / 2 px of its path
	/// hit once (the path between two ticks is swept: nothing slips through); behind it a trail of soot puffs, one every
	/// <see cref="PuffSpacing"/> px, each laid as the front passes, swelling and rising a little and thinning over
	/// <see cref="FadeTicks"/> ticks. ai[0] counts its ticks (every side counts the same); the trail's start is where each side
	/// first saw it (localAI). D1: the trail is computed while drawing (no list); at most ~30 puffs. D0: finite life, the tile
	/// check on a small box (a 2-tile tunnel doesn't stop it), positions checked.
	/// </summary>
	public class SmokerSmoke : CogpunkProjectile
	{
		public const int BandHeight = 38;                         // 10% under the player's 42 (user-set)
		public const int MoveTicks = SmokerBook.RangeTiles * 16 / (int)SmokerBook.Speed;   // 17
		public const int FadeTicks = 30;
		public const float PuffSpacing = 12f;
		private const int PuffFrames = 4, PuffSize = 40, PuffStride = 42;

		private ref float Ticks => ref Projectile.ai[0];
		private ref float StartX => ref Projectile.localAI[0];
		private ref float StartY => ref Projectile.localAI[1];
		private ref float StopTick => ref Projectile.localAI[2];

		public override void SetDefaults() {
			Projectile.width = 22;
			Projectile.height = BandHeight;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = ModContent.GetInstance<MechanistDamage>();
			Projectile.penetrate = -1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;              // each enemy once a cloud
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = MoveTicks + FadeTicks + 2;
			Projectile.aiStyle = -1;
		}

		private bool Moving => StopTick == 0f && Ticks < MoveTicks;

		public override void AI() {
			if (StartX == 0f && StartY == 0f) {
				StartX = Projectile.Center.X;
				StartY = Projectile.Center.Y;
			}
			Ticks++;
			if (!Moving) {
				if (StopTick == 0f) {
					StopTick = Ticks;
				}
				Projectile.velocity = Vector2.Zero;
				if (Ticks >= StopTick + FadeTicks) {
					Projectile.Kill();
				}
				return;
			}
			if (!Main.dedServ && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Smoke, out Dust d)) {
				d.velocity = Projectile.velocity * 0.15f + Main.rand.NextVector2Circular(0.6f, 0.6f);
				d.scale = 1.2f;
				d.alpha = 120;
			}
		}

		/// <summary>A small box against tiles (the band is the hitbox only for enemies).</summary>
		public override bool TileCollideStyle(ref int width, ref int height, ref bool fallThrough, ref Vector2 hitboxCenterFrac) {
			width = 8;
			height = 8;
			return true;
		}

		public override bool OnTileCollide(Vector2 oldVelocity) {
			Projectile.velocity = Vector2.Zero;
			StopTick = Ticks;                                 // it spreads against the wall and thins away
			return false;
		}

		public override bool? CanDamage() => Moving ? null : false;

		/// <summary>The band swept over the last tick's path: a line from where the front was to where it is, BandHeight wide.</summary>
		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox) {
			if (!Moving) {
				return false;
			}
			float point = 0f;
			Vector2 back = Projectile.Center - Projectile.velocity;
			return projHitbox.Intersects(targetHitbox)
				|| Collision.CheckAABBvLineCollision(targetHitbox.TopLeft(), targetHitbox.Size(), back, Projectile.Center, BandHeight, ref point);
		}

		// The trail: a puff every PuffSpacing px from the start to the front, each as old as the time since the front passed it.
		public override bool PreDraw(ref Color lightColor) {
			Texture2D sheet = TextureAssets.Projectile[Type].Value;
			Vector2 start = new(StartX, StartY);
			Vector2 path = Projectile.Center - start;
			float length = path.Length();
			if (!MathSafety.IsFinite(start) || !float.IsFinite(length) || length > 2000f) {
				return false;
			}
			Vector2 dir = length > 0.01f ? path / length : Vector2.UnitX;
			Vector2 normal = new(-dir.Y, dir.X);
			float speed = SmokerBook.Speed;
			int count = Math.Min(40, (int)(length / PuffSpacing) + 1);
			for (int k = 0; k < count; k++) {
				float along = k * PuffSpacing;
				float laid = along / speed;                       // the tick the front passed it
				float age = Ticks - laid;
				float life = MathHelper.Clamp(age / FadeTicks, 0f, 1f);
				float opacity = (1f - life) * (1f - life) * 0.85f;
				if (opacity <= 0.02f) {
					continue;
				}
				float wobble = ((k * 37) % 7 - 3) * 1.2f;         // fixed per puff: a ragged band, not a pipe
				Vector2 at = start + dir * along + normal * wobble - Vector2.UnitY * (age * 0.25f);
				Color light = Lighting.GetColor((int)(at.X / 16f), (int)(at.Y / 16f));
				float scale = 0.7f + 0.25f * MathHelper.Clamp(age / 10f, 0f, 1f);
				Rectangle source = new(0, (k % PuffFrames) * PuffStride, PuffSize, PuffSize);
				Main.EntitySpriteDraw(sheet, (at - Main.screenPosition).Floor(), source, light * opacity, 0f, new Vector2(PuffSize * 0.5f),
					scale, k % 2 == 0 ? SpriteEffects.None : SpriteEffects.FlipHorizontally);
			}
			return false;
		}

		public override string Texture => "Cogpunk/Content/Mechanist/Weapons/SmokerBookSmoke";
	}

	/// <summary>
	/// Puts a <see cref="SmokerBook"/> in <see cref="Chance"/> in 100 of the Underworld's Shadow Chests (user-set 2026-11-19:
	/// "can be found on hell chests"; Shadow and Locked Shadow Chests below the Underworld's top), in the first empty slot,
	/// and in one of them at least when the dice gave none (my call: every world has one). Runs after vanilla's last pass.
	/// D0: one bounded loop over <c>Main.maxChests</c>, coordinates checked, failures caught by <see cref="SafeGenPass"/>;
	/// only <c>WorldGen.genRand</c>.
	/// </summary>
	internal sealed class SmokerBookPass : SafeGenPass
	{
		public const int Chance = 25;                             // my call
		private const int ShadowStyle = 3, LockedShadowStyle = 4;

		public SmokerBookPass() : base("Cogpunk: Smoker Books", 0.2) {
		}

		protected override void Generate(GenerationProgress progress, GameConfiguration configuration) {
			progress.Message = Language.GetTextValue("Mods.Cogpunk.WorldGen.SmokerBooks");
			int type = ModContent.ItemType<SmokerBook>();
			int candidates = 0, placed = 0, fallback = -1;
			for (int i = 0; i < Main.maxChests; i++) {
				Chest chest = Main.chest[i];
				if (chest == null || chest.y < Main.UnderworldLayer || !TileSafety.TryGetTile(chest.x, chest.y, out Tile tile)
					|| !tile.HasTile || tile.TileType != TileID.Containers) {
					continue;
				}
				int style = tile.TileFrameX / 36;
				if (style != ShadowStyle && style != LockedShadowStyle) {
					continue;
				}
				candidates++;
				if (FirstEmptySlot(chest) < 0) {
					continue;
				}
				if (fallback < 0 || WorldGen.genRand.Next(candidates) == 0) {
					fallback = i;                                 // a fair pick among the chests with room
				}
				if (WorldGen.genRand.Next(100) < Chance && Put(chest, type)) {
					placed++;
				}
			}
			if (placed == 0 && fallback >= 0 && Put(Main.chest[fallback], type)) {
				placed++;
			}
			SafeLog.Info("WorldGen.SmokerBooks", $"Smoker Books: {placed} of {candidates} Shadow Chests.");
		}

		private static bool Put(Chest chest, int type) {
			int slot = FirstEmptySlot(chest);
			if (slot < 0) {
				return false;
			}
			chest.item[slot] ??= new Item();
			chest.item[slot].SetDefaults(type);
			return true;
		}

		private static int FirstEmptySlot(Chest chest) {
			int count = Math.Min(chest.item.Length, Chest.maxItems);
			for (int s = 0; s < count; s++) {
				if (chest.item[s] == null || chest.item[s].IsAir) {
					return s;
				}
			}
			return -1;
		}
	}

	/// <summary>Registers <see cref="SmokerBookPass"/> after vanilla's last pass ("Final Cleanup"; appended if it's missing).</summary>
	public sealed class SmokerBookWorldGen : ModSystem
	{
		public override void ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight) {
			GenPassUtils.InsertAfter(tasks, "Final Cleanup", new SmokerBookPass(), ref totalWeight);
		}
	}
}
