using System;
using System.IO;
using Cogpunk.Core.Networking;
using Cogpunk.Core.Safety;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace Cogpunk.Core.Combat
{
	/// <summary>
	/// Directional melee (user rule, 2026-11-26, 0.2.3: "our melee weapons for the mod must have directional swings that actualy
	/// track cursor position (like the diretional melee, and not like base terraria limited left and right locked swing
	/// position)"; the design is docs/design/melee-mechanics-study.md §3, built with public hooks only). A swing's arc (vanilla's,
	/// <see cref="VanillaArc"/>, or a weapon's own curve) is turned by the <b>aim</b>: the angle from the wielder to the cursor in
	/// the facing frame (0 ahead, + down), held to ±<see cref="MaxAim"/>. As each swing starts the wielder turns to the
	/// cursor's side (vanilla turns a player only for items that shoot, decompiled <c>Player.ItemCheck_Shoot</c>), and through the
	/// swing the aim follows the cursor (<see cref="Follow"/> of the way a tick); the side holds until the next swing (a turn in
	/// mid-swing would mirror the arc), and a cursor behind the wielder counts by its height only.
	/// <para>How a weapon uses it, from its <c>UseStyle</c> (it runs after vanilla posed the swing, decompiled
	/// <c>ItemCheck_ApplyUseStyle</c>, and before the melee hits are checked): <see cref="Aim"/> once a tick, the arc plus the aim
	/// posed with <see cref="SwingPose"/> (<see cref="PoseHeld"/> for a sprite the game draws), then <see cref="Note"/>; its hits
	/// along the drawn blade (<see cref="HeldBladeHits"/>, swept from the last tick's <see cref="Rotation"/>) and its
	/// <c>UseItemHitbox</c> the blade's bounds (<see cref="HeldBladeBounds"/>). Knockback follows the facing, as vanilla's.</para>
	/// <para>D2: the owner's aim reaches the others through <see cref="DirectionalAimPacket"/> (the player and the aim in 1.5°
	/// steps): at once when a swing starts, then at most every <see cref="SyncTicks"/> ticks while it turns more than a step; the
	/// others ease to it (<see cref="RemoteFollow"/>), so a late packet never snaps the pose; the facing comes with the player's
	/// own sync. Everything else (the arc, the pose, the ring of angles) is worked out on every side from the synced use. D0:
	/// a non-finite cursor or pose is ignored; the packet's player index and value are checked. D1: arithmetic, a fixed ring of
	/// <see cref="History"/> angles a player made on its first swing, a packet only while the aim changes.</para>
	/// </summary>
	public static class DirectionalSwing
	{
		/// <summary>~75°: the arc never turns past straight up or straight down.</summary>
		public const float MaxAim = 1.3f;
		/// <summary>Of the way to the cursor a tick, the owner (it tracks the cursor through the swing).</summary>
		public const float Follow = 0.35f;
		/// <summary>Of the way to the owner's last sent aim a tick, everyone else.</summary>
		public const float RemoteFollow = 0.5f;
		public const int SyncTicks = 3;
		/// <summary>The packet's unit (1.5°): ±<see cref="MaxAim"/> fits an sbyte.</summary>
		public const float SyncStep = MathHelper.Pi / 120f;
		public const int History = 12;

		/// <summary>Vanilla's sword swing in the facing frame (decompiled <c>ItemCheck_ApplyUseStyle_Inner</c>, useStyle 1:
		/// <c>itemRotation = (itemAnimation / max - 0.5) x -direction x 3.5 - direction x 0.3</c>, the blade 45° under it): from
		/// behind the head (<see cref="VanillaStart"/>, -162°) to ahead under the horizon (<see cref="VanillaEnd"/>, +38°),
		/// linear over the use.</summary>
		public const float VanillaStart = -1.75f - 0.3f - MathHelper.PiOver4, VanillaEnd = 1.75f - 0.3f - MathHelper.PiOver4;

		/// <summary>Vanilla's arc at <paramref name="done"/> of the use.</summary>
		public static float VanillaArc(float done) => MathHelper.Lerp(VanillaStart, VanillaEnd, MathHelper.Clamp(done, 0f, 1f));

		/// <summary>0..1: how far <paramref name="player"/>'s use has run, <paramref name="ticksBack"/> ticks ago.</summary>
		public static float Done(Player player, int ticksBack = 0) {
			int max = Math.Max(1, player.itemAnimationMax);
			return MathHelper.Clamp(1f - (player.itemAnimation + ticksBack) / (float)max, 0f, 1f);
		}

		/// <summary>Every side, once a tick of a directional swing (from the weapon's <c>UseStyle</c>): advances and returns the
		/// aim to add to the arc. The owner turns to the cursor's side as a swing starts and follows the cursor; the others ease
		/// to the owner's.</summary>
		public static float Aim(Player player) => player.GetModPlayer<DirectionalSwingPlayer>().Tick(player);

		/// <summary>The aim now, without advancing it (drawing, hits, effects).</summary>
		public static float AimOf(Player player) => player.GetModPlayer<DirectionalSwingPlayer>().Offset;

		/// <summary>Every side, after posing a tick of the swing: its <c>itemRotation</c> kept for the swept hits and the trails.</summary>
		public static void Note(Player player) => player.GetModPlayer<DirectionalSwingPlayer>().Note(player);

		/// <summary>The swing's <c>itemRotation</c> <paramref name="ticksBack"/> ticks ago (no further back than its first tick);
		/// <paramref name="fallback"/> before any is noted.</summary>
		public static float Rotation(Player player, int ticksBack, float fallback) => player.GetModPlayer<DirectionalSwingPlayer>().Rotation(ticksBack, fallback);

		/// <summary>Ticks of this swing noted so far (at most <see cref="History"/>).</summary>
		public static int Noted(Player player) => player.GetModPlayer<DirectionalSwingPlayer>().Noted;

		/// <summary>Poses a sprite the game draws in a swing (held by its bottom corner at <c>itemLocation</c>, turned by
		/// <c>itemRotation</c>: decompiled <c>DrawPlayer_27_HeldItem</c>) along <paramref name="facing"/>: the arm along the blade
		/// (<see cref="SwingPose.Apply"/>), then the corner moved back along the blade so the hand holds the sprite's grip,
		/// <paramref name="gripFromCorner"/> px up it at scale 1.</summary>
		public static void PoseHeld(Player player, float facing, float gripFromCorner, float scale) {
			if (!float.IsFinite(facing)) {
				return;
			}
			SwingPose.Apply(player, facing);
			if (gripFromCorner != 0f) {
				Vector2 along = SwingPose.BladeDirection(player, facing);
				Vector2 at = player.itemLocation - along * (gripFromCorner * scale);
				if (MathSafety.IsFinite(at)) {
					player.itemLocation = at;
				}
			}
		}

		/// <summary>The blade the game draws at <paramref name="itemRotation"/> (held by its corner at <c>itemLocation</c>), from
		/// <paramref name="from"/> to <paramref name="to"/> px along it, <paramref name="radius"/> thick, touches <paramref name="box"/>.</summary>
		public static bool HeldBladeHits(Player player, float itemRotation, float from, float to, float radius, Rectangle box) {
			Vector2 dir = SwingPose.HeldBladeDirection(player, itemRotation);
			return SwingPose.CapsuleHitsRect(player.itemLocation + dir * from, player.itemLocation + dir * to, radius, box);
		}

		/// <summary>The drawn blade at this tick's angle, halfway to the last tick's and at the last tick's (a fast blade turns
		/// 20-30° a tick: no enemy slips between two poses).</summary>
		public static bool HeldBladeSweepHits(Player player, float from, float to, float radius, Rectangle box) {
			float now = player.itemRotation;
			float before = Rotation(player, 1, now);
			return HeldBladeHits(player, now, from, to, radius, box) || HeldBladeHits(player, (now + before) * 0.5f, from, to, radius, box)
				|| HeldBladeHits(player, before, from, to, radius, box);
		}

		/// <summary>The drawn blade's bounds this tick, for <c>UseItemHitbox</c> (vanilla cuts grass and pots with it); false
		/// when the pose isn't finite.</summary>
		public static bool HeldBladeBounds(Player player, float from, float to, float radius, out Rectangle bounds) {
			Vector2 dir = SwingPose.HeldBladeDirection(player, player.itemRotation);
			Vector2 a = player.itemLocation + dir * from, b = player.itemLocation + dir * to;
			if (!MathSafety.IsFinite(a) || !MathSafety.IsFinite(b) || !float.IsFinite(radius)) {
				bounds = default;
				return false;
			}
			int left = (int)(MathF.Min(a.X, b.X) - radius), top = (int)(MathF.Min(a.Y, b.Y) - radius);
			bounds = new Rectangle(left, top, (int)(MathF.Abs(a.X - b.X) + 2f * radius), (int)(MathF.Abs(a.Y - b.Y) + 2f * radius));
			return true;
		}
	}

	/// <summary>A player's directional swing state (<see cref="DirectionalSwing"/>): the aim, the owner's last sent aim, and a
	/// ring of the swing's last <see cref="DirectionalSwing.History"/> item rotations.</summary>
	public sealed class DirectionalSwingPlayer : ModPlayer
	{
		/// <summary>The aim now (facing frame, radians).</summary>
		public float Offset;
		/// <summary>Everyone but the owner: the owner's last sent aim.</summary>
		public float Target;
		private float sent;
		private int sinceSent;
		private int lastAnimation;
		private float[] rotations;
		private int head, noted;

		public int Noted => noted;

		public float Tick(Player player) {
			bool start = player.ItemAnimationJustStarted || player.itemAnimation > lastAnimation;
			lastAnimation = player.itemAnimation;
			if (start) {
				noted = 0;                                     // a new swing: nothing behind it yet
			}
			if (player.whoAmI == Main.myPlayer && !Main.dedServ) {
				Vector2 to = Main.MouseWorld - player.MountedCenter;
				if (MathSafety.IsFinite(to) && to.LengthSquared() > 1f) {
					if (start) {
						player.ChangeDir(to.X < 0f ? -1 : 1);    // reaches the others with the player's own sync (message 13)
					}
					float want = MathHelper.Clamp(MathF.Atan2(to.Y * player.gravDir, MathF.Abs(to.X)), -DirectionalSwing.MaxAim, DirectionalSwing.MaxAim);
					Offset = start ? want : Offset + (want - Offset) * DirectionalSwing.Follow;
				}
				if (!float.IsFinite(Offset)) {
					Offset = 0f;
				}
				sinceSent++;
				if (Main.netMode == NetmodeID.MultiplayerClient
					&& (start || (sinceSent >= DirectionalSwing.SyncTicks && MathF.Abs(Offset - sent) >= DirectionalSwing.SyncStep))) {
					sent = Offset;
					sinceSent = 0;
					ModContent.GetInstance<DirectionalAimPacket>().Send(player.whoAmI, Offset);
				}
			}
			else {
				Offset = start || !float.IsFinite(Offset) ? Target : Offset + (Target - Offset) * DirectionalSwing.RemoteFollow;
			}
			return Offset;
		}

		public void Note(Player player) {
			rotations ??= new float[DirectionalSwing.History];
			head = (head + 1) % DirectionalSwing.History;
			rotations[head] = player.itemRotation;
			noted = Math.Min(noted + 1, DirectionalSwing.History);
		}

		public float Rotation(int ticksBack, float fallback) {
			if (rotations == null || noted <= 0) {
				return fallback;
			}
			int k = Math.Clamp(ticksBack, 0, noted - 1);
			return rotations[(head - k + DirectionalSwing.History) % DirectionalSwing.History];
		}
	}

	/// <summary>A player's directional swing aim (<see cref="DirectionalSwing"/>): the player byte and the aim in 1.5° steps (an
	/// sbyte); the owner's client -> the server, which relays it to the others. D0: the index checked, a client speaks only
	/// for its own player, the value clamped.</summary>
	public sealed class DirectionalAimPacket : CogpunkPacket
	{
		public void Send(int player, float offset, int ignoreClient = -1) {
			if (Main.netMode == NetmodeID.SinglePlayer) {
				return;
			}
			int step = (int)MathF.Round(MathHelper.Clamp(offset, -DirectionalSwing.MaxAim, DirectionalSwing.MaxAim) / DirectionalSwing.SyncStep);
			ModPacket packet = Begin();
			packet.Write((byte)player);
			packet.Write((sbyte)Math.Clamp(step, sbyte.MinValue, sbyte.MaxValue));
			packet.Send(-1, ignoreClient);
		}

		public override void Receive(BinaryReader reader, int sender) {
			int player = reader.ReadByte();
			float offset = MathHelper.Clamp(reader.ReadSByte() * DirectionalSwing.SyncStep, -DirectionalSwing.MaxAim, DirectionalSwing.MaxAim);
			if (player < 0 || player >= Main.maxPlayers || (Main.netMode == NetmodeID.Server && player != sender)) {
				return;
			}
			Player p = Main.player[player];
			if (p == null || !p.active || player == Main.myPlayer) {
				return;
			}
			p.GetModPlayer<DirectionalSwingPlayer>().Target = offset;
			if (Main.netMode == NetmodeID.Server) {
				Send(player, offset, sender);                  // tell everyone else
			}
		}
	}
}
