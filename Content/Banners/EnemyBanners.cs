using System.Collections.Generic;
using Cogpunk.Core.Templates;
using Terraria;
using Terraria.Enums;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Banners
{
	/// <summary>
	/// A banner for every Cogpunk enemy that isn't a boss or a mini-boss (user, 2026-11-25: "dont forget to create banners for
	/// each enemy we have (excluding bosses and mini bosses)"), working exactly as vanilla's (vanilla's banner rules: one dropped
	/// every <c>ItemID.Sets.KillsToBanner</c> kills, 50 by default; hung up, nearby players deal more damage to that enemy and
	/// take less from it). Built on tModLoader's <c>ModBannerTile</c> (one tile, a placement style per enemy: it applies the
	/// banner buff itself, decompiled <c>ModBannerTile.NearbyEffects</c>) and one banner item per enemy, all loaded from
	/// <see cref="EnemyBannerItem"/> with the enemy's name (<c>ToadstoolBanner</c>...). Each enemy calls
	/// <see cref="SetBanner"/> in its <c>SetDefaults</c> (<c>Banner = Type</c>, <c>BannerItem</c> = its banner: the
	/// ExampleMod pattern). Rare enemies drop theirs sooner (<see cref="Rare"/>: 10 kills, as vanilla's rare ones).
	/// Not here: the bosses and mini-bosses (Mechromancer, Sheriff, Jaeger), the bosses' own summons (Jade Bat, Jade Beetle,
	/// Conductor Ghost, Tar Tyrant's bubbles, the Fungimancer's mushrooms), critters (the Scrapworm).
	/// <para>Art: art/banners/make_banner_art.py (a Cogpunk banner: a brass rod with cog caps, crimson cloth in a brass trim, the
	/// enemy's own sprite shrunk into it, a notched end). The order of <see cref="Enemies"/> is the tile's style order: append
	/// new enemies at the end (a placed banner keeps its style).</para>
	/// </summary>
	public sealed class EnemyBanners : ILoadable
	{
		/// <summary>The enemies with a banner, in tile style order (append only).</summary>
		public static readonly string[] Enemies = {
			"Toadstool", "Cogscorpion", "FlyingBuddhaHead", "JadeGolem", "Coghawk", "BeatBoxer", "RhinoBeetle", "Trapper", "LivingTar",
			"RustCollector", "AnnoyOTron", "Boombot", "RogueMiceBot", "Cogtuna", "BrassBandit", "Dinamitrom", "MechanicalBull",
			"Splasher", "DeliveryDrone", "CrystalLizard", "Driller", "PuxaFrango", "DragoneteMiudo",
		};

		/// <summary>Rare enemies: their banner drops every 10 kills (vanilla's rare enemies, decompiled <c>KillsToBanner</c>).</summary>
		public static readonly HashSet<string> Rare = new() { "CrystalLizard", "PuxaFrango" };
		public const int RareKills = 10;

		private static readonly Dictionary<string, int> itemOf = new();

		public void Load(Mod mod) {
			for (int k = 0; k < Enemies.Length; k++) {
				mod.AddContent(new EnemyBannerItem(Enemies[k], k));
			}
		}

		public void Unload() {
			itemOf.Clear();
		}

		internal static void Register(string enemy, int itemType) => itemOf[enemy] = itemType;

		/// <summary>The banner item of an enemy by its class name, or 0 (none).</summary>
		public static int ItemFor(string enemy) => enemy != null && itemOf.TryGetValue(enemy, out int t) ? t : 0;

		/// <summary>Call in an enemy's <c>SetDefaults</c>: its own banner (only for the enemy listed by that exact name, so a
		/// subclass such as the Jade Beetle never takes the Rhino Beetle's).</summary>
		public static void SetBanner(ModNPC npc) {
			int item = ItemFor(npc.Name);
			if (item > 0) {
				npc.Banner = npc.Type;
				npc.BannerItem = item;
			}
		}
	}

	/// <summary>One enemy's banner item (loaded once per enemy by <see cref="EnemyBanners"/>): places its style of
	/// <see cref="EnemyBannerTile"/>; named and described from the enemy's own name, as vanilla's banners are.</summary>
	[Autoload(false)]
	public class EnemyBannerItem : CogpunkItem
	{
		private readonly string enemy;
		private readonly int style;

		public EnemyBannerItem(string enemy, int style) {
			this.enemy = enemy;
			this.style = style;
		}

		public override string Name => enemy + "Banner";

		private string texture;

		/// <summary>Its own sprite (art/banners/make_banner_art.py), through the mod's missing-texture fallback.</summary>
		public override string Texture => texture ??= TextureFallback.Resolve("Cogpunk/Content/Banners/Items/" + Name);

		protected override bool CloneNewInstances => true;

		private LocalizedText EnemyName => ModContent.TryFind("Cogpunk/" + enemy, out ModNPC npc) ? npc.DisplayName : Language.GetText(enemy);

		public override LocalizedText DisplayName => Language.GetText("Mods.Cogpunk.Banners.Name").WithFormatArgs(EnemyName);

		public override LocalizedText Tooltip => Language.GetText("Mods.Cogpunk.Banners.Tooltip").WithFormatArgs(EnemyName);

		public override void SetStaticDefaults() {
			EnemyBanners.Register(enemy, Type);
			if (EnemyBanners.Rare.Contains(enemy)) {
				ItemID.Sets.KillsToBanner[Type] = EnemyBanners.RareKills;
			}
		}

		public override void SetDefaults() {
			Item.DefaultToPlaceableTile(ModContent.TileType<EnemyBannerTile>(), style);
			Item.width = 12;
			Item.height = 28;
			Item.SetShopValues(ItemRarityColor.Blue1, Item.buyPrice(silver: 10));
		}
	}

	/// <summary>The placed banners: tModLoader's banner tile (anchoring, sway, the buff), one style per enemy.</summary>
	public class EnemyBannerTile : ModBannerTile
	{
	}
}
