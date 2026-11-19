using System;
using Cogpunk.Content.Bosses.Jadey.Buffs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Cogpunk.Core.Templates;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey.Weapons
{
	/// <summary>
	/// The <see cref="IncenseMace"/>'s right click (user-set 2026-11-18: "a quick incense aura effect around the player (25 tile
	/// area) that buffs allies that were on the area"): a ring of incense smoke rolls out from the wielder to
	/// <see cref="IncenseMace.AuraRadius"/> in <see cref="ExpandTicks"/> ticks and drifts away over <see cref="FadeTicks"/>.
	/// <para>D2, the blessing: the aura is an ordinary projectile, made by the owner and synced to every client; on its first
	/// tick on each client, that client blesses its own player (<see cref="IncenseBlessing"/>) if that player is alive, an ally
	/// of the wielder (anyone not an enemy in PvP, the wielder too) and within the radius of the aura's centre. Every player's
	/// buffs are theirs to set, so no packet and no buff on someone else's player; the buff's bonuses only matter to its owner's
	/// own attacks. D0: a finite life; no damage; the owner index is checked every tick. D1: the ring is <see cref="Puffs"/>
	/// small pre-drawn puffs placed on whole pixels (never scaled or turned), no allocation.</para>
	/// </summary>
	public class IncenseAura : CogpunkProjectile
	{
		public const int ExpandTicks = 24, FadeTicks = 21, LifeTicks = ExpandTicks + FadeTicks;
		public const int Puffs = 96;
		public const int PuffFrames = 4, PuffCell = 16, PuffGap = 2;

		private bool blessed;                                    // this client has checked its own player

		private ref float Age => ref Projectile.localAI[0];

		public override void SetDefaults() {
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = false;
			Projectile.hostile = false;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = LifeTicks;
		}

		public override bool? CanDamage() => false;

		public override void AI() {
			int o = Projectile.owner;
			if (o < 0 || o >= Main.maxPlayers || !Main.player[o].active) {
				Projectile.Kill();
				return;
			}
			Player owner = Main.player[o];
			Projectile.Center = owner.Center;                    // it rolls out round the wielder
			Projectile.velocity = Vector2.Zero;
			if (!blessed) {
				blessed = true;
				BlessLocalIfInReach(owner);
				Burst();
			}
			Age++;
			Lighting.AddLight(Projectile.Center, 0.35f, 0.3f, 0.45f);
		}

		/// <summary>This client's own player, blessed if alive, an ally of <paramref name="owner"/> and within the radius.</summary>
		private void BlessLocalIfInReach(Player owner) {
			if (Main.dedServ) {
				return;
			}
			Player me = Main.LocalPlayer;
			if (me == null || !me.active || me.dead || !Allies(me, owner)) {
				return;
			}
			if (Vector2.DistanceSquared(me.Center, Projectile.Center) > IncenseMace.AuraRadius * IncenseMace.AuraRadius) {
				return;
			}
			Bless(me);
		}

		/// <summary>Anyone not an enemy in PvP (vanilla's rule: both hostile and not on the same team).</summary>
		public static bool Allies(Player a, Player b) {
			return a.whoAmI == b.whoAmI || !(a.hostile && b.hostile && (a.team == 0 || a.team != b.team));
		}

		/// <summary>The blessing on <paramref name="player"/> (call on that player's own client).</summary>
		public static void Bless(Player player) {
			player.AddBuff(ModContent.BuffType<IncenseBlessing>(), IncenseMace.BlessingTicks);
		}

		/// <summary>Clients: a few golden motes off the censer as it opens (a one-shot burst).</summary>
		private void Burst() {
			if (Main.dedServ || !CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int k = 0; k < 12; k++) {
				if (SafeSpawn.TryNewDust(Projectile.Center - new Vector2(6f), 12, 12, DustID.GoldFlame, out Dust d)) {
					d.noGravity = true;
					d.velocity = Main.rand.NextVector2CircularEdge(3f, 3f);
					d.scale = 0.9f;
				}
			}
		}

		/// <summary>How far out the ring is (0..1, eased out) at <paramref name="age"/> ticks.</summary>
		public static float Reach(float age) {
			float t = Math.Clamp(age / ExpandTicks, 0f, 1f);
			return 1f - (1f - t) * (1f - t) * (1f - t);
		}

		/// <summary>The puff frame (0..3: curling up, full, thinning, wisp) at <paramref name="age"/> ticks.</summary>
		public static int PuffFrame(float age) {
			if (age < ExpandTicks * 0.4f) {
				return 0;
			}
			if (age < ExpandTicks) {
				return 1;
			}
			return age < ExpandTicks + FadeTicks * 0.5f ? 2 : 3;
		}

		public override bool PreDraw(ref Color lightColor) {
			Texture2D tex = TextureAssets.Projectile[Type].Value;
			int frame = Math.Clamp(PuffFrame(Age), 0, PuffFrames - 1);
			Rectangle source = new(0, frame * (PuffCell + PuffGap), PuffCell, PuffCell);
			if (source.Bottom > tex.Height) {
				return false;
			}
			float r = IncenseMace.AuraRadius * Reach(Age);
			float fade = Age < ExpandTicks ? 1f : Math.Clamp(1f - (Age - ExpandTicks) / FadeTicks, 0f, 1f);
			Color tint = Color.White * (0.85f * fade);
			Vector2 centre = Projectile.Center - Main.screenPosition;
			Vector2 origin = new(PuffCell * 0.5f);
			for (int k = 0; k < Puffs; k++) {
				float a = k * MathHelper.TwoPi / Puffs + (k % 2 == 0 ? 0f : 0.02f);
				float rr = r * (k % 3 == 0 ? 0.96f : 1f) + Age * 0.4f;     // a drifting, uneven edge
				Vector2 at = centre + new Vector2(MathF.Cos(a), MathF.Sin(a)) * rr;
				Main.EntitySpriteDraw(tex, new Vector2(MathF.Round(at.X), MathF.Round(at.Y)), source, tint, 0f, origin, 1f,
					k % 2 == 0 ? SpriteEffects.None : SpriteEffects.FlipHorizontally);
			}
			return false;
		}
	}
}
