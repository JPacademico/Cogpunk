using System;
using Cogpunk.Content.Underground.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
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
using R = Cogpunk.Content.Underground.NPCs.PuxaFrangoRigData;

namespace Cogpunk.Content.Underground.NPCs
{
	/// <summary>
	/// Puxa-frango ("chicken-puller", user-set 2026-10-28, designed from the user's reference image): a rare underground
	/// robot that creeps hunched over on long spindly legs and snatches with C-shaped pincer claws. It stalks its target
	/// slowly (<see cref="StalkSpeed"/>); within <see cref="LungeRange"/> and in sight it crouches for
	/// <see cref="CrouchTicks"/> (the telegraph: a creak, its claws opening wide), then lunges and snaps its claws shut.
	/// A snap that lands yanks the player towards it instead of knocking them away (the "pull" of its name) and hits
	/// harder (<see cref="SnapDamageMultiplier"/>). Then it recovers and stalks again (<see cref="LungeCooldown"/>).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor the Nymph, the rare cavern ambusher: 600 life / 16
	/// defense / 70 contact in Expert, value 2 gold): <see cref="Life"/> life, <see cref="Defense"/> defense,
	/// <see cref="ContactDamage"/> contact (the snap x <see cref="SnapDamageMultiplier"/>), knockback resistance
	/// <see cref="KnockbackResist"/>. Spawn: dirt and cavern layers, one at a time, weight <see cref="SpawnWeight"/> (the
	/// Nymph's ~1 in 160). Drops the <see cref="ChickenSnapper"/> 1 time in <see cref="SnapperOdds"/> (user-set 33%).</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the lunge cooldown; the server targets and decides,
	/// the lunge's velocity is synced with the state change; the contact hit is resolved on the hit player's client
	/// (vanilla), which applies the yank. D1: no allocation; effects client-side.</para>
	/// </summary>
	public class PuxaFrango : GridWalkerNPC
	{
		private enum Phase { Stalk, Crouch, Lunge, Recover }

		public const int Life = 640, ContactDamage = 56, Defense = 14;
		public const float KnockbackResist = 0.4f;
		public const float SnapDamageMultiplier = 1.4f;
		public const float StalkSpeed = 1.8f, StalkAccel = 0.12f, JumpSpeed = 7.5f;
		public const float LungeRange = 12f * 16f, LungeMinRange = 3f * 16f;
		public const float LungeSpeedX = 9f, LungeSpeedY = 3.5f;
		public const int CrouchTicks = 30, SnapTick = 10, LungeMaxTicks = 60, RecoverTicks = 24, LungeCooldown = 120;
		public const float YankKnockback = 7f;
		public const float VanillaKnockback = 4.5f;
		public const float SpawnWeight = 0.0065f;
		public const int SnapperOdds = 3;

		private static Asset<Texture2D> far, near;
		private static readonly string[] GoreNames = { "PuxaFrango_GoreHead", "PuxaFrango_GoreClaw", "PuxaFrango_GoreLeg" };

		private Phase CurrentPhase => (Phase)State;
		private ref float Cooldown => ref NPC.ai[2];

		protected override int CellWidth => R.CellWidth;
		protected override int CellHeight => R.CellHeight;
		protected override int OriginX => R.OriginX;
		protected override int OriginY => R.OriginY;
		protected override int FrameCount => R.Frames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => null;
		protected override IBestiaryInfoElement BestiaryBiome => BestiaryDatabaseNPCsPopulator.CommonTags.SpawnConditions.Biomes.Caverns;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
		}

		public override void Unload() {
			far = near = null;
		}

		public override void SetStaticDefaults() {
			base.SetStaticDefaults();
			CogpunkSets.Mechanical[Type] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;   // a machine
		}

		public override void SetDefaults() {
			Cogpunk.Content.Banners.EnemyBanners.SetBanner(this);         // its banner (2026-11-25)
			NPC.width = 34;
			NPC.height = 56;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = Item.buyPrice(gold: 1);
			NPC.aiStyle = -1;
			NPC.rarity = 2;                                 // the Lifeform Analyzer calls it out, like the Nymph
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo) {
			Player player = spawnInfo.Player;
			bool underground = player.ZoneDirtLayerHeight || player.ZoneRockLayerHeight;
			return underground && !player.ZoneDungeon && !spawnInfo.PlayerInTown && !spawnInfo.Water && !NPC.AnyNPCs(Type) ? SpawnWeight : 0f;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<ChickenSnapper>(), SnapperOdds));
		}

		protected override void UpdateState() {
			if (Cooldown > 0f) {
				Cooldown--;
			}
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			switch (CurrentPhase) {
				case Phase.Crouch:
					NPC.velocity.X *= 0.8f;
					NPC.direction = NPC.spriteDirection = dir;
					if (Timer >= CrouchTicks && IsAuthority) {
						NPC.velocity = new Vector2(dir * LungeSpeedX, -LungeSpeedY);
						ChangeState((int)Phase.Lunge);
					}
					break;
				case Phase.Lunge:
					if (IsAuthority && ((Timer > 6f && Grounded) || Timer >= LungeMaxTicks)) {
						Cooldown = LungeCooldown;
						ChangeState((int)Phase.Recover);
					}
					break;
				case Phase.Recover:
					NPC.velocity.X *= 0.85f;
					if (Timer >= RecoverTicks && IsAuthority) {
						ChangeState((int)Phase.Stalk);
					}
					break;
				default:
					Run(target != null ? dir : 0, StalkSpeed, StalkAccel, JumpSpeed);
					float adx = Math.Abs(dx);
					if (IsAuthority && target != null && Grounded && Cooldown <= 0f && adx <= LungeRange && adx >= LungeMinRange
						&& Math.Abs(target.Center.Y - NPC.Center.Y) < 64f && Collision.CanHitLine(NPC.Top, 1, 1, target.position, target.width, target.height)) {
						ChangeState((int)Phase.Crouch);
					}
					FaceMotion(dir);
					break;
			}
			if (!Main.dedServ) {
				Effects();
			}
		}

		private void Effects() {
			if (CurrentPhase == Phase.Crouch && Timer == 1f) {
				SoundEngine.PlaySound(SoundID.Item23 with { Pitch = 0.4f, Volume = 0.5f }, NPC.Center);      // a creak: coiling up
			}
			if (CurrentPhase == Phase.Lunge && Timer == SnapTick) {
				SoundEngine.PlaySound(SoundID.Item37 with { Pitch = 0.6f, Volume = 0.7f }, NPC.Center);      // the snap
			}
		}

		/// <summary>The snap (on the hit player's client): harder, and a yank towards it instead of a push away.</summary>
		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			if (CurrentPhase != Phase.Lunge) {
				return;
			}
			modifiers.SourceDamage *= SnapDamageMultiplier;
			modifiers.Knockback *= YankKnockback / VanillaKnockback;
			modifiers.HitDirectionOverride = target.Center.X >= NPC.Center.X ? -1 : 1;
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Crouch:
					return R.Crouch;
				case Phase.Lunge:
					return Timer < SnapTick ? R.Lunge : R.Snap;
				case Phase.Recover:
					return R.Idle;
			}
			if (!Grounded) {
				return R.Air;
			}
			if (Math.Abs(NPC.velocity.X) > 0.25f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= R.WalkStep * R.WalkFrames) {
					NPC.frameCounter -= R.WalkStep * R.WalkFrames;
				}
				return R.Walk + (int)(NPC.frameCounter / R.WalkStep) % R.WalkFrames;
			}
			return R.Idle + (int)(Timer / 24f) % 2;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 14;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.Iron, out _);
			}
			if (NPC.life > 0) {
				return;
			}
			for (int i = 0; i < GoreNames.Length; i++) {
				if (Mod.TryFind(GoreNames[i], out ModGore gore)) {
					SafeSpawn.TryNewGore(NPC.GetSource_Death(), NPC.Center, NPC.velocity * 0.4f + Main.rand.NextVector2Circular(3f, 3f), gore.Type, out _);
				}
			}
		}
	}
}
