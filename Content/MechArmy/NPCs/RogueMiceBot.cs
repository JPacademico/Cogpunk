using System;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.MechArmy.MechArmyRigData;

namespace Cogpunk.Content.MechArmy.NPCs
{
	/// <summary>
	/// Rogue Mice-bot (user-set 2026-10-27: "mice bots, like the ones the summon item spawns"): the Mice-bot minion's
	/// clockwork mouse gone feral, the Mech Army's swarm. Since 2026-10-28 (user: it was too big and too different) it is
	/// drawn from the minion's own sprite code at the minion's size, mirrored, with an ember eye, and its hitbox is the
	/// minion's (<see cref="Width"/> x <see cref="Height"/>). It races along the ground at its target (faster than a walking
	/// player), hops walls, and from <see cref="LeapMin"/> to <see cref="LeapMax"/> away pounces with its jaws open (a
	/// telegraphed leap: it crouches for <see cref="CrouchTicks"/> ticks first, then a squeak).
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor Goblin Peon, 120 life / 24 contact / 4 defense in
	/// Expert): <see cref="Life"/> life, <see cref="ContactDamage"/> contact, <see cref="Defense"/> defense, light
	/// (knockback resistance <see cref="KnockbackResist"/>). Spawns only with the Mech Army. Drops (user, 2026-10-28): the
	/// Goblin Peon's coins (value 100) and 1-2 Rusted Metal.</para>
	/// <para>D2: <c>ai[0]</c>/<c>ai[1]</c> state and timer, <c>ai[2]</c> the leap cooldown (every side counts it); the server
	/// targets and decides the leap (its velocity is synced by the state change). D1: no allocation.</para>
	/// </summary>
	public class RogueMiceBot : MechWalker
	{
		private enum Phase { Run, Crouch, Leap }

		public const int Life = 60, ContactDamage = 20, Defense = 4;
		public const int Width = 20, Height = 14;           // = MiceBotMinion's hitbox
		public const float KnockbackResist = 0.85f;
		public const float RunSpeed = 4.2f;                // a walking player runs at 3
		public const float Accel = 0.3f;
		public const float JumpSpeed = 7f;
		public const float LeapMin = 2f * 16f, LeapMax = 7f * 16f;
		public const float LeapSpeedX = 6.5f, LeapSpeedY = 4.5f;
		public const int CrouchTicks = 12;
		public const int LeapCooldown = 80;
		public const int MaxLeapTicks = 120;
		public const float RunAnimDistance = 6f;           // px of travel per run frame (= MiceBotMinion.RunAnimDistance)

		private static Asset<Texture2D> glow;

		private Phase CurrentPhase => (Phase)State;
		private ref float Cooldown => ref NPC.ai[2];

		protected override int CellWidth => R.MiceCellWidth;
		protected override int CellHeight => R.MiceCellHeight;
		protected override int OriginX => R.MiceOriginX;
		protected override int OriginY => R.MiceOriginY;
		protected override int FrameCount => R.MiceFrames;
		protected override Asset<Texture2D> FarSheet => null;         // one plane: the minion's sprite has no depth to split
		protected override Asset<Texture2D> NearSheet => null;
		protected override Asset<Texture2D> GlowSheet => glow;

		protected override void LoadSheets() {
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			NPC.width = Width;
			NPC.height = Height;
			SetExpertStats(Life, ContactDamage, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 100f;                                // the Goblin Peon's (decompiled NPC.SetDefaults, type 26)
			NPC.npcSlots = 0.75f;
			NPC.aiStyle = -1;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedMetal>(), 1, 1, 2));
		}

		protected override void UpdateState() {
			if (Cooldown > 0f) {
				Cooldown--;
			}
			Retarget();
			Player target = Target;
			float dx = target != null ? target.Center.X - NPC.Center.X : 0f;
			int dir = target != null ? (dx >= 0f ? 1 : -1) : (NPC.direction == 0 ? -1 : NPC.direction);
			float haste = Haste;
			switch (CurrentPhase) {
				case Phase.Crouch:
					NPC.velocity.X *= 0.8f;
					NPC.direction = NPC.spriteDirection = dir;
					if (Timer >= CrouchTicks && IsAuthority) {
						NPC.velocity = new Vector2(dir * LeapSpeedX * haste, -LeapSpeedY);
						ChangeState((int)Phase.Leap);
					}
					break;
				case Phase.Leap:
					if (Timer == 1f && !Main.dedServ) {
						SoundEngine.PlaySound(SoundID.Item1 with { Pitch = 0.9f, Volume = 0.45f }, NPC.Center);
					}
					if (IsAuthority && ((Timer > 6f && Grounded) || Timer >= MaxLeapTicks)) {
						Cooldown = LeapCooldown;
						ChangeState((int)Phase.Run);
					}
					break;
				default:
					Run(target != null ? dir : NPC.direction == 0 ? -1 : NPC.direction, target != null ? RunSpeed * haste : RunSpeed * 0.3f, Accel * haste, JumpSpeed);
					if (target != null && Grounded && target.Bottom.Y < NPC.Top.Y - 32f && Math.Abs(dx) < 96f) {
						NPC.velocity.Y = -JumpSpeed;                // it's above: hop up after it
					}
					float adx = Math.Abs(dx);
					if (IsAuthority && target != null && Grounded && Cooldown <= 0f && adx >= LeapMin && adx <= LeapMax
						&& Math.Abs(target.Center.Y - NPC.Center.Y) < 48f && Collision.CanHitLine(NPC.Top, 1, 1, target.position, target.width, target.height)) {
						ChangeState((int)Phase.Crouch);
					}
					FaceMotion(dir);
					break;
			}
		}

		protected override int PickFrame() {
			switch (CurrentPhase) {
				case Phase.Crouch:
					return R.MiceIdle + 1;
				case Phase.Leap:
					return Timer < 10f || !Grounded ? (NPC.HasValidTarget && Vector2.DistanceSquared(Main.player[NPC.target].Center, NPC.Center) < 48f * 48f ? R.MiceBite : R.MiceLeap) : R.MiceRun;
			}
			if (!Grounded) {
				return R.MiceLeap;
			}
			if (Math.Abs(NPC.velocity.X) > 0.3f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= RunAnimDistance * R.MiceRunFrames) {
					NPC.frameCounter -= RunAnimDistance * R.MiceRunFrames;
				}
				return R.MiceRun + (int)(NPC.frameCounter / RunAnimDistance) % R.MiceRunFrames;
			}
			return R.MiceIdle + (int)(Timer / 20f) % 2;
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 12;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 2 == 0 ? DustID.Copper : DustID.Iron, out _);
			}
			if (NPC.life <= 0) {
				MechArmyGores.Spawn(NPC, "RogueMiceBot_GoreShell", "RogueMiceBot_GoreWheel", "RogueMiceBot_GoreWheel");
			}
		}
	}
}
