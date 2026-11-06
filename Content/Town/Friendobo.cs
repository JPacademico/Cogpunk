using System.Collections.Generic;
using Cogpunk.Content.Bosses.CursedConductor;
using Cogpunk.Content.Bosses.CursedConductor.Items;
using Cogpunk.Content.Bosses.TarTyrant;
using Cogpunk.Content.Bosses.TarTyrant.Summon;
using Cogpunk.Content.Bosses.TrashTr0m;
using Cogpunk.Content.Junkyard.Items;
using Cogpunk.Content.MechArmy;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.Personalities;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.Utilities;

namespace Cogpunk.Content.Town
{
	/// <summary>
	/// Friendobô (user-set 2026-11-03): an old bartender robot in a top hat and a monocle, Cogpunk's first town NPC. He moves
	/// into a free house once the world has beaten the Mech Army (<see cref="CanTownNPCSpawn"/> reads its downed flag, saved
	/// and synced by WorldFlagSystem). His shop sells Rusted Cogs and Rusted Scrap at <see cref="ScrapPrice"/> copper each
	/// (user-set) and each boss's summon once that boss has been beaten: the Junkbait (Trash-Tr0m), the Scrapworm (Tar
	/// Tyrant) and the Cursed Whistle (the Cursed Conductor, 2026-11-04), at the items' own value. Set up like ExampleMod 1.4.4's <c>ExamplePerson</c> ([AutoloadHead], 25 frames
	/// animated as the Guide, <c>NPCShop</c> with <c>Condition</c>s); he throws the Tavernkeep's mugs when enemies come
	/// near (decompiled <c>NPC.TownNPCAttackProj</c>, type 550: projectile 669, speed 6, gravity correction 16).
	/// <para>D2: vanilla runs town NPCs (spawning on the server, shops on the client that opens them, the conditions read
	/// world flags every side has). D0: the shop is built once at load; no per-tick work of our own.</para>
	/// </summary>
	[AutoloadHead]
	public class Friendobo : CogpunkNPC
	{
		public const string ShopName = "Shop";
		public const int ScrapPrice = 50;               // copper, Rusted Cogs and Rusted Scrap (user-set)
		private const int StandardLines = 6;
		private static readonly string[] GoreNames = { "Friendobo_GoreHead", "Friendobo_GoreArm", "Friendobo_GoreLeg" };

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 25;
			NPCID.Sets.ExtraFramesCount[Type] = 9;
			NPCID.Sets.AttackFrameCount[Type] = 4;
			NPCID.Sets.DangerDetectRange[Type] = 600;
			NPCID.Sets.AttackType[Type] = 0;            // throwing
			NPCID.Sets.AttackTime[Type] = 60;
			NPCID.Sets.AttackAverageChance[Type] = 30;
			NPCID.Sets.HatOffsetY[Type] = 4;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Velocity = 1f, Direction = -1 });

			NPC.Happiness
				.SetBiomeAffection<DesertBiome>(AffectionLevel.Like)
				.SetBiomeAffection<SnowBiome>(AffectionLevel.Dislike)       // the cold seizes his joints
				.SetNPCAffection(NPCID.DD2Bartender, AffectionLevel.Love)  // a fellow bartender
				.SetNPCAffection(NPCID.Mechanic, AffectionLevel.Like)
				.SetNPCAffection(NPCID.Cyborg, AffectionLevel.Like)
				.SetNPCAffection(NPCID.GoblinTinkerer, AffectionLevel.Dislike);   // keeps taking him apart "to see"
		}

		public override void SetDefaults() {
			NPC.townNPC = true;
			NPC.friendly = true;
			NPC.width = 18;
			NPC.height = 40;
			NPC.aiStyle = NPCAIStyleID.Passive;
			NPC.damage = 10;
			NPC.defense = 15;
			NPC.lifeMax = 250;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.knockBackResist = 0.5f;
			AnimationType = NPCID.Guide;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Surface,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		public override bool CanTownNPCSpawn(int numTownNPCs) => ModContent.GetInstance<MechArmyInvasion>().Downed;

		public override List<string> SetNPCNameList() => new() {
			"Gearhart", "Cogsworth", "Barnaby Bolt", "Rivet", "Copperfield", "Monty", "Sir Sprocket", "Old Tinny",
		};

		public override string GetChat() {
			WeightedRandom<string> chat = new();
			for (int i = 1; i <= StandardLines; i++) {
				chat.Add(this.GetLocalization("Chat" + i).Value);
			}
			if (NPC.FindFirstNPC(NPCID.DD2Bartender) >= 0) {
				chat.Add(this.GetLocalization("ChatTavernkeep").Value, 0.6);
			}
			if (NPC.FindFirstNPC(NPCID.Mechanic) >= 0) {
				chat.Add(this.GetLocalization("ChatMechanic").Value, 0.6);
			}
			return chat;
		}

		public override void SetChatButtons(ref string button, ref string button2) {
			button = Language.GetTextValue("LegacyInterface.28");   // "Shop"
		}

		public override void OnChatButtonClicked(bool firstButton, ref string shop) {
			if (firstButton) {
				shop = ShopName;
			}
		}

		public override void AddShops() {
			Condition trashTr0m = new(Mod.GetLocalization("Conditions.DownedTrashTr0m"), () => TrashTr0mSystem.Downed);
			Condition tarTyrant = new(Mod.GetLocalization("Conditions.DownedTarTyrant"), () => TarTyrantSystem.Downed);
			Condition cursedConductor = new(Mod.GetLocalization("Conditions.DownedCursedConductor"), () => CursedConductorSystem.Downed);
			new NPCShop(Type, ShopName)
				.Add(new Item(ModContent.ItemType<RustedCog>()) { shopCustomPrice = Item.buyPrice(copper: ScrapPrice) })
				.Add(new Item(ModContent.ItemType<RustedScrap>()) { shopCustomPrice = Item.buyPrice(copper: ScrapPrice) })
				.Add<Junkbait>(trashTr0m)
				.Add<Scrapworm>(tarTyrant)
				.Add<CursedWhistle>(cursedConductor)
				.Register();
		}

		public override void TownNPCAttackStrength(ref int damage, ref float knockback) {
			damage = 24;
			knockback = 9f;                              // the Tavernkeep's
		}

		public override void TownNPCAttackCooldown(ref int cooldown, ref int randExtraCooldown) {
			cooldown = 120;
			randExtraCooldown = 60;
		}

		public override void TownNPCAttackProj(ref int projType, ref int attackDelay) {
			projType = ProjectileID.Ale;                 // a mug, like the Tavernkeep's
			attackDelay = 10;
		}

		public override void TownNPCAttackProjSpeed(ref float multiplier, ref float gravityCorrection, ref float randomOffset) {
			multiplier = 6f;
			gravityCorrection = 16f;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 2 : 10;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.Iron, out _);
			}
			if (NPC.life <= 0) {
				foreach (string name in GoreNames) {
					if (Mod.TryFind(name, out ModGore gore)) {
						SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.position + new Vector2(Main.rand.Next(NPC.width), Main.rand.Next(NPC.height)),
							NPC.velocity * 0.5f + Main.rand.NextVector2Circular(2f, 2f), gore.Type, out _);
					}
				}
			}
		}
	}
}
