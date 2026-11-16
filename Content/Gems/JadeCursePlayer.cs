using System;
using Cogpunk.Content.Gems.Buffs;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Gems
{
	/// <summary>
	/// The jade curse on players (user-set 2026-11-10: "jade golem should apply jade curse to the player on hit"): the
	/// <see cref="JadeCurseNPC"/> rules turned on the player. Every hit from a <see cref="Coghaven.NPCs.JadeGolem"/> (its
	/// body or its <see cref="Coghaven.Projectiles.JadeRay"/>) adds a stack (<see cref="JadeCurse"/>, refreshed for
	/// <see cref="JadeCurseNPC.CurseTicks"/>; the stacks go when it runs out); each stack makes the player's attacks
	/// <see cref="JadeCurseNPC.SlowPerStack"/> slower (all classes' attack speed). At <see cref="JadeCurseNPC.Stacks"/> the
	/// player turns to jade for <see cref="JadeCurseNPC.PetrifyTicks"/> ticks (<see cref="JadePetrified"/>): no moving,
	/// jumping, hooking or item use (it still falls), drawn jade green, still hurt as usual; then
	/// <see cref="JadeCurseNPC.WardTicks"/> ticks of <see cref="JadeWard"/>, when the curse can't take hold again.
	/// <para>D2: the hooks that land it run on the hit player's own client (decompiled tModLoader 1.4.4:
	/// <c>GlobalNPC.OnHitPlayer</c> "on the local client only", <c>ModProjectile.OnHitPlayer</c> "on the client taking
	/// damage"), so the stacks are that client's; the buffs it adds reach everyone through vanilla's buff sync (the local
	/// player's buff list is sent when it changes), and every client draws the jade and plays the turn from the buff. The
	/// controls are cleared on the owner (<see cref="SetControls"/>), whose synced controls then hold the statue still on
	/// every side. D0: guarded indices; no allocation; nothing spawned but client dust through <see cref="SafeSpawn"/>.</para>
	/// </summary>
	public sealed class JadeCursePlayer : ModPlayer
	{
		/// <summary>The local player's stacks (owner-side; others see the buff).</summary>
		public byte Stacks;
		private bool wasPetrified;

		public bool Petrified => Player.HasBuff(ModContent.BuffType<JadePetrified>());

		/// <summary>The hit player's own client: one stack; at the count, turned to jade and warded.</summary>
		public static void Hit(Player player) {
			if (player == null || !player.active || player.dead || player.whoAmI != Main.myPlayer) {
				return;
			}
			int curse = ModContent.BuffType<JadeCurse>(), stone = ModContent.BuffType<JadePetrified>(), ward = ModContent.BuffType<JadeWard>();
			if (player.buffImmune[curse] || player.HasBuff(ward) || player.HasBuff(stone)) {
				return;
			}
			JadeCursePlayer jade = player.GetModPlayer<JadeCursePlayer>();
			jade.Stacks = (byte)Math.Min(byte.MaxValue, jade.Stacks + 1);
			if (jade.Stacks >= JadeCurseNPC.Stacks) {
				jade.Stacks = 0;
				player.ClearBuff(curse);
				player.AddBuff(stone, JadeCurseNPC.PetrifyTicks);
				player.AddBuff(ward, JadeCurseNPC.WardTicks);
			}
			else {
				player.AddBuff(curse, JadeCurseNPC.CurseTicks);
			}
		}

		/// <summary>
		/// The hit player's own client: turned straight to jade, as if three stacks had landed (Jadey's petrify zone, user
		/// 2026-11-16: "petrify in jade any player on the area (like it has recieved 3 stacks of jade curse)"). The same rules
		/// as a third stack: the ward of a recent petrification, or immunity to the curse, keeps it off.
		/// </summary>
		public static void Petrify(Player player) {
			if (player == null || !player.active || player.dead || player.whoAmI != Main.myPlayer) {
				return;
			}
			int curse = ModContent.BuffType<JadeCurse>(), stone = ModContent.BuffType<JadePetrified>(), ward = ModContent.BuffType<JadeWard>();
			if (player.buffImmune[curse] || player.HasBuff(ward) || player.HasBuff(stone)) {
				return;
			}
			player.GetModPlayer<JadeCursePlayer>().Stacks = 0;
			player.ClearBuff(curse);
			player.AddBuff(stone, JadeCurseNPC.PetrifyTicks);
			player.AddBuff(ward, JadeCurseNPC.WardTicks);
		}

		/// <summary>Ticks of immunity a hit that sets <see cref="ShortImmunity"/> leaves (Jadey's lasers: "3 jade lasers in sequence
		/// (0.3 seconds between each) each dealing small damage but applying a stack of jade curse": vanilla's 40 ticks after a
		/// hit would let only the first of three lasers 18 ticks apart land; my call: 12).</summary>
		public const int ShortImmunityTicks = 12;

		/// <summary>Set on the hit player's own client by a hit whose immunity is short (its <c>OnHitPlayer</c> runs before vanilla
		/// sets the immunity, decompiled <c>Player.Hurt</c>: <c>PlayerLoader.OnHurt</c> first); <see cref="PostHurt"/> shortens it.</summary>
		public bool ShortImmunity;

		public override void PostHurt(Player.HurtInfo info) {
			if (!ShortImmunity) {
				return;
			}
			ShortImmunity = false;
			if (Player.immuneTime > ShortImmunityTicks) {
				Player.immuneTime = ShortImmunityTicks;
			}
			int slot = info.CooldownCounter;
			if (slot >= 0 && slot < Player.hurtCooldowns.Length && Player.hurtCooldowns[slot] > ShortImmunityTicks) {
				Player.hurtCooldowns[slot] = ShortImmunityTicks;
			}
		}

		public override void ResetEffects() {
			if (Stacks > 0 && !Player.HasBuff(ModContent.BuffType<JadeCurse>())) {
				Stacks = 0;
			}
		}

		public override void PostUpdateEquips() {
			if (Stacks > 0) {
				Player.GetAttackSpeed(DamageClass.Generic) -= JadeCurseNPC.SlowPerStack * Stacks;
			}
		}

		/// <summary>The owner: a statue can't move, jump, hook, mount or use anything (inventory and chat keys stay).</summary>
		public override void SetControls() {
			if (!Petrified) {
				return;
			}
			Player.controlLeft = Player.controlRight = Player.controlUp = Player.controlDown = false;
			Player.controlJump = Player.controlUseItem = Player.controlUseTile = Player.controlThrow = false;
			Player.controlHook = Player.controlMount = Player.controlQuickHeal = Player.controlQuickMana = false;
			Player.controlSmart = false;
		}

		public override void PreUpdateMovement() {
			if (Petrified) {
				Player.velocity.X = 0f;                       // it stands where it turned (gravity still pulls it down)
			}
		}

		/// <summary>Every client: the turn to jade and back (from the synced buff): a crack and shards.</summary>
		public override void PostUpdate() {
			bool stone = Petrified;
			if (stone == wasPetrified) {
				return;
			}
			wasPetrified = stone;
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item27 with { Pitch = stone ? -0.5f : 0.1f, Volume = 0.8f }, Player.Center);
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			int count = stone ? 10 : 16;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(Player.position, Player.width, Player.height, DustID.GemEmerald, out Dust d)) {
					d.velocity = Main.rand.NextVector2Circular(3f, 3f);
					d.noGravity = Main.rand.NextBool();
					d.scale = 1.2f;
				}
			}
		}

		/// <summary>Every client: jade green while turned to stone; a jade mote now and then while cursed.</summary>
		public override void DrawEffects(PlayerDrawSet drawInfo, ref float r, ref float g, ref float b, ref float a, ref bool fullBright) {
			if (drawInfo.shadow != 0f) {
				return;
			}
			if (Petrified) {
				r *= JadeCurseNPC.Jade.R / 255f;
				g *= JadeCurseNPC.Jade.G / 255f;
				b *= JadeCurseNPC.Jade.B / 255f;
				return;
			}
			if (Player.HasBuff(ModContent.BuffType<JadeCurse>()) && Main.rand.NextBool(10) && CogpunkClientConfig.RollEffect()
				&& SafeSpawn.TryNewDust(Player.position, Player.width, Player.height, DustID.GemEmerald, out Dust mote)) {
				mote.noGravity = true;
				mote.velocity = new Vector2(0f, -0.6f);
				mote.scale = 0.8f;
				drawInfo.DustCache.Add(mote.dustIndex);
			}
		}
	}
}
