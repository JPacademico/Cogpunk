using System;
using System.Collections.Generic;
using Cogpunk.Content.Coghaven;
using Cogpunk.Content.Junkyard;
using Cogpunk.Content.Research.Items;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace Cogpunk.Content.Research
{
	/// <summary>
	/// A character's research (user, 2026-11-18: "our big craft unlocking mechanic"): their unspent knowledge points
	/// (<see cref="Knowledge"/>), the knowledge tasks they have done (each once: <see cref="KnowledgeTasks"/>), the nodes they
	/// have unlocked ("the unlocks are individual (each player should have his menu)") and the secret nodes they have seen, and
	/// what some nodes ask of them: which base ore tiers they have collected (<see cref="AllOreTiers"/>) and which edges of the
	/// world they have reached (<see cref="ReachedBothEdges"/>). Every character starts with an <see cref="AncientResearchBook"/>
	/// ("every player should start with a Ancient research book"); a character made before this update gets one the first time
	/// it enters a world.
	/// <para>The owner's client watches for the individual tasks (biomes, chests, coins, angler quests, pickups, purchases) a
	/// few times a second; the server tells it about the world's (first boss kills, events: <see cref="ResearchWorld"/>) and
	/// about its kills of rare creatures (<see cref="ResearchGlobalNPC"/>).</para>
	/// <para>D2: the character's own data, saved with it by name (D0 rule 9); the unlocked nodes are synced to the server and
	/// the other clients (<see cref="ResearchSyncPacket"/>, the ModPlayer sync pattern), since their bonuses act on every side
	/// (move speed) and on the server (the double ore). D1: the task checks run every <see cref="CheckInterval"/> ticks on the
	/// owner's client only, without allocating.</para>
	/// </summary>
	public sealed class ResearchPlayer : ModPlayer
	{
		public const int CheckInterval = 30;
		private const int MaxSaved = 512;                        // D0: a cap on what a save can make us hold
		public const long PlatinumTarget = 10L * 1000000L;       // user-set: 10 platinum coins, in copper
		public const int AnglerTarget = 5;                       // user-set: 5 fisherman quests
		public const int TownTarget = 10;                        // user-set: 10 housed NPCs

		/// <summary>Unspent knowledge points.</summary>
		public int Knowledge;

		private HashSet<string> earned;
		private HashSet<string> unlocked;
		private HashSet<string> revealed;
		private bool[] unlockedBits = Array.Empty<bool>();       // by node index (the sync mask), rebuilt from `unlocked`
		private byte oreTiers;                                   // bit k: base tier k collected
		private byte edges;                                      // bit 0: the ocean, bit 1: the Junkyard
		private byte gemStaffs;                                  // bit k: Weapons.BundleOfWands.StaffItems[k] had at some point
		private byte found;                                      // FoundAlchemy | FoundCooking | FoundStone (2026-11-24), saved
		private const byte FoundAlchemy = 1, FoundCooking = 2, FoundStone = 4, FoundRobe = 8;
		private bool reportedStaffs;                             // this session: the world was told (Bundle Up!)
		private int quietTicks;                                  // a manual's own chat line covers the reveals it causes
		private bool announceReveal;                             // a reveal was kept since the last "Knowledge expanded!"
		private int missStacks;                                  // Trigger Finger: ranged shots missed since the last hit (owner)
		private bool gotBook;
		private int lastChest = -1;
		private static readonly int[] noSlots = Array.Empty<int>();
		/// <summary>Guards the sets: vanilla saves the character on a thread-pool thread (decompiled
		/// <c>WorldGen.saveToonWhilePlaying</c>), so a save must never read a set while the game adds to it.</summary>
		private readonly object sync = new();
		private int saveIn = -1;                                // ticks until the progress is saved (-1: nothing to save)
		public const int SaveDelay = 60;                        // a change is saved a second later (several at once, one save)
		private const int MaxDistinctKinds = 50;                // a Distinct cost can't count more kinds than the 50 slots hold

		public bool AllOreTiers => (oreTiers & 0xF) == 0xF;
		public bool ReachedBothEdges => (edges & 3) == 3;
		/// <summary>Has had every pre-Hardmode gem staff (at some point: <see cref="Weapons.BundleOfWands.StaffItems"/>).</summary>
		public bool AllGemStaffs => (gemStaffs & 0x7F) == 0x7F;
		public bool Earned(string key) => earned != null && key != null && earned.Contains(key);

		/// <summary>Has found an Alchemy Table: stood within its crafting range or held one (user, 2026-11-24: "finds a alchemy
		/// table (gets within crafting range, or gets one in the inventory)"); Fulfilling Concoction's reveal.</summary>
		public bool FoundAlchemyTable => (found & FoundAlchemy) != 0;

		/// <summary>Has found a Cooking Pot (or a Cauldron, its other style): within its use range or held ("finds a cooking pot
		/// (gets into use range or gets one on the inventory)"); Seasoning's and Proper Meal's reveal.</summary>
		public bool FoundCookingPot => (found & FoundCooking) != 0;

		/// <summary>Has touched a Fundamental Stone (right-clicked one, sealed or not): the window's Mystery of the Past tab
		/// shows (user, 2026-11-24: "a new tab that appears once the player has interacted with a fundamental stone").</summary>
		public bool MysteryTab => (found & FoundStone) != 0;

		/// <summary>Has had a gem robe (any of vanilla's seven or the Jade Robe) in the inventory or worn: RGBT's reveal (user,
		/// 2026-11-24: "show only an "?" until the player has obtained at leat one gem robe (any)"); saved.</summary>
		public bool FoundGemRobe => (found & FoundRobe) != 0;

		/// <summary>The local player right-clicked a Fundamental Stone (<see cref="Secrets.FundamentalStoneTile"/>).</summary>
		public void TouchStone() {
			if (Player.whoAmI == Main.myPlayer && (found & FoundStone) == 0) {
				found |= FoundStone;
				MarkDirty();
			}
		}

		public override void Initialize() {
			earned = new HashSet<string>();
			unlocked = new HashSet<string>();
			revealed = new HashSet<string>();
			unlockedBits = Array.Empty<bool>();
			Knowledge = 0;
			oreTiers = 0;
			edges = 0;
			gemStaffs = 0;
			found = 0;
			reportedStaffs = false;
			quietTicks = 0;
			gotBook = false;
		}

		// --- nodes ------------------------------------------------------------------------------------------------------------

		public bool Has(ResearchNode node) => node != null && node.Index < unlockedBits.Length && unlockedBits[node.Index];

		public bool Has(string name) => Has(ResearchNodes.Get(name));

		/// <summary>A node that isn't secret, a secret node the player has seen or unlocked, or one whose reveal holds now. Once
		/// seen a node is kept for good (user, 2026-11-24: "when a "?" is revealed or unlocked it should never return to "?" again
		/// and instead stay revealed/unlocked so theres no confusion to the player"): the moment its reveal holds or it is
		/// unlocked it goes into the saved set (<see cref="Remember"/>), whatever later happens to the world or the step that
		/// revealed it (a stone deactivated, another world without the boss).</summary>
		public bool Visible(ResearchNode node) {
			if (node.Reveal == null) {
				return true;
			}
			lock (sync) {
				if (revealed.Contains(node.Name)) {
					return true;
				}
			}
			if (Has(node)) {
				Remember(node, announce: false);                   // unlocked is seen
				return true;
			}
			if (Player.whoAmI == Main.myPlayer && node.Reveal(Player)) {
				Remember(node, announce: true);
				return true;
			}
			return false;
		}

		/// <summary>The owner: keeps <paramref name="node"/> seen for good (saved), and queues "Knowledge expanded!" once.</summary>
		private void Remember(ResearchNode node, bool announce) {
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			bool added;
			lock (sync) {
				added = revealed.Count < MaxSaved && revealed.Add(node.Name);
			}
			if (added) {
				MarkDirty();
				announceReveal |= announce;
			}
		}

		/// <summary>The owner: every reveal checked now (entering a world, opening the window), so nothing waits 30 ticks.</summary>
		public void CheckRevealsNow() {
			if (Player.whoAmI == Main.myPlayer) {
				CheckReveals();
			}
		}

		/// <summary>The owner's client, every <see cref="CheckInterval"/> ticks: secret nodes whose reveal now holds are kept for
		/// good, with "Knowledge expanded!" in chat (user, 2026-11-18) unless a manual just said it (<see cref="QuietReveals"/>).</summary>
		private void CheckReveals() {
			var nodes = ResearchNodes.All;
			for (int k = 0; k < nodes.Count; k++) {
				ResearchNode node = nodes[k];
				if (node.Reveal == null) {
					continue;
				}
				bool known;
				lock (sync) {
					known = revealed.Contains(node.Name);
				}
				if (known) {
					continue;
				}
				if (Has(node)) {
					Remember(node, announce: false);
				}
				else if (node.Reveal(Player)) {
					Remember(node, announce: true);
				}
			}
			AnnounceReveals();
		}

		/// <summary>The owner: "Knowledge expanded!" for the reveals since the last line, unless a manual just said it.</summary>
		private void AnnounceReveals() {
			if (!announceReveal) {
				return;
			}
			announceReveal = false;
			if (quietTicks <= 0 && !Main.dedServ) {
				Main.NewText(Language.GetTextValue("Mods.Cogpunk.Research.KnowledgeExpanded"), new Color(223, 185, 78));
				SoundEngine.PlaySound(SoundID.Item29 with { Pitch = 0.3f, Volume = 0.5f }, Player.Center);
			}
		}

		/// <summary>A manual was read (it says "Knowledge expanded!" itself): the reveals it causes go without a second line.</summary>
		public void QuietReveals(int ticks = 120) {
			quietTicks = Math.Max(quietTicks, ticks);
		}

		private void RebuildBits() {
			int n = ResearchNodes.All.Count;
			bool[] bits = unlockedBits.Length == n ? unlockedBits : new bool[n];
			lock (sync) {
				for (int k = 0; k < n; k++) {
					bits[k] = unlocked.Contains(ResearchNodes.All[k].Name);
				}
			}
			unlockedBits = bits;
		}

		/// <summary>Why <paramref name="node"/> can't be unlocked now (<see cref="Blocker.None"/>: it can).</summary>
		public Blocker Check(ResearchNode node) {
			if (Has(node)) {
				return Blocker.Unlocked;
			}
			if (!Visible(node)) {
				return Blocker.Hidden;                              // a secret node can't be had before it is revealed
			}
			foreach (string req in node.Requires) {
				if (!Has(req)) {
					return Blocker.Requires;
				}
			}
			if (Knowledge < node.Cost) {
				return Blocker.Knowledge;
			}
			if (node.Condition != null && !node.Condition(Player)) {
				return Blocker.Condition;
			}
			foreach (ResearchItemCost cost in node.Items) {
				if (CountItems(cost) < cost.Count) {
					return Blocker.Items;
				}
			}
			return Blocker.None;
		}

		public enum Blocker { None, Unlocked, Hidden, Requires, Knowledge, Condition, Items }

		/// <summary>How many items in the main inventory (slots 0-49) match <paramref name="cost"/>; for a
		/// <see cref="ResearchItemCost.Distinct"/> cost, how many different kinds (each kind once, whatever its stack).</summary>
		public int CountItems(ResearchItemCost cost) {
			int n = 0;
			for (int i = 0; i < 50 && i < Player.inventory.Length; i++) {
				Item it = Player.inventory[i];
				if (it == null || it.IsAir || !cost.Matches(it)) {
					continue;
				}
				if (!cost.Distinct) {
					n += it.stack;
				}
				else if (!SeenBefore(it.type, i)) {
					n++;
				}
			}
			return n;
		}

		/// <summary>A kind already counted in an earlier slot (a Distinct cost; 50 slots at most: no allocation, D1).</summary>
		private bool SeenBefore(int type, int slot) {
			for (int j = 0; j < slot; j++) {
				Item other = Player.inventory[j];
				if (other != null && !other.IsAir && other.type == type) {
					return true;
				}
			}
			return false;
		}

		/// <summary>The owner's client: unlocks <paramref name="node"/> if it can (spends the points, takes the items left to
		/// right, top to bottom: inventory slot order), tells the server, and returns whether it did.</summary>
		public bool TryUnlock(ResearchNode node) {
			if (Player.whoAmI != Main.myPlayer || Check(node) != Blocker.None) {
				return false;
			}
			Span<int> taken = stackalloc int[MaxDistinctKinds];          // a Distinct cost's kinds so far (no allocation, D1)
			foreach (ResearchItemCost cost in node.Items) {
				int left = cost.Count;
				int kinds = 0;
				for (int i = 0; i < 50 && i < Player.inventory.Length && left > 0; i++) {
					Item it = Player.inventory[i];
					if (it == null || it.IsAir || !cost.Matches(it)) {
						continue;
					}
					int take = Math.Min(left, it.stack);
					if (cost.Distinct) {
						if (taken[..kinds].Contains(it.type) || kinds >= taken.Length) {
							continue;                                    // one of each kind, the first ones met
						}
						taken[kinds++] = it.type;
						take = 1;
					}
					it.stack -= take;
					left -= take;
					if (it.stack <= 0) {
						it.TurnToAir();
					}
				}
			}
			lock (sync) {
				Knowledge -= node.Cost;
				unlocked.Add(node.Name);
				if (revealed.Count < MaxSaved) {
					revealed.Add(node.Name);                     // unlocked is seen, for good
				}
			}
			RebuildBits();
			Recipe.FindRecipes();                                // a recipe it unlocks shows at once
			SyncPlayer(-1, Main.myPlayer, false);
			MarkDirty();
			return true;
		}

		public override void PostUpdateEquips() {
			var nodes = ResearchNodes.All;
			for (int k = 0; k < nodes.Count && k < unlockedBits.Length; k++) {
				if (unlockedBits[k]) {
					nodes[k].Passive?.Invoke(Player);
				}
			}
		}

		/// <summary>"Hit the Joints" (user-set 2026-11-18: "+10% damage against mech enemies permanently"): every hit, any class,
		/// on a machine (<see cref="Core.Systems.CogpunkSets.Mechanical"/>).</summary>
		public override void ModifyHitNPC(NPC target, ref NPC.HitModifiers modifiers) {
			if (Has(ResearchNodes.HitTheJoints) && Core.Systems.CogpunkSets.IsMechanical(target)) {
				modifiers.SourceDamage *= 1f + ResearchNodes.HitTheJointsBonus;
			}
		}

		/// <summary>"Just the Tip" (user-set 2026-11-18: "make so spear weapons deal 25% more damage when hiting enemies on the max
		/// range (ending frames of the thrust or initial frame of the return motion)"). Runs where the hit is decided: the
		/// spear's owner (D2).</summary>
		public override void ModifyHitNPCWithProj(Projectile proj, NPC target, ref NPC.HitModifiers modifiers) {
			if (Has(ResearchNodes.JustTheTip) && AtTheTip(proj, Player)) {
				modifiers.SourceDamage *= 1f + ResearchNodes.JustTheTipBonus;
			}
			if (missStacks > 0 && proj.DamageType.CountsAsClass(DamageClass.Ranged) && Has(ResearchNodes.TriggerFinger)) {
				modifiers.SourceDamage *= 1f + ResearchNodes.TriggerFingerBonus * missStacks;
			}
		}

		public override void OnHitNPCWithProj(Projectile proj, NPC target, NPC.HitInfo hit, int damageDone) {
			if (damageDone > 0 && proj.DamageType.CountsAsClass(DamageClass.Ranged)) {
				missStacks = 0;                                  // "the next successful hit": the stacks are spent
			}
			Calcify(target, proj.type);
			GreenIsGoodKill(target);
		}

		public override void OnHitNPCWithItem(Item item, NPC target, NPC.HitInfo hit, int damageDone) {
			Calcify(target, -1);
			GreenIsGoodKill(target);
		}

		/// <summary>"Green = Good" (user-set 2026-11-24: "heal when killing a jade petrified enemy (20 health)"): the hit that killed
		/// an enemy turned to jade (<see cref="Gems.JadeCurseNPC.Petrified"/>; its life gone on the hitting client) heals its
		/// player <see cref="ResearchNodes.GreenIsGoodHeal"/> (vanilla's <c>Player.Heal</c>: the number shows, message 35 tells
		/// the others). Not for statue spawns, critters or dummies.</summary>
		private void GreenIsGoodKill(NPC target) {
			if (Player.whoAmI != Main.myPlayer || target == null || target.life > 0 || target.SpawnedFromStatue || target.friendly
				|| target.lifeMax <= 5 || target.CountsAsACritter || target.immortal || !Has(ResearchNodes.GreenIsGood)
				|| !Gems.JadeCurseNPC.Petrified(target)) {
				return;
			}
			Player.Heal(ResearchNodes.GreenIsGoodHeal);
		}

		/// <summary>"Trigger Finger" (user-set 2026-11-19: "affter missing a shot with a ranged weapon (not causing damage with
		/// the attack) it gives the next successfull hit +25% bonus damage (stacking up to 4 times)"): a shot of the owner's
		/// ranged weapon died without hitting anything (<see cref="TriggerFingerShot"/>).</summary>
		public void ShotMissed() {
			if (Player.whoAmI == Main.myPlayer && Has(ResearchNodes.TriggerFinger)) {
				missStacks = Math.Min(ResearchNodes.TriggerFingerStacks, missStacks + 1);
			}
		}

		/// <summary>"Calcified" (user-set 2026-11-19: "every enemy killed launches a small bone fliyng that deals 40 damage if it
		/// hits another enemy"): the hit that killed <paramref name="target"/> (its life gone on the hitting client, which owns
		/// the bone: D2) throws a <see cref="CalcifiedBone"/> up out of it. Never from a bone's own kill (no chain, D0 rule
		/// 4), nor from statue spawns, critters or dummies.</summary>
		private void Calcify(NPC target, int projType) {
			if (Player.whoAmI != Main.myPlayer || target == null || target.life > 0 || !Has(ResearchNodes.Calcified)
				|| projType == ModContent.ProjectileType<CalcifiedBone>() || target.SpawnedFromStatue || target.friendly
				|| target.lifeMax <= 5 || target.CountsAsACritter || target.immortal) {
				return;
			}
			Vector2 velocity = new(Main.rand.NextFloat(-3.5f, 3.5f), Main.rand.NextFloat(-8f, -5.5f));
			Core.Safety.SafeSpawn.TryNewProjectile(Player.GetSource_OnHit(target), target.Center, velocity, ModContent.ProjectileType<CalcifiedBone>(),
				ResearchNodes.CalcifiedDamage, 2f, out _, Player.whoAmI);
		}

		/// <summary>"Slimed!" (user-set 2026-11-19: "makes so the player aply slimed effect to enemy upon contact"): an enemy that
		/// touches the player is slimed (<see cref="ResearchSlimed"/>; synced by vanilla's NPC buff message).</summary>
		public override void OnHitByNPC(NPC npc, Player.HurtInfo hurtInfo) {
			if (Has(ResearchNodes.Slimed) && npc != null && npc.active && !npc.friendly) {
				npc.AddBuff(ModContent.BuffType<ResearchSlimed>(), ResearchNodes.SlimedTicks);
			}
		}

		/// <summary>
		/// A spear's thrust at full reach: its last <see cref="ResearchNodes.TipThrustFrames"/> frames out or its first
		/// <see cref="ResearchNodes.TipReturnFrames"/> back.
		/// <list type="bullet">
		/// <item>Vanilla's spears (<c>ProjAIStyleID.Spear</c>; decompiled 1.4.4 <c>Projectile.AI_019_Spears</c>: the reach is
		/// set from the owner's <c>itemAnimation</c> each tick, growing while it is at least <c>itemAnimationMax / 3</c>,
		/// largest exactly there, shrinking after). The jousting lances share that AI but don't thrust: left out.</item>
		/// <item>Cogpunk's Screwdriver (<see cref="Scrap.Weapons.ScrewdriverProjectile"/>): out over the first half of its life
		/// and back, the turn at <c>timeLeft == duration / 2</c>.</item>
		/// </list>
		/// Other mods' spears with their own AI can't be read and get nothing.
		/// </summary>
		public static bool AtTheTip(Projectile proj, Player owner) {
			if (proj == null || owner == null || proj.owner != owner.whoAmI) {
				return false;
			}
			if (proj.aiStyle == ProjAIStyleID.Spear) {
				if (proj.type == ProjectileID.JoustingLance || proj.type == ProjectileID.ShadowJoustingLance || proj.type == ProjectileID.HallowJoustingLance) {
					return false;
				}
				int turn = owner.itemAnimationMax / 3;
				int a = owner.itemAnimation;
				return a >= turn - ResearchNodes.TipReturnFrames && a < turn + ResearchNodes.TipThrustFrames;
			}
			if (proj.type == ModContent.ProjectileType<Scrap.Weapons.ScrewdriverProjectile>()) {
				int half = Math.Max(2, owner.itemAnimationMax) / 2;
				int t = proj.timeLeft;
				return t >= half - ResearchNodes.TipReturnFrames && t < half + ResearchNodes.TipThrustFrames;
			}
			return false;
		}

		// --- knowledge --------------------------------------------------------------------------------------------------------

		/// <summary>The owner's client: <paramref name="points"/> for the task <paramref name="key"/> the first time it is done
		/// (each task once per character), with a line in chat, a chime and a "+1" over the head.</summary>
		public void Grant(string key, string reason, int points = 1) {
			if (Player.whoAmI != Main.myPlayer || earned == null || string.IsNullOrEmpty(key) || points <= 0) {
				return;
			}
			lock (sync) {
				if (earned.Count >= MaxSaved || !earned.Add(key)) {
					return;                                          // each task once per character: no farming
				}
				Knowledge += points;
			}
			MarkDirty();
			if (Main.dedServ) {
				return;
			}
			// user, 2026-11-18: "chat should notify individualy with a message when a player gains a research point "gained
			// knowledge!"" (this client's own chat: only this player sees it)
			Main.NewText(Language.GetTextValue("Mods.Cogpunk.Research.Gained", points, reason), new Color(140, 201, 176));
			CombatText.NewText(Player.getRect(), new Color(140, 228, 88), Language.GetTextValue("Mods.Cogpunk.Research.GainedShort", points));
			SoundEngine.PlaySound(SoundID.ResearchComplete with { Volume = 0.6f }, Player.Center);
		}

		/// <summary>The owner's client: a task named by its static key (Mods.Cogpunk.Research.Tasks.&lt;key&gt; is the reason).</summary>
		public void Grant(string key) => Grant(key, Language.GetTextValue("Mods.Cogpunk.Research.Tasks." + key));

		/// <summary>The owner: research changed; the character is saved <see cref="SaveDelay"/> ticks later (vanilla's own
		/// in-game character save, the one it runs every 5 minutes in multiplayer and on death), so a crash, a lost
		/// connection or a closed game can't take it away.</summary>
		public void MarkDirty() {
			if (Player.whoAmI == Main.myPlayer && !Main.dedServ && saveIn < 0) {
				saveIn = SaveDelay;
			}
		}

		public override void PostUpdate() {
			if (Player.whoAmI != Main.myPlayer || Main.dedServ || Main.gameMenu) {
				return;
			}
			if (saveIn >= 0 && --saveIn < 0 && Main.ActivePlayerFileData != null && !Main.ActivePlayerFileData.ServerSideCharacter) {
				WorldGen.saveToonWhilePlaying();
			}
			CheckChest();
			if (quietTicks > 0) {
				quietTicks--;
			}
			if ((Main.GameUpdateCount + (uint)Player.whoAmI) % CheckInterval != 0) {
				return;
			}
			if ((found & (FoundAlchemy | FoundCooking)) != (FoundAlchemy | FoundCooking)) {
				FindStations();
			}
			CheckReveals();
			if (AllGemStaffs && !reportedStaffs && !ResearchWorld.AllGemStaffs) {
				reportedStaffs = true;                               // once a session: the server sets it for the world
				ResearchWorld.ReportAllGemStaffs();
			}
			if (Player.ZoneMarble) {
				Grant(KnowledgeTasks.Marble);
			}
			if (Player.ZoneGranite) {
				Grant(KnowledgeTasks.Granite);
			}
			if (Player.ZoneGlowshroom) {
				Grant(KnowledgeTasks.GlowingMushroom);
			}
			if (OnCloudIsland()) {
				Grant(KnowledgeTasks.SkyIsland);
			}
			if (Player.anglerQuestsFinished >= AnglerTarget) {
				Grant(KnowledgeTasks.Angler5);
			}
			if (Savings() >= PlatinumTarget) {
				Grant(KnowledgeTasks.Platinum10);
			}
			if (KnowledgeTasks.HousedTownNPCs() >= TownTarget) {
				Grant(KnowledgeTasks.Town10);
			}
			if (Player.ZoneBeach) {
				edges |= 1;
			}
			if (Player.InModBiome<JunkyardBiome>()) {
				edges |= 2;
			}
			for (int i = 0; i < 58 && i < Player.inventory.Length; i++) {
				Item it = Player.inventory[i];
				if (it != null && !it.IsAir) {
					Collected(it.type);
				}
			}
			if ((found & FoundRobe) == 0) {
				for (int i = 0; i < Player.armor.Length && i < 20; i++) {
					Item it = Player.armor[i];
					if (it != null && !it.IsAir && ResearchRecipes.IsGemRobe(it.type)) {
						found |= FoundRobe;
						MarkDirty();
						break;
					}
				}
			}
		}

		/// <summary>The owner's client, every <see cref="CheckInterval"/> ticks until both are found: an Alchemy Table or a Cooking
		/// Pot within vanilla's crafting reach (decompiled 1.4.4 <c>Player.AdjTiles</c>: 4 tiles either side of the player's middle,
		/// 3 above its feet to 2 below; vanilla only runs it with the inventory open, so the scan is ours: 54 tiles, bounds
		/// checked, D0), or held in the inventory (the Cauldron is a Cooking Pot style).</summary>
		private void FindStations() {
			byte before = found;
			if (Player.alchemyTable) {
				found |= FoundAlchemy;
			}
			if (Player.adjTile.Length > TileID.CookingPots && Player.adjTile[TileID.CookingPots]) {
				found |= FoundCooking;
			}
			int cx = (int)((Player.position.X + Player.width / 2f) / 16f), feet = (int)((Player.position.Y + Player.height) / 16f);
			for (int x = cx - 4; x <= cx + 4; x++) {
				for (int y = feet - 3; y < feet + 3; y++) {
					if (!Core.Safety.TileSafety.TryGetTile(x, y, out Tile t) || !t.HasTile) {
						continue;
					}
					if (t.TileType == TileID.AlchemyTable) {
						found |= FoundAlchemy;
					}
					else if (t.TileType == TileID.CookingPots) {
						found |= FoundCooking;
					}
				}
			}
			for (int i = 0; i < 58 && i < Player.inventory.Length; i++) {
				int type = Player.inventory[i]?.type ?? 0;
				if (type == ItemID.AlchemyTable) {
					found |= FoundAlchemy;
				}
				else if (type == ItemID.CookingPot || type == ItemID.Cauldron) {
					found |= FoundCooking;
				}
			}
			if (found != before) {
				MarkDirty();
			}
		}

		/// <summary>A base ore tier collected (<see cref="ResearchNodes.TheBasics"/>), or a gem staff had (Bundle Up!).</summary>
		private void Collected(int type) {
			if ((found & FoundRobe) == 0 && ResearchRecipes.IsGemRobe(type)) {
				found |= FoundRobe;                                  // RGBT's reveal (2026-11-24)
				MarkDirty();
			}
			int tier = ResearchItems.BaseTier(type);
			if (tier >= 0) {
				oreTiers |= (byte)(1 << tier);
			}
			int[] staffs = Weapons.BundleOfWands.StaffItems;
			for (int k = 0; k < staffs.Length && k < 8; k++) {
				if (staffs[k] == type) {
					if ((gemStaffs & (1 << k)) == 0) {
						gemStaffs |= (byte)(1 << k);
						MarkDirty();
					}
					break;
				}
			}
		}

		/// <summary>Standing on (or just over) a floating island's clouds high in the sky, or in Coghaven (a floating island too).</summary>
		private bool OnCloudIsland() {
			if (Player.InModBiome<CoghavenBiome>()) {
				return true;
			}
			if (!Player.ZoneSkyHeight) {
				return false;
			}
			int x0 = (int)(Player.position.X / 16f) - 2, x1 = (int)((Player.position.X + Player.width) / 16f) + 2;
			int y0 = (int)(Player.Bottom.Y / 16f) - 1, y1 = y0 + 4;
			for (int y = y0; y <= y1; y++) {
				for (int x = x0; x <= x1; x++) {
					if (!Core.Safety.TileSafety.TryGetTile(x, y, out Tile t) || !t.HasTile) {
						continue;
					}
					ushort type = t.TileType;
					if (type == TileID.Cloud || type == TileID.RainCloud || type == TileID.SnowCloud) {
						return true;
					}
				}
			}
			return false;
		}

		/// <summary>Coins in the inventory and every bank (piggy bank, safe, forge, void vault), in copper.</summary>
		private long Savings() {
			long total = Utils.CoinsCount(out _, Player.inventory, noSlots);
			total += Utils.CoinsCount(out _, Player.bank.item, noSlots);
			total += Utils.CoinsCount(out _, Player.bank2.item, noSlots);
			total += Utils.CoinsCount(out _, Player.bank3.item, noSlots);
			total += Utils.CoinsCount(out _, Player.bank4.item, noSlots);
			return total;
		}

		/// <summary>A chest just opened: an ocean's Water Chest or a Reef Chest is the "coral chest" (my reading: vanilla 1.4.4 has
		/// no natural coral chest; the Reef Chest is its Coral furniture's chest, ItemID.CoralChest).</summary>
		private void CheckChest() {
			int c = Player.chest;
			if (c == lastChest) {
				return;
			}
			lastChest = c;
			if (c < 0 || c >= Main.maxChests || Main.chest[c] == null) {
				return;
			}
			Chest chest = Main.chest[c];
			if (!Core.Safety.TileSafety.TryGetTile(chest.x, chest.y, out Tile t) || !t.HasTile) {
				return;
			}
			int style = t.TileFrameX / 36;
			if ((t.TileType == TileID.Containers && style == KnowledgeTasks.WaterChestStyle)
				|| (t.TileType == TileID.Containers2 && style == KnowledgeTasks.ReefChestStyle)) {
				Grant(KnowledgeTasks.CoralChest);
			}
		}

		public override bool OnPickup(Item item) {
			if (Player.whoAmI == Main.myPlayer && item != null) {
				if (item.type == ItemID.FallenStar) {
					Grant(KnowledgeTasks.FallenStar);
				}
				Collected(item.type);
			}
			return true;
		}

		public override void PostBuyItem(NPC vendor, Item[] shopInventory, Item item) {
			if (Player.whoAmI == Main.myPlayer && vendor != null && vendor.type == NPCID.TravellingMerchant) {
				Grant(KnowledgeTasks.TravelingMerchant);
			}
		}

		// --- the book ---------------------------------------------------------------------------------------------------------

		public override IEnumerable<Item> AddStartingItems(bool mediumCoreDeath) {
			if (mediumCoreDeath) {
				return Array.Empty<Item>();
			}
			gotBook = true;
			return new[] { new Item(ModContent.ItemType<AncientResearchBook>()) };
		}

		public override void OnEnterWorld() {
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}
			missStacks = 0;
			reportedStaffs = false;                              // a new world: tell it too
			CheckReveals();                                      // keep whatever this world reveals at once
			if (gotBook) {
				return;
			}
			gotBook = true;                                      // a character made before the research update: one book, once
			Player.QuickSpawnItem(Player.GetSource_GiftOrReward(), ModContent.ItemType<AncientResearchBook>());
		}

		// --- saving and sync --------------------------------------------------------------------------------------------------

		public override void SaveData(TagCompound tag) {
			lock (sync) {
				tag["Knowledge"] = Knowledge;
				tag["Earned"] = new List<string>(earned);
				tag["Unlocked"] = new List<string>(unlocked);
				tag["Revealed"] = new List<string>(revealed);
				tag["OreTiers"] = oreTiers;
				tag["Edges"] = edges;
				tag["GemStaffs"] = gemStaffs;
				tag["Found"] = found;
				tag["GotBook"] = gotBook;
			}
		}

		public override void LoadData(TagCompound tag) {
			lock (sync) {
				Knowledge = Math.Max(0, tag.GetInt("Knowledge"));
				Fill(earned, tag, "Earned");
				Fill(unlocked, tag, "Unlocked");
				Fill(revealed, tag, "Revealed");
				oreTiers = tag.GetByte("OreTiers");
				edges = tag.GetByte("Edges");
				gemStaffs = tag.GetByte("GemStaffs");
				found = tag.GetByte("Found");
				gotBook = tag.GetBool("GotBook");
				for (int k = 0; k < Secrets.FundamentalStones.Count; k++) {
					if (earned.Contains(KnowledgeTasks.StoneKey(k))) {
						found |= FoundStone;                         // read a stone before the tab existed: it shows
					}
				}
			}
			RebuildBits();
		}

		private static void Fill(HashSet<string> set, TagCompound tag, string key) {
			set.Clear();
			if (!tag.ContainsKey(key)) {
				return;
			}
			foreach (string s in tag.GetList<string>(key)) {
				if (!string.IsNullOrEmpty(s) && set.Count < MaxSaved) {
					set.Add(s);
				}
			}
		}

		/// <summary>The unlocked nodes as bits (byte k holds nodes 8k..8k+7), from this side's copy (on the server and other
		/// clients the bits are all there is: the names live on the owner's client).</summary>
		public byte[] Mask() {
			byte[] mask = new byte[(unlockedBits.Length + 7) / 8];
			for (int k = 0; k < unlockedBits.Length; k++) {
				if (unlockedBits[k]) {
					mask[k >> 3] |= (byte)(1 << (k & 7));
				}
			}
			return mask;
		}

		/// <summary>Another side's copy of this player's unlocked nodes (from <see cref="ResearchSyncPacket"/>).</summary>
		public void ApplyMask(byte[] mask) {
			int n = ResearchNodes.All.Count;
			if (unlockedBits.Length != n) {
				unlockedBits = new bool[n];
			}
			for (int k = 0; k < n; k++) {
				unlockedBits[k] = (k >> 3) < mask.Length && (mask[k >> 3] & (1 << (k & 7))) != 0;
			}
		}

		public override void SyncPlayer(int toWho, int fromWho, bool newPlayer) {
			ModContent.GetInstance<ResearchSyncPacket>().Send(Player.whoAmI, Mask(), toWho, fromWho);
		}

		public override void CopyClientState(ModPlayer targetCopy) {
			ResearchPlayer copy = (ResearchPlayer)targetCopy;
			if (copy.unlockedBits.Length != unlockedBits.Length) {
				copy.unlockedBits = new bool[unlockedBits.Length];        // only when the node count changes (D1)
			}
			Array.Copy(unlockedBits, copy.unlockedBits, unlockedBits.Length);
		}

		public override void SendClientChanges(ModPlayer clientPlayer) {
			bool[] old = ((ResearchPlayer)clientPlayer).unlockedBits;
			if (old.Length != unlockedBits.Length) {
				SyncPlayer(-1, Main.myPlayer, false);
				return;
			}
			for (int k = 0; k < old.Length; k++) {
				if (old[k] != unlockedBits[k]) {
					SyncPlayer(-1, Main.myPlayer, false);
					return;
				}
			}
		}

		// --- the tooltips' progress lines -------------------------------------------------------------------------------------

		public static string OreTiersText(Player p) {
			ResearchPlayer r = p.GetModPlayer<ResearchPlayer>();
			return Language.GetTextValue("Mods.Cogpunk.Research.Conditions.OreTiers", Mark((r.oreTiers & 1) != 0), Mark((r.oreTiers & 2) != 0),
				Mark((r.oreTiers & 4) != 0), Mark((r.oreTiers & 8) != 0));
		}

		public static string EdgesText(Player p) {
			ResearchPlayer r = p.GetModPlayer<ResearchPlayer>();
			return Language.GetTextValue("Mods.Cogpunk.Research.Conditions.Edges", Mark((r.edges & 1) != 0), Mark((r.edges & 2) != 0));
		}

		private static string Mark(bool done) => Language.GetTextValue(done ? "Mods.Cogpunk.Research.Found" : "Mods.Cogpunk.Research.Missing");
	}
}
