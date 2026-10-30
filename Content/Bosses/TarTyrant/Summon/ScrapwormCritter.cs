using Cogpunk.Core.Templates;
using Terraria;
using Terraria.GameContent.Bestiary;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TarTyrant.Summon
{
	/// <summary>
	/// The Scrapworm (user-set 2026-10-28): a rare, harmless worm of rusted scrap rings that crawls the underground like
	/// vanilla's Worm (its AI and animation, <c>aiStyle</c> 66, decompiled <c>NPC.SetDefaults</c> type 357). Caught with a
	/// bug net it becomes the <see cref="Scrapworm"/> bait that calls Tar Tyrant out of the Junkyard's tar.
	/// <para>Spawn: the dirt and cavern layers, outside the Dungeon and towns, weight <see cref="SpawnWeight"/> against
	/// vanilla's whole pool (weight 1): about one natural underground spawn in 80. The Lifeform Analyzer calls it out
	/// (rarity like the Truffle Worm's). Like the Truffle Worm, hostile things don't hurt it.</para>
	/// </summary>
	public class ScrapwormCritter : CogpunkNPC
	{
		public const float SpawnWeight = 0.0125f;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = 2;
			Main.npcCatchable[Type] = true;
			NPCID.Sets.CountsAsCritter[Type] = true;
			NPCID.Sets.TakesDamageFromHostilesWithoutBeingFriendly[Type] = false;
		}

		public override void SetDefaults() {
			NPC.CloneDefaults(NPCID.Worm);
			NPC.width = 16;
			NPC.height = 6;
			NPC.aiStyle = 66;
			AIType = NPCID.Worm;
			AnimationType = NPCID.Worm;
			NPC.catchItem = ModContent.ItemType<Scrapworm>();
			NPC.rarity = 3;
			NPC.dontTakeDamageFromHostiles = true;
			NPC.HitSound = SoundID.NPCHit4 with { Pitch = 0.6f };
			NPC.DeathSound = SoundID.NPCDeath1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player player = spawnInfo.Player;
			bool underground = player.ZoneDirtLayerHeight || player.ZoneRockLayerHeight;
			return underground && !player.ZoneDungeon && !spawnInfo.PlayerInTown && !spawnInfo.Water ? SpawnWeight : 0f;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Underground,
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Caverns,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}
	}
}
