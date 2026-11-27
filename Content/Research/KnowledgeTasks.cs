using Terraria;
using Terraria.ID;
using Terraria.Localization;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// The tasks that give knowledge points (user, 2026-11-18; "I will add more later"), each worth one point, once per character
	/// (my call for the world-wide ones too, so a new world can't be farmed for them; see <see cref="ResearchWorld"/>):
	/// <list type="bullet">
	/// <item>To every player in the world: the world's first defeat of each boss or mini-boss (<see cref="Boss"/>), the world's
	/// first full clear of each event (<see cref="Event"/>), and the world having <see cref="ResearchPlayer.TownTarget"/>
	/// housed NPCs (<see cref="Town10"/>, checked by each player's client, so latecomers get it too).</item>
	/// <item>Each player for themself: <see cref="Angler5"/>, <see cref="CoralChest"/>, <see cref="Platinum10"/>, every
	/// Fundamental Stone read (<see cref="Stone"/>), <see cref="SkyIsland"/>, <see cref="Marble"/>, <see cref="Granite"/>,
	/// <see cref="PinkSlime"/>, <see cref="Gnome"/>, <see cref="TravelingMerchant"/>, <see cref="Combinator"/>,
	/// <see cref="FallenStar"/>, <see cref="GlowingMushroom"/> (2026-11-19).</item>
	/// </list>
	/// The keys are saved names (D0 rule 9): never rename one.
	/// </summary>
	public static class KnowledgeTasks
	{
		public const string Angler5 = "Angler5", CoralChest = "CoralChest", Platinum10 = "Platinum10", SkyIsland = "SkyIsland",
			Marble = "Marble", Granite = "Granite", PinkSlime = "PinkSlime", Gnome = "Gnome", TravelingMerchant = "TravelingMerchant",
			Combinator = "Combinator", FallenStar = "FallenStar", Town10 = "Town10",
			GlowingMushroom = "GlowingMushroom";               // 2026-11-19: "visiting a blue mushroom area for the first time"

		/// <summary>Vanilla's chest styles (decompiled 1.4.4 <c>Item.SetDefaults</c>: the Water Chest is tile 21 style 17, the
		/// Reef Chest, <c>ItemID.CoralChest</c> 5156, tile 467 style 14).</summary>
		public const int WaterChestStyle = 17, ReefChestStyle = 14;

		public static string Stone(int index) => "FundamentalStone" + (index + 1);

		/// <summary>The keys of <see cref="Stone"/>, built once (the Mystery of the Past's reveals read them every frame the
		/// window is open: no string building, D1); null outside 0..4.</summary>
		private static readonly string[] stoneKeys = { "FundamentalStone1", "FundamentalStone2", "FundamentalStone3", "FundamentalStone4",
			"FundamentalStone5" };

		public static string StoneKey(int index) => index >= 0 && index < stoneKeys.Length ? stoneKeys[index] : null;

		/// <summary>The world's first demon altar smashed (user, 2026-11-24: "breaking a demon altar for the first time rewards a
		/// knowledge point globally"): every player in the world, once per character (<see cref="ResearchWorld"/>).</summary>
		public const string DemonAltar = "DemonAltar";

		// 2026-11-25 (user: "add some more knowledge point rewards")
		/// <summary>"after breaking a crimsom or corruption heart on the world (globaly)": the world's first Shadow Orb or Crimson
		/// Heart smashed (vanilla's <c>WorldGen.shadowOrbSmashed</c>), every player in the world (<see cref="ResearchWorld"/>).</summary>
		public const string EvilHeart = "EvilHeart";
		/// <summary>"after geting a diamond for the first time": a Diamond picked up or in the inventory.</summary>
		public const string Diamond = "Diamond";
		/// <summary>A kind of townsfolk moving into the world for the first time (user, 2026-11-25: "its one time per new npc (not
		/// counting the guide), for example: the first time a nurse comes, the first time a driad comes and so on. ensure no
		/// exploits and dont count the traveling merchant"): one point per kind, to every player in the world as it arrives, once
		/// per character (the key names the kind); the world remembers every kind that has lived in it, so a respawn never
		/// counts (<see cref="ResearchWorld"/>).</summary>
		public static string TownNPC(int type) => "TownNPC:" + NameOf(type);

		/// <summary>"after killing another player for the first time (individual)".</summary>
		public const string PlayerKill = "PlayerKill";
		/// <summary>"putting coins on the piggy bank for the first time (individualy)".</summary>
		public const string PiggyBank = "PiggyBank";

		// 0.3.0 (user, 2026-11-27: "killing a driller for the first time rewards a knowledge point, killing a coghawk for the first time should also rewards one")
		public const string Driller = "Driller", Coghawk = "Coghawk";

		// 0.4.0 (user, 2026-11-27: "make it so getting a heart crystal for the first time rewards a knowledge point")
		public const string LifeCrystal = "LifeCrystal";

		/// <summary>A boss or mini-boss by its canonical NPC type (the Twins and the Eater of Worlds count once).</summary>
		public static string Boss(int type) => "Boss:" + NameOf(type);

		public static string Event(string name) => "Event:" + name;

		/// <summary>The NPC's saved name: vanilla's internal name, or Mod/Name for a modded NPC.</summary>
		public static string NameOf(int type) {
			if (type > 0 && type < NPCID.Count) {
				return NPCID.Search.TryGetName(type, out string n) ? n : type.ToString();
			}
			Terraria.ModLoader.ModNPC modNPC = type >= NPCID.Count && type < Terraria.ModLoader.NPCLoader.NPCCount ? Terraria.ModLoader.NPCLoader.GetNPC(type) : null;
			return modNPC != null ? modNPC.FullName : type.ToString();
		}

		/// <summary>Housed town NPCs in the world (every client has them: vanilla syncs homes).</summary>
		public static int HousedTownNPCs() {
			int n = 0;
			foreach (NPC npc in Main.ActiveNPCs) {
				if (npc.townNPC && !npc.homeless) {
					n++;
				}
			}
			return n;
		}

		/// <summary>The reason shown for a server-told task (see <see cref="ResearchGrantPacket"/>).</summary>
		public static string BossReason(int type) => Language.GetTextValue("Mods.Cogpunk.Research.Tasks.Boss", Lang.GetNPCNameValue(type));

		public static string EventReason(string name) => Language.GetTextValue("Mods.Cogpunk.Research.Tasks.Event",
			Language.GetTextValue("Mods.Cogpunk.Research.Events." + name));
	}
}
