using System;
using Cogpunk.Content.Bosses.CursedConductor.Buffs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent.Bestiary;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.CursedConductor.NPCs
{
	/// <summary>
	/// One of the Cursed Conductor's ghosts (user-set 2026-11-05: "spawn a ghost: default terraria cemetery ghost, slightly
	/// more damage but less health and less movement speed; these ghosts should target the closest player"): vanilla's
	/// graveyard Ghost (NPC 316: its sprite and its frames, <c>AnimationType</c>) with its own slower chase. Vanilla's
	/// (decompiled <c>NPC.SetDefaults</c> 316 and <c>NPC.AI</c> style 22): 50 life, 15 contact, 4 defense in Classic (100 / 30 in
	/// Expert), drifting at up to 2 px a tick sideways (+0.1 a tick) and 1.5 up and down (+0.04), through blocks. This one,
	/// in Expert (D3 rule 0): <see cref="ExpertLife"/> life (less), <see cref="ExpertDamage"/> contact (slightly more),
	/// <see cref="Defense"/> defense, and <see cref="MaxSpeedX"/> / <see cref="MaxSpeedY"/> px a tick (slower), after the closest
	/// player (retargeted every <see cref="RetargetTicks"/>). A cursed player takes 25% more from it
	/// (<see cref="ConductorCurse"/>); a furious ghost (<c>ai[0]</c> = 1, out of town) hits 1.5x.
	/// <para>It fades in as it rises out of its rift and fades away when the Conductor is gone (no loot, no banner, not in
	/// the bestiary: a boss's minion). D2: the server spawns it and retargets; the drift runs on every side from synced
	/// state and is resynced every <see cref="ResyncTicks"/>. D1: no allocation.</para>
	/// </summary>
	public class ConductorGhost : CogpunkNPC
	{
		public const int ExpertLife = 60, ExpertDamage = 36, Defense = 4;   // vanilla's Expert 100 / 30 / 4 (my calls)
		public const float MaxSpeedX = 1.5f, AccelX = 0.08f;               // vanilla's 2 / 0.1
		public const float MaxSpeedY = 1.1f, AccelY = 0.035f;              // vanilla's 1.5 / 0.04
		public const float FuryDamage = 1.5f;
		public const int RetargetTicks = 30, ResyncTicks = 60, FadeInTicks = 24, FadeOutTicks = 30;
		public const int Alpha = 100;                                       // vanilla's ghost is drawn see-through

		private int baseDamage = -1;

		private ref float Furious => ref NPC.ai[0];
		private ref float Age => ref NPC.ai[1];
		private ref float Leaving => ref NPC.ai[2];

		public override string Texture => "Terraria/Images/NPC_" + NPCID.Ghost;

		public override void SetStaticDefaults() {
			Main.npcFrameCount[Type] = Main.npcFrameCount[NPCID.Ghost];
			NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers() { Hide = true });
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Poisoned] = true;
			NPCID.Sets.SpecificDebuffImmunity[Type][BuffID.Confused] = true;
		}

		public override void SetDefaults() {
			NPC.width = 24;
			NPC.height = 44;
			SetExpertStats(ExpertLife, ExpertDamage, Defense);
			NPC.knockBackResist = 0.5f;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.aiStyle = -1;
			NPC.alpha = 255;
			NPC.value = 0f;
			NPC.npcSlots = 0f;
			NPC.HitSound = SoundID.NPCHit1;
			NPC.DeathSound = SoundID.NPCDeath6;
			AnimationType = NPCID.Ghost;
		}

		public override void SetBestiary(BestiaryDatabase database, BestiaryEntry bestiaryEntry) {
		}

		public override void AI() {
			Age++;
			if (baseDamage < 0) {
				baseDamage = NPC.damage;
			}
			NPC.damage = Furious == 1f ? (int)(baseDamage * FuryDamage) : baseDamage;
			bool authority = Main.netMode != NetmodeID.MultiplayerClient;
			if (authority && (int)Age % RetargetTicks == 1) {
				NPC.TargetClosest(false);
				if (Leaving == 0f && !NPC.AnyNPCs(ModContent.NPCType<CursedConductor>())) {
					Leaving = 1f;                                  // the fight is over: it fades away
					NPC.netUpdate = true;
				}
			}
			if (Leaving != 0f || !NPC.HasValidTarget) {
				NPC.velocity *= 0.92f;
				NPC.alpha = Math.Min(255, NPC.alpha + 255 / FadeOutTicks);
				if (NPC.alpha >= 255 && authority) {
					NPC.active = false;
					if (Main.netMode == NetmodeID.Server) {
						NetMessage.SendData(MessageID.SyncNPC, number: NPC.whoAmI);
					}
				}
				return;
			}
			NPC.alpha = Math.Max(Alpha, 255 - (int)(Age * (255 - Alpha) / FadeInTicks));
			Player target = Main.player[NPC.target];
			Vector2 to = target.Center - NPC.Center;
			NPC.velocity.X = MathHelper.Clamp(NPC.velocity.X + Math.Sign(to.X) * AccelX, -MaxSpeedX, MaxSpeedX);
			NPC.velocity.Y = MathHelper.Clamp(NPC.velocity.Y + Math.Sign(to.Y - 8f) * AccelY + MathF.Sin(Age * 0.06f) * 0.01f, -MaxSpeedY, MaxSpeedY);
			if (Math.Abs(to.X) > 4f) {
				NPC.direction = NPC.spriteDirection = to.X > 0f ? 1 : -1;
			}
			if (authority && (int)Age % ResyncTicks == 0) {
				NPC.netUpdate = true;
			}
			if (!Main.dedServ) {
				Lighting.AddLight(NPC.Center, 0.1f, 0.3f, 0.25f);
				if (Main.rand.NextBool(10) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.CursedTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity *= 0.3f;
				}
			}
		}

		public override void ModifyHitPlayer(Player target, ref Player.HurtModifiers modifiers) {
			ConductorCurse.Amplify(target, ref modifiers);
		}

		public override bool CanHitPlayer(Player target, ref int cooldownSlot) => NPC.alpha < 200;

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life <= 0 ? 14 : 3;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, DustID.CursedTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity *= NPC.life <= 0 ? 2f : 1f;
				}
			}
		}
	}
}
