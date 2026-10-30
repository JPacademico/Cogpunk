using System;
using Cogpunk.Content.MechArmy.Minions;
using Cogpunk.Content.Scrap.Items;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Systems;
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
	/// Annoy-o-tron ("Alarmobô" in Portuguese; user-set 2026-10-27): a little alarm box on treads whose head is a red
	/// emergency beacon, spinning, with a siren that never stops (<see cref="MechArmySounds.Alarm"/>, every
	/// <see cref="SirenInterval"/> ticks). It never attacks and has no contact damage: it follows another enemy around
	/// (<see cref="PickLeader"/>: the closest hostile within <see cref="LeaderRange"/>, matching its pace up to
	/// <see cref="MaxFollowSpeed"/> so a hasted pack doesn't outrun the alarm) and keeps every enemy within
	/// <see cref="AlarmRange"/> (15 tiles: 10 user-set on 2026-10-27, +50% on 2026-10-28) hasted: +50% speed
	/// (<see cref="NPCHaste"/>; hasted enemies pulse red).
	/// With no one to follow it hangs back from the players, between <see cref="ShyMin"/> and <see cref="ShyMax"/> away.
	/// <para>Stats (Expert, D3 rule 0; docs/balance/npcs.csv; anchor Goblin Sorcerer, the goblin army's support caster, 80
	/// life / 2 defense in Expert): <see cref="Life"/> life, <see cref="Defense"/> defense, no damage. At most two at once
	/// (<see cref="MechArmyInvasion.MaxAnnoyOTrons"/>), so the sirens stay bearable. Drops (user, 2026-10-28): the Goblin
	/// Sorcerer's coins (value 200), 1-2 Rusted Metal and the <see cref="AlarmHead"/> (<see cref="AlarmHeadDrop"/>: 1 in
	/// 10, 1 in 100 once one has dropped in the world).</para>
	/// <para>D2: the server picks the target and the leader (<c>ai[2]</c> = leader index + 1, synced on change); following
	/// runs on every side. The haste is applied on every side from the synced positions every <see cref="AlarmRefresh"/>
	/// ticks (no packets; the server's positions win). D1: one pass over the NPCs every <see cref="AlarmRefresh"/> ticks and
	/// every <see cref="LeaderInterval"/> ticks; light, sound and the beacon are client-side.</para>
	/// </summary>
	public class AnnoyOTron : MechWalker
	{
		public const int Life = 100, Defense = 6;
		public const float KnockbackResist = 0.5f;
		public const float AlarmRange = 15f * 16f;          // 10 tiles + 50% (user, 2026-10-28); the Alarm Head's minion uses it too
		public const int AlarmRefresh = 10;
		public const int HasteTicks = AlarmRefresh * 2;
		public const float LeaderRange = 50f * 16f;
		public const int LeaderInterval = 30;
		public const float FollowSpeed = 3.2f;
		/// <summary>It keeps pace with a faster leader (its speed + <see cref="PaceMargin"/>), up to this.</summary>
		public const float MaxFollowSpeed = 7f;
		public const float PaceMargin = 0.5f;
		public const float Accel = 0.18f;
		public const float JumpSpeed = 7.5f;
		public const float KeepDistance = 4f * 16f;
		public const float ShyMin = 10f * 16f, ShyMax = 18f * 16f;
		public const int SirenInterval = 60;
		public const int BeaconTicks = 4;                  // per beacon frame: a full turn in 32 ticks (about 2 a second)
		public const float RunAnimDistance = 4f;

		private static Asset<Texture2D> far, near, glow, beacon, beaconGlow;

		private ref float LeaderSlot => ref NPC.ai[2];

		protected override int CellWidth => R.AnnoyCellWidth;
		protected override int CellHeight => R.AnnoyCellHeight;
		protected override int OriginX => R.AnnoyOriginX;
		protected override int OriginY => R.AnnoyOriginY;
		protected override int FrameCount => R.AnnoyFrames;
		protected override Asset<Texture2D> FarSheet => far;
		protected override Asset<Texture2D> NearSheet => near;
		protected override Asset<Texture2D> GlowSheet => glow;

		protected override void LoadSheets() {
			far = DepthLayers.RequestOptional(Texture + "_Far");
			near = DepthLayers.RequestOptional(Texture + "_Near");
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
			beacon = DepthLayers.RequestOptional(Texture + "_Beacon");
			beaconGlow = DepthLayers.RequestOptional(Texture + "_BeaconGlow");
		}

		public override void Unload() {
			far = near = glow = beacon = beaconGlow = null;
		}

		public override void SetDefaults() {
			NPC.width = 24;
			NPC.height = 30;
			SetExpertStats(Life, 0, Defense);
			NPC.knockBackResist = KnockbackResist;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 200f;                                // the Goblin Sorcerer's (decompiled NPC.SetDefaults, type 29)
			NPC.aiStyle = -1;
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot) {
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<RustedMetal>(), 1, 1, 2));
			npcLoot.Add(new AlarmHeadDrop());
		}

		private NPC Leader {
			get {
				int i = (int)LeaderSlot - 1;
				if (i < 0 || i >= Main.maxNPCs) {
					return null;
				}
				NPC n = Main.npc[i];
				return n.active && IsFollowable(n) ? n : null;
			}
		}

		private bool IsFollowable(NPC other) {
			return other.whoAmI != NPC.whoAmI && other.type != Type && !other.friendly && !other.townNPC && other.lifeMax > 5
				&& !other.dontTakeDamage && !NPCID.Sets.ProjectileNPC[other.type] && !NPCID.Sets.CountsAsCritter[other.type];
		}

		/// <summary>Server: the closest enemy worth following (the Jaeger first if one is near: it guards the big one).</summary>
		private void PickLeader() {
			int best = -1;
			float bestScore = LeaderRange * LeaderRange;
			int jaeger = ModContent.NPCType<Jaeger>();
			foreach (NPC other in Main.ActiveNPCs) {
				if (!IsFollowable(other)) {
					continue;
				}
				float d = Vector2.DistanceSquared(other.Center, NPC.Center);
				if (other.type == jaeger) {
					d *= 0.25f;
				}
				if (d < bestScore) {
					bestScore = d;
					best = other.whoAmI;
				}
			}
			float slot = best + 1;
			if (slot != LeaderSlot) {
				LeaderSlot = slot;
				NPC.netUpdate = true;
			}
		}

		protected override void UpdateState() {
			Retarget();
			if (IsAuthority && (Timer % LeaderInterval == 1f || (LeaderSlot != 0f && Leader == null))) {
				PickLeader();
			}
			NPC leader = Leader;
			Player target = Target;
			int dir = 0;
			float speed = FollowSpeed;
			if (leader != null) {
				float dx = leader.Center.X - NPC.Center.X;
				dir = Math.Abs(dx) > KeepDistance ? Math.Sign(dx) : 0;
				speed = MathHelper.Clamp(Math.Abs(leader.velocity.X) + PaceMargin, FollowSpeed, MaxFollowSpeed);   // keep the escort inside the alarm
				if (Grounded && leader.Bottom.Y < NPC.Top.Y - 40f && Math.Abs(dx) < 160f) {
					NPC.velocity.Y = -JumpSpeed;                // follow it up a ledge
				}
			}
			else if (target != null) {
				float dx = target.Center.X - NPC.Center.X;
				float adx = Math.Abs(dx);
				dir = adx > ShyMax ? Math.Sign(dx) : (adx < ShyMin ? -Math.Sign(dx) : 0);
			}
			Run(dir, speed, Accel * (speed / FollowSpeed), JumpSpeed);
			int face = leader != null ? Math.Sign(leader.Center.X - NPC.Center.X) : (target != null ? Math.Sign(target.Center.X - NPC.Center.X) : 0);
			FaceMotion(face);
			if (Timer % AlarmRefresh == 0f) {
				SoundTheAlarm();
			}
			if (!Main.dedServ) {
				Effects();
			}
		}

		/// <summary>Every side: hastes every enemy within <see cref="AlarmRange"/> (except other Annoy-o-trons).</summary>
		private void SoundTheAlarm() {
			float range = AlarmRange * AlarmRange;
			foreach (NPC other in Main.ActiveNPCs) {
				if (other.whoAmI != NPC.whoAmI && other.type != Type && Vector2.DistanceSquared(other.Center, NPC.Center) <= range) {
					NPCHaste.Apply(other, HasteTicks);
				}
			}
		}

		private Vector2 BeaconPoint => NPC.Bottom + new Vector2(0f, -22f * 2f + R.AnnoyBeaconY[Math.Clamp(Frame, 0, R.AnnoyFrames - 1)]);

		private int BeaconFrame => (int)((Main.GameUpdateCount / BeaconTicks + (uint)NPC.whoAmI) % R.BeaconFrames);

		/// <summary>Clients: the siren and the sweeping red light.</summary>
		private void Effects() {
			if ((Main.GameUpdateCount + (uint)NPC.whoAmI * 7u) % SirenInterval == 0) {
				SoundEngine.PlaySound(MechArmySounds.Alarm, NPC.Center);
			}
			float facing = MathF.Cos(MathHelper.TwoPi * BeaconFrame / R.BeaconFrames);
			float strength = 0.55f + 0.45f * Math.Max(0f, facing);
			Lighting.AddLight(BeaconPoint, 0.95f * strength, 0.18f * strength, 0.06f * strength);
		}

		protected override int PickFrame() {
			if (!Grounded) {
				return R.AnnoyHop;
			}
			if (Math.Abs(NPC.velocity.X) > 0.3f) {
				NPC.frameCounter += Math.Abs(NPC.velocity.X);
				if (NPC.frameCounter >= RunAnimDistance * R.AnnoyDriveFrames) {
					NPC.frameCounter -= RunAnimDistance * R.AnnoyDriveFrames;
				}
				return R.AnnoyDrive + (int)(NPC.frameCounter / RunAnimDistance) % R.AnnoyDriveFrames;
			}
			return R.AnnoyIdle + (int)(Timer / 8f) % 2;     // the speaker throbs
		}

		protected override void DrawExtras(SpriteBatch spriteBatch, Vector2 anchor, Color light, bool flip, float scale, bool dummy) {
			int bob = R.AnnoyBeaconY[Math.Clamp(dummy ? 0 : Frame, 0, R.AnnoyFrames - 1)];
			int frame = dummy ? 0 : BeaconFrame;
			Vector2 at = anchor + new Vector2(0f, bob * scale);
			if (beacon?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, beacon.Value, frame, 1, CellWidth, CellHeight, R.CellPadding, OriginX, OriginY, at, 0, light, flip, scale);
			}
			if (beaconGlow?.IsLoaded == true) {
				DepthLayers.DrawCell(spriteBatch, beaconGlow.Value, frame, 1, CellWidth, CellHeight, R.CellPadding, OriginX, OriginY, at, 0, Color.White * NPC.Opacity, flip, scale);
			}
		}

		public override void HitEffect(NPC.HitInfo hit) {
			if (Main.dedServ) {
				return;
			}
			int count = NPC.life > 0 ? 3 : 12;
			for (int i = 0; i < count; i++) {
				SafeSpawn.TryNewDust(NPC.position, NPC.width, NPC.height, i % 2 == 0 ? DustID.Iron : DustID.Torch, out _);
			}
			if (NPC.life <= 0) {
				MechArmyGores.Spawn(NPC, "AnnoyOTron_GoreBeacon", "AnnoyOTron_GoreSpeaker");
			}
		}
	}
}
