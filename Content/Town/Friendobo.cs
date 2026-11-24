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
using Terraria.GameContent;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.Personalities;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.Utilities;

namespace Cogpunk.Content.Town
{
	/// <summary>
	/// The Last Ghedalari (O Último Ghedalari; user, 2026-11-24: "remake our main npc Friendobot it will now be called "last
	/// Ghedalari" an ancient humanoid species core for our mod lore. the design should be based on the draenei for the
	/// biological body features (skin color, bigger ears, hoofs/bended backwards legs, glow eyes without pulpil), and on the
	/// zandalari trolls for the culture adornments (armors, weapons, inka based structures, clothes)"), Cogpunk's first town NPC:
	/// the last of the Ghedalari, a tall blue-skinned people with long swept-back ears, glowing eyes without pupils and
	/// hoofed legs bent backwards, dressed in the gold of a culture that built in stepped stone (a sun-disc collar, stepped gold
	/// pauldrons and belt plate, a red and teal loincloth, gold greaves) and armed with a spear. He was the Friendo-bot (an old
	/// bartender robot) until 2026-11-24, and the Friendobô before 2026-11-11: the class, its textures and saves keep the old
	/// name <c>Friendobo</c>, as Westworld keeps <c>OldBrassTown</c>. The Ghedalari are a seed of the mod's lore (more of
	/// them to come, the user's: nothing more about them is decided here).
	/// <para>He moves into a free house once the world has beaten the Mech Army (<see cref="CanTownNPCSpawn"/> reads its downed
	/// flag, saved and synced by WorldFlagSystem). His shop is the Friendo-bot's: Rusted Cogs and Rusted Scrap at
	/// <see cref="ScrapPrice"/> copper each (user-set), the Steam Injector, and each boss's summon once that boss has been
	/// beaten (rule, user 2026-11-17: "make this a rule for every boss that we add": the Junkbait, the Scrapworm, the Cursed
	/// Whistle, the Jade Incense, the Rainbow Mushroom), at the items' own value.</para>
	/// <para>Vanilla's townsfolk in every respect (ExampleMod 1.4.4's <c>ExamplePerson</c>): vanilla's town AI and the Guide's
	/// frame rules over a 25-frame sheet at vanilla's density (art/town/make_ghedalari_art.py: standing, in the air, 14
	/// walking frames, the two chat gestures, sitting, talking, blinking, a 4-frame throw); he throws javelins when enemies come
	/// near (decompiled <c>NPC.TownNPCAttackProj</c>: projectile 507, the player's Javelin); a party hat on his crest
	/// (<c>HatOffsetY</c>); a shimmered form (<c>ShimmerTownTransform</c>: pale violet skin and jade where the gold was;
	/// <see cref="TownNPCProfile"/>) with its own map head; his face as an emote when other townsfolk talk about him
	/// (<see cref="FriendoboEmote"/>); happiness and an <c>NPCShop</c> with <c>Condition</c>s.</para>
	/// <para>D2: vanilla runs town NPCs (spawning on the server, shops on the client that opens them, the conditions read
	/// world flags every side has; the shimmered variant is vanilla's synced <c>townNpcVariationIndex</c>). D0: the shop and
	/// the profile are built once; the shimmer head and textures are only asked for when they exist, on clients; no per-tick
	/// work of our own.</para>
	/// </summary>
	[AutoloadHead]
	public class Friendobo : CogpunkNPC
	{
		public const string ShopName = "Shop";
		public const int ScrapPrice = 50;               // copper, Rusted Cogs and Rusted Scrap (user-set)
		/// <summary>His lines as chat text in the Ghedalari script (<see cref="Secrets.GhedalariScript.Phrases"/>), built once.</summary>
		private static string[] lines;
		private static string witchDoctorLine, dryadLine;
		private static readonly string[] GoreNames = { "Friendobo_GoreHead", "Friendobo_GoreArm", "Friendobo_GoreLeg" };
		/// <summary>The party hat sits on his gold crest: vanilla puts it at the hitbox's top plus this (down); the crest rises
		/// over his hitbox as the old top hat did.</summary>
		public const int PartyHatOffsetY = -10;

		private static int shimmerHead = -1;
		private static bool hasShimmer;
		private static ITownNPCProfile profile;

		/// <summary>The shimmered form's map and housing head (clients, when the texture exists: ExampleMod's
		/// <c>Mod.AddNPCHeadTexture</c> in <c>Load</c>).</summary>
		public override void Load() {
			string head = Texture + "_Shimmer_Head";
			if (!Main.dedServ && ModContent.HasAsset(head)) {
				shimmerHead = Mod.AddNPCHeadTexture(Type, head);
			}
		}

		public override void Unload() {
			profile = null;
			shimmerHead = -1;
			lines = null;
			witchDoctorLine = dryadLine = null;
		}

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 25;
			NPCID.Sets.ExtraFramesCount[Type] = 9;
			NPCID.Sets.AttackFrameCount[Type] = 4;
			NPCID.Sets.DangerDetectRange[Type] = 600;
			NPCID.Sets.AttackType[Type] = 0;            // throwing
			NPCID.Sets.AttackTime[Type] = 60;
			NPCID.Sets.AttackAverageChance[Type] = 30;
			NPCID.Sets.HatOffsetY[Type] = PartyHatOffsetY;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Velocity = 1f, Direction = -1 });
			hasShimmer = Main.dedServ || ModContent.HasAsset(Texture + "_Shimmer");
			NPCID.Sets.ShimmerTownTransform[Type] = true;
			NPCID.Sets.FaceEmote[Type] = ModContent.EmoteBubbleType<FriendoboEmote>();

			NPC.Happiness
				.SetBiomeAffection<JungleBiome>(AffectionLevel.Like)        // stepped stone under green: home, almost
				.SetBiomeAffection<SnowBiome>(AffectionLevel.Dislike)       // hooves on ice
				.SetNPCAffection(NPCID.WitchDoctor, AffectionLevel.Love)    // masks like the faces his people carved
				.SetNPCAffection(NPCID.Dryad, AffectionLevel.Like)          // the one other who remembers
				.SetNPCAffection(NPCID.ArmsDealer, AffectionLevel.Dislike); // loud weapons
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
			NPC.HitSound = SoundID.NPCHit1;
			NPC.DeathSound = SoundID.NPCDeath1;
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

		/// <summary>His two looks (vanilla picks by the synced <c>townNpcVariationIndex</c>: 1 once shimmered); no party texture
		/// (vanilla then draws the party hat on the plain one). Built once; a client without the shimmered sheet keeps the
		/// plain look.</summary>
		public override ITownNPCProfile TownNPCProfile() {
			if (profile == null) {
				int head = NPCHeadLoader.GetHeadSlot(HeadTexture);
				Profiles.DefaultNPCProfile plain = new(Texture, head, null);
				profile = hasShimmer
					? new Profiles.StackedNPCProfile(plain, new Profiles.DefaultNPCProfile(Texture + "_Shimmer", shimmerHead >= 0 ? shimmerHead : head, null))
					: plain;
			}
			return profile;
		}

		public override List<string> SetNPCNameList() => new() {
			"Xal'tuq", "Kazhuro", "Tzuvan", "Ahuyan", "Mal'quri", "Quel'atuk", "Oyan Tekka", "Izharu",
		};

		/// <summary>He speaks only Ghedalari (user, 2026-11-24: "The last Ghedalari npc should have frases about his species with
		/// humour and some hints about the stones, but it should talk in Ghedalari symbols"): each line is a phrase of runes
		/// drawn by the <c>[ghd]</c> chat tag (<see cref="Secrets.GhedalariTagHandler"/>); a rune the player has learned on a
		/// translated stone shows its picture when hovered.</summary>
		public override string GetChat() {
			if (lines == null) {
				short[][] phrases = Secrets.GhedalariScript.Phrases;
				lines = new string[phrases.Length];
				for (int k = 0; k < phrases.Length; k++) {
					lines[k] = Secrets.GhedalariScript.ChatTag(phrases[k]);
				}
				witchDoctorLine = Secrets.GhedalariScript.ChatTag(Secrets.GhedalariScript.WitchDoctorPhrase);
				dryadLine = Secrets.GhedalariScript.ChatTag(Secrets.GhedalariScript.DryadPhrase);
			}
			WeightedRandom<string> chat = new();
			foreach (string line in lines) {
				chat.Add(line);
			}
			if (NPC.FindFirstNPC(NPCID.WitchDoctor) >= 0) {
				chat.Add(witchDoctorLine, 0.6);
			}
			if (NPC.FindFirstNPC(NPCID.Dryad) >= 0) {
				chat.Add(dryadLine, 0.6);
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
			Condition jadey = new(Mod.GetLocalization("Conditions.DownedJadey"), () => Bosses.Jadey.JadeySystem.Downed);
			Condition fungimancer = new(Mod.GetLocalization("Conditions.DownedFungimancer"), () => Bosses.Fungimancer.FungimancerSystem.Downed);
			new NPCShop(Type, ShopName)
				.Add(new Item(ModContent.ItemType<RustedCog>()) { shopCustomPrice = Item.buyPrice(copper: ScrapPrice) })
				.Add(new Item(ModContent.ItemType<RustedScrap>()) { shopCustomPrice = Item.buyPrice(copper: ScrapPrice) })
				.Add<Junkbait>(trashTr0m)
				.Add<Scrapworm>(tarTyrant)
				.Add<CursedWhistle>(cursedConductor)
				.Add<Bosses.Jadey.Items.JadeIncense>(jadey)
				.Add<Bosses.Fungimancer.Items.RainbowMushroom>(fungimancer)   // 2026-11-19: the Fungimancer's summon
				.Add<Mechanist.Stations.SteamInjector>()          // user, 2026-11-12: 35 gold (its value), always in stock
				.Register();
		}

		public override void TownNPCAttackStrength(ref int damage, ref float knockback) {
			damage = 24;
			knockback = 6f;
		}

		public override void TownNPCAttackCooldown(ref int cooldown, ref int randExtraCooldown) {
			cooldown = 120;
			randExtraCooldown = 60;
		}

		public override void TownNPCAttackProj(ref int projType, ref int attackDelay) {
			projType = ProjectileID.JavelinFriendly;     // a spear's people: the player's Javelin
			attackDelay = 10;
		}

		public override void TownNPCAttackProjSpeed(ref float multiplier, ref float gravityCorrection, ref float randomOffset) {
			multiplier = 11f;
			gravityCorrection = 8f;
			randomOffset = 0.5f;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 12;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.Blood, out _);
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
