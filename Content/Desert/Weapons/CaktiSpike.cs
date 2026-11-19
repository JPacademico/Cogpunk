using System;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Desert.Weapons
{
	/// <summary>
	/// The <see cref="Cakti"/>'s spike (2026-11-17): a thin cactus needle that flies dead straight and fast, sticks in the first
	/// enemy it hits (<see cref="Stuck"/>, for <see cref="StickTicks"/> ticks: user-set, 5 s) and, if that enemy dies with it in
	/// it, is flung out of the body in a random direction (<see cref="Flung"/>: "when the enemy dies it shoots the spikes that
	/// were on him everywhere"), hurting the next enemy it meets once. A flung spike never sticks again (D0 rule 4: no chains).
	/// An enemy holds at most <see cref="MaxStuck"/> of one player's spikes; a new one pushes the oldest out.
	/// <para><c>ai[0]</c>: the state; <c>ai[1]</c>: the enemy it is stuck in; <c>ai[2]</c>: its heading (one of
	/// <see cref="Headings"/> pre-rendered: never rotated at runtime). While stuck it rides the enemy at the offset kept in its
	/// velocity (<see cref="ShouldUpdatePosition"/> false), as ExampleMod 1.4.4's sticky javelin does.</para>
	/// <para>D2: a player's projectile: the owner sticks it (its hit) and flings it (it sees the enemy gone; the enemy's type is
	/// remembered so a new NPC in the slot doesn't count), each a <c>netUpdate</c>; every side rides and draws it from the synced
	/// state. D0: the enemy index is checked every tick; finite lifetimes in every state; the per-enemy cap's scan runs once per
	/// stick. D1: no allocation.</para>
	/// </summary>
	public class CaktiSpike : CogpunkProjectile
	{
		public const float Flying = 0f, Stuck = 1f, Flung = 2f;
		public const int StickTicks = 300;                   // user-set: 5 s
		public const int MaxStuck = 12;                      // my call: one player's spikes in one enemy
		public const float FlingSpeed = 9f;
		public const int FlingTicks = 50;
		public const float Embed = 0.7f;                     // a stuck spike sits this far from the centre's offset at impact
		public const int Headings = 16, Cell = 18, Gap = 2;

		private ref float State => ref Projectile.ai[0];
		private ref float Victim => ref Projectile.ai[1];
		private ref float Heading => ref Projectile.ai[2];
		private ref float VictimType => ref Projectile.localAI[0];

		public override void SetDefaults() {
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = -1;
			Projectile.tileCollide = true;
			Projectile.timeLeft = 180;
			Projectile.extraUpdates = 1;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
		}

		public override bool ShouldUpdatePosition() => State != Stuck;

		public override void AI() {
			Projectile.extraUpdates = State == Flying ? 1 : 0;      // every side, from the synced state
			if (State == Stuck) {
				int v = (int)Victim;
				NPC npc = v >= 0 && v < Main.maxNPCs ? Main.npc[v] : null;
				bool alive = npc != null && npc.active && npc.life > 0 && (VictimType == 0f || npc.type == (int)VictimType);
				if (!alive) {
					if (Projectile.owner == Main.myPlayer) {
						Fling();
					}
					return;
				}
				Projectile.Center = npc.Center + Projectile.velocity;
				Projectile.gfxOffY = npc.gfxOffY;
				return;
			}
			float angle = Projectile.velocity.ToRotation();
			if (float.IsFinite(angle)) {
				Heading = ((int)MathF.Round(angle / MathHelper.TwoPi * Headings) % Headings + Headings) % Headings;
			}
		}

		/// <summary>The owner: out of a dead enemy, in a random direction (a flung spike hurts once and never sticks).</summary>
		private void Fling() {
			State = Flung;
			float a = Main.rand.NextFloat(MathHelper.TwoPi);
			Projectile.velocity = new Vector2(MathF.Cos(a), MathF.Sin(a)) * FlingSpeed;
			Projectile.timeLeft = FlingTicks;
			Projectile.tileCollide = true;
			Array.Clear(Projectile.localNPCImmunity);
			Projectile.netUpdate = true;
		}

		public override bool? CanHitNPC(NPC target) => State == Stuck ? false : null;

		public override bool? CanDamage() => State == Stuck ? false : null;

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone) {
			if (State == Flung) {
				Projectile.Kill();
				return;
			}
			if (State != Flying || Projectile.owner != Main.myPlayer) {
				return;
			}
			if (!target.active || target.life <= 0) {
				Projectile.Kill();                                  // the hit killed it: nothing to stick in
				return;
			}
			State = Stuck;
			Victim = target.whoAmI;
			VictimType = target.type;
			Projectile.velocity = (Projectile.Center - target.Center) * Embed;
			Projectile.timeLeft = StickTicks;
			Projectile.tileCollide = false;
			Projectile.netUpdate = true;
			PushOutOldest(target.whoAmI);
		}

		/// <summary>The owner: at most <see cref="MaxStuck"/> of their spikes in one enemy; past it the oldest drops out.</summary>
		private void PushOutOldest(int victim) {
			int count = 0, oldest = -1, oldestLeft = int.MaxValue;
			foreach (Projectile p in Main.ActiveProjectiles) {
				if (p.type != Type || p.owner != Projectile.owner || p.ai[0] != Stuck || (int)p.ai[1] != victim) {
					continue;
				}
				count++;
				if (p.whoAmI != Projectile.whoAmI && p.timeLeft < oldestLeft) {
					oldestLeft = p.timeLeft;
					oldest = p.whoAmI;
				}
			}
			if (count > MaxStuck && oldest >= 0) {
				Main.projectile[oldest].Kill();
			}
		}

		public override void OnKill(int timeLeft) {
			if (Main.dedServ || State == Stuck || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Dig with { Pitch = 0.6f, Volume = 0.35f, MaxInstances = 3 }, Projectile.Center);
			for (int i = 0; i < 2; i++) {
				if (SafeSpawn.TryNewDust(Projectile.position, Projectile.width, Projectile.height, DustID.JunglePlants, out Dust d)) {
					d.velocity *= 0.4f;
					d.scale = 0.7f;
				}
			}
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			int h = Math.Clamp((int)Heading, 0, Headings - 1);
			Rectangle frame = new(0, h * (Cell + Gap), Cell, Cell);
			if (frame.Bottom > tex.Height) {
				return false;
			}
			Vector2 at = Projectile.Center - Main.screenPosition + new Vector2(0f, Projectile.gfxOffY);
			Main.EntitySpriteDraw(tex, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), frame, lightColor, 0f, new Vector2(Cell / 2f), 1f,
				SpriteEffects.None);
			return false;
		}
	}
}
