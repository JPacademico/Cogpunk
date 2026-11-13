using System;
using Cogpunk.Content.Combinator.Items;
using Cogpunk.Content.Furniture;
using Cogpunk.Content.Junkyard;
using Cogpunk.Content.OldBrassTown;
using Cogpunk.Content.OldBrassTown.Tiles;
using Cogpunk.Content.OldBrassTown.Weapons;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Combinator
{
	/// <summary>
	/// Where the Combinator's three parts come from (user-set 2026-11-12), once per world each:
	/// <list type="bullet">
	/// <item><see cref="TheFirstHalf"/>: Trash-Tr0m's chest, the Scrappy Trunk cache under the Junkyard's central heap (locked
	/// until his Lost Key opens it).</item>
	/// <item><see cref="TheSecondHalf"/>: Westworld's bank vault, the Brass Strongbox the Sheriff's Key opens (or, in a town
	/// built without the vault, the buried cache that holds its loot).</item>
	/// <item>The <see cref="CombinatorBlueprint"/>: the Wall of Flesh, on its first defeat only (<see cref="BlueprintDrop"/>).</item>
	/// </list>
	/// The halves are put in their chests by this system, so the Junkyard and Westworld code needn't know about them: at the
	/// end of world generation (<see cref="PostWorldGen"/>) for new worlds, and on the first load for worlds made before
	/// (<see cref="PostWorldLoad"/>: a locked cache or strongbox simply gets it; an opened one too, at the central heap / in
	/// the town). Each is placed once (the world flags <see cref="FirstHalfFlag"/>, <see cref="SecondHalfFlag"/>, saved by
	/// name): taking it out, moving it or crafting with it never brings another.
	/// <para>D2: chests and loot are the server's (or singleplayer's); the flags go out with the world data. D0: one bounded
	/// pass over <c>Main.chest</c>; a full chest is retried on a later load (logged once).</para>
	/// </summary>
	public sealed class CombinatorSystem : ModSystem
	{
		public static int FirstHalfFlag { get; private set; } = -1;
		public static int SecondHalfFlag { get; private set; } = -1;
		public static int BlueprintFlag { get; private set; } = -1;

		public override void Load() {
			FirstHalfFlag = WorldFlagSystem.Register("CombinatorFirstHalfPlaced");
			SecondHalfFlag = WorldFlagSystem.Register("CombinatorSecondHalfPlaced");
			BlueprintFlag = WorldFlagSystem.Register("CombinatorBlueprintDropped");
		}

		public override void Unload() {
			FirstHalfFlag = SecondHalfFlag = BlueprintFlag = -1;
		}

		public override void PostWorldGen() {
			StockHalves();
		}

		public override void PostWorldLoad() {
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				StockHalves();
			}
		}

		private static void StockHalves() {
			try {
				if (!WorldFlagSystem.Get(FirstHalfFlag) && TryStock(ModContent.ItemType<TheFirstHalf>(), JunkyardCacheChest())) {
					WorldFlagSystem.Flag(FirstHalfFlag) = true;
				}
				if (!WorldFlagSystem.Get(SecondHalfFlag) && TryStock(ModContent.ItemType<TheSecondHalf>(), WestworldVaultChest())) {
					WorldFlagSystem.Flag(SecondHalfFlag) = true;
				}
			}
			catch (Exception e) {
				SafeLog.Warn("Combinator.StockFailed", "Combinator: the halves could not be stocked ({0}).", e.Message);
			}
		}

		/// <summary>Puts one <paramref name="type"/> in chest <paramref name="index"/> (unless it's already there); true when the
		/// chest holds one now.</summary>
		private static bool TryStock(int type, int index) {
			if (index < 0 || index >= Main.maxChests || Main.chest[index] == null) {
				return false;
			}
			Chest chest = Main.chest[index];
			int empty = -1;
			for (int k = 0; k < chest.item.Length; k++) {
				Item it = chest.item[k];
				if (it != null && !it.IsAir && it.type == type) {
					return true;
				}
				if (empty < 0 && (it == null || it.IsAir)) {
					empty = k;
				}
			}
			if (empty < 0) {
				SafeLog.Warn("Combinator.ChestFull", "Combinator: a chest for item {0} is full; it will be tried again on the next load.", type);
				return false;
			}
			chest.item[empty] ??= new Item();
			chest.item[empty].SetDefaults(type);
			chest.item[empty].stack = 1;
			return true;
		}

		/// <summary>The Junkyard's cache: a Scrappy Trunk in the Junkyard, the locked one first, else the one nearest the
		/// central heap's column (an opened cache is a plain trunk).</summary>
		private static int JunkyardCacheChest() {
			if (!JunkyardSystem.Exists) {
				return -1;
			}
			int trunk = ModContent.TileType<ScrappyTrunkTile>();
			int centreX = JunkyardSystem.SurfaceArea.Center.X;
			int best = -1, bestD = int.MaxValue;
			for (int i = 0; i < Main.maxChests; i++) {
				Chest c = Main.chest[i];
				if (c == null || !JunkyardSystem.ContainsTile(new Point(c.x, c.y)) || !TileSafety.TryGetTile(c.x, c.y, out Tile t)
					|| !t.HasTile || t.TileType != trunk) {
					continue;
				}
				if (ScrappyTrunkTile.IsLocked(t)) {
					return i;
				}
				int d = Math.Abs(c.x - centreX);
				if (d < bestD) {
					bestD = d;
					best = i;
				}
			}
			return best;
		}

		/// <summary>Westworld's vault: the Brass Strongbox in the town; else the chest holding the vault's loot (the buried
		/// cache, when the town has no vault).</summary>
		private static int WestworldVaultChest() {
			int box = ModContent.TileType<BrassStrongboxTile>();
			int revolver = ModContent.ItemType<SheriffsRevolver>();
			int fallback = -1;
			for (int i = 0; i < Main.maxChests; i++) {
				Chest c = Main.chest[i];
				if (c == null || !OldBrassTownSystem.ContainsTile(new Point(c.x, c.y)) || !TileSafety.TryGetTile(c.x, c.y, out Tile t) || !t.HasTile) {
					continue;
				}
				if (t.TileType == box) {
					return i;
				}
				if (fallback < 0) {
					for (int k = 0; k < c.item.Length; k++) {
						if (c.item[k] != null && c.item[k].type == revolver) {
							fallback = i;
							break;
						}
					}
				}
			}
			return fallback;
		}
	}

	/// <summary>
	/// The Wall of Flesh's <see cref="CombinatorBlueprint"/>: one per world, on its first defeat (user-set 2026-11-12: "only on
	/// the first kill"). A world flag (<see cref="CombinatorSystem.BlueprintFlag"/>) marks it dropped, set on the server the
	/// moment it drops and sent with the world data, as the Alarm Head's odds are (<c>AlarmHeadDrop</c>). A world that was
	/// already in Hardmode before Cogpunk came gets it from its next Wall of Flesh. Not in the treasure bag: it drops loose, in
	/// every mode, for whoever is there.
	/// </summary>
	public sealed class BlueprintDrop : ItemDropWithConditionRule
	{
		public BlueprintDrop() : base(ModContent.ItemType<CombinatorBlueprint>(), 1, 1, 1, new FirstDefeatCondition()) {
		}

		public override ItemDropAttemptResult TryDroppingItem(DropAttemptInfo info) {
			ItemDropAttemptResult result = base.TryDroppingItem(info);
			if (result.State == ItemDropAttemptResultState.Success && !WorldFlagSystem.Get(CombinatorSystem.BlueprintFlag)) {
				WorldFlagSystem.Flag(CombinatorSystem.BlueprintFlag) = true;
				if (Main.netMode == NetmodeID.Server) {
					NetMessage.SendData(MessageID.WorldData);
				}
			}
			return result;
		}

		private sealed class FirstDefeatCondition : IItemDropRuleCondition
		{
			public bool CanDrop(DropAttemptInfo info) => !WorldFlagSystem.Get(CombinatorSystem.BlueprintFlag);

			public bool CanShowItemDropInUI() => true;

			public string GetConditionDescription() => Language.GetTextValue("Mods.Cogpunk.DropConditions.CombinatorFirstKill");
		}
	}

	/// <summary>Adds <see cref="BlueprintDrop"/> to the Wall of Flesh's loot (its own rules are untouched).</summary>
	public sealed class WallOfFleshBlueprint : GlobalNPC
	{
		public override bool AppliesToEntity(NPC entity, bool lateInstantiation) => entity.type == NPCID.WallofFlesh;

		public override void ModifyNPCLoot(NPC npc, NPCLoot npcLoot) {
			npcLoot.Add(new BlueprintDrop());
		}
	}
}
