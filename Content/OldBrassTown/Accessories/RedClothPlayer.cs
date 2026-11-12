using System;
using System.IO;
using Cogpunk.Core.Configs;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace Cogpunk.Content.OldBrassTown.Accessories
{
	/// <summary>
	/// The <see cref="RedCloth"/>'s dodge: while the cloth is worn and not recharging (<see cref="RedClothCooldown"/>), the next
	/// enemy touch is cancelled (<see cref="ConsumableDodge"/>), the wearer gets <see cref="RedCloth.ImmuneTicks"/> ticks of
	/// immunity against everything (as vanilla's dodges give, decompiled <c>Player.ShadowDodge</c>:
	/// <c>SetImmuneTimeForAllTypes</c>; the user's 0.7 s whatever else is worn) and the recharge starts.
	/// <para>A touch is what vanilla's enemy collision reports: <c>Player.Update_NPCCollision</c> hurts with
	/// <c>PlayerDeathReason.ByNPC</c> (an NPC, no projectile); a projectile's hit names its projectile and isn't dodged.
	/// vanilla's own dodges run first (decompiled <c>Player.Hurt</c>: the Black Belt, the Brain of Confusion and Shadow Dodge,
	/// then the mods' <c>ConsumableDodge</c>), so the cloth stays ready when one of them takes the hit; an undodgeable hit
	/// never reaches it.</para>
	/// <para>D2: vanilla resolves a touch on the touched player's own client, the only one that calls <c>ConsumableDodge</c>;
	/// the recharge is a buff (synced by vanilla) and the dodge's looks go to the other clients through
	/// <see cref="RedClothPacket"/>. D1: a flag, a buff lookup per hit. D0: the source index is range-checked.</para>
	/// </summary>
	public sealed class RedClothPlayer : ModPlayer
	{
		private const int Threads = 14;
		private static readonly SoundStyle FlapSound = SoundID.Item32 with { Pitch = 0.35f, Volume = 0.9f, PitchVariance = 0.1f };
		private static readonly SoundStyle SwishSound = SoundID.Item1 with { Pitch = 0.5f, Volume = 0.7f };
		public static readonly Color ClothRed = new(206, 74, 56);

		/// <summary>Set by the accessory every tick.</summary>
		public bool Cloth;

		public override void ResetEffects() {
			Cloth = false;
		}

		/// <summary>Worn and not recharging.</summary>
		public bool Ready => Cloth && !Player.HasBuff(ModContent.BuffType<RedClothCooldown>());

		/// <summary>An enemy's body touching the player (vanilla's collision hurts with <c>PlayerDeathReason.ByNPC</c>).</summary>
		public static bool IsTouch(in Player.HurtInfo info) {
			PlayerDeathReason source = info.DamageSource;
			if (source == null || info.PvP) {
				return false;
			}
			int npc = source.SourceNPCIndex;
			return npc >= 0 && npc < Main.maxNPCs && source.SourceProjectileLocalIndex < 0 && source.SourceProjectileType <= 0;
		}

		public override bool ConsumableDodge(Player.HurtInfo info) {
			if (!Ready || !IsTouch(info)) {
				return false;
			}
			Player.SetImmuneTimeForAllTypes(RedCloth.ImmuneTicks);
			Player.AddBuff(ModContent.BuffType<RedClothCooldown>(), RedCloth.RechargeTicks);
			int from = info.DamageSource.SourceNPCIndex;
			int side = Main.npc[from].Center.X < Player.Center.X ? -1 : 1;
			Effects(Player, side);
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				ModContent.GetInstance<RedClothPacket>().Send(Player.whoAmI, side);
			}
			return true;
		}

		/// <summary>Every client: the cloth whips across where the enemy came from, "Ole!", a flap and a swish; the immunity's
		/// blink on another client's copy of the player.</summary>
		public static void Effects(Player player, int side) {
			if (player.whoAmI != Main.myPlayer) {
				player.SetImmuneTimeForAllTypes(RedCloth.ImmuneTicks);   // only the blink: hits on them are their client's
			}
			if (Main.dedServ) {
				return;
			}
			SoundEngine.PlaySound(FlapSound, player.Center);
			SoundEngine.PlaySound(SwishSound, player.Center);
			CombatText.NewText(player.Hitbox, ClothRed, Language.GetTextValue("Mods.Cogpunk.Items.RedCloth.Ole"), dramatic: true);
			if (!CogpunkClientConfig.RollEffect()) {
				return;
			}
			for (int i = 0; i < Threads; i++) {                 // the cloth's sweep: a red arc on the enemy's side
				float a = MathHelper.Lerp(-1.2f, 1.2f, i / (float)(Threads - 1));
				Vector2 arc = new(side * MathF.Cos(a) * 22f, MathF.Sin(a) * 26f);
				if (SafeSpawn.TryNewDust(player.Center + arc - new Vector2(3f), 6, 6, DustID.RedTorch, out Dust d)) {
					d.noGravity = true;
					d.velocity = new Vector2(-side * 1.5f, MathF.Sin(a) * -2.5f);
					d.scale = 1.2f;
				}
			}
		}
	}

	/// <summary>
	/// Dodging client -> server -> the other clients: a Red Cloth dodge happened (player, the enemy's side), so they show it.
	/// Two bytes. The server relays only a dodge for the sender's own player (D0: the index is validated).
	/// </summary>
	public sealed class RedClothPacket : CogpunkPacket
	{
		public void Send(int player, int side, int ignoreClient = -1) {
			ModPacket packet = Begin();
			packet.Write((byte)player);
			packet.Write((sbyte)(side >= 0 ? 1 : -1));
			packet.Send(-1, ignoreClient);
		}

		public override void Receive(BinaryReader reader, int sender) {
			int player = reader.ReadByte();
			int side = reader.ReadSByte();
			if (player >= Main.maxPlayers || !Main.player[player].active) {
				SafeLog.Warn("Net.RedCloth.BadPlayer", "Dropped a Red Cloth packet for player {0}.", player);
				return;
			}
			if (Main.netMode == NetmodeID.Server) {
				if (player != sender) {
					SafeLog.Warn("Net.RedCloth.Spoof", "Dropped a Red Cloth packet from client {0} for player {1}.", sender, player);
					return;
				}
				Send(player, side, ignoreClient: sender);
				return;
			}
			if (player != Main.myPlayer) {
				RedClothPlayer.Effects(Main.player[player], side);
			}
		}
	}
}
