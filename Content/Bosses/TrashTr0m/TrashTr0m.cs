using System;
using System.Collections.Generic;
using Cogpunk.Content.Junkyard;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
using Cogpunk.Core.Templates;
using Cogpunk.Core.UI;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.Chat;
using Terraria.GameContent;
using Terraria.GameContent.Bestiary;
using Terraria.Graphics.CameraModifiers;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.TrashTr0m
{
	/// <summary>
	/// Trash-Tr0m, the Junkyard's guardian: the torn-off upper half of a giant construction robot (head, shoulders, torso
	/// and arms, a grinder for a mouth, nothing below the ragged waist) welded back together from scrap. It sleeps in the
	/// central heap and climbs out when someone tries to open the Junkyard Cache (<see cref="TrashTr0mSummon"/>); the
	/// cache stays sealed until it dies (<see cref="TrashTr0mSystem.Downed"/>).
	/// <para><b>This update:</b> the summon, the emergence intro and a placeholder fight (it stays planted in the heap,
	/// turns to face its target and deals contact damage). Attacks, final stats and drops come in a later update; the
	/// placeholder stats copy the Eye of Cthulhu (docs/balance/bosses.csv).</para>
	/// <para><b>Emergence</b> (<see cref="Phase.Emerge"/>, <see cref="EmergeTicks"/> = 4 s): the heap rumbles
	/// (<see cref="RumbleTicks"/>), the boss heaves itself up out of the ground (<see cref="RiseTicks"/>, the sprite is
	/// drawn clipped at the ground line, so nothing moves through tiles), its name card appears once the head is out
	/// (<see cref="TitleTick"/>) and it roars with its grinder spinning (<see cref="RoarTicks"/>). Every client within
	/// <see cref="CameraLockRange"/> has its camera locked on it for the whole intro (<see cref="TrashTr0mSystem"/>).
	/// It can't hurt or be hurt until the intro ends (D3 fairness).</para>
	/// <para>D2: <see cref="StateMachineNPC"/> keeps state and timer in the synced <c>ai[0]</c>/<c>ai[1]</c> and only the
	/// server changes state; the intro, camera, card, dust and sounds are all derived from them on each client, so a
	/// player joining mid-intro sees the rest of it. <c>localAI[0]</c> and <c>localAI[1]</c> (not synced) only remember
	/// that this client already showed the card and which intro tick it last played effects for. D0: the boss is spawned through <c>SafeSpawn</c> (critical) by the server; visuals use
	/// <c>SafeSpawn</c> dust and bounds-checked tiles; nothing here loops without a fixed cap.</para>
	/// </summary>
	[AutoloadBossHead]
	public class TrashTr0m : StateMachineNPC
	{
		public enum Phase
		{
			Emerge,
			Idle,          // placeholder until the attack patterns exist
			Retreat,
		}

		// --- sprite sheet (art/bosses/trashtr0m/make_trashtr0m_art.py): vertical frames, 2 px padding -----------------
		public const int FrameCount = 6;
		public const int FrameWidth = 216;
		public const int FrameHeight = 168;
		public const int FrameStride = FrameHeight + 2;
		public const int TicksPerFrame = 6;            // grinder spin, idle (10 frames/s)
		public const int RoarTicksPerFrame = 3;        // grinder spin, roaring

		// Emitters on the sprite, in frame pixels of the left-facing sheet.
		private static readonly Vector2 ExhaustA = new(164, 8);
		private static readonly Vector2 ExhaustB = new(180, 16);
		private static readonly Vector2 Mouth = new(93, 92);
		private const int WaistLeft = 66, WaistRight = 154, WaistY = 150;

		// --- intro -------------------------------------------------------------------------------------------------
		public const int RumbleTicks = 45;
		public const int RiseTicks = 135;
		public const int RoarTicks = 60;
		public const int EmergeTicks = RumbleTicks + RiseTicks + RoarTicks;   // 240 ticks = 4 s
		public const int TitleTick = RumbleTicks + 90;                        // head and shoulders are out
		public const int TitleHoldTicks = EmergeTicks - TitleTick + 45;
		public const int CameraEaseTicks = 30;
		public const float CameraLockRange = 150f * 16f;
		public const int RetreatTicks = 90;
		public const float DespawnRange = 300f * 16f;

		// --- placeholder stats (= Eye of Cthulhu, terraria.wiki.gg 1.4.4; balance pass in the attacks update) --------
		public const int BaseLife = 2800;
		public const int BaseDefense = 12;
		public const int BaseContactDamage = 15;

		private static Asset<Texture2D> glow;
		private static LocalizedText epithet;

		private Phase CurrentPhase => (Phase)State;

		public bool IsEmerging => CurrentPhase == Phase.Emerge;

		private bool IsRoaring => IsEmerging && Timer >= RumbleTicks + RiseTicks;

		private ref float TitleShown => ref NPC.localAI[0];

		// Highest intro tick this client has played effects for: a timer resync from the server can step Timer back a
		// tick or two, and one-shot sounds must not play twice.
		private ref float LastEffectTick => ref NPC.localAI[1];

		private static readonly Color UnsealedColor = new(223, 185, 78);   // Brass 4, the cache's glow

		/// <summary>Where the camera looks during the intro: the middle of the fully risen boss.</summary>
		public Vector2 CameraFocus => NPC.Bottom - new Vector2(0f, FrameHeight * 0.55f);

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = FrameCount;
			NPCID.Sets.MPAllowedEnemies[Type] = true;
			NPCID.Sets.BossBestiaryPriority.Add(Type);
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() {
				Scale = 0.5f,
				PortraitScale = 0.7f,
				Position = new Vector2(0f, 12f),
				PortraitPositionYOverride = 8f,
			});
			CogpunkSets.Mechanical[Type] = true;
			epithet = this.GetLocalization("Epithet");

			const string glowPath = "Cogpunk/Content/Bosses/TrashTr0m/TrashTr0m_Glow";
			if (!Main.dedServ && ModContent.HasAsset(glowPath)) {
				glow = ModContent.Request<Texture2D>(glowPath);
			}
		}

		public override void Unload() {
			glow = null;
			epithet = null;
		}

		public override void SetDefaults() {
			NPC.width = 132;
			NPC.height = 150;
			NPC.lifeMax = BaseLife;
			NPC.defense = BaseDefense;
			NPC.damage = BaseContactDamage;
			NPC.knockBackResist = 0f;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.boss = true;
			NPC.npcSlots = 10f;
			NPC.aiStyle = -1;
			NPC.value = Item.buyPrice(gold: 3);
			NPC.SpawnWithHigherTime(30);
			if (!Main.dedServ) {
				Music = MusicID.Boss1;
			}
		}

		// Same curve as the Eye of Cthulhu (decompiled NPC.ScaleStats_ApplyMultiplayerStats, type 4): Expert 3640, Master 4641.
		public override void ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment) {
			NPC.lifeMax = (int)(NPC.lifeMax * 0.65f * balance * bossAdjustment);
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				ModContent.GetInstance<JunkyardBiome>().ModBiomeBestiaryInfoElement,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		public override bool CanHitPlayer(Player target, ref int cooldownSlot) {
			cooldownSlot = ImmunityCooldownID.Bosses;
			return CurrentPhase == Phase.Idle;
		}

		// ------------------------------------------------------------------------------------------------------------
		// State machine (every side; only the server changes state)
		// ------------------------------------------------------------------------------------------------------------

		protected override void UpdateState() {
			NPC.velocity = Vector2.Zero;
			NPC.dontTakeDamage = CurrentPhase != Phase.Idle;
			switch (CurrentPhase) {
				case Phase.Emerge:
					DoEmerge();
					break;
				case Phase.Idle:
					DoIdle();
					break;
				case Phase.Retreat:
					DoRetreat();
					break;
				default:
					ChangeState((int)Phase.Idle);       // an unknown state from a newer version: recover (D0)
					break;
			}
		}

		private void DoEmerge() {
			if (!Main.dedServ) {
				TrashTr0mSystem.TrackIntro(NPC.whoAmI);
				EmergeEffects();
			}
			FaceTarget();
			if (Timer >= EmergeTicks && RetargetOrRetreat()) {
				ChangeState((int)Phase.Idle);            // (RetargetOrRetreat already switched to Retreat if nobody is left)
			}
		}

		private void DoIdle() {
			if (!RetargetOrRetreat()) {
				return;
			}
			FaceTarget();
			if (!Main.dedServ) {
				AmbientEffects();
			}
		}

		private void DoRetreat() {
			if (!Main.dedServ && Timer % 3 == 0) {
				GroundDebris(2);
			}
			if (Timer >= RetreatTicks && IsAuthority) {
				NPC.active = false;
				if (Main.netMode == NetmodeID.Server) {
					NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
				}
			}
		}

		/// <summary>Server: keeps a living target within <see cref="DespawnRange"/>, or burrows back into the heap. True while fighting.</summary>
		private bool RetargetOrRetreat() {
			if (!IsAuthority) {
				return true;
			}
			if (!HasTargetInRange()) {
				int old = NPC.target;
				NPC.TargetClosest(false);
				if (NPC.target != old) {
					NPC.netUpdate = true;
				}
			}
			if (!HasTargetInRange()) {
				ChangeState((int)Phase.Retreat);
				return false;
			}
			return true;
		}

		private bool HasTargetInRange() {
			return NPC.HasValidTarget && Vector2.DistanceSquared(Main.player[NPC.target].Center, NPC.Center) < DespawnRange * DespawnRange;
		}

		private void FaceTarget() {
			if (NPC.target < 0 || NPC.target >= Main.maxPlayers || !Main.player[NPC.target].active) {
				return;
			}
			NPC.direction = NPC.spriteDirection = Main.player[NPC.target].Center.X >= NPC.Center.X ? 1 : -1;
		}

		public override void OnKill() {
			NPC.SetEventFlagCleared(ref TrashTr0mSystem.DownedFlag, -1);   // vanilla sends WorldData after a boss kill
			if (Main.netMode == NetmodeID.Server) {
				ChatHelper.BroadcastChatMessage(NetworkText.FromKey(this.GetLocalizationKey("CacheUnsealed")), UnsealedColor);
			}
			else if (Main.netMode == NetmodeID.SinglePlayer) {
				Main.NewText(this.GetLocalization("CacheUnsealed").Value, UnsealedColor);
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Intro timing, shared by the camera and the drawing
		// ------------------------------------------------------------------------------------------------------------

		/// <summary>0..1: how firmly <paramref name="viewer"/>'s camera is locked on the boss right now.</summary>
		public float CameraLock(Player viewer) {
			if (!IsEmerging || viewer == null || !viewer.active
				|| Vector2.DistanceSquared(viewer.Center, CameraFocus) > CameraLockRange * CameraLockRange) {
				return 0f;
			}
			float t = Timer;
			float easeIn = t / CameraEaseTicks;
			float easeOut = (EmergeTicks - t) / CameraEaseTicks;
			return MathHelper.Clamp(Math.Min(easeIn, easeOut), 0f, 1f);
		}

		/// <summary>How many pixels of the sprite are still below the ground line (even, so the 2x art stays on its grid).</summary>
		private int BuriedPixels() {
			float buried;
			switch (CurrentPhase) {
				case Phase.Emerge:
					if (Timer < RumbleTicks) {
						return FrameHeight;
					}
					float p = MathHelper.Clamp((Timer - RumbleTicks) / RiseTicks, 0f, 1f);
					float eased = 1f - (1f - p) * (1f - p);
					eased += 0.035f * MathF.Sin(p * MathHelper.TwoPi * 3f) * (1f - p);   // three heaves, settling
					buried = (1f - MathHelper.Clamp(eased, 0f, 1f)) * FrameHeight;
					break;
				case Phase.Retreat:
					float q = MathHelper.Clamp(Timer / RetreatTicks, 0f, 1f);
					buried = q * q * FrameHeight;
					break;
				default:
					return 0;
			}
			return Math.Clamp((int)(buried * 0.5f) * 2, 0, FrameHeight);
		}

		/// <summary>A point on the sprite (frame pixels of the left-facing sheet) in world space, following the facing.</summary>
		private Vector2 SpritePoint(Vector2 framePixel) {
			float dx = framePixel.X - FrameWidth * 0.5f;
			if (NPC.spriteDirection == 1) {
				dx = -dx;
			}
			return NPC.Bottom + new Vector2(dx, framePixel.Y - FrameHeight + BuriedPixels());
		}

		// ------------------------------------------------------------------------------------------------------------
		// Client visuals
		// ------------------------------------------------------------------------------------------------------------

		private void EmergeEffects() {
			int t = (int)Timer;
			if (t <= LastEffectTick) {
				return;
			}
			LastEffectTick = t;
			bool shake = CogpunkClientConfig.Instance?.ScreenShake ?? true;
			if (t == 1) {
				SoundEngine.PlaySound(SoundID.DeerclopsRubbleAttack with { Pitch = -0.5f }, NPC.Bottom);
				if (shake) {
					Main.instance.CameraModifiers.Add(new PunchCameraModifier(NPC.Bottom, Vector2.UnitY, 3f, 12f, RumbleTicks + RiseTicks, 2400f, "Cogpunk:TrashTr0mRumble"));
				}
			}
			if (t < RumbleTicks + RiseTicks && t % 2 == 0) {
				GroundDebris(t < RumbleTicks ? 1 : 3);
			}
			if (t == RumbleTicks || t == RumbleTicks + 45 || t == RumbleTicks + 90) {
				SoundEngine.PlaySound(SoundID.Item14 with { Pitch = -0.6f, Volume = 0.8f }, NPC.Bottom);   // a heave breaks the crust
			}
			if (t >= RumbleTicks && t < RumbleTicks + RiseTicks && t % 6 == 0) {
				WaistSparks(2);
			}
			if (TitleShown == 0f && t >= TitleTick && Main.LocalPlayer != null
				&& Vector2.DistanceSquared(Main.LocalPlayer.Center, CameraFocus) <= CameraLockRange * CameraLockRange) {
				TitleShown = 1f;
				BossTitleSystem.Show(DisplayName, epithet, TitleHoldTicks);
			}
			if (t == RumbleTicks + RiseTicks) {
				SoundEngine.PlaySound(SoundID.Roar with { Pitch = -0.45f }, NPC.Center);
				if (shake) {
					Main.instance.CameraModifiers.Add(new PunchCameraModifier(NPC.Center, Vector2.UnitX, 9f, 10f, 40, 2400f, "Cogpunk:TrashTr0mRoar"));
				}
			}
			if (IsRoaring && t % 15 == 0) {
				SoundEngine.PlaySound(SoundID.Item22 with { Pitch = -0.4f, MaxInstances = 2 }, SpritePoint(Mouth));
				ExhaustPuff(3);
			}
		}

		private void AmbientEffects() {
			uint t = Main.GameUpdateCount;
			if ((t + (uint)NPC.whoAmI * 7) % 24 == 0) {
				ExhaustPuff(1);
			}
			if (Main.rand.NextBool(20)) {
				WaistSparks(1);
			}
		}

		/// <summary>Scrap dust thrown up along the ground line under the boss (the heap breaking open).</summary>
		private void GroundDebris(int count) {
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			int left = (int)((NPC.Bottom.X - FrameWidth * 0.4f) / 16f);
			int width = Math.Max(1, (int)(FrameWidth * 0.8f / 16f));
			int row = (int)(NPC.Bottom.Y / 16f);
			for (int i = 0; i < count; i++) {
				int x = left + Main.rand.Next(width);
				if (!SafeSpawn.TryTileDust(x, row) && !SafeSpawn.TryTileDust(x, row - 1)) {
					SafeSpawn.TryNewDust(new Vector2(x * 16f, row * 16f - 8f), 16, 8, DustID.Smoke, out _, 0f, -1.5f, 120, new Color(127, 135, 148));
				}
			}
		}

		private void WaistSparks(int count) {
			for (int i = 0; i < count; i++) {
				Vector2 at = SpritePoint(new Vector2(Main.rand.Next(WaistLeft, WaistRight), WaistY));
				if (SafeSpawn.TryNewDust(at, 0, 0, DustID.Torch, out Dust spark, 0f, 0f, 0, default, 1.1f)) {
					spark.position = at;
					spark.velocity = new Vector2(Main.rand.NextFloat(-1.5f, 1.5f), Main.rand.NextFloat(0.5f, 2.5f));
					spark.noGravity = false;
				}
			}
		}

		private void ExhaustPuff(int count) {
			for (int i = 0; i < count; i++) {
				Vector2 at = SpritePoint(Main.rand.NextBool() ? ExhaustA : ExhaustB);
				if (CogpunkClientConfig.RollEffect() && SafeSpawn.TryNewDust(at - new Vector2(4f), 8, 8, DustID.Smoke, out Dust smoke, 0f, 0f, 100, new Color(195, 200, 205), 1.3f)) {
					smoke.velocity = new Vector2(Main.rand.NextFloat(-0.4f, 0.4f), -Main.rand.NextFloat(1.5f, 2.5f));
					smoke.noGravity = true;
				}
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int sparks = NPC.life > 0 ? 3 : 40;
			for (int i = 0; i < sparks; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, NPC.life > 0 ? DustID.Iron : DustID.Torch, out Dust d)) {
					d.velocity *= NPC.life > 0 ? 1f : 3f;
				}
			}
			if (NPC.life <= 0) {
				for (int i = 0; i < 20; i++) {
					SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.Smoke, out _, 0f, -1f, 100, new Color(79, 85, 98), 2f);
				}
			}
		}

		// ------------------------------------------------------------------------------------------------------------
		// Animation and drawing (clients)
		// ------------------------------------------------------------------------------------------------------------

		public override void FindFrame(int frameHeight) {
			int ticks = IsRoaring ? RoarTicksPerFrame : TicksPerFrame;
			if (++NPC.frameCounter >= ticks) {
				NPC.frameCounter = 0;
				int frame = (NPC.frame.Y / FrameStride + 1) % FrameCount;
				NPC.frame.Y = frame * FrameStride;
			}
			NPC.frame.Width = FrameWidth;
			NPC.frame.Height = FrameHeight;
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			int buried = NPC.IsABestiaryIconDummy ? 0 : BuriedPixels();
			int visible = FrameHeight - buried;
			if (visible <= 0) {
				return false;
			}
			// Only the part above the ground line is drawn: the boss rises out of the heap, never through it.
			Rectangle source = new(0, NPC.frame.Y, FrameWidth, visible);
			Vector2 origin = new(FrameWidth * 0.5f, visible);
			Vector2 position = NPC.Bottom - screenPos + new Vector2(0f, NPC.gfxOffY);
			position = new Vector2(MathF.Round(position.X), MathF.Round(position.Y));
			SpriteEffects effects = NPC.spriteDirection == 1 ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			spriteBatch.Draw(TextureAssets.Npc[Type].Value, position, source, NPC.GetAlpha(drawColor), 0f, origin, 1f, effects, 0f);
			if (glow != null && glow.IsLoaded) {
				// Eyes, furnace and throat: full brightness, pulsing (and flaring while it roars).
				float pulse = IsRoaring ? 1f : 0.8f + 0.2f * MathF.Sin(Main.GlobalTimeWrappedHourly * 4f);
				spriteBatch.Draw(glow.Value, position, source, Color.White * pulse * NPC.Opacity, 0f, origin, 1f, effects, 0f);
			}
			return false;
		}

		public override void BossHeadSlot(ref int index) {
			if (IsEmerging && Timer < RumbleTicks) {
				index = -1;                                  // still buried: no map icon yet
			}
		}
	}
}
