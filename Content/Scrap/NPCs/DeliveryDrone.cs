using System;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.GameContent.Bestiary;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Scrap.NPCs
{
	/// <summary>
	/// Delivery Drone (Drone de Entregas), a rare thief (user-set 2026-11-10b: "a new rare enemy that can spawn anywhere when
	/// there are dropped items or coins on the ground for more than 20 seconds called Amazonian drone [renamed Delivery Drone, 2026-11-11], a scrappy thief drone
	/// that steals dropped items and then flies away. It should take 3 seconds to scan an item and after scanning it steals
	/// and flies out of the screen; once it is out of view for any player it despawns. Make it low health so it's more of a
	/// fun enemy than a strong one"). <see cref="DeliveryDroneSystem"/> sends one for an item that has lain on the ground
	/// <see cref="DeliveryDroneSystem.LyingTicks"/> near a player. 2026-11-11 (user): renamed from the Amazonian Drone, "it should now scan for seconds before stealing" (the number was missing: my call, <see cref="ScanTicks"/> = 5 s, was 3), 30 life (was 40).
	/// <list type="number">
	/// <item>Approach: it flies in from off screen to hover <see cref="HoverHeight"/> over its item.</item>
	/// <item>Scan: <see cref="ScanTicks"/> (5 s) over it, a red beam sweeping the item, the lights on its back counting
	/// the seconds (<see cref="Scans"/>).</item>
	/// <item>Flee: it snatches the item (gone from the world) and flies up and away from the players until no player can
	/// see it (<see cref="OutOfView"/>), then it is gone, the item with it.</item>
	/// </list>
	/// An item taken first (a player picks it up) sends it to another lying item within <see cref="RetargetRange"/>, else
	/// it leaves empty-handed. Hit before it has the item, it panics: it snatches the item if it is hovering over it and
	/// flees (my call). Shot down, it drops what it stole, untouched (stack, prefix and modded data), and a few Rusted Cogs.
	/// <para>Stats (Expert): <see cref="Life"/> life, <see cref="Defense"/> defense, no contact damage (a nuisance, not a
	/// threat). D2: the server decides everything (which item, the steal, the flight, the despawn); ai[0] phase, ai[1]
	/// timer, ai[2] the item's index + 1 (clients draw the beam at it), ai[3] the stolen item's type (clients draw it in the
	/// claw); the stolen item itself lives on the server only. D0: the item index is range-checked every use; the stolen item
	/// is dropped through <see cref="SafeSpawn"/>; every phase has a time limit (<see cref="MaxApproachTicks"/>,
	/// <see cref="MaxFleeTicks"/>), and a drone at the world's edge leaves. D1: one pass over the items only when it needs a
	/// new one; no allocation per tick (the stolen item is cloned once, at the steal). Art: art/scrap/make_delivery_drone_art.py.</para>
	/// </summary>
	public class DeliveryDrone : CogpunkNPC
	{
		private enum Phase { Approach, Scan, Flee }

		public const int Life = 30, Defense = 2;                       // Expert: user-set 2026-11-11 (40 before)
		public const int ScanTicks = 300;                              // my call 2026-11-11 ("scan for seconds": the number was missing; 3 s before)
		public const float HoverHeight = 52f;                          // its centre over the item's
		public const float ApproachSpeed = 5f, ApproachTurn = 0.08f;
		public const float FleeSpeed = 10f, FleeTurn = 0.06f;
		public const float RetargetRange = 20f * 16f;
		public const float SnatchRange = 90f;                          // hit while this close to its item: it snatches it
		public const int MaxApproachTicks = 900;                       // 15 s to reach the item, or it gives up
		public const int MaxFleeTicks = 900;                           // 15 s of flight, then it is gone wherever it is
		/// <summary>Out of every player's view: vanilla never shows more than <c>Main.maxScreenW</c> x <c>maxScreenH</c>
		/// (1920 x 1200) world px round a player, plus a margin.</summary>
		public const float ViewHalfWidth = 1920f * 0.5f + 160f, ViewHalfHeight = 1200f * 0.5f + 160f;
		public const int CogMin = 1, CogMax = 3;
		public const int Frames = 6, RotorFrames = 3, FrameTicks = 2;
		public const int FrameW = 64, FrameH = 44, Gap = 2;
		public const int EyeX = 15, EyeY = 31, ClawX = 32, ClawY = 42;    // game px in a left-facing frame
		private const int Scans = ScanTicks / 60;                      // the lights on its back: one a second

		private static Asset<Texture2D> glow;
		private static readonly string[] GoreNames = { "DeliveryDrone_GoreRotor", "DeliveryDrone_GoreRotor", "DeliveryDrone_GoreBox" };
		private static readonly SoundStyle GrabSound = SoundID.Grab with { Pitch = -0.2f, Volume = 0.9f };
		private static readonly SoundStyle BlipSound = SoundID.MenuTick with { Volume = 0.6f };

		private Phase CurrentPhase {
			get => (Phase)(int)NPC.ai[0];
			set => NPC.ai[0] = (int)value;
		}

		private ref float Timer => ref NPC.ai[1];

		/// <summary>The item it is after, or -1 (ai[2] holds index + 1, synced).</summary>
		private int ItemIndex {
			get => (int)NPC.ai[2] - 1;
			set => NPC.ai[2] = value + 1;
		}

		/// <summary>The stolen item's type, or 0 (synced: clients draw it in the claw).</summary>
		private int StolenType => (int)NPC.ai[3];

		/// <summary>Server: what it stole, whole.</summary>
		private Item stolen;
		private int seenStolen;                                        // clients: the type last seen in ai[3] (the grab's sound)

		private static bool IsAuthority => Main.netMode != NetmodeID.MultiplayerClient;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = Frames;
			NPCID.Sets.CantTakeLunchMoney[Type] = true;               // it steals its own way
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			NPC.width = 44;
			NPC.height = 30;
			SetExpertStats(Life, 0, Defense);
			NPC.damage = 0;
			NPC.knockBackResist = 0.6f;
			NPC.noGravity = true;
			NPC.noTileCollide = true;                                 // it must reach the item and leave, whatever is in the way
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Item.buyPrice(silver: 2);
			NPC.aiStyle = -1;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Surface,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) => 0f;     // only DeliveryDroneSystem sends one

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedCog>(), 1, CogMin, CogMax));
		}

		// ------------------------------------------------------------------------------------------------------------
		// The item
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>The item it is after, if it still lies there to be had (<see cref="DeliveryDroneSystem.CanSteal"/>).</summary>
		private Item TargetItem {
			get {
				int i = ItemIndex;
				if (i < 0 || i >= Main.maxItems) {
					return null;
				}
				Item item = Main.item[i];
				return DeliveryDroneSystem.CanSteal(item, 0) ? item : null;
			}
		}

		/// <summary>Server: takes the item out of the world and keeps it.</summary>
		private void Steal(Item item) {
			int index = ItemIndex;
			if (item == null || index < 0 || index >= Main.maxItems || StolenType > 0) {
				return;
			}
			stolen = item.Clone();
			NPC.ai[3] = item.type;
			item.TurnToAir();
			item.active = false;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncItem, -1, -1, null, index);   // as vanilla's thieves do (Item.GetPickedUpByMonsters_Money)
			}
			ItemIndex = -1;
			NPC.netUpdate = true;
		}

		/// <summary>Server: the next lying item within <see cref="RetargetRange"/>, or -1.</summary>
		private int FindNear() {
			int best = -1;
			float bestDistance = RetargetRange * RetargetRange;
			for (int i = 0; i < Main.maxItems; i++) {
				Item item = Main.item[i];
				if (!DeliveryDroneSystem.CanSteal(item, DeliveryDroneSystem.LyingTicks)) {
					continue;
				}
				float d = Vector2.DistanceSquared(item.Center, NPC.Center);
				if (d < bestDistance) {
					bestDistance = d;
					best = i;
				}
			}
			return best;
		}

		private void ChangePhase(Phase next) {
			CurrentPhase = next;
			Timer = 0f;
			NPC.netUpdate = true;
		}

		/// <summary>Out of every player's view (vanilla's biggest view round each player, plus a margin).</summary>
		private bool OutOfView() {
			foreach (Player player in Main.ActivePlayers) {
				if (player.dead) {
					continue;
				}
				Vector2 d = NPC.Center - player.Center;
				if (Math.Abs(d.X) < ViewHalfWidth && Math.Abs(d.Y) < ViewHalfHeight) {
					return false;
				}
			}
			return true;
		}

		/// <summary>Server: gone, quietly (no loot, no death), as vanilla despawns (decompiled <c>NPC.CheckActive</c>).</summary>
		private void Leave() {
			NPC.active = false;
			if (Main.netMode == NetmodeID.Server) {
				NPC.netSkip = -1;
				NPC.life = 0;
				NetMessage.SendData(MessageID.SyncNPC, -1, -1, null, NPC.whoAmI);
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// AI
		// ------------------------------------------------------------------------------------------------------------

		public override void AI() {
			Timer++;
			Item item = CurrentPhase == Phase.Flee ? null : TargetItem;
			if (IsAuthority && CurrentPhase != Phase.Flee && item == null) {
				int next = FindNear();                                // taken first: another lying item near, or away
				if (next >= 0) {
					ItemIndex = next;
					ChangePhase(Phase.Approach);
					item = TargetItem;
				}
				else {
					ItemIndex = -1;
					ChangePhase(Phase.Flee);
				}
			}
			switch (CurrentPhase) {
				case Phase.Approach:
					if (item != null) {
						Vector2 to = item.Center - new Vector2(0f, HoverHeight) - NPC.Center;
						float speed = Math.Min(ApproachSpeed, to.Length() * 0.12f);
						NPC.velocity = Vector2.Lerp(NPC.velocity, to.SafeNormalize(Vector2.Zero) * speed, ApproachTurn);
						FaceTowards(item.Center.X - NPC.Center.X);
						if (IsAuthority && to.LengthSquared() < 10f * 10f) {
							ChangePhase(Phase.Scan);
						}
					}
					if (IsAuthority && Timer > MaxApproachTicks) {
						ChangePhase(Phase.Flee);                    // couldn't get there
					}
					break;
				case Phase.Scan:
					if (item != null) {
						float bob = MathF.Sin(Timer * 0.08f) * 3f;
						Vector2 to = item.Center - new Vector2(0f, HoverHeight + bob) - NPC.Center;
						NPC.velocity = Vector2.Lerp(NPC.velocity, to * 0.2f, 0.2f);
						FaceTowards(item.Center.X - NPC.Center.X);
						if (!Main.dedServ && Timer % 60f == 1f) {
							SoundEngine.PlaySound(BlipSound with { Pitch = -0.2f + 0.3f * (Timer / 60f) }, NPC.Center);
						}
						if (IsAuthority && Timer >= ScanTicks) {
							Steal(item);
							ChangePhase(Phase.Flee);
						}
					}
					break;
				default:
					Flee();
					break;
			}
			MathSafety.Sanitize(ref NPC.velocity);
			if (StolenType != seenStolen) {                           // every side: the snatch
				if (StolenType > 0 && !Main.dedServ) {
					SoundEngine.PlaySound(GrabSound, NPC.Center);
				}
				seenStolen = StolenType;
			}
			if (!Main.dedServ) {
				Lighting.AddLight(NPC.Center, 0.25f, 0.05f, 0.04f);
			}
		}

		private void FaceTowards(float dx) {
			if (Math.Abs(dx) > 4f) {
				NPC.direction = NPC.spriteDirection = dx > 0f ? 1 : -1;
			}
		}

		/// <summary>Up and away from the closest player; gone once no player can see it (or after
		/// <see cref="MaxFleeTicks"/>, or at the world's edge).</summary>
		private void Flee() {
			Player near = null;
			float best = float.MaxValue;
			foreach (Player player in Main.ActivePlayers) {
				float d = Vector2.DistanceSquared(player.Center, NPC.Center);
				if (!player.dead && d < best) {
					best = d;
					near = player;
				}
			}
			int away = near == null ? (NPC.direction == 0 ? 1 : NPC.direction) : (NPC.Center.X >= near.Center.X ? 1 : -1);
			Vector2 want = new(away * FleeSpeed * 0.8f, -FleeSpeed * 0.6f);
			NPC.velocity = Vector2.Lerp(NPC.velocity, want, FleeTurn);
			NPC.direction = NPC.spriteDirection = away;
			if (!IsAuthority) {
				return;
			}
			bool edge = !TileSafety.InWorld((int)(NPC.Center.X / 16f), (int)(NPC.Center.Y / 16f), 45);
			if (OutOfView() || Timer > MaxFleeTicks || edge) {
				Leave();
			}
		}

		/// <summary>Every side runs the strike; the server reacts: a drone hovering over its item snatches it and flees, any
		/// other flees.</summary>
		public override void HitEffect(NPC.HitInfo hit) {
			if (IsAuthority && NPC.life > 0 && CurrentPhase != Phase.Flee) {
				Item item = TargetItem;
				if (item != null && Vector2.Distance(item.Center, NPC.Center) < SnatchRange) {
					Steal(item);
				}
				ChangePhase(Phase.Flee);
			}
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 14;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.Torch : DustID.Iron, out _);
			}
			if (NPC.life > 0) {
				return;
			}
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center, NPC.velocity * 0.3f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
				}
			}
		}

		/// <summary>Server: what it stole falls back out, whole.</summary>
		public override void OnKill() {
			if (stolen != null && !stolen.IsAir) {
				SafeSpawn.TryNewItem(NPC.GetSource_Loot(), NPC.Hitbox, stolen, out _);
			}
			stolen = null;
		}

		// ------------------------------------------------------------------------------------------------------------
		// Looks
		// ------------------------------------------------------------------------------------------------------------

		public override void FindFrame(int frameHeight) {
			int rotor = (int)(Main.GameUpdateCount / FrameTicks % RotorFrames);
			NPC.frame.Y = ((StolenType > 0 ? RotorFrames : 0) + rotor) * frameHeight;
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			Texture2D texture = TextureAssets.Npc[Type].Value;
			int frame = Math.Clamp(NPC.frame.Y / Math.Max(1, NPC.frame.Height), 0, Frames - 1);
			Rectangle source = new(0, frame * (FrameH + Gap), FrameW, FrameH);
			if (source.Bottom > texture.Height) {
				return false;                                     // the fallback texture: draw nothing rather than garbage
			}
			bool flip = NPC.spriteDirection == 1;                 // the art faces left
			Vector2 topLeft = (NPC.Center - screenPos - new Vector2(FrameW * 0.5f, FrameH * 0.5f) + new Vector2(0f, NPC.gfxOffY)).Floor();
			SpriteEffects fx = flip ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			if (!NPC.IsABestiaryIconDummy) {
				DrawScan(spriteBatch, topLeft, flip, screenPos);
			}
			spriteBatch.Draw(texture, topLeft, source, NPC.GetAlpha(drawColor), 0f, Vector2.Zero, 1f, fx, 0f);
			if (glow?.IsLoaded == true) {
				spriteBatch.Draw(glow.Value, topLeft, source, Color.White * NPC.Opacity, 0f, Vector2.Zero, 1f, fx, 0f);
			}
			int type = StolenType;
			if (type > 0 && type < TextureAssets.Item.Length) {      // the loot hangs in its claw
				Main.instance.LoadItem(type);
				Texture2D icon = TextureAssets.Item[type].Value;
				Rectangle itemFrame = Main.itemAnimations[type] != null ? Main.itemAnimations[type].GetFrame(icon) : icon.Frame();
				float scale = Math.Min(1f, 28f / Math.Max(itemFrame.Width, itemFrame.Height));
				Vector2 claw = topLeft + new Vector2(flip ? FrameW - ClawX : ClawX, ClawY);
				spriteBatch.Draw(icon, claw.Floor(), itemFrame, NPC.GetAlpha(drawColor), 0f, new Vector2(itemFrame.Width * 0.5f, 2f), scale,
					SpriteEffects.None, 0f);
			}
			return false;
		}

		/// <summary>The scan: a red cone from its eye over the item, a bright line sweeping it, and on its back the seconds
		/// counted (a light a second). Drawn added onto what is behind (alpha 0), with the vanilla 1 px texture.</summary>
		private void DrawScan(SpriteBatch spriteBatch, Vector2 topLeft, bool flip, Vector2 screenPos) {
			if (CurrentPhase != Phase.Scan) {
				return;
			}
			int i = ItemIndex;
			if (i < 0 || i >= Main.maxItems || !Main.item[i].active) {
				return;
			}
			Item item = Main.item[i];
			Texture2D pixel = TextureAssets.MagicPixel.Value;
			Rectangle one = new(0, 0, 1, 1);
			Vector2 eye = topLeft + new Vector2(flip ? FrameW - EyeX : EyeX, EyeY);
			Rectangle box = item.Hitbox;
			float top = box.Top - screenPos.Y, bottom = box.Bottom - screenPos.Y;
			float left = box.Left - screenPos.X - 4f, right = box.Right - screenPos.X + 4f;
			Color beam = new Color(206, 74, 56, 0);
			int rows = Math.Clamp((int)((bottom - eye.Y) / 2f), 1, 120);
			for (int r = 0; r < rows; r++) {                           // the cone: 2 px rows from the eye to the item's foot
				float y = eye.Y + r * 2f;
				float t = r / (float)rows;
				float l = MathHelper.Lerp(eye.X - 1f, left, t), w = MathHelper.Lerp(2f, right - left, t);
				spriteBatch.Draw(pixel, new Vector2(MathF.Floor(l), MathF.Floor(y)), one, beam * (0.12f + 0.12f * t), 0f, Vector2.Zero,
					new Vector2(MathF.Max(2f, MathF.Floor(w)), 2f), SpriteEffects.None, 0f);
			}
			float sweep = top + (bottom - top) * (0.5f + 0.5f * MathF.Sin(Timer * 0.15f));   // the scan line over the item
			spriteBatch.Draw(pixel, new Vector2(MathF.Floor(left), MathF.Floor(sweep)), one, new Color(255, 150, 120, 0) * 0.8f, 0f, Vector2.Zero,
				new Vector2(MathF.Floor(right - left), 2f), SpriteEffects.None, 0f);
			int lit = Math.Clamp((int)(Timer / 60f) + 1, 1, Scans);
			for (int k = 0; k < Scans; k++) {                          // the seconds: three lights on its back
				Vector2 at = topLeft + new Vector2((flip ? FrameW - 22 - k * 5 : 22 + k * 5) - 2, 10);
				Color c = k < lit ? new Color(236, 122, 88) : new Color(84, 20, 28);
				spriteBatch.Draw(pixel, at, one, c, 0f, Vector2.Zero, new Vector2(4f, 4f), SpriteEffects.None, 0f);
			}
		}
	}
}
