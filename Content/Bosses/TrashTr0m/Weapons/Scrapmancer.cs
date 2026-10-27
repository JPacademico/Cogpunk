using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m.Weapons
{
	/// <summary>
	/// Scrapmancer (Trash-Tr0m drop, magic): a small open palm of rusted metal plates and riveted finger joints, an aether
	/// stone set in it (user-set 2026-10-27: a hand, not a staff). Each swing slams the palm down and sends Trash-Tr0m's junk shockwave (<see cref="ScrapmancerWave"/>) rolling along the ground towards
	/// the cursor's side: it follows the terrain, pierces every enemy (each once), knocks them flying and runs a whole screen
	/// (<see cref="ScrapmancerWave.Lifetime"/> x <see cref="WaveSpeed"/> = 1920 px) unless a wall or a pit breaks it.
	/// <para>It needs ground within <see cref="MaxGroundDrop"/> tiles below the player: without it <see cref="CanUseItem"/>
	/// refuses, so no mana is spent on a wave that couldn't exist. Only the owner spawns (D2).
	/// Balance: docs/balance/weapons.csv (anchor: Vilethorn).</para>
	/// </summary>
	public class Scrapmancer : CogpunkItem
	{
		public const int UseTime = 30;
		public const int ManaCost = 12;
		public const float WaveSpeed = 16f;
		public const int MaxGroundDrop = 20;            // tiles below the player's feet searched for ground
		private const int StartAhead = 20;              // px in front of the player where the wave starts

		public override void SetStaticDefaults() {
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = 33;
			Item.crit = 0;                               // + the player's base 4% = 4%
			Item.knockBack = 9f;                         // "very strong"
			Item.DamageType = DamageClass.Magic;
			Item.mana = ManaCost;
			Item.useStyle = ItemUseStyleID.Swing;        // raised and slammed down
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.UseSound = SoundID.Item8 with { Pitch = -0.4f };
			Item.shoot = ModContent.ProjectileType<ScrapmancerWave>();
			Item.shootSpeed = WaveSpeed;
			Item.width = 40;
			Item.height = 40;
			Item.value = Item.sellPrice(gold: 1);
			Item.rare = ItemRarityID.Blue;
		}

		public override bool CanUseItem(Player player) {
			return FindStart(player, WaveDirection(player), out _);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			int dir = WaveDirection(player);
			player.ChangeDir(dir);
			if (FindStart(player, dir, out Vector2 bottom)) {
				Vector2 centre = bottom - new Vector2(0f, ScrapmancerWave.HitboxHeight * 0.5f);
				SafeSpawn.TryNewProjectile(source, centre, new Vector2(dir * WaveSpeed, 0f), type, damage, knockback, out _, player.whoAmI);
			}
			return false;
		}

		/// <summary>Towards the cursor (owner-side input; other sides never call this).</summary>
		private static int WaveDirection(Player player) {
			if (player.whoAmI != Main.myPlayer) {
				return player.direction;
			}
			return Main.MouseWorld.X >= player.Center.X ? 1 : -1;
		}

		/// <summary>The ground point the wave starts from: the first surface under a point just ahead of the player, from a
		/// tile above the feet down to <see cref="MaxGroundDrop"/> tiles. At most MaxGroundDrop + 2 bounds-checked reads (D0).</summary>
		public static bool FindStart(Player player, int dir, out Vector2 bottom) {
			int x = (int)((player.Center.X + dir * StartAhead) / 16f);
			int feet = (int)(player.Bottom.Y / 16f);
			bool airAbove = !ScrapmancerWave.Solid(x, feet - 2);
			for (int y = feet - 1; y <= feet + MaxGroundDrop; y++) {
				bool solid = ScrapmancerWave.Solid(x, y);
				if (solid && airAbove) {
					bottom = new Vector2(x * 16f + 8f, y * 16f);
					return true;
				}
				airAbove = !solid;
			}
			bottom = Vector2.Zero;
			return false;
		}
	}
}
