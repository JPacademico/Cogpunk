using System;
using Cogpunk.Content.Bosses.Fungimancer.Projectiles;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Fungimancer.NPCs
{
	/// <summary>
	/// Shared rules of the Fungimancer's mushrooms (NPCs because players can hit them, as vanilla's Detonating Bubbles): they
	/// belong to the boss in <c>ai[0]</c> and pop when it is gone; they never count as kills (no banners, no tally, no crit slow
	/// motion: vanilla's <c>PositiveNPCTypesExcludedFromDeathTally</c>), take no natural-spawn room, drop nothing, hide from the
	/// bestiary; the server decides their bursts and sends them.
	/// </summary>
	public abstract class FungimancerMushroom : CogpunkNPC
	{
		public override void SetStaticDefaults() {
			NPCID.Sets.PositiveNPCTypesExcludedFromDeathTally[Type] = true;
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Hide = true });
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		protected void Common() {
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.knockBackResist = 0f;
			NPC.npcSlots = 0f;
			NPC.value = 0f;
			NPC.aiStyle = -1;
			NPC.lavaImmune = true;
		}

		/// <summary>The boss this belongs to, alive and still the Fungimancer; null otherwise.</summary>
		protected NPC Boss {
			get {
				int i = (int)NPC.ai[0];
				return i >= 0 && i < Main.maxNPCs && Main.npc[i].active && Main.npc[i].ModNPC is Fungimancer ? Main.npc[i] : null;
			}
		}

		/// <summary>The server: gone at once (no death, no loot), the removal sent.</summary>
		protected void Vanish() {
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}
			NPC.life = 0;
			NPC.active = false;
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
			}
		}

		protected static void Pop(Vector2 at, int dust, int count) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(at - new Vector2(8f), 16, 16, dust, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(3f, 3f);
				}
			}
		}

		/// <summary>Draws one frame of a vertical sheet (frames <paramref name="frameHeight"/> px, 2 px under each) with its glow,
		/// its middle at <paramref name="center"/> (on the 2 px grid).</summary>
		protected static void DrawFrame(SpriteBatch sb, Texture2D tex, Texture2D glow, int frame, int frameHeight, Vector2 center, Color light) {
			Rectangle src = new(0, frame * (frameHeight + 2), tex.Width, frameHeight);
			Vector2 at = center - Main.screenPosition - new Vector2(tex.Width * 0.5f, frameHeight * 0.5f);
			at = new Vector2(MathF.Round(at.X / 2f) * 2f, MathF.Round(at.Y / 2f) * 2f);
			sb.Draw(tex, at, src, light);
			if (glow != null) {
				sb.Draw(glow, at, src, Color.White);
			}
		}
	}

	/// <summary>
	/// The mushrooms he rains (user, 2026-11-25: "during the fight every 1 seconds it should spawn a small floaty mushroom that comes
	/// swaying falling and if in contact with a player deals small damage and aply confusion for 2 seconds ... it can be damaged by
	/// a player and if destroyed or when it lands on the ground it should burst a 4x4 spore cloud that lasts 1.5 seconds ... make
	/// some adjustments to ensure that the mushroom never spawn inside a block and instantaneously burst"): it drifts down at
	/// <see cref="FallSpeed"/> swaying side to side; its touch hurts and confuses; shot down or landing (on a block, in a liquid, or
	/// after <see cref="MaxAge"/>) it bursts into a <see cref="SporeCloud"/>. It is never spawned inside blocks (the boss checks the
	/// spot) and can't burst on the ground for its first <see cref="Grace"/> ticks.
	/// </summary>
	public class FloatyMushroom : FungimancerMushroom
	{
		public const int Life = 40, ContactDamage = 50, CloudDamage = 40, ConfusionTicks = 120, Grace = 20, MaxAge = 900;
		public const float FallSpeed = 1.5f, SwayX = 1.1f, SwayRate = 0.05f;
		public const int FrameHeight = 24;

		private static Asset<Texture2D> glow;

		private ref float Age => ref NPC.ai[2];

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			Main.npcFrameCount[Type] = 3;
			if (!Main.dedServ) {
				glow = ModContent.Request<Texture2D>(Texture + "_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			NPC.width = 20;
			NPC.height = 20;
			SetExpertStats(Life, ContactDamage, 0);
			Common();
			NPC.HitSound = SoundID.NPCHit1;
			NPC.DeathSound = SoundID.Item16 with { Pitch = 0.3f };
		}

		public override void AI() {
			Age++;
			float sway = MathF.Cos(Age * SwayRate + NPC.ai[1]);
			NPC.velocity = new Vector2(sway * SwayX, FallSpeed);
			NPC.spriteDirection = 1;
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}
			if (Boss == null) {
				Vanish();
				return;
			}
			bool landed = Age > Grace && (NPC.wet || Collision.SolidCollision(NPC.BottomLeft - new Vector2(0f, 6f), NPC.width, 8));
			if (landed || Age >= MaxAge) {
				Burst();
				Vanish();
			}
			if ((int)Age % 60 == 0) {
				NPC.netUpdate = true;
			}
		}

		/// <summary>The server: its spore cloud.</summary>
		private void Burst() {
			SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), NPC.Center, Vector2.Zero, ModContent.ProjectileType<SporeCloud>(),
				ExpertStats.HostileProjectile(NPC, CloudDamage), 0f, out _);
		}

		public override void OnKill() {
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				Burst();                                             // shot down: it bursts as well
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			target.AddBuff(BuffID.Confused, ConfusionTicks);
		}

		public override void HitEffect(NPC.HitInfo hit) {
			Pop(NPC.Center, DustID.GlowingMushroom, NPC.life > 0 ? 2 : 10);
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			float vx = NPC.velocity.X;
			int frame = vx < -0.45f ? 0 : vx > 0.45f ? 2 : 1;
			DrawFrame(spriteBatch, TextureAssets.Npc[Type].Value, glow?.IsLoaded == true ? glow.Value : null, frame, FrameHeight, NPC.Center,
				NPC.GetAlpha(drawColor));
			return false;
		}
	}

	/// <summary>
	/// The orbiting toadstools (user, 2026-11-25: "he summons 6 mushroons that spin arround him and if not detroyed in 6 seconds they
	/// burst into 1-2 toadstools, he cant cast it again if theres still mushrooms arround it"): six red caps circling him at
	/// <see cref="Radius"/> (their slot in <c>ai[1]</c>, their age in <c>ai[2]</c>), hurting what they touch; in their last
	/// second they swell; at <see cref="Hatch"/> (6 s) the server turns each into 1-2 <see cref="Toadstool"/>s (the boss's own: no
	/// loot; never more than <see cref="MaxToads"/> of his alive).
	/// </summary>
	public class OrbitMushroom : FungimancerMushroom
	{
		public const int Life = 250, ContactDamage = 90, Defense = 10, Hatch = 360, SwellAt = 300, MaxToads = 8;
		public const float Radius = 7f * 16f, Spin = 0.035f;
		public const int FrameHeight = 32;

		private static Asset<Texture2D> glow;

		private ref float Age => ref NPC.ai[2];

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			Main.npcFrameCount[Type] = 4;
			if (!Main.dedServ) {
				glow = ModContent.Request<Texture2D>(Texture + "_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			NPC.width = 28;
			NPC.height = 28;
			SetExpertStats(Life, ContactDamage, Defense);
			Common();
			NPC.HitSound = SoundID.NPCHit1;
			NPC.DeathSound = SoundID.NPCDeath1 with { Pitch = 0.4f };
		}

		public override void AI() {
			Age++;
			NPC boss = Boss;
			if (boss == null) {
				Vanish();
				return;
			}
			float a = NPC.ai[1] + Age * Spin;
			Vector2 spot = boss.Center + a.ToRotationVector2() * Radius;
			NPC.velocity = spot - NPC.Center;                        // it rides the ring (its next position is the spot)
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}
			if (Age >= Hatch) {
				HatchToads(boss);
				Vanish();
			}
			else if ((int)Age % 60 == 0) {
				NPC.netUpdate = true;
			}
		}

		/// <summary>The server: 1-2 toadstools where it is (fewer when he already has many), a puff of spores.</summary>
		private void HatchToads(NPC boss) {
			int mine = 0;
			int toad = ModContent.NPCType<Toadstool>();
			foreach (NPC n in Main.ActiveNPCs) {
				if (n.type == toad && n.ai[3] == 1f) {
					mine++;
				}
			}
			int count = Math.Min(Main.rand.Next(1, 3), MaxToads - mine);
			for (int k = 0; k < count; k++) {
				if (SafeSpawn.TryNewNPC(NPC.GetSource_FromAI(), (int)NPC.Center.X + k * 20 - 10, (int)NPC.Bottom.Y, toad, out NPC t, ai3: 1f)) {
					t.velocity = new Vector2(Main.rand.NextFloat(-2f, 2f), -3f);
					t.netUpdate = true;
				}
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			Pop(NPC.Center, DustID.Blood, NPC.life > 0 ? 2 : 12);
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			int age = (int)Age;
			int frame = age < SwellAt ? age / 15 % 2 : 2 + (age - SwellAt) / 8 % 2;
			DrawFrame(spriteBatch, TextureAssets.Npc[Type].Value, glow?.IsLoaded == true ? glow.Value : null, frame, FrameHeight, NPC.Center,
				NPC.GetAlpha(drawColor));
			return false;
		}
	}

	/// <summary>
	/// The rainbow mushroom he channels (user, 2026-11-25: "chanel a growing rainbow mushroom for 5 seconds ... the mushroom can be
	/// damaged and destroyed with briefly stuns the boss but if not destroyed it blows up"): it grows over his raised hands in 6
	/// stages; its death stuns him (<see cref="Fungimancer.MushroomDestroyed"/>); if it still stands when his channel ends, he
	/// blows it up himself. Harmless to touch. Its life (<see cref="Life"/>, Expert) is a damage race for the 5 s.
	/// </summary>
	public class ChannelMushroom : FungimancerMushroom
	{
		public const int Life = 3600, Stages = 6, FrameHeight = 72;

		/// <summary>Each growth stage's sprite, game px (ChannelMushroom.png's opaque bounds, 2026-11-25): the hitbox grows with
		/// it (tools/check_hitboxes.py), so a sprout is not hit through the air where the full cap will be.</summary>
		private static readonly Point[] StageSize = { new(32, 22), new(40, 30), new(52, 36), new(60, 44), new(72, 52), new(84, 58) };

		private static Asset<Texture2D> glow;

		private ref float Age => ref NPC.ai[1];

		/// <summary>The growth stage (every side derives it from the synced age).</summary>
		private int Stage => Math.Clamp((int)(Age * Stages / Fungimancer.ChannelTicks), 0, Stages - 1);

		/// <summary>The hitbox to the stage's size, its bottom kept where it was (it grows up from his hands).</summary>
		private void FitStage() {
			Point size = StageSize[Stage];
			if (NPC.width == size.X && NPC.height == size.Y) {
				return;
			}
			Vector2 bottom = NPC.Bottom;
			NPC.width = size.X;
			NPC.height = size.Y;
			NPC.Bottom = bottom;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			Main.npcFrameCount[Type] = Stages;
			if (!Main.dedServ) {
				glow = ModContent.Request<Texture2D>(Texture + "_Glow");
			}
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			NPC.width = StageSize[0].X;
			NPC.height = StageSize[0].Y;
			SetExpertStats(Life, 0, 0);
			NPC.damage = 0;
			Common();
			NPC.HitSound = SoundID.NPCHit13;
			NPC.DeathSound = SoundID.Item27 with { Pitch = -0.3f };
		}

		public override bool CanHitPlayer(Player target, ref int cooldownSlot) => false;

		public override void AI() {
			Age++;
			NPC boss = Boss;
			if (boss == null || boss.ModNPC is not Fungimancer f || !f.Channeling) {
				Vanish();
				return;
			}
			FitStage();
			Vector2 spot = f.ChannelPoint - new Vector2(0f, NPC.height * 0.5f);
			NPC.velocity = spot - NPC.Center;
			if (!Main.dedServ && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.RainbowMk2, out Dust d, 0f, 0f, 0,
					Spectrum.At((int)(Main.GameUpdateCount / 3)), 1.1f)) {
				d.noGravity = true;
				d.velocity = new Vector2(0f, -1.2f);
			}
			if (!Main.dedServ) {
				Lighting.AddLight(NPC.Center, 0.6f, 0.4f, 0.6f);
			}
		}

		public override void OnKill() {
			if (Main.netMode != NetmodeID.MultiplayerClient && Boss?.ModNPC is Fungimancer f) {
				f.MushroomDestroyed();
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 2 : 40;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.RainbowMk2, out Dust d, 0f, 0f, 0, Spectrum.At(i), 1.2f)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2Circular(NPC.life > 0 ? 2f : 6f, NPC.life > 0 ? 2f : 6f);
				}
			}
		}

		public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor) {
			int stage = Stage;
			Texture2D tex = TextureAssets.Npc[Type].Value;
			Rectangle src = new(0, stage * (FrameHeight + 2), tex.Width, FrameHeight);
			Vector2 at = NPC.Bottom - Main.screenPosition - new Vector2(tex.Width * 0.5f, FrameHeight);
			at = new Vector2(MathF.Round(at.X / 2f) * 2f, MathF.Round(at.Y / 2f) * 2f);
			spriteBatch.Draw(tex, at, src, Color.Lerp(NPC.GetAlpha(drawColor), Color.White, 0.5f));
			if (glow?.IsLoaded == true) {
				spriteBatch.Draw(glow.Value, at, src, Color.White * 0.9f);
			}
			return false;
		}
	}
}
