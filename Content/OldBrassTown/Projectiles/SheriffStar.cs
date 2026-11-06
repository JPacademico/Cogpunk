using System;
using Cogpunk.Content.OldBrassTown.NPCs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Cogpunk.Core.Visuals;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using ReLogic.Content;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using R = Cogpunk.Content.OldBrassTown.NPCs.SheriffRigData;

namespace Cogpunk.Content.OldBrassTown.Projectiles
{
	/// <summary>
	/// One of the <see cref="Sheriff"/>'s three sheriff stars (user-set 2026-11-04: "three sheriff stars that float above him
	/// and attack the player then come back to him, every 2 seconds"). It floats in its place over his hat, spinning; when his
	/// stars' clock (<see cref="Sheriff.StarClock"/>) starts a cycle it flashes (its rim lit: the telegraph, until it flies),
	/// then at its own launch tick (<see cref="Sheriff.StarTelegraph"/> + slot x <see cref="Sheriff.StarStagger"/>) it flies at
	/// where the Sheriff's target is at that moment, <see cref="OutSpeed"/> for <see cref="OutTicks"/> ticks, and homes back
	/// to its place at <see cref="ReturnSpeed"/>. It only hurts while flying (out and back), never while it floats.
	/// <para>D2: spawned by the server with <c>ai[0]</c> = the Sheriff, <c>ai[1]</c> = its slot; every side follows the
	/// Sheriff's synced clock and target, so no packet of its own (each client's copy aims at the target as that client sees
	/// it; the hit player's client decides the hit, as with any hostile projectile). D0: a missing, dead or changed Sheriff
	/// ends it within <see cref="KeepAliveTicks"/> ticks (its timeLeft is only refreshed while he lives). D1: no allocation;
	/// a spark now and then, client-side.</para>
	/// </summary>
	public class SheriffStar : CogpunkProjectile
	{
		public const float OutSpeed = 9f;
		public const int OutTicks = 24;                     // about 13 tiles out
		public const float ReturnSpeed = 11f;
		public const float HomeSnap = 8f;
		public const int KeepAliveTicks = 3;
		public const int SpinTicks = 4, FastSpinTicks = 2;
		private const int Size = 26;

		private static Asset<Texture2D> glow;

		private int Slot => Math.Clamp((int)Projectile.ai[1], 0, Sheriff.StarCount - 1);
		private ref float Mode => ref Projectile.localAI[0];        // 0 home, 1 out, 2 back (each side's own copy)
		private bool Flying => Mode != 0f;

		public override void SetStaticDefaults() {
			Main.projFrames[Type] = R.StarSpin * 2;                 // spin frames, then the same with the rim lit
			glow = DepthLayers.RequestOptional(Texture + "_Glow");
		}

		public override void Unload() {
			glow = null;
		}

		public override void SetDefaults() {
			Projectile.width = 20;
			Projectile.height = 20;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;                         // it always finds its way back over the hat
			Projectile.ignoreWater = true;
			Projectile.timeLeft = KeepAliveTicks;
			Projectile.aiStyle = -1;
		}

		private bool TryGetSheriff(out Sheriff sheriff) {
			sheriff = null;
			int index = (int)Projectile.ai[0];
			if (index < 0 || index >= Main.maxNPCs) {
				return false;
			}
			NPC npc = Main.npc[index];
			if (!npc.active || npc.ModNPC is not Sheriff s) {
				return false;
			}
			sheriff = s;
			return true;
		}

		public override void AI() {
			if (!TryGetSheriff(out Sheriff sheriff)) {
				return;                                             // no refresh: it fades out of existence in a few ticks
			}
			Projectile.timeLeft = KeepAliveTicks;
			NPC npc = sheriff.NPC;
			int clock = (int)sheriff.StarClock;
			int launch = Sheriff.StarTelegraph + Slot * Sheriff.StarStagger;
			Vector2 home = sheriff.StarHome(Slot);
			if (clock == launch && npc.HasValidTarget && Mode == 0f) {
				Player target = Main.player[npc.target];
				Projectile.velocity = (target.Center - Projectile.Center).SafeNormalize(Vector2.UnitY) * OutSpeed;
				Mode = 1f;
			}
			if (Mode == 1f && (clock >= launch + OutTicks || clock < launch)) {
				Mode = 2f;
			}
			if (Mode == 2f) {
				Vector2 to = home - Projectile.Center;
				float distance = to.Length();
				if (distance < HomeSnap) {
					Mode = 0f;
				}
				else {
					Projectile.velocity = to / distance * Math.Min(ReturnSpeed, distance);
				}
			}
			if (Mode == 0f) {
				Projectile.velocity = Vector2.Zero;
				Projectile.Center = home;
			}
			MathSafety.Sanitize(ref Projectile.velocity);
			bool telegraph = Mode == 0f && clock < launch && clock > 0;
			int spin = Flying || telegraph ? FastSpinTicks : SpinTicks;
			int turn = (int)(Main.GameUpdateCount / (uint)spin + (uint)Slot) % R.StarSpin;
			Projectile.frame = turn + (telegraph ? R.StarSpin : 0);
			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, 0.45f, 0.3f, 0.1f);
				if (Flying && Main.rand.NextBool(3) && CogpunkClientConfig.RollEffect()
					&& SafeSpawn.TryNewDust(Projectile.Center - new Vector2(4f), 8, 8, DustID.GoldFlame, out Dust spark)) {
					spark.noGravity = true;
					spark.velocity *= 0.3f;
				}
			}
		}

		public override bool CanHitPlayer(Player target) => Flying;

		public override void OnKill(int timeLeft) {
			if (Main.dedServ) {
				return;
			}
			for (int i = 0; i < 6; i++) {
				SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.GoldCoin, out _);
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			Rectangle source = new(0, Math.Clamp(Projectile.frame, 0, R.StarSpin * 2 - 1) * (Size + 2), Size, Size);
			Vector2 at = (Projectile.Center - Main.screenPosition - new Vector2(Size * 0.5f)).Floor();
			Main.EntitySpriteDraw(texture, at, source, Color.Lerp(lightColor, Color.White, 0.5f), 0f, Vector2.Zero, 1f, SpriteEffects.None);
			if (glow?.IsLoaded == true) {
				Main.EntitySpriteDraw(glow.Value, at, source, Color.White, 0f, Vector2.Zero, 1f, SpriteEffects.None);
			}
			return false;
		}
	}
}
