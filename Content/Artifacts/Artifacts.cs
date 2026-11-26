using System;
using System.Collections.Generic;
using System.IO;
using Cogpunk.Content.Research;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ModLoader.Default;

namespace Cogpunk.Content.Artifacts
{
	/// <summary>
	/// Artifacts (user, 2026-11-26: "a new important mechanic for our mod, it should be called "Artifacts". artifacts are rare
	/// drops or secret itens that can only be obtained once per WORLD and have the artifact tag on it. artifact weapons cant be
	/// combined on the combinator, only one artifact accessory can be equiped at a time, artifacts cant be stolen by the drone.
	/// Picking an artifact for the first time rewards a knowledge point and unlocks a new tab on the ancient research table
	/// called "Artifacts". Artifacts should not be bound by normal balancing metrics, being able to be up to 80% better than
	/// other itens on its category").
	/// <list type="bullet">
	/// <item>An artifact is an item listed in <see cref="Names"/> (its class name), flagged in <see cref="CogpunkSets.Artifact"/>
	/// and given <see cref="ArtifactRarity"/>: the tag and a line in its tooltip (<see cref="ArtifactGlobalItem"/>).</item>
	/// <item>Once per world: each artifact has a world flag (<see cref="WorldFlagSystem"/>, saved by name and synced), set when
	/// someone in the world first picks it up (the picker's client tells the server, <see cref="ArtifactPickupPacket"/>); its drop
	/// rule (<see cref="ArtifactDropRule"/>) never drops it again in that world. While a dropped artifact lies on the ground
	/// unclaimed, no second one drops (<see cref="Dropped"/>, this session only: should the world close with it still lying
	/// there, it may drop again).</item>
	/// <item>The first time a character picks up each artifact: one knowledge point (a task, <see cref="TaskKey"/>, so never
	/// twice for one artifact), its record in the research window's Artifacts tab, which shows from the first one on
	/// (<see cref="ResearchPlayer.ArtifactsTab"/>).</item>
	/// <item>Never combined (<see cref="Combinator.Combination.CombinationRules"/>), never stolen (the Delivery Drone), never
	/// researched in Journey mode (no duplicates), and one artifact accessory worn at a time (<see cref="ArtifactGlobalItem"/>).</item>
	/// <item>Balance (D3 rule 11): up to 80% over the same-tier anchor of its category.</item>
	/// </list>
	/// D0: lookups bounds-checked; the packet's item type checked (an artifact, else ignored). D2: the server decides the drops
	/// and keeps the world flags; the picker's client pays its own knowledge point (as every task).
	/// </summary>
	public sealed class ArtifactSystem : ModSystem
	{
		/// <summary>The artifacts' item class names, in a fixed order (their world flags are saved by these names: never rename
		/// one). 2026-11-26: the Jade Cursed Glaives.</summary>
		public static readonly string[] Names = { "JadeCursedGlaives" };

		private static int[] flags = Array.Empty<int>();
		private static int[] types = Array.Empty<int>();
		private static bool[] dropped = Array.Empty<bool>();
		private static string[] taskKeys = Array.Empty<string>();

		/// <summary>The artifacts' item types, in <see cref="Names"/>' order (0 for one missing); found on first use after the
		/// items are loaded (the research tree asks in its own PostSetupContent, whichever system runs first).</summary>
		public static IReadOnlyList<int> Types {
			get {
				EnsureTypes();
				return types;
			}
		}

		private static void EnsureTypes() {
			if (types.Length == Names.Length) {
				return;
			}
			int[] found = new int[Names.Length];
			for (int k = 0; k < Names.Length; k++) {
				found[k] = ModContent.TryFind("Cogpunk/" + Names[k], out ModItem item) ? item.Type : 0;
				if (found[k] <= 0) {
					SafeLog.Warn("ArtifactSystem.Missing", "Artifact {0} has no item; it is skipped.", Names[k]);
				}
			}
			types = found;
		}

		public override void Load() {
			flags = new int[Names.Length];
			dropped = new bool[Names.Length];
			taskKeys = new string[Names.Length];
			for (int k = 0; k < Names.Length; k++) {
				flags[k] = WorldFlagSystem.Register("Artifact." + Names[k]);
				taskKeys[k] = "Artifact:" + Names[k];
			}
		}

		public override void PostSetupContent() {
			EnsureTypes();
		}

		public override void Unload() {
			flags = Array.Empty<int>();
			types = Array.Empty<int>();
			dropped = Array.Empty<bool>();
			taskKeys = Array.Empty<string>();
		}

		public override void ClearWorld() {
			Array.Clear(dropped);
		}

		/// <summary>The index of <paramref name="type"/> among the artifacts, or -1.</summary>
		public static int IndexOf(int type) {
			if (type <= ItemID.None) {
				return -1;
			}
			EnsureTypes();
			for (int k = 0; k < types.Length; k++) {
				if (types[k] == type) {
					return k;
				}
			}
			return -1;
		}

		public static bool IsArtifact(int type) => CogpunkSets.IsArtifactType(type);

		public static bool IsArtifact(Item item) => item != null && !item.IsAir && IsArtifact(item.type);

		/// <summary>The knowledge task of its first pickup ("Artifact:" + its name; saved: never rename), or null.</summary>
		public static string TaskKey(int type) {
			int k = IndexOf(type);
			return k >= 0 ? taskKeys[k] : null;
		}

		/// <summary>Someone in this world has picked it up (it never drops here again).</summary>
		public static bool Obtained(int type) {
			int k = IndexOf(type);
			return k >= 0 && WorldFlagSystem.Get(flags[k]);
		}

		/// <summary>One lies on the ground, dropped this session and not yet picked up (the server's).</summary>
		public static bool Dropped(int type) {
			int k = IndexOf(type);
			return k >= 0 && dropped[k];
		}

		/// <summary>It may drop now (the server asks): an artifact neither obtained in this world nor lying on its ground.</summary>
		public static bool Available(int type) {
			int k = IndexOf(type);
			return k >= 0 && !WorldFlagSystem.Get(flags[k]) && !dropped[k];
		}

		/// <summary>The server: one just dropped.</summary>
		public static void MarkDropped(int type) {
			int k = IndexOf(type);
			if (k >= 0) {
				dropped[k] = true;
			}
		}

		/// <summary>The server (or singleplayer): someone picked it up; this world is done with it (saved, synced).</summary>
		public static void MarkObtained(int type) {
			int k = IndexOf(type);
			if (k < 0 || Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}
			dropped[k] = false;
			if (WorldFlagSystem.Get(flags[k])) {
				return;
			}
			WorldFlagSystem.Flag(flags[k]) = true;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.WorldData);
			}
		}

		/// <summary>The picker's client: an artifact was picked up. The world is told (the server keeps its flag), and the
		/// character's first one of this kind pays a knowledge point and records it in the Artifacts tab.</summary>
		public static void OnPickedUp(Player player, Item item) {
			if (player == null || player.whoAmI != Main.myPlayer || !IsArtifact(item)) {
				return;
			}
			if (Main.netMode == NetmodeID.SinglePlayer) {
				MarkObtained(item.type);
			}
			else if (Main.netMode == NetmodeID.MultiplayerClient && !Obtained(item.type)) {
				ModContent.GetInstance<ArtifactPickupPacket>().Send(item.type);
			}
			player.GetModPlayer<ResearchPlayer>().FoundArtifact(item.type);
		}
	}

	/// <summary>The artifacts' rarity: a slow shimmer between jade and gold (allocation-free: two colours and a sine).</summary>
	public sealed class ArtifactRarity : ModRarity
	{
		private static readonly Color Jade = new(126, 230, 160), Gold = new(255, 211, 92);

		public override Color RarityColor => Color.Lerp(Jade, Gold, (MathF.Sin(Main.GlobalTimeWrappedHourly * 2.4f) + 1f) * 0.5f);

		/// <summary>The tag's colour (the tooltip line): the rarity's.</summary>
		public static Color Tint => Color.Lerp(Jade, Gold, (MathF.Sin(Main.GlobalTimeWrappedHourly * 2.4f) + 1f) * 0.5f);
	}

	/// <summary>The artifacts' items: the tag in the tooltip, one artifact accessory worn at a time, the pickup.</summary>
	public sealed class ArtifactGlobalItem : GlobalItem
	{
		public override bool AppliesToEntity(Item entity, bool lateInstantiation) => ArtifactSystem.IsArtifact(entity.type);

		public override void ModifyTooltips(Item item, List<TooltipLine> tooltips) {
			int at = tooltips.FindIndex(static l => l.Mod == "Terraria" && l.Name == "ItemName");
			TooltipLine tag = new(Mod, "ArtifactTag", Language.GetTextValue("Mods.Cogpunk.Artifacts.Tag")) { OverrideColor = ArtifactRarity.Tint };
			tooltips.Insert(at >= 0 ? at + 1 : 0, tag);
			if (item.accessory) {
				tooltips.Add(new TooltipLine(Mod, "ArtifactOneWorn", Language.GetTextValue("Mods.Cogpunk.Artifacts.OneAccessory")) {
					OverrideColor = new Color(190, 190, 200),
				});
			}
		}

		/// <summary>"only one artifact accessory can be equiped at a time": refused while another one is worn in another slot:
		/// vanilla's seven functional accessory slots (armor 3..9) and, for the player whose slots the modded ones read now
		/// (tModLoader's <c>ModAccessorySlot</c>s follow <c>Main.CurrentPlayer</c>), the modded ones.</summary>
		public override bool CanEquipAccessory(Item item, Player player, int slot, bool modded) {
			if (!item.accessory) {
				return true;
			}
			for (int i = 3; i < 10 && i < player.armor.Length; i++) {
				if (!modded && i == slot) {
					continue;                                    // the slot it goes into: what is there now comes out
				}
				if (WornElsewhere(player.armor[i], item)) {
					return false;
				}
			}
			if (Main.CurrentPlayer != player) {
				return true;
			}
			ModAccessorySlotPlayer slots = player.GetModPlayer<ModAccessorySlotPlayer>();
			AccessorySlotLoader loader = LoaderManager.Get<AccessorySlotLoader>();
			for (int k = 0; k < slots.SlotCount; k++) {
				if (modded && k == slot) {
					continue;
				}
				if (WornElsewhere(loader.Get(k, player).FunctionalItem, item)) {
					return false;
				}
			}
			return true;
		}

		private static bool WornElsewhere(Item other, Item item) => other != null && !other.IsAir && !ReferenceEquals(other, item) && ArtifactSystem.IsArtifact(other);

		public override bool OnPickup(Item item, Player player) {
			ArtifactSystem.OnPickedUp(player, item);
			return true;
		}
	}

	/// <summary>
	/// An artifact's drop: <see cref="Denominator"/> to 1 (with the killer's luck, as vanilla's own rules), only while
	/// <see cref="ArtifactSystem.Available"/> and the rule's own test hold; a drop marks it lying on the ground. Secret: it shows in no
	/// bestiary (user: "rare drops or secret itens").
	/// </summary>
	public sealed class ArtifactDropRule : IItemDropRule
	{
		public readonly int ItemType;
		public readonly int Denominator;
		private readonly Func<DropAttemptInfo, bool> test;

		public List<IItemDropRuleChainAttempt> ChainedRules { get; } = new();

		public ArtifactDropRule(int itemType, int denominator, Func<DropAttemptInfo, bool> test = null) {
			ItemType = itemType;
			Denominator = Math.Max(1, denominator);
			this.test = test;
		}

		public bool CanDrop(DropAttemptInfo info) => !info.IsInSimulation && ArtifactSystem.Available(ItemType) && (test == null || test(info));

		public ItemDropAttemptResult TryDroppingItem(DropAttemptInfo info) {
			int roll = info.player != null ? info.player.RollLuck(Denominator) : info.rng.Next(Denominator);
			if (roll != 0) {
				return new ItemDropAttemptResult { State = ItemDropAttemptResultState.FailedRandomRoll };
			}
			CommonCode.DropItem(info, ItemType, 1);
			ArtifactSystem.MarkDropped(ItemType);
			return new ItemDropAttemptResult { State = ItemDropAttemptResultState.Success };
		}

		public void ReportDroprates(List<DropRateInfo> drops, DropRateInfoChainFeed ratesInfo) {
			// secret: not listed
		}
	}

	/// <summary>The picker's client -> the server: an artifact (its item type) was picked up; the world flag is set and synced.
	/// D0: the type must be an artifact's, from a real player; anything else is ignored.</summary>
	public sealed class ArtifactPickupPacket : CogpunkPacket
	{
		public void Send(int type) {
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				return;
			}
			ModPacket packet = Begin();
			packet.Write(type);
			packet.Send();
		}

		public override void Receive(BinaryReader reader, int sender) {
			int type = reader.ReadInt32();
			if (Main.netMode != NetmodeID.Server || sender < 0 || sender >= Main.maxPlayers || !Main.player[sender].active) {
				return;
			}
			if (ArtifactSystem.IndexOf(type) >= 0) {
				ArtifactSystem.MarkObtained(type);
			}
		}
	}

	/// <summary>
	/// Where artifacts drop. 2026-11-26: the Jade Cursed Glaives (user: "it does not drop from jadey anymore, instead it has a 1%
	/// drop chance when killing an enemy that is jade petrified"): from any enemy turned to jade (<see cref="Gems.JadeCurseNPC.Petrified"/>)
	/// as it dies, 1 in <see cref="GlaiveOdds"/>; not a critter, a dummy, a friendly or a statue's spawn.
	/// </summary>
	public sealed class ArtifactGlobalNPC : GlobalNPC
	{
		public const int GlaiveOdds = 100;                  // user-set: 1%

		public override void ModifyGlobalLoot(GlobalLoot globalLoot) {
			int glaive = ModContent.ItemType<Bosses.Jadey.Weapons.JadeCursedGlaives>();
			globalLoot.Add(new ArtifactDropRule(glaive, GlaiveOdds, static info => PetrifiedEnemy(info.npc)));
		}

		private static bool PetrifiedEnemy(NPC npc) {
			return npc != null && !npc.SpawnedFromStatue && Core.Combat.CritKillSlowMotion.Counts(npc) && Gems.JadeCurseNPC.Petrified(npc);
		}
	}
}
