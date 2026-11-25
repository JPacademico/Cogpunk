using System;
using Cogpunk.Content.Underground.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.Underground.NPCs.CrystalLizardRigData;

namespace Cogpunk.Content.Underground.NPCs
{
	/// <summary>
	/// The Crystal Lizard (user, 2026-11-25: "a new enemy that can spawn on the underground called "cristal lizard" its a small
	/// rare underground enemy that runs from the player when takes damage or comes close and if not killed in 5 seconds it dugs
	/// away and despawns. It should have good armor and drop from 1-5 gold coins and 1-3 of a random gem and a small chance to
	/// drop a accessory called "tearstone""): a slate lizard armoured in crystal, a lucky find.
	/// <list type="bullet">
	/// <item>Calm, it potters about. A player within <see cref="AlertRange"/>, or any hit, sets it running away from the nearest
	/// player (<see cref="FleeSpeed"/>, jumping walls; cornered for <see cref="CorneredTicks"/>, it doubles back past them).</item>
	/// <item><see cref="FleeTicks"/> (5 s, user-set) after it was startled it digs into the ground where it stands
	/// (<see cref="DigTicks"/>: nose down, sinking, dirt flying; it can still be hit for the first half) and is gone: no loot.</item>
	/// <item>Killed: 1-5 Gold Coins, 1-3 of one random gem (vanilla's seven and Jade), the <see cref="Tearstone"/> 1 time in
	/// <see cref="TearstoneOdds"/> (all user-set but the gem list and the Tearstone's odds, my calls).</item>
	/// <item>Harmless: no contact damage. Spawns underground (the dirt and cavern layers, not the Dungeon or the Temple), rarely
	/// (<see cref="SpawnWeight"/>), one at a time; the Lifeform Analyzer calls it out.</item>
	/// </list>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv): "good armor": the cavern's armoured Giant Shelly
	/// (terraria.wiki.gg 1.4.4 Expert pre-Hardmode: 100 life, 12 defense, 24 while spinning in its shell) for its kind; this one
	/// has a little more life and far more defense (<see cref="Defense"/>: a pre-Hardmode weapon's 20-30 damage is cut by 16), so
	/// it takes a few good hits in the 5 s it allows.</para>
	/// <para>D2: the server decides (startle, flight direction, the dig and the despawn, sent with SyncNPC); movement runs on every
	/// side from the synced state. D0: drops through vanilla's loot rules; the despawn is the server's; no per-tick allocation.</para>
	/// </summary>
	public class CrystalLizard : GridWalkerNPC
	{
		private enum Phase { Calm, Flee, Dig }

		public const int Life = 160, Defense = 32;
		public const float AlertRange = 14f * 16f;
		public const int FleeTicks = 5 * 60;                            // user-set: "if not killed in 5 seconds it dugs away"
		public const int DigTicks = 40, DigVulnerableTicks = 20;
		public const int CorneredTicks = 40;
		public const float FleeSpeed = 6.2f, FleeAccel = 0.35f, JumpSpeed = 6.5f, CalmSpeed = 0.5f, CalmAccel = 0.05f;
		public const float SpawnWeight = 0.012f;
		public const int TearstoneOdds = 10;                            // "a small chance" (my call: 10%; the lizard is rare)
		public const int GoldMin = 1, GoldMax = 5, GemMin = 1, GemMax = 3;

		private static Asset<Texture2D> far, glow;

		private Phase CurrentPhase => (Phase)State;
		private ref float FleeDir => ref NPC.ai[2];                     // the way it runs (-1, 1), set by the server
		private ref float Stuck => ref NPC.ai[3];                       // ticks without headway (every side, from the same motion)

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => null;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Caverns;

		/// <summary>The rig origin from the hitbox's middle (facing left: the body box isn't centred on it).</summary>
		public const int RigShift = -(R.BodyLeft + R.BodyRight) / 2;

		protected override Vector2 DrawAnchor => NPC.Bottom + new Vector2(NPC.spriteDirection == 1 ? -RigShift : RigShift, 0f);

		/// <summary>While digging away it sinks into the ground over <see cref="DigTicks"/> (the sprite cut at the ground line).</summary>
		protected override int Buried => CurrentPhase == Phase.Dig ? (int)(Math.Clamp(Timer / DigTicks, 0f, 1f) * R.CellHeight) & ~1 : 0;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			far = glow = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		public override void SetDefaults() {
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = R.BodyRight - R.BodyLeft;
			NPC.height = -R.BodyTop;
			SetExpertStats(Life, 0, Defense);
			NPC.damage = 0;                                              // harmless: it only runs
			NPC.knockBackResist = 0.3f;
			NPC.HitSound = SoundID.NPCHit5;                             // a crystal's chime
			NPC.DeathSound = SoundID.Item27;                            // shattering crystal
			NPC.value = 0f;                                             // its gold is a drop (1-5 Gold Coins)
			NPC.aiStyle = -1;
			NPC.rarity = 3;                                             // the Lifeform Analyzer calls it out
		}

		public override bool CanHitPlayer(Player target, ref int cooldownSlot) => false;

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player player = spawnInfo.Player;
			bool underground = player.ZoneDirtLayerHeight || player.ZoneRockLayerHeight;
			return underground && !player.ZoneDungeon && !player.ZoneLihzhardTemple && !spawnInfo.PlayerInTown && !spawnInfo.Water
				&& !NPC.AnyNPCs(Type) ? SpawnWeight : 0f;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ItemID.GoldCoin, 1, GoldMin, GoldMax));
			npcLoot.Add(new OneFromRulesRule(1,
				ItemDropRule.Common(ItemID.Amethyst, 1, GemMin, GemMax), ItemDropRule.Common(ItemID.Topaz, 1, GemMin, GemMax),
				ItemDropRule.Common(ItemID.Sapphire, 1, GemMin, GemMax), ItemDropRule.Common(ItemID.Emerald, 1, GemMin, GemMax),
				ItemDropRule.Common(ItemID.Ruby, 1, GemMin, GemMax), ItemDropRule.Common(ItemID.Diamond, 1, GemMin, GemMax),
				ItemDropRule.Common(ItemID.Amber, 1, GemMin, GemMax), ItemDropRule.Common(ModContent.ItemType<Gems.Items.Jade>(), 1, GemMin, GemMax)));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<Tearstone>(), TearstoneOdds));
		}

		protected override void UpdateState() {
			switch (CurrentPhase) {
				case Phase.Flee:
					Flee();
					break;
				case Phase.Dig:
					NPC.velocity.X *= 0.6f;
					NPC.dontTakeDamage = Timer >= DigVulnerableTicks;
					if (IsAuthority && Timer >= DigTicks) {
						NPC.active = false;                            // gone into the rock: no loot (it didn't die)
						if (Main.netMode == NetmodeID.Server) {
							NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
						}
					}
					break;
				default:
					Calm();
					break;
			}
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Calm: a slow potter that turns now and then; the server watches for a player coming close.</summary>
		private void Calm() {
			int dir = NPC.direction == 0 ? -1 : NPC.direction;
			Run(dir, CalmSpeed, CalmAccel, 4f);
			FaceMotion(dir);
			if (!IsAuthority) {
				return;
			}
			if ((int)Timer % 180 == 179) {
				NPC.direction = -dir;                                   // turns round now and then
				NPC.netUpdate = true;
			}
			if ((int)Timer % 10 == 0) {
				foreach (Player player in Main.ActivePlayers) {
					if (!player.dead && Vector2.DistanceSquared(player.Center, NPC.Center) <= AlertRange * AlertRange) {
						Startle();
						break;
					}
				}
			}
		}

		/// <summary>Server: it bolts, away from the nearest player.</summary>
		private void Startle() {
			if (!IsAuthority || CurrentPhase != Phase.Calm) {
				return;
			}
			int nearest = Player.FindClosest(NPC.position, NPC.width, NPC.height);
			float away = nearest >= 0 && nearest < Main.maxPlayers && Main.player[nearest].active
				? (NPC.Center.X >= Main.player[nearest].Center.X ? 1f : -1f) : -NPC.direction;
			FleeDir = away;
			Stuck = 0f;
			ChangeState((int)Phase.Flee);
		}

		private void Flee() {
			int dir = FleeDir >= 0f ? 1 : -1;
			Run(dir, FleeSpeed, FleeAccel, JumpSpeed);
			FaceMotion(dir);
			Stuck = Math.Abs(NPC.velocity.X) < 0.3f ? Stuck + 1f : 0f;
			if (!IsAuthority) {
				return;
			}
			if (Stuck >= CorneredTicks) {
				FleeDir = -dir;                                          // cornered: it doubles back past them
				Stuck = 0f;
				NPC.netUpdate = true;
			}
			else if ((int)Timer % 30 == 0) {
				int nearest = Player.FindClosest(NPC.position, NPC.width, NPC.height);
				if (nearest >= 0 && nearest < Main.maxPlayers && Main.player[nearest].active
					&& Vector2.DistanceSquared(Main.player[nearest].Center, NPC.Center) < 6f * 16f * 6f * 16f) {
					float away = NPC.Center.X >= Main.player[nearest].Center.X ? 1f : -1f;
					if (away != FleeDir) {
						FleeDir = away;                                  // a player got round it: away from them again
						NPC.netUpdate = true;
					}
				}
			}
			if (Timer >= FleeTicks && Grounded) {
				ChangeState((int)Phase.Dig);
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (NPC.life > 0) {
				Startle();                                               // any hit sets it running (the server's copy decides)
			}
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 4 : 18;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 2 == 0 ? DustID.BlueCrystalShard : DustID.GemDiamond, out Dust d)) {
					d.noGravity = i % 3 != 0;
					d.velocity *= NPC.life > 0 ? 1f : 1.8f;
				}
			}
		}

		private void Effects() {
			if (CurrentPhase == Phase.Flee && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Item25 with { Pitch = 0.6f, Volume = 0.5f }, NPC.Center);   // a startled chirp
			}
			if (CurrentPhase == Phase.Dig) {
				if (Timer == 1f) {
					SoundEngine.PlaySound(SoundID.Dig with { Pitch = 0.2f }, NPC.Bottom);
				}
				if ((int)Timer % 4 == 0 && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(0f, 6f), NPC.width, 6, DustID.Dirt, out Dust dirt)) {
					dirt.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), Main.rand.NextFloat(-3f, -1f));
				}
			}
			if (Main.rand.NextBool(30) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(NPC.position, NPC.width, 8, DustID.GemDiamond, out Dust sparkle)) {
				sparkle.noGravity = true;                               // its crystals glint
				sparkle.velocity = Vector2.Zero;
				sparkle.scale = 0.6f;
			}
			Lighting.AddLight(NPC.Top + new Vector2(0f, 6f), 0.06f, 0.20f, 0.26f);
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Dig:
					return R.Dig + Math.Clamp((int)(Timer * R.DigFrames / DigTicks), 0, R.DigFrames - 1);
				case Phase.Flee:
					if (Timer < 8f) {
						return R.Alert;                                  // the moment it notices you
					}
					if (!Grounded) {
						return R.Run + 1;
					}
					NPC.frameCounter += Math.Abs(NPC.velocity.X);
					if (NPC.frameCounter >= R.RunStep * R.RunFrames) {
						NPC.frameCounter -= R.RunStep * R.RunFrames;
					}
					return R.Run + (int)(NPC.frameCounter / Math.Max(1, R.RunStep)) % R.RunFrames;
			}
			if (Math.Abs(NPC.velocity.X) > 0.2f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= R.RunStep * R.RunFrames) {
					NPC.frameCounter -= R.RunStep * R.RunFrames;
				}
				return R.Run + (int)(NPC.frameCounter / Math.Max(1, R.RunStep)) % R.RunFrames;
			}
			return R.Idle + (int)(Timer / 30f) % R.IdleFrames;
		}
	}
}
