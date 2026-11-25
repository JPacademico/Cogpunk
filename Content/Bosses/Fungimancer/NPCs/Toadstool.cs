using System;
using Cogpunk.Content.Bosses.Fungimancer.Projectiles;
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
using R = Cogpunk.Content.Bosses.Fungimancer.NPCs.ToadstoolRigData;

namespace Cogpunk.Content.Bosses.Fungimancer.NPCs
{
	/// <summary>
	/// The Toadstool (user, 2026-11-25: "a new enemy called toadstoll that spawns on mushroom biomes and its a medium frog with
	/// small mushrooms growing on his back that try to jump at the player and deals contact damage and causes confusion, they
	/// also burst into a spore cloud when killed"), the Fungimancer's kin: the toads his orbiting mushrooms burst into, and the
	/// shape his polymorph gives a player (<see cref="DrawForm"/>).
	/// <list type="bullet">
	/// <item>It sits a moment (<see cref="SitMin"/>-<see cref="SitMax"/> ticks, rolled by the server), crouches
	/// (<see cref="CrouchTicks"/>: the anticipation, a croak) and leaps at its target on a ballistic arc aimed at where they
	/// stand (an air time from the distance, the launch from vanilla's NPC gravity), lands with a squash and sits again.</item>
	/// <item>Its touch hurts and confuses (vanilla's Confused, <see cref="ConfusionTicks"/>).</item>
	/// <item>Killed, it bursts into a <see cref="SporeCloud"/> (the server spawns it, the cloud's damage
	/// <see cref="CloudDamage"/>).</item>
	/// <item>Spawns in the glowing mushroom fields, surface and underground (weight <see cref="SpawnWeight"/>); the Fungimancer's
	/// own (<see cref="FromBoss"/>, <c>ai[3]</c>) drop nothing.</item>
	/// </list>
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv): the glowing mushroom fields' own, terraria.wiki.gg 1.4.4 Expert:
	/// Anomura Fungus 460 life / 24 defense / 76 contact, Mushi Ladybug 440 / 16 / 120; this one is softer (it leaps, and its
	/// confusion and cloud are its danger).</para>
	/// <para>D2: the server decides the leaps (the arc rides the NPC's synced velocity) and the sit times; frames are picked on
	/// clients from the synced state. D0: spawns through SafeSpawn; numbers clamped. D1: no allocation per tick.</para>
	/// </summary>
	public class Toadstool : GridWalkerNPC
	{
		private enum Phase { Sit, Crouch, Air, Land }

		public const int Life = 320, ContactDamage = 70, Defense = 14;
		public const int ConfusionTicks = 120;                          // 2 s, as the Fungimancer's mushrooms (my call)
		public const int CloudDamage = 24;                              // Expert, the cloud it bursts into
		public const float KnockbackResist = 0.5f;
		public const int SitMin = 40, SitMax = 80, CrouchTicks = 18, LandTicks = 10, AirMaxTicks = 300;
		public const float LeapRange = 26f * 16f, LeapReachX = 14f * 16f, LeapReachY = 12f * 16f;
		public const float NPCGravity = 0.3f;                           // vanilla's NPC gravity (decompiled NPC.UpdateNPC_UpdateGravity)
		public const float MaxLeapVX = 6.5f, MinLeapVY = 4.5f, MaxLeapVY = 11f;
		public const float SpawnWeight = 0.3f;

		private static Asset<Texture2D> far, glow, middle;

		private Phase CurrentPhase => (Phase)State;
		private ref float SitTicks => ref NPC.ai[2];                    // this sit's length (the server rolls it)

		/// <summary>Burst out of the Fungimancer's mushrooms: drops nothing (synced, <c>ai[3]</c>).</summary>
		public bool FromBoss {
			get => NPC.ai[3] == 1f;
			set => NPC.ai[3] = value ? 1f : 0f;
		}

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => null;
		protected override Asset<Texture2D> GlowSheet => glow;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.UndergroundMushroom;

		/// <summary>The rig origin from the hitbox's middle (facing left; the body box isn't centred on it).</summary>
		public const int RigShift = -(R.BodyLeft + R.BodyRight) / 2;

		protected override Vector2 DrawAnchor => NPC.Bottom + new Vector2(NPC.spriteDirection == 1 ? -RigShift : RigShift, 0f);

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
			middle = DepthLayers.RequestOptional(Texture);
		}

		public override void Unload() {
			far = glow = middle = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;     // its own spores
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;
		}

		public override void SetDefaults() {
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = R.BodyRight - R.BodyLeft;
			NPC.height = -R.BodyTop;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit13;
			NPC.DeathSound = SoundID.NPCDeath1;
			NPC.value = Item.buyPrice(silver: 12);                      // the Anomura Fungus's (13 silver)
			NPC.aiStyle = -1;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player player = spawnInfo.Player;
			return player.ZoneGlowshroom && !spawnInfo.PlayerInTown && !spawnInfo.Water && !player.ZoneDungeon ? SpawnWeight : 0f;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
			bestiaryEntry.Info.AddRange(new IBestiaryInfoElement[] {
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.UndergroundMushroom,
				BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.SurfaceMushroom,
				new FlavorTextBestiaryInfoElement(this.GetLocalizationKey("Bestiary")),
			});
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ItemID.GlowingMushroom, 2, 2, 4));   // half the time, 2-4 (my call)
		}

		/// <summary>The server (or singleplayer), as it dies: the spore cloud; the Fungimancer's own drop nothing.</summary>
		public override bool PreKill() {
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				SafeSpawn.TryNewProjectile(NPC.GetSource_Death(), NPC.Center, Vector2.Zero, ModContent.ProjectileType<SporeCloud>(),
					ExpertStats.HostileProjectile(NPC, CloudDamage), 0f, out _);
			}
			return !FromBoss;
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo hurtInfo) {
			target.AddBuff(BuffID.Confused, ConfusionTicks);
		}

		protected override void UpdateState() {
			Retarget();
			Player target = Target;
			switch (CurrentPhase) {
				case Phase.Crouch:
					NPC.velocity.X *= 0.7f;
					FaceTarget(target);
					if (IsAuthority && Timer >= CrouchTicks) {
						Leap(target);
						ChangeState((int)Phase.Air);
					}
					break;
				case Phase.Air:
					if (Math.Abs(NPC.velocity.X) > 0.1f) {
						NPC.direction = NPC.spriteDirection = Math.Sign(NPC.velocity.X);
					}
					if (IsAuthority && ((Timer > 4f && Grounded) || Timer >= AirMaxTicks)) {
						ChangeState((int)Phase.Land);
					}
					break;
				case Phase.Land:
					NPC.velocity.X *= 0.75f;
					if (IsAuthority && Timer >= LandTicks) {
						SitTicks = Main.rand.Next(SitMin, SitMax + 1);
						ChangeState((int)Phase.Sit);
					}
					break;
				default:
					NPC.velocity.X *= Grounded ? 0.8f : 0.99f;
					FaceTarget(target);
					if (IsAuthority && Grounded && target != null && Timer >= Math.Max(SitMin, SitTicks)
						&& Vector2.DistanceSquared(target.Center, NPC.Center) <= LeapRange * LeapRange) {
						ChangeState((int)Phase.Crouch);
					}
					break;
			}
			if (!Main.dedServ) {
				Effects();
			}
		}

		private void FaceTarget(Player target) {
			if (target != null && Math.Abs(target.Center.X - NPC.Center.X) > 8f) {
				NPC.direction = NPC.spriteDirection = target.Center.X > NPC.Center.X ? 1 : -1;
			}
		}

		/// <summary>Server: the leap, a ballistic arc landing where the target stands (within reach): an air time that grows with
		/// the distance, the horizontal speed to cover it, the vertical speed that lands it there under vanilla's gravity,
		/// clamped to a frog's hop.</summary>
		private void Leap(Player target) {
			if (target == null) {
				NPC.velocity = new Vector2(NPC.direction * 2f, -MinLeapVY);
				NPC.netUpdate = true;
				return;
			}
			float dx = MathHelper.Clamp(target.Center.X - NPC.Center.X, -LeapReachX, LeapReachX);
			float dy = MathHelper.Clamp(target.Bottom.Y - NPC.Bottom.Y, -LeapReachY, LeapReachY);
			float t = MathHelper.Clamp(Math.Abs(dx) / 5f, 28f, 50f);
			float vx = MathHelper.Clamp(dx / t, -MaxLeapVX, MaxLeapVX);
			float vy = MathHelper.Clamp((dy - 0.5f * NPCGravity * t * t) / t, -MaxLeapVY, -MinLeapVY);
			NPC.velocity = new Vector2(vx, vy);
			if (Math.Abs(vx) > 0.1f) {
				NPC.direction = NPC.spriteDirection = Math.Sign(vx);
			}
			NPC.netUpdate = true;
		}

		private void Effects() {
			if (CurrentPhase == Phase.Crouch && Timer == 2f) {
				SoundEngine.PlaySound(SoundID.Zombie13 with { Pitch = 0.5f, Volume = 0.45f, MaxInstances = 3 }, NPC.Center);   // a croak
			}
			if (CurrentPhase == Phase.Land && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.NPCHit13 with { Pitch = -0.4f, Volume = 0.35f, MaxInstances = 3 }, NPC.Bottom);  // a soft slap
				for (int i = 0; i < 3; i++) {
					if (CogpunkClientConfig.RollEffect() && SafeSpawn.TryNewDust(NPC.BottomLeft - new Vector2(0f, 4f), NPC.width, 4, DustID.GlowingMushroom, out Dust d)) {
						d.noGravity = true;
						d.velocity = new Vector2(Main.rand.NextFloat(-1.5f, 1.5f), -0.6f);
					}
				}
			}
			if (Main.rand.NextBool(40) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(NPC.position, NPC.width, 10, DustID.GlowingMushroom, out Dust spore)) {
				spore.noGravity = true;                                  // a spore from the caps now and then
				spore.velocity = new Vector2(0f, -0.5f);
				spore.scale = 0.8f;
			}
			Lighting.AddLight(NPC.Top + new Vector2(0f, 6f), 0.05f, 0.18f, 0.24f);   // the caps' glow
		}

		protected override int PickFrame() => FrameFor((int)CurrentPhase, NPC.velocity, (int)Timer);

		/// <summary>The frame for a phase (0 sit, 1 crouch, 2 air, 3 land), a velocity and a timer (also the polymorph's).</summary>
		public static int FrameFor(int phase, Vector2 velocity, int timer) {
			switch (phase) {
				case 1:
					return R.Crouch;
				case 2:
					return velocity.Y < -3f ? R.Leap : velocity.Y > 3f ? R.Fall : R.Air;
				case 3:
					return R.Land;
			}
			int step = timer / 10 % 4;                                   // the sac: 0 1 2 1
			return R.Idle + (step == 3 ? 1 : step);
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 16;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 3 == 0 ? DustID.GlowingMushroom : DustID.GreenBlood, out Dust d)) {
					d.velocity *= NPC.life > 0 ? 1f : 2f;
				}
			}
			if (NPC.life <= 0) {
				SoundEngine.PlaySound(SoundID.Item16 with { Pitch = -0.3f, Volume = 0.6f }, NPC.Center);   // the spores puff out
			}
		}

		/// <summary>The toad (far, middle and glow planes) as a polymorphed player's look (<see cref="Polymorph.PolymorphDrawLayer"/>):
		/// three entries in the player's draw list, its feet at <paramref name="feet"/> (screen px, on the 2 px grid), facing right
		/// when <paramref name="facingRight"/> (the art faces left). Clients only; nothing when the sheet is missing.</summary>
		public static void AddFormDrawData(ref Terraria.DataStructures.PlayerDrawSet drawInfo, Vector2 feet, int frame, bool facingRight, Color light) {
			if (Main.dedServ || middle?.IsLoaded != true) {
				return;
			}
			frame = Math.Clamp(frame, 0, R.Frames - 1);
			Rectangle src = new(0, frame * (R.CellHeight + 2), R.CellWidth, R.CellHeight);
			Vector2 origin = new(facingRight ? R.CellWidth - R.OriginX : R.OriginX, R.OriginY);
			SpriteEffects fx = facingRight ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
			Vector2 at = new(MathF.Round(feet.X / 2f) * 2f, MathF.Round(feet.Y / 2f) * 2f);
			if (far?.IsLoaded == true) {
				drawInfo.DrawDataCache.Add(new Terraria.DataStructures.DrawData(far.Value, at, src, DepthLayers.Tint(light, DepthLayers.Far), 0f, origin, 1f, fx));
			}
			drawInfo.DrawDataCache.Add(new Terraria.DataStructures.DrawData(middle.Value, at, src, light, 0f, origin, 1f, fx));
			if (glow?.IsLoaded == true) {
				drawInfo.DrawDataCache.Add(new Terraria.DataStructures.DrawData(glow.Value, at, src, Color.White, 0f, origin, 1f, fx));
			}
		}
	}
}
