using System;
using Cogpunk.Content.Bosses.Jadey.Buffs;
using Cogpunk.Content.Bosses.Jadey.Items;
using Cogpunk.Content.Gems;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Content.Bosses.Jadey
{
	/// <summary>
	/// The <see cref="JadeShaperPendant"/>'s save (user-set 2026-11-17). A hit that would kill the wearer turns them into a jade
	/// statue instead (<see cref="JadeStatue"/>, <see cref="JadeShaperPendant.StatueTicks"/> ticks) and starts the
	/// <see cref="JadeShaperPendant.CooldownTicks"/> recharge (<see cref="JadeShaperRest"/>). The statue can't move, jump, hook,
	/// mount or use anything (its controls are cleared like the jade curse's petrification, <see cref="JadeCursePlayer"/>), takes
	/// no damage, but is still knocked back ("to ensure that fights like the wall of flesh still works").
	/// <list type="bullet">
	/// <item>Lethal, dodgeable hits: <see cref="ConsumableDodge"/> (decompiled <c>Player.Hurt</c>: asked on the hurt player's own
	/// client after vanilla's Black Belt, Brain of Confusion and Shadow Dodge, with the final damage), so another dodge that would
	/// have saved the player doesn't spend the pendant.</item>
	/// <item>Every other death (undodgeable hits, drowning, the Wall's tongue: vanilla's <c>Player.KillMe</c>):
	/// <see cref="PreKill"/>, which refuses the death and leaves 1 life.</item>
	/// <item>While a statue, dodgeable hits do no damage but push (<see cref="FreeDodge"/> + <see cref="Push"/>: vanilla's knockback,
	/// decompiled <c>Player.Hurt</c>: velocity = knockback x direction sideways and knockback x 7/9 up, not on a minecart; at most
	/// once every <see cref="PushGateTicks"/> ticks, vanilla's immunity after a 1-damage hit, since a dodged hit gives no immunity
	/// and contact would push every tick);
	/// undodgeable ones do nothing (<see cref="ImmuneTo"/>); and the statue can't die (<see cref="PreKill"/>).</item>
	/// </list>
	/// <para>D2: all of it runs on the wearer's own client (vanilla asks only there); the buffs it adds reach everyone through
	/// vanilla's buff sync, so every client draws the statue and plays its crack; the push is sent like vanilla's knockback
	/// (message 13), the restored life like a hurt's (message 16). D0/D1: no allocation; dust through <see cref="SafeSpawn"/>.</para>
	/// </summary>
	public sealed class JadeShaperPlayer : ModPlayer
	{
		public const int PushGateTicks = 20;              // vanilla's immunity after a 1-damage hit: a push carries the statue
		                                                   // ~5 tiles, ahead of the Wall of Flesh, without pinballing it off normal foes

		/// <summary>Set every tick by the equipped pendant.</summary>
		public bool Pendant;
		private bool wasStatue;
		private int pushGate;

		public bool Statue => Player.HasBuff(ModContent.BuffType<JadeStatue>());

		public bool Resting => Player.HasBuff(ModContent.BuffType<JadeShaperRest>());

		public override void ResetEffects() {
			Pendant = false;
			if (pushGate > 0) {
				pushGate--;
			}
		}

		public override bool ImmuneTo(PlayerDeathReason damageSource, int cooldownCounter, bool dodgeable) => !dodgeable && Statue;

		public override bool FreeDodge(Player.HurtInfo info) {
			if (!Statue) {
				return false;
			}
			Push(info);
			return true;
		}

		public override bool ConsumableDodge(Player.HurtInfo info) {
			if (!Pendant || Resting || Player.whoAmI != Main.myPlayer || info.Damage < Player.statLife) {
				return false;
			}
			Enshrine();
			Push(info);
			return true;
		}

		public override bool PreKill(double damage, int hitDirection, bool pvp, ref bool playSound, ref bool genDust, ref PlayerDeathReason damageSource) {
			if (Player.whoAmI != Main.myPlayer) {
				return true;                               // only the owner decides; remote copies follow its real death message
			}
			if (!Statue) {
				if (!Pendant || Resting) {
					return true;
				}
				Enshrine();
			}
			Player.statLife = Math.Max(Player.statLife, 1);
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				NetMessage.SendData(MessageID.PlayerLifeMana, -1, -1, null, Player.whoAmI);
			}
			return false;
		}

		private void Enshrine() {
			Player.AddBuff(ModContent.BuffType<JadeStatue>(), JadeShaperPendant.StatueTicks);
			Player.AddBuff(ModContent.BuffType<JadeShaperRest>(), JadeShaperPendant.CooldownTicks);
		}

		/// <summary>Vanilla's knockback for a hit the statue shrugged off.</summary>
		private void Push(Player.HurtInfo info) {
			if (pushGate > 0 || info.Knockback == 0f || info.HitDirection == 0 || (Player.mount.Active && Player.mount.Cart)) {
				return;
			}
			pushGate = PushGateTicks;
			Player.velocity.X = info.Knockback * info.HitDirection;
			Player.velocity.Y = info.Knockback * -7f / 9f;
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				NetMessage.SendData(MessageID.PlayerControls, -1, -1, null, Player.whoAmI);
			}
		}

		/// <summary>The owner: a statue can't move, jump, hook, mount or use anything (inventory and chat keys stay).</summary>
		public override void SetControls() {
			if (!Statue) {
				return;
			}
			Player.controlLeft = Player.controlRight = Player.controlUp = Player.controlDown = false;
			Player.controlJump = Player.controlUseItem = Player.controlUseTile = Player.controlThrow = false;
			Player.controlHook = Player.controlMount = Player.controlQuickHeal = Player.controlQuickMana = false;
			Player.controlSmart = false;
		}

		/// <summary>Every client: the turn to jade and back (from the synced buff): a crack and shards.</summary>
		public override void PostUpdate() {
			bool stone = Statue;
			if (stone == wasStatue) {
				return;
			}
			wasStatue = stone;
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(SoundID.Item27 with { Pitch = stone ? -0.6f : 0.15f, Volume = 0.9f }, Player.Center);
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			int count = stone ? 18 : 24;
			for (int i = 0; i < count; i++) {
				if (SafeSpawn.TryNewDust(Player.position, Player.width, Player.height, DustID.GemEmerald, out Dust d)) {
					d.velocity = Main.rand.NextVector2Circular(3.5f, 3.5f);
					d.noGravity = Main.rand.NextBool();
					d.scale = 1.3f;
				}
			}
		}

		/// <summary>Every client: the statue is drawn jade green.</summary>
		public override void DrawEffects(PlayerDrawSet drawInfo, ref float r, ref float g, ref float b, ref float a, ref bool fullBright) {
			if (drawInfo.shadow != 0f || !Statue) {
				return;
			}
			r *= JadeCurseNPC.Jade.R / 255f;
			g *= JadeCurseNPC.Jade.G / 255f;
			b *= JadeCurseNPC.Jade.B / 255f;
		}
	}
}
