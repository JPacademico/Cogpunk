using Cogpunk.Content.Gems.Projectiles;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems.Items
{
	/// <summary>
	/// Jade Staff (Cajado de Jade), jade's gem staff (user-set 2026-11-09: "a jade staff mage weapon that shoots a wave motion
	/// jade magic projectile (like the diamond staff projectile but jade green); it should be like the gem staffs in
	/// attributes and apply the jade curse on hit"). The Emerald Staff's numbers, as jade sits at the Emerald's rarity
	/// (decompiled 1.4.4 <c>Item.SetDefaults</c> 742: 19 damage, use time 32, 6 mana, shot speed 8, knockback 4.25, auto
	/// swing, Blue rarity, value 15000; <c>Recipe</c>: 10 Tungsten Bars + 8 gems at an anvil; here Silver or Tungsten, so
	/// every world can make it). It fires a <see cref="JadeBolt"/> that weaves as it flies, homes in on enemies turned to jade
	/// (2026-11-10) and lays the <see cref="JadeCurseNPC"/> curse on what it hits. Held and aimed like vanilla's gem staffs
	/// (<c>Item.staff</c>: drawn turned along the aim, the arm towards the cursor); redrawn 2026-11-10 (user: "more like a
	/// terraria gem staff, only with a brass and red detail on the staff and the jade gem on the tip"). Balance:
	/// docs/balance/weapons.csv. Art: art/gems/make_jade_art.py (the first staff in previous/).
	/// </summary>
	public class JadeStaff : CogpunkItem
	{
		public const int Damage = 19, UseTime = 32, Mana = 6, BarCost = 10, JadeCost = 8;
		public const float ShotSpeed = 8f, Knockback = 4.25f;

		public override LocalizedText Tooltip => base.Tooltip.WithFormatArgs((int)(JadeCurseNPC.SlowPerStack * 100f), JadeCurseNPC.Stacks,
			JadeCurseNPC.PetrifyTicks / 60f, JadeCurseNPC.WardTicks / 60, JadeCurseNPC.BossStacks, JadeCurseNPC.BossPetrifyLimit);

		public override void SetStaticDefaults() {
			Item.staff[Type] = true;                            // drawn turned 45 degrees in the hand, as vanilla's staffs
			Item.ResearchUnlockCount = 1;
		}

		public override void SetDefaults() {
			Item.damage = Damage;
			Item.DamageType = DamageClass.Magic;
			Item.mana = Mana;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.useTime = UseTime;
			Item.useAnimation = UseTime;
			Item.UseSound = SoundID.Item43;
			Item.autoReuse = true;
			Item.noMelee = true;
			Item.shoot = ModContent.ProjectileType<JadeBolt>();
			Item.shootSpeed = ShotSpeed;
			Item.knockBack = Knockback;
			Item.width = 40;
			Item.height = 40;
			Item.value = 15000;
			Item.rare = ItemRarityID.Blue;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback) {
			// the bolt's straight course rides in ai[0], ai[1] (synced with it): it weaves about that line
			SafeSpawn.TryNewProjectile(source, position, velocity, type, damage, knockback, out _, player.whoAmI, velocity.X, velocity.Y);
			return false;
		}

		public override void AddRecipes() {
			CreateRecipe().AddRecipeGroup(VanillaRecipeGroups.SilverBar, BarCost).AddIngredient<Jade>(JadeCost).AddTile(TileID.Anvils).Register();
		}
	}
}
