using System;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Research.Items
{
	/// <summary>
	/// Driller Extractor (user-set 2026-11-27: "unlocked by 'pre-hardmode drill?!' ... it should be the fastest pre hardmode
	/// mining tool (but with platinum level pickaxe power). it should be crafted using 4 platinum/gold bars and 6 rusted cogs.
	/// it should automatically extract when mining silt or scrap blocks or other extractable blocks (like the extractinator
	/// does)"): a handheld brass-and-steel rotary drill salvaged from a Driller's nose cone with an inline sifter chute.
	/// <para>D3: 59% pickaxe power (the Platinum Pickaxe's exact value, decompiled <c>Item.SetDefaults</c> 3485) and
	/// <see cref="UseTime"/> = 8 (27% faster than vanilla's fastest pre-Hardmode pickaxe, the Bone Pickaxe's 11, and just over
	/// the Hardmode Cobalt Drill's 7). D0/D2: auto-extraction runs in <see cref="DrillerExtractorGlobalTile.CanDrop"/> on the
	/// server or singleplayer, replacing the raw Silt/Slush/Desert Fossil/Rusted Scrap drop so blocks can never be placed back
	/// down and infinitely farmed.</para>
	/// </summary>
	public class DrillerExtractor : CogpunkItem
	{
		public const int Damage = 10;
		public const int PickPower = 59;                          // Platinum Pickaxe's exact pickaxe power
		public const int UseTime = 8;                             // fastest pre-Hardmode mining tool (Bone Pickaxe = 11)
		public const int AnimationTicks = 15;
		public const float Knockback = 1.5f;
		public const float ShootSpeed = 28f;
		public const int BarCost = 4, CogCost = 6;                // user-set: 4 platinum/gold bars and 6 rusted cogs

		public override void SetStaticDefaults() {
			ItemID.Sets.IsDrill[Type] = true;
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.DamageType = DamageClass.MeleeNoSpeed;
			Item.width = 44;
			Item.height = 22;
			Item.useTime = UseTime;
			Item.useAnimation = AnimationTicks;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.channel = true;
			Item.noMelee = true;
			Item.noUseGraphic = true;
			Item.autoReuse = true;
			Item.pick = PickPower;
			Item.knockBack = Knockback;
			Item.shoot = ModContent.ProjectileType<DrillerExtractorProjectile>();
			Item.shootSpeed = ShootSpeed;
			Item.UseSound = SoundID.Item23;
			Item.rare = ItemRarityID.Green;
			Item.value = Item.sellPrice(gold: 1, silver: 20);
		}

		public override void AddRecipes() {
			CreateRecipe()
				.AddRecipeGroup(VanillaRecipeGroups.GoldBar, BarCost)
				.AddIngredient<RustedCog>(CogCost)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}

	/// <summary>
	/// Held rotary drill projectile for <see cref="DrillerExtractor"/>: uses vanilla's drill AI (<c>ProjAIStyleID.Drill</c>) for
	/// channelled aiming, sound and dust, and draws from a <see cref="Headings"/> x <see cref="Spins"/> sculpted sheet so the
	/// sprite is never rotated at runtime (D4 rule 14).
	/// </summary>
	public class DrillerExtractorProjectile : CogpunkProjectile
	{
		public const int Headings = 16, Spins = 3;
		public const int Cell = 52, Stride = 54;

		private static Asset<Texture2D> glow;

		public override void SetStaticDefaults() {
			if (!Main.dedServ) {
				glow = DepthLayers.RequestOptional(Texture + "_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 22;
			Projectile.height = 22;
			Projectile.aiStyle = ProjAIStyleID.Drill;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.hide = true;
			Projectile.ownerHitCheck = true;
			Projectile.DamageType = DamageClass.MeleeNoSpeed;
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D sheet = TextureAssets.Projectile[Type].Value;
			float angle = Projectile.velocity.LengthSquared() > 0.01f ? Projectile.velocity.ToRotation() : 0f;
			int heading = ((int)MathF.Round(angle / MathHelper.TwoPi * Headings) % Headings + Headings) % Headings;
			int spin = (int)(Main.GameUpdateCount / 2u % (uint)Spins);
			Rectangle source = new(heading * Stride, spin * Stride, Cell, Cell);
			if (source.Right > sheet.Width || source.Bottom > sheet.Height) {
				return true;
			}
			Player owner = Main.player[Projectile.owner];
			Vector2 at = Projectile.Center - Main.screenPosition + new Vector2(0f, owner.gfxOffY) - new Vector2(Cell * 0.5f);
			at = new Vector2(MathF.Round(at.X / 2f) * 2f, MathF.Round(at.Y / 2f) * 2f);
			Main.EntitySpriteDraw(sheet, at, source, Projectile.GetAlpha(lightColor), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true) {
				Main.EntitySpriteDraw(glow.Value, at, source, Color.White * Projectile.Opacity, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}

	/// <summary>
	/// Auto-extracts any extractable block (<c>ItemID.Sets.ExtractinatorMode[dropItem] &gt;= 0</c>: Silt, Slush, Desert Fossil,
	/// Rusted Scrap, and any other mod's extractable block) mined by a player holding <see cref="DrillerExtractor"/>, running
	/// the exact decompiled 1.4.4 <c>Player.ExtractinatorUse</c> + <c>ItemLoader.ExtractinatorUse</c> table and suppressing the
	/// raw block drop so blocks cannot be placed back down to farm.
	/// </summary>
	public sealed class DrillerExtractorGlobalTile : GlobalTile
	{
		public const float MaxRangePx = 12f * 16f;
		private static int[] extractItemOfTile;
		private static int drillerItemType = -1;

		public static void BuildExtractTable() {
			extractItemOfTile = new int[TileLoader.TileCount];
			drillerItemType = ModContent.ItemType<DrillerExtractor>();
			for (int itemType = 1; itemType < ItemLoader.ItemCount; itemType++) {
				if (itemType >= ItemID.Sets.ExtractinatorMode.Length || ItemID.Sets.ExtractinatorMode[itemType] < 0) {
					continue;
				}
				if (!ContentSamples.ItemsByType.TryGetValue(itemType, out Item sample)) {
					continue;
				}
				int t = sample.createTile;
				if (t >= 0 && t < extractItemOfTile.Length && extractItemOfTile[t] == 0) {
					extractItemOfTile[t] = itemType;
				}
			}
		}

		public override void Unload() {
			extractItemOfTile = null;
			drillerItemType = -1;
		}

		public override bool CanDrop(int i, int j, int type) {
			if (Main.netMode == NetmodeID.MultiplayerClient || extractItemOfTile == null || type < 0 || type >= extractItemOfTile.Length) {
				return true;
			}
			int blockItem = extractItemOfTile[type];
			if (blockItem <= 0) {
				return true;
			}
			Vector2 tileWorld = new(i * 16f + 8f, j * 16f + 8f);
			int p = Player.FindClosest(new Vector2(i * 16f, j * 16f), 16, 16);
			if (p < 0 || p >= Main.maxPlayers) {
				return true;
			}
			Player miner = Main.player[p];
			if (miner == null || !miner.active || miner.dead || miner.HeldItem?.type != drillerItemType
				|| Vector2.DistanceSquared(miner.Center, tileWorld) > MaxRangePx * MaxRangePx) {
				return true;
			}
			int extractType = ItemID.Sets.ExtractinatorMode[blockItem];
			RollExtractinator(extractType, TileID.Extractinator, out int resultType, out int resultStack);
			if (resultType > ItemID.None && resultStack > 0
				&& SafeSpawn.TryNewItem(new EntitySource_TileBreak(i, j), new Rectangle(i * 16, j * 16, 16, 16), resultType, resultStack, out _)) {
				return false;                                     // raw block replaced by extracted loot
			}
			return true;
		}

		/// <summary>Exact 1.4.4 <c>Player.ExtractinatorUse</c> table + <c>ItemLoader.ExtractinatorUse</c> (decompiled Player.cs 41292-41691).</summary>
		public static void RollExtractinator(int extractType, int extractinatorBlockType, out int resultType, out int resultStack) {
			int mosquitoOdds = 5000, gemOdds = 25, amberOdds = 50, fossilOdds = -1, junkOdds = -1, mossOdds = -1, coinFlag = 1;
			switch (extractType) {
				case ItemID.DesertFossil:
					mosquitoOdds /= 3;
					gemOdds *= 2;
					amberOdds = 20;
					fossilOdds = 10;
					break;
				case ItemID.OldShoe:
				case ItemID.FishingSeaweed:
				case ItemID.TinCan:
					mosquitoOdds = gemOdds = amberOdds = fossilOdds = coinFlag = -1;
					junkOdds = 1;
					break;
				case ItemID.LavaMoss:
					mosquitoOdds = gemOdds = amberOdds = fossilOdds = junkOdds = coinFlag = -1;
					mossOdds = 1;
					break;
			}

			resultType = -1;
			resultStack = 1;
			if (fossilOdds != -1 && Main.rand.NextBool(fossilOdds)) {
				resultType = ItemID.FossilOre;
				if (Main.rand.NextBool(5)) resultStack += Main.rand.Next(2);
				if (Main.rand.NextBool(10)) resultStack += Main.rand.Next(3);
				if (Main.rand.NextBool(15)) resultStack += Main.rand.Next(4);
			}
			else if (coinFlag != -1 && Main.rand.NextBool(2)) {
				if (Main.rand.NextBool(12000)) {
					resultType = ItemID.PlatinumCoin;
					for (int k = 0; k < 3; k++) if (Main.rand.NextBool(14)) resultStack += Main.rand.Next(0, 2);
				}
				else if (Main.rand.NextBool(800)) {
					resultType = ItemID.GoldCoin;
					for (int k = 0; k < 5; k++) if (Main.rand.NextBool(6)) resultStack += Main.rand.Next(1, 21);
				}
				else if (Main.rand.NextBool(60)) {
					resultType = ItemID.SilverCoin;
					for (int k = 0; k < 4; k++) if (Main.rand.NextBool(4)) resultStack += Main.rand.Next(5, 26);
				}
				else {
					resultType = ItemID.CopperCoin;
					for (int k = 0; k < 4; k++) if (Main.rand.NextBool(3)) resultStack += Main.rand.Next(10, 26);
				}
			}
			else if (mosquitoOdds != -1 && Main.rand.NextBool(mosquitoOdds)) {
				resultType = ItemID.AmberMosquito;
			}
			else if (junkOdds != -1) {
				resultType = Main.rand.Next(4) != 1 ? ItemID.Snail : Main.rand.Next(3) != 1 ? ItemID.ApprenticeBait
					: Main.rand.Next(3) == 1 ? ItemID.JourneymanBait : ItemID.Worm;
			}
			else if (mossOdds != -1) {
				resultType = Main.rand.Next(5) switch {
					0 => ItemID.GreenMoss,
					1 => ItemID.BrownMoss,
					2 => ItemID.RedMoss,
					3 => ItemID.BlueMoss,
					_ => ItemID.PurpleMoss,
				};
			}
			else if (gemOdds != -1 && Main.rand.NextBool(gemOdds)) {
				resultType = Main.rand.Next(6) switch {
					0 => ItemID.Amethyst,
					1 => ItemID.Topaz,
					2 => ItemID.Sapphire,
					3 => ItemID.Emerald,
					4 => ItemID.Ruby,
					_ => ItemID.Diamond,
				};
				AddBonusStack(ref resultStack);
			}
			else if (amberOdds != -1 && Main.rand.NextBool(amberOdds)) {
				resultType = ItemID.Amber;
				AddBonusStack(ref resultStack);
			}
			else if (Main.rand.NextBool(3)) {
				if (Main.rand.NextBool(5000)) {
					resultType = ItemID.PlatinumCoin;
					for (int k = 0; k < 5; k++) if (Main.rand.NextBool(10)) resultStack += Main.rand.Next(0, 3);
				}
				else if (Main.rand.NextBool(400)) {
					resultType = ItemID.GoldCoin;
					for (int k = 0; k < 5; k++) if (Main.rand.NextBool(5)) resultStack += Main.rand.Next(1, 21);
				}
				else if (Main.rand.NextBool(30)) {
					resultType = ItemID.SilverCoin;
					for (int k = 0; k < 4; k++) if (Main.rand.NextBool(3)) resultStack += Main.rand.Next(5, 26);
				}
				else {
					resultType = ItemID.CopperCoin;
					for (int k = 0; k < 4; k++) if (Main.rand.NextBool(2)) resultStack += Main.rand.Next(10, 26);
				}
			}
			else {
				resultType = Main.rand.Next(8) switch {
					0 => ItemID.CopperOre,
					1 => ItemID.IronOre,
					2 => ItemID.SilverOre,
					3 => ItemID.GoldOre,
					4 => ItemID.TinOre,
					5 => ItemID.LeadOre,
					6 => ItemID.TungstenOre,
					_ => ItemID.PlatinumOre,
				};
				AddBonusStack(ref resultStack);
			}

			ItemLoader.ExtractinatorUse(ref resultType, ref resultStack, extractType, extractinatorBlockType);
		}

		private static void AddBonusStack(ref int resultStack) {
			if (Main.rand.NextBool(20)) resultStack += Main.rand.Next(0, 2);
			if (Main.rand.NextBool(30)) resultStack += Main.rand.Next(0, 3);
			if (Main.rand.NextBool(40)) resultStack += Main.rand.Next(0, 4);
			if (Main.rand.NextBool(50)) resultStack += Main.rand.Next(0, 5);
			if (Main.rand.NextBool(60)) resultStack += Main.rand.Next(0, 6);
		}
	}
}
